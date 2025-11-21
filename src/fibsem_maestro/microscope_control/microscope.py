import logging
import os

from scipy.spatial import distance

from fibsem_maestro.tools.support import StagePosition, Point, ScanningArea
from fibsem_maestro.microscope_control.autoscript_control import AutoscriptMicroscopeControl
from fibsem_maestro.settings import Settings

class GlobalMicroscope:
    _instance = None
    _microscope = None

    # Singleton construction
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GlobalMicroscope, cls).__new__(cls)
        return cls._instance

    @property
    def microscope_instance(self):
        return self._microscope

    @microscope_instance.setter
    def microscope_instance(self, value):
        self._microscope = value


def create_microscope():
    settings = Settings()
    library = settings('general', 'library')

    if library.lower() == 'autoscript':
        microscope_base = AutoscriptMicroscopeControl
    else:
        raise ValueError(f"Invalid microscope control type: {library}")

    class Microscope(microscope_base):
        _instance = None

        # Singleton construction
        def __new__(cls, *args, **kwargs):
            if cls._instance is None:
                cls._instance = super(Microscope, cls).__new__(cls)
            return cls._instance

        def __init__(self):
            """
            Initializes a new instance of the class.

            """
            self.settings = Settings()
            super().__init__(self.settings('microscope', 'ip_address'))

            self.beam = self.electron_beam  # default setting for actual beam

            self._detector_contrast_backup = None
            self._detector_brightness_backup = None
            stage_trial_setting = self.settings('microscope', 'stage_trials', return_object=True)
            self.stage_trial_counter = stage_trial_setting.value
            stage_trial_setting.add_handler(self.update_stage_trial_counter)

        def update_stage_trial_counter(self, value):
            self.stage_trial_counter = value

        def stage_move_with_verification(self, new_stage_position: StagePosition):
            """
            Moves the stage to the specified position and verifies the movement within a tolerance.

            :param new_stage_position: The new position of the stage.
            :return: None
            """
            stage_tolerance = self.settings('microscope', 'stage_tolerance')
            stage_trials = self.settings('microscope', 'stage_trials')
            self.position = new_stage_position  # set stage position
            position = self.position  # get stage position
            # after movement, verify whether the movement is within tolerance
            dist = distance.euclidean(position.to_array(), new_stage_position.to_xy())

            if dist > stage_tolerance:
                logging.warning(
                    f"Stage reached position {new_stage_position} is too far ({dist}) from defined "
                    f"position {new_stage_position} ")
                self.stage_trial_counter -= 1
                self.stage_move_with_verification(new_stage_position)  # move again
                if self.stage_trial_counter == 0:
                    logging.error("Stage movement failed after multiple trials")
                    raise Exception("Stage movement failed after multiple trials")
            else:
                # reset trials counter
                self.stage_trial_counter = stage_trials

        def add_beam_shift_with_verification(self, new_beam_shift: Point):
            """ Beam shift increment"""
            return self.beam_shift_with_verification(self.beam.beam_shift + new_beam_shift)

        def beam_shift_with_verification(self, new_beam_shift: Point):
            """
            Do beam shift.
            If the beam shift is out of range, do relative movement by stage.
            """
            beam_shift_tolerance = self.settings('microscope', 'beam_shift_tolerance')
            relative_beam_shift_to_stage = self.settings('microscope', 'relative_beam_shift_to_stage')

            try:
                self.beam.beam_shift = new_beam_shift  # set beam shift
                dist = distance.euclidean(self.beam.beam_shift.to_array(), new_beam_shift.to_array())
                if dist > float(beam_shift_tolerance):
                    raise Exception("Beam shift out of range")
            except Exception as e:  # if any problem with beam shift or out of range -> stage move
                logging.warning("Beam shift is out of range. Stage position needs to be adjusted. " + repr(e))
                # stage move = beam shift * shift conversion
                new_stage_move = new_beam_shift * Point(relative_beam_shift_to_stage[0],
                                                        relative_beam_shift_to_stage[1])
                new_stage_move *= self.beam.beam_shift_to_stage_move  # Direction conversion
                self.relative_position = StagePosition(x=new_stage_move.x, y=new_stage_move.y)
                self.beam.beam_shift = Point(0, 0)  # zero beam shift
                return False
            return True

        def blank_screen(self):
            """
            Make a black screen (blank and grab frame).
            :return: None
            """
            contrast_backup = self.beam.detector_contrast
            brightness_backup = self.beam.detector_brightness
            dwell_backup = self.beam.dwell_time
            li_backup = self.beam.line_integration
            scanning_area_backup = self.beam.scanning_area
            pixel_backup = self.beam.pixel_size
            self.beam.pixel_size = 20e-9
            self.beam.scanning_area = None
            self.beam.detector_contrast = 0
            self.beam.detector_brightness = 0
            self.beam.blank()
            self.beam.line_integration = 1
            self.beam.dwell_time = self.beam.minimal_dwell
            self.beam.grab_frame(file_name=None)
            self.beam.scanning_area = scanning_area_backup
            self.beam.dwell_time = dwell_backup
            self.beam.detector_contrast = contrast_backup
            self.beam.detector_brightness = brightness_backup
            self.beam.line_integration = li_backup
            self.beam.pixel_size = pixel_backup

        def total_blank(self):
            """
            Blank with zero contrast and brightness
            :return:
            """
            if not self.beam.detector_contrast == 0:
                self._detector_contrast_backup = self.beam.detector_contrast
            if not self.beam.detector_brightness == 0:
                self._detector_brightness_backup = self.beam.detector_brightness
            self.beam.detector_contrast = 0
            self.beam.detector_brightness = 0
            self.beam.blank()

        def total_unblank(self):
            if self._detector_contrast_backup is not None and not self._detector_contrast_backup == 0:
                self.beam.detector_contrast = self._detector_contrast_backup
            if self._detector_brightness_backup is not None and not self._detector_brightness_backup == 0:
                self.beam.detector_brightness = self._detector_brightness_backup
            self.beam.unblank()

        def apply_beam_settings(self, image_settings):
            if 'bit_depth' in image_settings:
                self.beam.bit_depth = image_settings['bit_depth']
            if 'field_of_view' in image_settings:# and self.electron_beam.extended_resolution:
                self.beam.horizontal_field_width = image_settings['field_of_view'][0]
                self.beam.vertical_field_width = image_settings['field_of_view'][1]
            # call pixel size from Beam class, set correct resolution
            if 'pixel_size' in image_settings:# and self.electron_beam.extended_resolution:
                self.beam.pixel_size = float(image_settings['pixel_size'])
            if 'images_line_integration' in image_settings:
                self.beam.line_integration = image_settings['images_line_integration']
            if 'dwell' in image_settings:
                self.beam.dwell_time = image_settings['dwell']
            if 'imaging_area' in image_settings:
                self.beam.scanning_area = ScanningArea.from_dict(image_settings['imaging_area'])
            else:
                self.beam.scanning_area = None

        def acquire_image(self, slice_number=None):
            """
            Acquires an images using the microscope's electron beam.
            The resolution is set based on the FoV and pixe_size.
            It can acquire multiple images if the li (setting images_line_integration) is array.
            It saves image (data_dir used)

            :param slice_number: Optional slice number for the image. Defaults to None.
            :return: The acquired image.
            """
            imaging_settings_name = self.settings('acquisition', 'image_name')
            imaging_settings = self.settings('image', imaging_settings_name)
            data_dir =  self.settings('dirs', 'output_images')

            self.apply_beam_settings(imaging_settings)

            if slice_number is not None:
                img_name = f"slice_{slice_number:05}.tif"
            else:
                img_name = f"slice_test.tif"

            img_name = os.path.join(data_dir, img_name)
            logging.info(f"Acquiring {img_name}.")
            image = self.beam.grab_frame(img_name)
            if slice_number is not None:
                print(f"Image {slice_number} acquired.")

            return image

    return Microscope  # factory
