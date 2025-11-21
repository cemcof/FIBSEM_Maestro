import numpy as np
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from pynput.mouse import Button, Controller
import time
from tifffile import TiffFile
import tifffile
import re
from fibsem_maestro.tools.image_tools import template_matching
import pyautogui

pattern_file = "D://Data//Calibrations//sputter_bitmap2.bmp"

class MouseClick():
    def __init__(self,microscope):
        self.insert_point = (288, 754)
        self.retract_point = (288, 786)
        self.goto_point = (402, 734)
        self.template_image_filename_retracted = "d:\\Data\\Calibrations\\sputter_template_retracted.tiff"
        self.template_image_retracted = TiffFile(self.template_image_filename_retracted).asarray()
        self.template_image_filename_inserted = "d:\\Data\\Calibrations\\sputter_template_inserted.tiff"
        self.template_image_inserted = TiffFile(self.template_image_filename_inserted).asarray()
        self.mouse = Controller()
        self.microscope = microscope

    def check_retracted(self, save_image = False):
        self.microscope.imaging.set_active_view(4)
        self.microscope.imaging.set_active_device(ImagingDevice.CCD_CAMERA)
        self.microscope.imaging.start_acquisition()
        # Get one image while the camera is acquiring
        image = self.microscope.imaging.get_image().data

        # convert to 8b
        if image.max() > 255:
            image = ((image - image.min()) / (image.max() - image.min()) * 255).astype(
                np.uint8)

        if save_image:
            image = image[300:900, 700:1200]
            tifffile.imwrite(self.template_image_filename_retracted, image)
            return True
        image = image[500:600, 900:1000]
        _, _, similarity = template_matching(self.template_image_retracted, image, blur=3)
        self.microscope.imaging.set_active_view(2)
        print('Similarity: ', similarity)
        return similarity > 0.9

    def check_inserted(self, save_image = False):
        self.microscope.imaging.set_active_view(4)
        self.microscope.imaging.set_active_device(ImagingDevice.CCD_CAMERA)
        self.microscope.imaging.start_acquisition()
        # Get one image while the camera is acquiring
        image = self.microscope.imaging.get_image().data

        # convert to 8b
        if image.max() > 255:
            image = ((image - image.min()) / (image.max() - image.min()) * 255).astype(
                np.uint8)

        if save_image:
            image = image[300:900, 700:1200]
            tifffile.imwrite(self.template_image_filename_inserted, image)
            return True
        image = image[500:600, 900:1000]
        _, _, similarity = template_matching(self.template_image_inserted, image, blur=3)
        self.microscope.imaging.set_active_view(2)
        print('Similarity: ', similarity)
        return similarity > 0.9


    def shutter_insert(self):
        pyautogui.moveTo(self.insert_point[0], self.insert_point[1])
        pyautogui.click()
        pyautogui.moveTo(self.goto_point[0], self.goto_point[1])
        pyautogui.click()
        time.sleep(4)

        if not self.check_inserted():
            raise Exception('Shutter insertion error!')

    def shutter_retract(self):
        pyautogui.moveTo(self.retract_point[0], self.retract_point[1])
        pyautogui.click()
        pyautogui.moveTo(self.goto_point[0], self.goto_point[1])
        pyautogui.click()
        time.sleep(4)

        if not self.check_retracted():
            raise Exception('Shutter retraction error!')

class Action:
    def __init__(self, description, value_getter, value_setter, target_value):
        self.description = description
        self.value_getter = value_getter
        self.value_setter = value_setter
        self.target_value = target_value

    def backup(self):
        self.backuped_value = self.value_getter

    def set_value(self, value):
        if callable(self.value_setter):
            self.value_setter(value)
        else:
            self.value_setter.value = value
actions = []

