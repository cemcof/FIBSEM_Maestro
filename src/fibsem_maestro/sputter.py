from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from pynput.mouse import Button, Controller
import time

pattern_file = "D://Data//Calibrations//uSputter//milling_pattern_shutter.bmp"

class WindowMgr:
    """Encapsulates some calls to the winapi for window management"""

    def __init__ (self):
        """Constructor"""
        self._handle = None


    def find_window(self, class_name, window_name=None):
        """find a window by its class_name"""
        self._handle = win32gui.FindWindow(class_name, window_name)

    def _window_enum_callback(self, hwnd, wildcard):
        """Pass to win32gui.EnumWindows() to check all the opened windows"""
        if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) is not None:
            self._handle = hwnd

    def find_window_wildcard(self, wildcard):
        """find a window whose title matches the wildcard regex"""
        self._handle = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)

    def set_foreground(self):
        """put the window in the foreground"""
        win32gui.SetForegroundWindow(self._handle)

    def move_window(self, x, y, w, h):
        win32gui.MoveWindow(self._handle, x, y, w, h, True)

class MouseClick():
    def __init__(self,microscope):
        self.insert_point = (264, 1022)
        self.retract_point = (260, 1051)
        self.mouse = Controller()
        self.microscope = microscope

    def shutter_insert(self):
        self.set_window()
        self.mouse.position = self.insert_point
        self.mouse.press(Button.left)
        self.mouse.release(Button.left)

        timer_counter = 0
        while True:
            time.sleep(0.1)
            if self.microscope.beams.electron_beam.protective_shutter.state == 'Inserted':
                break
            timer_counter += 1
            if timer_counter > 100:
                raise Exception('Shutter cannot be inserted')

    def shutter_retract(self):
        self.set_window()
        self.mouse.position = self.retract_point
        self.mouse.press(Button.left)
        self.mouse.release(Button.left)

        timer_counter = 0
        while True:
            time.sleep(0.1)
            if self.microscope.beams.electron_beam.protective_shutter.state == 'Retracted':
                break
            timer_counter += 1
            if timer_counter > 100:
                raise Exception('Shutter cannot be retracted')

    def set_window(self):
        w = WindowMgr()
        w.find_window_wildcard("BhvRetractableDevice.*")
        w.set_foreground()
        w.move_window(0, 900, 400, 200)

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

def sputter(grid, microscope):
    shutter = MouseClick(microscope)

    microscope.specimen.stage.unlink()

    actions = [
        Action("working distance", microscope.beams.ion_beam.working_distance.value,
               microscope.beams.ion_beam.working_distance, 0.01828830330208136),
        Action("beam shift", microscope.beams.ion_beam.beam_shift.value, microscope.beams.ion_beam.beam_shift,
               Point(0, 0)),
        Action("beam voltage", microscope.beams.ion_beam.high_voltage.value, microscope.beams.ion_beam.high_voltage,
               16e3),
        Action("scan rotation", microscope.beams.ion_beam.scanning.rotation.value,
               microscope.beams.ion_beam.scanning.rotation, 0),
        Action("resolution", microscope.beams.ion_beam.scanning.resolution.value,
               microscope.beams.ion_beam.scanning.resolution, "3072x2048"),
        Action("dwell time", microscope.beams.ion_beam.scanning.dwell_time.value,
               microscope.beams.ion_beam.scanning.dwell_time, 25e-9),
        Action("electron wd", microscope.beams.electron_beam.working_distance.value,
               microscope.beams.electron_beam.working_distance.set_value_no_degauss, 4e-3)
    ]

    if grid == 1:
        a = Action("stage position", microscope.specimen.stage.current_position,
                   microscope.specimen.stage.absolute_move,
                   StagePosition(x=-0.0032502501, y=0.0016220833, z=0.028018293, r=-3.1375509, t=2.2244392e-05))
    elif grid == 2:
        a = Action("stage position", microscope.specimen.stage.current_position,
                   microscope.specimen.stage.absolute_move,
                   StagePosition(x=0.0026719999, y=0.00148725, z=0.028017843, r=-3.1375509, t=1.404909e-05))
    else:
        raise Exception('Invalid grid number.')

    actions = [a, *actions]  # add stage move as a first

    if microscope.beams.ion_beam.source.plasma_gas.value == PlasmaGasType.ARGON:
        actions.append(Action("beam current", microscope.beams.ion_beam.beam_current.value,
                              microscope.beams.ion_beam.beam_current, None))
    elif microscope.beams.ion_beam.source.plasma_gas.value == PlasmaGasType.OXYGEN:
        actions.append(Action("beam current", microscope.beams.ion_beam.beam_current.value,
                              microscope.beams.ion_beam.beam_current, 280e-9))
    elif microscope.beams.ion_beam.source.plasma_gas.value == PlasmaGasType.XENON:
        actions.append(Action("beam current", microscope.beams.ion_beam.beam_current.value,
                              microscope.beams.ion_beam.beam_current, 200e-9))
    elif microscope.beams.ion_beam.source.plasma_gas.value == PlasmaGasType.NITROGEN:
        actions.append(Action("beam current", microscope.beams.ion_beam.beam_current.value,
                              microscope.beams.ion_beam.beam_current, 510e-9))
    actions.append(Action("hfw", microscope.beams.ion_beam.horizontal_field_width.value,
                          microscope.beams.ion_beam.horizontal_field_width, 1.84e-3))

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

    #microscope.beams.electron_beam.optical_mode.value = OpticalMode.FIELD_FREE

    # Make sure the stage Z is linked to the free working distance
    microscope.specimen.stage.link()

    # Get the platinum GIS port object
    usputter = microscope.gas.get_gis_port("uSputter")

    # shutter on
    shutter.shutter_insert()

    # Insert the uSputter
    usputter.insert()

    # prepare for patterning
    microscope.specimen.stage.unlink()
    microscope.beams.ion_beam.unblank()
    microscope.imaging.stop_acquisition()
    microscope.patterning.clear_patterns()
    microscope.patterning.set_default_beam_type(BeamType.ION)
    microscope.patterning.set_default_application_file("Si")
    # Create the bitmap pattern definition from a BMP file
    bpd = BitmapPatternDefinition.load(pattern_file)
    # Create a new pattern using the bitmap pattern definition
    microscope.patterning.create_bitmap(0, 0, 1.837e-3, 1.224e-3, 0.04e-6, bpd)  # by Z, you change time

    print("Performing patterning...")
    microscope.patterning.run()

    # Retract the GIS needle
    microscope.patterning.clear_patterns()
    usputter.retract()

    # shutter off
    shutter.shutter_retract()

    print('Restore states')
    for action in actions:
        print(f'-> {action.description}')
        action.set_value(action.backuped_value)

import win32gui
import re




if __name__ == "__main__":
    mouse = Controller()
    print(mouse.position)
    microscope = SdbMicroscopeClient()
    microscope.connect('localhost')
    sputter(1, microscope)
