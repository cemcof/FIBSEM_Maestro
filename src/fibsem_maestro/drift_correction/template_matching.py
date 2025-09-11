import logging
import os
import numpy as np
import tifffile
from tifffile import TiffFile


from fibsem_maestro.microscope_control.microscope import GlobalMicroscope
from fibsem_maestro.tools.image_tools import template_matching
from fibsem_maestro.tools.support import Point, ScanningArea
from fibsem_maestro.logger import Logger
from fibsem_maestro.settings import Settings


class TemplateMatchingDriftCorrection:
    def __init__(self):
        self._microscope = GlobalMicroscope().microscope_instance
        self.settings = Settings()
        self.template_matching_image = None  # acquired template matching image
        self.heat_map = None

    def _prepare_image(self, img):
        # convert to 8bit if necessary
        if np.max(img) > 255:
            logging.warning('Template matching: Incorrect bit depth. Converting to 8 bit')
            img = (img / np.max(img) * 255).astype('uint8')
        return img

    def _calculate_shift(self, img, slice_number, area, shift_x, shift_y, index):
        """
        :param img: The image to be matched against the template image.
        :type img: numpy.ndarray
        :param area: The area of the image to be matched.
        :type area: Tuple[int, int, int, int]
        :param shift_x: A list to store the calculated X-shifts.
        :type shift_x: List[float]
        :param shift_y: A list to store the calculated Y-shifts.
        :type shift_y: List[float]
        :return: None

        This method calculates the shift between the template image and the given area of the input image. It uses
        template matching with the TM_CCOEFF_NORMED method to find the best match. The calculated shift values are
        stored in the shift_x and shift_y lists, and the new_areas list is updated with the shifted areas. The
        template image file is refreshed with the new area and saved.

        This method does not return any value.
        """
        min_confidence = self.settings('drift_correction', 'min_confidence')
        rescan = self.settings('drift_correction', 'rescan')
        blur = self.settings('drift_correction', 'blur')
        correction_margin = self.settings('drift_correction', 'correction_margin')
        template_matching_dir = self.settings('dirs', 'template_matching')
        template_image_name = os.path.join(template_matching_dir, f"dc_template_{index}.tiff")

        leftop, [width, height] = area.to_img_coordinates(img.shape)


        # Access metadata using TiffFile
        with TiffFile(template_image_name) as template_image:
            pixel_size = template_image.imagej_metadata['pixel_size']
            correction_margin = int(correction_margin / pixel_size)
            template_image = template_image.asarray()

            # padding for save cropping
            img_padded = np.pad(img, ((correction_margin, correction_margin), (correction_margin, correction_margin)), mode='constant', constant_values=0)
            x = leftop.x - correction_margin + correction_margin  # take padding into consideration
            y = leftop.y - correction_margin + correction_margin
            w = width + 2 * correction_margin
            h = height + 2 * correction_margin
            img_cropped = img_padded[x:x + w, y:y + h]

            # locate
            dx, dy, maxVal, heatmap = template_matching(template_image, img_cropped, blur=blur,return_heatmap=True)

            dx_m = dx * pixel_size
            dy_m = dy * pixel_size

            # log
            Logger.log_params[f"template_dx_{index}"] = dx_m
            Logger.log_params[f"template_dy_{index}"] = dy_m
            Logger.log_params[f"template_confidence_{index}"] = maxVal

            logging.info(f'Drift correction on template {index}: {dx_m},{dy_m}. Confidence: {maxVal}')

            # save shift
            if maxVal > min_confidence:
                # self._microscope.image_to_beam_shift.x is applied later
                shift_x.append(dx_m)
                shift_y.append(dy_m)
            else:
                logging.warning("Confidence too low")

            # refresh template
            new_x = int(leftop.x + dx)
            new_y = int(leftop.y + dy)

            self.templates_positions[index] = np.array([new_x, new_y, width, height])
            self.heat_map.append(heatmap)

            # rewrite template
            if slice_number > 0 and slice_number % rescan == 0:
                logging.warning('Template matching rescan.')
                new_template_image = img[new_x:new_x + width, new_y:new_y + height]
                self.save_template(new_template_image, index, img.pixel_size)


    def _shift_process(self, shift_x, shift_y):
        if len(shift_x) == 0:
            logging.error("Confidence of all templates is too low. Drift correction disabled")
            shift_x, shift_y = 0, 0

        # final shift
        shift_x = np.median(shift_x)
        shift_y = np.median(shift_y)

        shift_x *= self._microscope.beam.image_to_beam_shift.x  # beam shift X axis is reversed to image axis
        shift_y *= self._microscope.beam.image_to_beam_shift.y
        return shift_x, shift_y

    def update_templates(self, image):
        areas = self.settings('drift_correction', 'driftcorr_areas')

        if len(areas) == 0:
            logging.error('Template matching enabled but no areas not found. Drift correction disabled')
            return

        for i, area in enumerate(areas):
            leftop, [width, height] = ScanningArea.from_dict(area).to_img_coordinates(image.shape)
            template_image = image[leftop.x:leftop.x + width, leftop.y:leftop.y + height]
            self.save_template(template_image, i, image.pixel_size)

    def save_template(self, template_image, index, pixel_size):
        template_matching_dir = self.settings('dirs', 'template_matching')
        template_image_name = os.path.join(template_matching_dir, f"dc_template_{index}.tiff")

        template_image = self._prepare_image(template_image)
        tifffile.imwrite(template_image_name, template_image, imagej=True, metadata={'pixel_size': pixel_size})


    def __call__(self, img, slice_number):
        """
        :param img: The input image for drift correction.
        :param slice_number: The number of the image slice.
        :return: The point object representing the calculated beam shift.
        """
        areas = self.settings('drift_correction', 'driftcorr_areas')
        imaging_settings = self.settings('image', 'driftcorr')

        if len(areas) == 0:
            logging.error('Template matching enabled but no areas not found. Drift correction disabled')
            return

        self._microscope.apply_beam_settings(imaging_settings)
        logging.info(f"Acquiring drifcorr image")
        img = self._microscope.beam.grab_frame()

        shift_x = []
        shift_y = []
        # convert to 8b if needed
        self.template_matching_image = self._prepare_image(img)

        # store template positions
        self.templates_positions = [0] * len(areas)
        self.heat_map = []

        for i, area in enumerate(areas):
            # update shifts (shift_x, shift_y)
            self._calculate_shift(self.template_matching_image, slice_number, ScanningArea.from_dict(area), shift_x, shift_y, i)

        # log image with rectangles on areas positions
        Logger.create_log_template_matching(self)

        # calculate final shift
        shift_x, shift_y = self._shift_process(shift_x, shift_y)

        # log final shift
        Logger.log_params['template_matching_beam_shift_x'] = float(shift_x)
        Logger.log_params['template_matching_beam_shift_y'] = float(shift_y)
        Logger.log_template_matching.save_curve_image()  # save template matching log image (the rectangles of tm locations were drew after tm calculation)

        print(f'Template matching shift: {shift_x},{shift_x}')
        logging.info(f'Template matching shift: {shift_x},{shift_x}')

        # perform beam shift
        bs = Point(shift_x, shift_y)
        self._microscope.add_beam_shift_with_verification(bs)
        return bs

    def test(self):
        bs = self.__call__(None, slice_number=0)
        if bs is not None:
            print(bs.to_dict())