def sputter(grid, microscope):
    global actions
    shutter = MouseClick(microscope)

    microscope.specimen.stage.unlink()

    actions = [
        Action("working distance", microscope.beams.ion_beam.working_distance.value,
               microscope.beams.ion_beam.working_distance, 0.0189),
        Action("beam shift", microscope.beams.ion_beam.beam_shift.value, microscope.beams.ion_beam.beam_shift,
               Point(0, 0)),
        Action("beam voltage", microscope.beams.ion_beam.high_voltage.value, microscope.beams.ion_beam.high_voltage,
               16e3),
        Action("scan rotation", microscope.beams.ion_beam.scanning.rotation.value,
               microscope.beams.ion_beam.scanning.rotation, 3.14159265),
        Action("resolution", microscope.beams.ion_beam.scanning.resolution.value,
               microscope.beams.ion_beam.scanning.resolution, "1536x1024"),
        Action("dwell time", microscope.beams.ion_beam.scanning.dwell_time.value,
               microscope.beams.ion_beam.scanning.dwell_time, 25e-9),
        Action("electron wd", microscope.beams.electron_beam.working_distance.value,
               microscope.beams.electron_beam.working_distance.set_value_no_degauss, 4e-3)
    ]

    if grid == 1:
        a = Action("stage position", microscope.specimen.stage.current_position,
                   microscope.specimen.stage.absolute_move,
                   #StagePosition(x=-0.0026250513, y=0.00388875, z=0.030274852, r=-1.221621, t=-0.087239775))
                   StagePosition(x=-0.0027167, y=0.0041181, z=0.0292194, r=-1.221621, t=-0.087239775))
    elif grid == 2:
        raise NotImplementedError("Not implemented yet.")
    else:
        raise Exception('Invalid grid number.')

    actions = [a, *actions]  # add stage move as a first

    if microscope.beams.ion_beam.source.plasma_gas.value == PlasmaGasType.ARGON:
        actions.append(Action("beam current", microscope.beams.ion_beam.beam_current.value,
                              microscope.beams.ion_beam.beam_current, None))
    elif microscope.beams.ion_beam.source.plasma_gas.value == PlasmaGasType.OXYGEN:
        actions.append(Action("beam current", microscope.beams.ion_beam.beam_current.value,
                              microscope.beams.ion_beam.beam_current, 840e-9))
    elif microscope.beams.ion_beam.source.plasma_gas.value == PlasmaGasType.XENON:
        actions.append(Action("beam current", microscope.beams.ion_beam.beam_current.value,
                              microscope.beams.ion_beam.beam_current, 840e-9))
    elif microscope.beams.ion_beam.source.plasma_gas.value == PlasmaGasType.NITROGEN:
        actions.append(Action("beam current", microscope.beams.ion_beam.beam_current.value,
                              microscope.beams.ion_beam.beam_current, 510e-9))

    actions.append(Action("hfw", microscope.beams.ion_beam.horizontal_field_width.value,
                          microscope.beams.ion_beam.horizontal_field_width, 1.90e-3)) #2.16e-3

    microscope.imaging.set_active_view(2)
    microscope.imaging.set_active_device(ImagingDevice.ION_BEAM)
    microscope.imaging.stop_acquisition()
    microscope.beams.ion_beam.turn_on()

    print('Backuping states')
    for action in actions:
        print(f'-> {action.description}')
        action.backup()

    print('Microscope setting')
    for action in actions:
        print(f'-> {action.description}')
        action.set_value(action.target_value)

    # shutter on
    shutter.shutter_insert()


    # prepare for patterning
    microscope.beams.ion_beam.unblank()
    microscope.imaging.stop_acquisition()
    microscope.patterning.clear_patterns()
    microscope.patterning.set_default_beam_type(BeamType.ION)
    microscope.patterning.set_default_application_file("Si")
    # Create the bitmap pattern definition from a BMP file
    bpd = BitmapPatternDefinition.load(pattern_file)
    time.sleep(0.5)
    # Create a new pattern using the bitmap pattern definition
    #microscope.patterning.create_bitmap(0, 0, 2.136e-3, 1.424e-3, 0.01, bpd)  # by Z, you change time 0.00924e-6
    microscope.patterning.create_bitmap(0, 0, 1895.05e-6, 1251.82e-6, 0.0055483871e-6, bpd)  # by Z, you change time 0.00924e-6 0.0060483871e-6

    print("Performing patterning...")
    microscope.patterning.run()

    # Retract the GIS needle
    microscope.patterning.clear_patterns()

    # shutter off
    shutter.shutter_retract()

def sputter_restore():
    print('Restore states')
    for action in actions:
        print(f'-> {action.description}')
        action.set_value(action.backuped_value)


if __name__ == "__main__":
    mouse = Controller()
    print(mouse.position)
    microscope = SdbMicroscopeClient()
    microscope.connect('localhost')
    sputter(1, microscope)
    sputter_restore()
