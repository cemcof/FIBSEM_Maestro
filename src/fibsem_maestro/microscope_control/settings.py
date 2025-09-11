import logging
import yaml

from fibsem_maestro.microscope_control.abstract_control import MicroscopeControl
from fibsem_maestro.tools.support import Point, StagePosition, ScanningArea


def save_settings(microscope: MicroscopeControl, settings: list, path):
    # populate settings dict with settings names and their values read from microscope
    settings_dict = {}
    for setting in reversed(settings): # position used to be the firs in the list - it must be last in dict in order to be processed first (stage position affect wd)
        try:
            if '.' in setting:
                # inner attribute -> beam setting
                [beam, setting_attribute] = setting.split('.')
                value = getattr(getattr(microscope, beam), setting_attribute)
            else:
                # simple attribute
                value = getattr(microscope, setting)
        except Exception as e:
            logging.error(f'The value {setting} cannot be read from microscope. Setting to None.')
            logging.error(repr(e))
            value = None

        settings_dict[setting] = value
    # write to file
    with open(path, 'w') as f:
        yaml.dump(settings_dict, f)


def load_settings(microscope: MicroscopeControl, path):
    # read settings from file
    with open(path, "r") as f:
        settings_dict = yaml.safe_load(f)

    # apply each setting to the microscope
    for setting, value in settings_dict.items():
        try:
            if '.' in setting:
                # beam settings
                substrings = setting.split('.')
                beam = getattr(microscope, substrings[0])
                if not hasattr(beam, substrings[1]):
                    logging.warning(f'The setting {setting} is not microscope property, saving as stand alone property')
                setattr(beam, substrings[1], value)
            else:
                if not hasattr(microscope, setting):
                    logging.warning(f'The setting {setting} is not microscope property, saving as stand alone property')
                # direct microscope settings
                setattr(microscope, setting, value)
        except Exception as e:
            logging.error(f'The value {setting} cannot be set to {value} in microscope')
            logging.error(repr(e))


def point_constructor(loader, node):
    values = loader.construct_mapping(node)
    return Point(x=values['_x'], y=values['_y'])


def stage_position_constructor(loader, node):
    values = loader.construct_mapping(node)
    return StagePosition(**values)


def scanning_area_constructor(loader, node):
    values = loader.construct_mapping(node)
    return ScanningArea(**values)


# class loaders
yaml.SafeLoader.add_constructor(
    u'tag:yaml.org,2002:python/object:fibsem_maestro.tools.support.Point',
    point_constructor)

# class loaders
yaml.SafeLoader.add_constructor(
    u'tag:yaml.org,2002:python/object:fibsem_maestro.tools.support.StagePosition',
    stage_position_constructor)

# class loaders
yaml.SafeLoader.add_constructor(
    u'tag:yaml.org,2002:python/object:fibsem_maestro.tools.support.ScanningArea',
    scanning_area_constructor)

