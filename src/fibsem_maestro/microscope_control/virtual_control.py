from enum import Enum
import matplotlib.image as mpimg
from fibsem_maestro.tools.support import Image

""" Provides fake classes for virtual control
The classes act like AS classes"""


class ImagingDevice(Enum):
    ELECTRON_BEAM = 1
    ION_BEAM = 2

class BeamType(Enum):
    ELECTRON = 1
    ION = 2

class StagePosition:
    """ Fake stage position. It save all arguments in the constructor to attributes """
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class EmptyClass:
    """Empty class for fake classes in AS Microscope instance"""
    def __getattr__(self, attr):
        raise AttributeError(f"Simulation object has no attribute {attr}. You need to set it first!")


class VirtualMicroscope:
    """ Fake AS Microscope class """
    def __init__(self):
        self.is_virtual = True
        self.specimen = EmptyClass()
        self.specimen.stage = EmptyClass()
        self.specimen.stage.absolute_move = self.specimen_stage_absolute_move
        self.beams = EmptyClass()
        self.beams.electron_beam = VirtualMicroscopeBeam()
        self.beams.ion_beam = VirtualMicroscopeBeam()
        self.detector = EmptyClass()
        self.detector.contrast = EmptyClass()
        self.detector.brightness = EmptyClass()
        self.imaging = EmptyClass()
        self.imaging.grab_frame = lambda : None
        self.imaging.get_image = lambda: None
        self.imaging.set_active_view = lambda x: None
        self.imaging.set_active_device = lambda x: None

    def specimen_stage_absolute_move(self, goal):
        self.specimen.stage.current_position = goal


class VirtualMicroscopeBeam():
    """ Fake AS Microscope.electron_beam class and Microscope.ion_beam class """
    def __init__(self):
        self.is_virtual = True
        self.working_distance = EmptyClass()
        self.working_distance.value = 0
        self.working_distance.set_value_no_degauss = self.working_distance_set_value_no_degauss
        self.stigmator = EmptyClass()
        self.lens_alignment = EmptyClass()
        self.beam_shift = EmptyClass()
        self.scanning = EmptyClass()
        self.scanning.dwell_time = EmptyClass()
        self.scanning.bit_depth = EmptyClass()
        self.resolution = EmptyClass()
        self.horizontal_field_width = EmptyClass()
        self.vertical_field_width = EmptyClass()

    def working_distance_set_value_no_degauss(self, value):
        self.working_distance.value = value

    def get_image(self):
        image = mpimg.imread('oxford.jpg')
        image = Image(image, 10e-9)  # pixel size 10e-9
        return image

