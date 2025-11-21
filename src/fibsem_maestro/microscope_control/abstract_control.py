import math
from abc import ABC, abstractmethod
from fibsem_maestro.tools.support import StagePosition, ScanningArea

class BeamControl(ABC):
    """
    This is an abstract base class providing an interface for controlling a beam (can be electron or ion) in a microscope.

    Methods:
        working_distance: Getter and setter for the working distance associated with the current beam control.
        stigmator_x, stigmator_y: Getter and setter for the x, y stigmatism of the current beam control.
        lens_alignment_x, lens_alignment_y: Getter and setter for the x, y alignment of the beam lens.
        beam_shift_x, beam_shift_y: Getter and setter for the x, y shift of the beam control.
        detector_contrast, detector_brightness: Getter and setter for the contrast and brightness of the detector in the beam control.
        blank, unblank: Method to blank and unblank the beam.
        start_acquisition, stop_acquisition: Methods to start and stop the beam acquisition.
        grab_frame: Method to retrieve a frame.
        get_image: Method to retrieve the actual image.
        line_integration: Method to perform line integration on the currently scanned line.
        dwell_time: Getter and setter for the dwell time of the beam control.
        bit_depth: Getter and setter for the bit depth of the image from the microscope.
        resolution: Getter and setter for the resolution of the image.
        hfw: Getter and setter for the horizontal field width.
        pixel_size: Getter for the pixel size of the image from the microscope.
    """

    @property
    @abstractmethod
    def working_distance(self):
        pass

    @working_distance.setter
    @abstractmethod
    def working_distance(self, wd: float):
        pass

    @property
    @abstractmethod
    def stigmator_x(self):
        pass

    @stigmator_x.setter
    @abstractmethod
    def stigmator_x(self, value):
        pass

    @property
    @abstractmethod
    def stigmator_y(self):
        pass

    @stigmator_y.setter
    @abstractmethod
    def stigmator_y(self, value):
        pass

    @property
    @abstractmethod
    def stigmator(self):
        pass

    @stigmator.setter
    def stigmator(self, value):
        pass

    @property
    @abstractmethod
    def lens_alignment_x(self):
        pass

    @lens_alignment_x.setter
    @abstractmethod
    def lens_alignment_x(self, value):
        pass

    @property
    @abstractmethod
    def lens_alignment_y(self):
        pass

    @lens_alignment_y.setter
    @abstractmethod
    def lens_alignment_y(self, value):
        pass

    @property
    @abstractmethod
    def lens_alignment(self):
        pass

    @lens_alignment.setter
    def lens_alignment(self, point):
        pass

    @property
    @abstractmethod
    def beam_shift_x(self):
        pass

    @beam_shift_x.setter
    @abstractmethod
    def beam_shift_x(self, value):
        pass

    @property
    @abstractmethod
    def beam_shift_y(self):
        pass

    @beam_shift_y.setter
    @abstractmethod
    def beam_shift_y(self, value):
        pass

    @property
    @abstractmethod
    def beam_shift(self):
        pass

    @beam_shift.setter
    def beam_shift(self, point):
        pass

    @property
    @abstractmethod
    def detector_contrast(self):
        pass

    @detector_contrast.setter
    @abstractmethod
    def detector_contrast(self, value):
        pass

    @property
    @abstractmethod
    def detector_brightness(self):
        pass

    @detector_brightness.setter
    @abstractmethod
    def detector_brightness(self, value):
        pass

    @property
    @abstractmethod
    def source_tilt(self):
        pass

    @source_tilt.setter
    @abstractmethod
    def source_tilt(self, value):
        pass

    @abstractmethod
    def blank(self):
        pass

    @abstractmethod
    def unblank(self):
        pass

    @abstractmethod
    def start_acquisition(self):
        pass

    @abstractmethod
    def stop_acquisition(self):
        pass

    @abstractmethod
    def grab_frame(self, file_name):
        pass

    @abstractmethod
    def get_image(self):
        pass

    @abstractmethod
    def rectangle_milling(self, app_file: str, leftop, size, depth: float, direction: str):
        pass

    @property
    @abstractmethod
    def line_integration(self):
        pass

    @line_integration.setter
    @abstractmethod
    def line_integration(self, li):
        pass

    @property
    @abstractmethod
    def dwell_time(self):
        pass

    @dwell_time.setter
    @abstractmethod
    def dwell_time(self, value):
        pass

    @property
    @abstractmethod
    def bit_depth(self):
        pass

    @bit_depth.setter
    @abstractmethod
    def bit_depth(self, value):
        pass

    @property
    @abstractmethod
    def resolution(self):
        pass

    @resolution.setter
    @abstractmethod
    def resolution(self, value):
        pass

    @property
    @abstractmethod
    def horizontal_field_width(self):
        pass

    @horizontal_field_width.setter
    @abstractmethod
    def horizontal_field_width(self, value):
        pass

    @property
    @abstractmethod
    def vertical_field_width(self):
        pass

    @vertical_field_width.setter
    @abstractmethod
    def vertical_field_width(self, value):
        pass

    @property
    @abstractmethod
    def pixel_size(self):
        pass

    @pixel_size.setter
    @abstractmethod
    def pixel_size(self, pixel):
        pass

    @property
    @abstractmethod
    def scanning_area(self):
        pass

    @scanning_area.setter
    @abstractmethod
    def scanning_area(self, value: ScanningArea):
        pass

    @property
    @abstractmethod
    def beam_shift_to_stage_move(self):
        pass

    @property
    @abstractmethod
    def image_to_beam_shift(self):
        pass

    @property
    @abstractmethod
    def minimal_dwell(self):
        pass

    @abstractmethod
    def limits(self, var):
        pass

class MicroscopeControl(ABC):
    """
    This is an abstract base class designated for controlling a microscope.

    The methods provided by this class serve as an interface that should be
    concretely implemented by any microscope-specific control class
    (for example: FIBSEM API, direct Autoscript).

    These methods include the basic functionalities needed for controlling
    the various components and parameters of a microscope such as the stage,
    and beams.

    Methods:
        position - Getter and setter for the position of the microscope stage.
    """

    @property
    @abstractmethod
    def position(self):
        pass

    @position.setter
    @abstractmethod
    def position(self, goal: StagePosition):
        pass

    @property
    @abstractmethod
    def relative_position(self):
        pass

    @relative_position.setter
    @abstractmethod
    def relative_position(self, goal: StagePosition):
        pass

    @position.setter
    @abstractmethod
    def position(self, goal: StagePosition):
        pass

    @property
    @abstractmethod
    def electron_beam(self) -> BeamControl:
        """
        Returns the electron beam of the microscope.

        :return: The electron_beam instance of BeamControl
        """
        pass

    @property
    @abstractmethod
    def ion_beam(self) -> BeamControl:
        """
        Returns the ion beam of the microscope.

        :return: The ion_beam instance of BeamControl
        """
        pass
