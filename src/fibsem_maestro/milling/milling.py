import logging
import os

import numpy as np
from colorama import Fore

from fibsem_maestro.microscope_control.settings import load_settings, save_settings
from fibsem_maestro.microscope_control.microscope import GlobalMicroscope
from fibsem_maestro.tools.image_tools import template_matching, template_matching_subpixel, shift_sift
from fibsem_maestro.tools.support import ScanningArea, Point, Image
from fibsem_maestro.logger import Logger
from fibsem_maestro.settings import Settings

class Milling:
    def __init__(self):
        self._microscope = GlobalMicroscope().microscope_instance
        self.settings = Settings()
        self._fiducial_template = None
        self._fiducial_source_image_resolution = None
        self._fiducial_image = None
        self._subpixel_log = None
        self._similarity_map = None
        self._similarity = None
        self.position = None  # position [m] from milling start edge
        self.reset_position()

    def load_settings(self):
        """ Load microscope settings from file and set microscope for milling """
        settings_dir = self.settings('dirs', 'project')
        settings_file = self.settings('milling', 'settings_file')
        # set microscope
        try:
            logging.info('Microscope setting loading (fib)')
            load_settings(self._microscope, os.path.join(settings_dir, settings_file))
            self._microscope.beam = self._microscope.ion_beam  # set ion as default beam
            print(Fore.GREEN + 'Microscope fib settings applied')
        except Exception as e:
            logging.error('Loading of microscope fib settings failed! ' + repr(e))
            print(Fore.RED + 'Application of microscope fib settings failed!')
            raise Exception(e)

    def save_settings(self):
        """ Save microscope settings from file from microscope for milling"""
        settings_dir = self.settings('dirs', 'project')
        settings_file = self.settings('milling', 'settings_file')
        variables_to_save = self.settings('milling', 'variables_to_save')

        settings_to_save = variables_to_save
        try:
            save_settings(self._microscope,
                          settings=settings_to_save,
                          path=os.path.join(settings_dir, settings_file))
            print(Fore.GREEN + 'Microscope fib settings saved')
        except Exception as e:
            logging.error('Microscope fib settings saving error! ' + repr(e))
            print(Fore.RED + 'Microscope fib settings saving failed!')
            raise Exception(e)

    def init_position(self, img_shape):
        """ Return the initial edge of milling area (based on mill direction)"""
        leftop, [_, height] = ScanningArea.from_dict(self.settings('milling', 'milling_area')).to_img_coordinates(img_shape)
        direction = self.settings('milling', 'direction')

        return leftop.y if direction > 0 else leftop.y + height


    @property
    def fiducial_with_margin(self):
        """ Get fiducial area extended by the margin"""
        fiducial_area = ScanningArea.from_dict(self.settings('milling', 'fiducial_area'))
        fiducial_margin = self.settings('milling', 'fiducial_margin')
        if self._fiducial_template is None:
            raise ValueError('FIB template is not defined!')
        pixel_size = self._fiducial_template.pixel_size

        leftop_px, [width_px, height_px] = fiducial_area.to_img_coordinates(self._fiducial_source_image_resolution)
        leftop_px.x -= fiducial_margin / pixel_size
        leftop_px.y -= fiducial_margin / pixel_size
        width_px += 2*fiducial_margin / pixel_size
        height_px += 2*fiducial_margin / pixel_size

        return ScanningArea.from_image_coordinates(self._fiducial_source_image_resolution, leftop_px.x,
                                                   leftop_px.y, width_px, height_px)

    def milling_init(self):
        """ Save the milling fiducial """
        fiducial_rescan = self.settings('milling', 'fiducial_rescan')
        fiducial_area = ScanningArea.from_dict(self.settings('milling', 'fiducial_area'))
        minimal_similarity = self.settings('milling', 'minimal_similarity')
        slice_distance = self.settings('milling', 'slice_distance')
        blur = self.settings('milling', 'blur')

        image = None
        pixel_size = None
        # scan the fiducial several times
        for i in range(fiducial_rescan):
            self._microscope.ion_beam.scanning_area = fiducial_area
            acquired_image = self._microscope.ion_beam.grab_frame()
            if image is None:
                image = np.zeros([fiducial_rescan, acquired_image.width, acquired_image.height])
            image[i] = acquired_image
            pixel_size = acquired_image.pixel_size

        # all possible pairs of rescan images (without repetitions)
        pairs = [(a, b) for a in range(fiducial_rescan) for b in range(a + 1, fiducial_rescan)]
        for a, b in pairs:
            dx, dy, max_val = template_matching(image[a], image[b], blur)
            if max_val < minimal_similarity:
                print(Fore.RED, f'Fiducial scan failed. Scan similarity is too low.')
                logging.error(
                    f'Fiducial scan failed. Similarity {a + 1}-{b + 1} is {max_val}. Threshold is set to {minimal_similarity}')
                self._fiducial_template = None
                return
            drift = np.sqrt(dx**2+dy**2)
            if drift > slice_distance:
                print(Fore.RED, 'Fiducial scan failed. Drift is too high.')
                logging.error(
                    f'Fiducial scan failed. Drift is {drift} and slice distance is {slice_distance}')
                self._fiducial_template = None
                return

        # calculate template as mean of images
        self._fiducial_template = Image(np.mean(image, axis=0), pixel_size)
        Logger.create_log_fib(self)
        Logger.log_fib.save_fib_images()  # save template
        self.save_settings()  # save microscope settings
        self._fiducial_source_image_resolution = self._microscope.ion_beam.resolution

    def fiducial_correction(self):
        """ Set beam_shift & stage to mill """
        minimal_similarity = self.settings('milling', 'minimal_similarity')
        blur = self.settings('milling', 'blur')
        upscale = self.settings('milling', 'upscale')
        full_image_scans = self.settings('milling', 'full_image_scans')
        fiducial_scans = self.settings('milling', 'fiducial_scans')

        self._microscope.ion_beam.scanning_area = None
        for _ in range(full_image_scans):
            self._microscope.ion_beam.grab_frame()  # take one dummy - it increases robustness

        self._microscope.ion_beam.scanning_area = self.fiducial_with_margin
        for _ in range(fiducial_scans):
            fiducial_image = self._microscope.ion_beam.grab_frame()

        self._subpixel_log, dx, dy, sim, heatmap = template_matching_subpixel(fiducial_image, self._fiducial_template, blur, upsampling_factor=upscale, return_heatmap=True)
        # self._subpixel_log, dx, dy, sim, heatmap = shift_sift(fiducial_image, self._fiducial_template,
        #                                                                       blur)
        print(f'Fiducial found with similarity {sim}')
        if sim < minimal_similarity:
            print(Fore.RED, 'Fiducial localization failed')
            raise RuntimeError(f'Fiducial localization failed. Similarity: {sim}')

        # convert shift in the image to the beam shift
        shift_x = dx * fiducial_image.pixel_size
        shift_y = dy * fiducial_image.pixel_size

        logging.info(f'Milling correction: x={shift_x}, y={shift_y}')

        self._fiducial_image = fiducial_image  # log images
        self._similarity_map = heatmap
        self._similarity = sim
        Logger.log_params['fib_similarity'] = sim
        Logger.log_params['fib_driftcorr_x'] = float(shift_x)
        Logger.log_params['fib_driftcorr_y'] = float(shift_y)
        return shift_x, shift_y

    def reset_position(self):
        self.position = 0

    def milling(self, slice_number: int, milling_depth: float, shift_x=0, shift_y=0, shift_y_px=0):
        slice_distance = self.settings('milling', 'slice_distance')
        direction = self.settings('milling', 'direction')
        pattern_file = self.settings('milling', 'pattern_file')
        fiducial_update = self.settings('milling', 'fiducial_update')
        milling_area = ScanningArea.from_dict(self.settings('milling', 'milling_area'))
        fiducial_area = ScanningArea.from_dict(self.settings('milling', 'fiducial_area'))

        if self._fiducial_template is None:
            raise Exception('FIB template is not defined.')

        pixel_size = self._fiducial_template.pixel_size
        img_shape = self._microscope.ion_beam.resolution
        # final pattern position [px]
        pattern_position = self.init_position(img_shape) + (self.position+shift_y) / pixel_size

        left_top, size = milling_area.to_img_coordinates(img_shape)  # defined area
        left_top.y = pattern_position
        left_top.x += shift_x / pixel_size
        size[1] = slice_distance / pixel_size  # modify height

        # pixels in image -> meters
        left_top *= pixel_size
        size[0] *= pixel_size
        size[1] *= pixel_size
        left_top.y += shift_y_px # modify pattern y

        logging.debug('Pattern position: ' + str(left_top.y))
        Logger.log_params['fib_pattern_position'] = float(left_top.y)
        Logger.log_params['fib_pattern_position_raw'] = float(self.position)

        logging.info(f'Milling on position: {left_top} Size:{size[0]},{size[1]}')
        logging.info(f'Milling on raw position: {self.position} with additional shift {shift_y_px}px')
        direction = 'up' if direction < 0 else 'down'
        fov = [self._microscope.ion_beam.horizontal_field_width,
               self._microscope.ion_beam.vertical_field_width]

        self._microscope.ion_beam.rectangle_milling(pattern_file, leftop=left_top, size=size,
                                                    fov=fov,
                                                    depth=milling_depth,
                                                    direction=direction)

        # fiducial image rescan
        if self._similarity is not None and self._similarity < fiducial_update:
            print(Fore.YELLOW, 'Milling fiducial update')
            # convert to relative size
            shift_x_ratio = shift_x / fov[0]
            shift_y_ratio = shift_y / fov[1]
            # shift milling and fiducial area
            milling_area.leftop += Point(shift_x_ratio, shift_y_ratio)
            fiducial_area.leftop += Point(shift_x_ratio, shift_y_ratio)
            # save settings
            self.settings.set('milling', 'milling_area', value=milling_area.to_dict())
            self.settings.set('milling', 'fiducial_area', value=fiducial_area.to_dict())
            logging.warning(f'Milling fiducial update. Sim: {self._similarity}')
            self.milling_init()

    def __call__(self, slice_number: int):
        milling_enabled = self.settings('milling', 'enabled')
        scanning_frequency = self.settings('milling', 'scanning_frequency')
        milling_depth = self.settings('milling', 'milling_depth')
        relocate_pattern = self.settings('milling', 'relocate_pattern')
        slice_distance = self.settings('milling', 'slice_distance')
        direction = self.settings('milling', 'direction')
        milling_progress = self.settings('milling', 'milling_progress')

        if type(milling_depth) is float:
            milling_depth = [milling_depth]

        if type(relocate_pattern) is float or type(relocate_pattern) is int:
            relocate_pattern = [relocate_pattern]

        if milling_enabled:
            # increment milling pattern position by slice distance
            if milling_progress:
                self.position += slice_distance * direction

            self._microscope.beam = self._microscope.ion_beam  # switch to ion
            self.load_settings()  # apply fib settings

            final_shift_x, final_shift_y = 0, 0

            counter = 1
            for md, shift_y_px in zip(milling_depth, relocate_pattern):
                print(f'Milling number {counter}')
                counter += 1
                if slice_number % scanning_frequency == 0:
                    shiftx, shifty = self.fiducial_correction()  # set beam shift to correct drifts
                else:
                    shiftx, shifty = 0, 0

                # first run
                if final_shift_x == 0 and final_shift_y == 0:
                    final_shift_x, final_shift_y = shiftx, shifty

                self.milling(slice_number, md, shift_x=shiftx, shift_y = shifty, shift_y_px=shift_y_px)  # pattern milling

            # recentering
            # perform beam shift
            bs = Point(-final_shift_x, final_shift_y)
            self._microscope.add_beam_shift_with_verification(bs)

            self.save_settings()
            Logger.create_log_fib(self)
            Logger.log_fib.save_fib_images()  # save log images
