import copy

import yaml
import logging

class Setting:
    def __init__(self, value):
        self._value = value
        self.value_change_handlers = []  # handlers called on value change

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value != self._value:
            self._value = value
            for handler in self.value_change_handlers:
                logging.debug(f"Handling value {self._value} for handler {handler}")
                handler(value)

    def add_handler(self, handler):
        self.value_change_handlers.append(handler)
        logging.debug(f'Setting handler to {self._value} added')

class Settings:
    """ Settings singleton handles all settings (load/save from/to file, manage assertions...)"""

    _instance = None
    _settings = None
    _settings_comments = None
    _default_filename = None

    # Singleton construction
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance

    @property
    def settings(self):
        """ Raw settings data """
        return self._settings

    def get(self, *args, **kwargs):
        """

        Method to retrieve values from settings.

        Parameters:
        - *args: tuple containing keys to retrieve settings from nested dictionary.
        - return_object: bool to indicate whether to return the setting object itself or its value.

        Return Type:
        - Depends on the value of get_object parameter. If get_object is True, returns the setting object. Otherwise, returns the value of the setting.

        """
        setting = self._settings
        comment = self._settings_comments
        for setting_key in args:
            try:
                # If current setting is list of settings, search by name. Otherwise search by dict key
                if isinstance(setting, list):
                    setting = Settings._find_by_name(setting_key, setting)
                else:
                    setting = setting[setting_key]
                    if comment is not None:
                        if setting_key in comment.keys():
                            comment = comment[setting_key]
            except KeyError:
                logging.error(f'{setting_key} is not defined in settings!')
                return None
        if 'return_object' in kwargs and kwargs['return_object']:
            return setting
        else:
            value = Settings._get_values(setting)
            if 'return_comment' in kwargs and kwargs['return_comment']:
                return value, comment
            else:
                return value

    def __call__(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    @staticmethod
    def _find_by_name(dict_name, setting):
        """
        Find the item in the given setting dictionary by name.

        Parameters:
        dict_name (str): The name to search for in the setting dictionary.
        setting (dict): The setting dictionary to search in.

        Returns:
        The item with the matching name from the setting dictionary.
        """
        if dict_name == 'none':
            return None
        else:
            try:
                return [x for x in setting if x['name'].value == dict_name][0]
            except Exception as e:
                logging.error(f'Setting {dict_name} not found!')
                raise e

    @staticmethod
    def _is_value(v):
        # is ScanningArea struct (dict x,y,width,height) -> IT IS VALUE
        is_scanning_area = isinstance(v, dict) and 'x' in v and 'y' in v and 'width' in v and 'height' in v
        # is settings list -> IT IS NOT VALUE
        is_list_of_dict = isinstance(v, list) and all([isinstance(x, dict) for x in v])
        # is list of ScanningArea -> IT IS VALUE
        is_list_scanning_area = isinstance(v, list) and all([isinstance(x, dict) and hasattr(x, 'x') and hasattr(x, 'y')
                                                             and hasattr(x, 'width') and hasattr(x, 'height')
                                                             for x in v])
        # variable is list of dicts but not a list of scanning areas
        if is_list_of_dict and not is_list_scanning_area:
            return False  # NOT VALUE
        # variable is dict (encoded ScanningArea)
        if is_scanning_area:
            return True  # IS VALUE
        if isinstance(v, dict):
            return False
        return True


    @staticmethod
    def _replace_values_with_object(structure):
        """

        @staticmethod
        def _replace_values_with_object(structure)

        This method recursively walks through a nested structure and replaces all values that are not dictionaries or lists with a custom object (Setting).

        Parameters:
            structure: dict or list
                The nested structure to be processed.

        Returns:
            None

        """
        if isinstance(structure, dict):
            for k, v in structure.items():
                if not Settings._is_value(v):
                    Settings._replace_values_with_object(v)
                else:
                    structure[k] = Setting(structure[k])  # Replace with your object
        elif isinstance(structure, list):
            for i in range(len(structure)):
                v = structure[i]
                if not Settings._is_value(v):
                    Settings._replace_values_with_object(v)
                else:
                    structure[i] = Setting(structure[i])  # Replace with your object

    @staticmethod
    def _update_object(settings, new_settings):
        """ Update settings with new values. """
        if isinstance(new_settings, dict):
            for k, v in new_settings.items():
                if not Settings._is_value(v):
                    if k in settings.keys():
                        Settings._update_object(settings[k], v)
                else:
                    if k in settings.keys():
                        settings[k].value = v  # Replace with your object
        elif isinstance(new_settings, list):
            for i in range(len(new_settings)):
                v = new_settings[i]
                if not Settings._is_value(v):
                    Settings._update_object(settings[i], v)
                else:
                    settings[i].value = v  # Replace with your object

    @staticmethod
    def _get_values(structure):
        result_values = None
        if isinstance(structure, dict):
            result_values = {}
            for k, v in structure.items():
                if isinstance(v, (dict, list)):
                    result_values[k] = Settings._get_values(v)
                elif isinstance(v, Setting):  # Replace 'Object' with your class name
                    result_values[k] = structure[k].value  # Replace with your value
                else:
                    raise ValueError('Unknown setting type!')
        elif isinstance(structure, list):
            result_values = []
            for i in range(len(structure)):
                if isinstance(structure[i], (dict, list)):
                    result_values.append(Settings._get_values(structure[i]))
                elif isinstance(structure[i], Setting):  # Replace 'Object' with your class name
                    result_values.append(structure[i].value)  # Replace with your value
                else:
                    raise ValueError('Unknown setting type!')
        else:
            result_values = structure.value

        return result_values


    def set(self, *args, value):
        """
        Set value of a setting in the configuration.

        Parameters:
            args : List of keys to access the nested setting dictionary.
            value (any): Value to be set for the given nested setting.

        Returns:
            None
        """
        # TODO: set assertions
        setting = self._settings
        for setting_key in args[:-1]:
            # If current setting is list of settings, search by name. Otherwise, search by dict key
            if isinstance(setting, list):
                setting = Settings._find_by_name(setting_key, setting)
            else:
                setting = setting[setting_key]

        if args[-1] in setting.keys():
            if isinstance(setting[args[-1]], list):
                setting[args[-1]] = Setting(value)
            else:
                setting[args[-1]].value = value
            logging.debug(f'Setting value {args} to {value}')
        else:
            raise ValueError(f'{args[-1]} is not defined in settings!')

    def append(self, *args, value):
        """Append a new setting to list setting"""
        setting = self._settings
        for setting_key in args:
            try:
                # If current setting is list of settings, search by name. Otherwise search by dict key
                if isinstance(setting, list):
                    setting = Settings._find_by_name(setting_key, setting)
                else:
                    setting = setting[setting_key]
            except KeyError:
                logging.error(f'{setting_key} is not defined in settings!')
                return None

        if isinstance(setting, list):
            Settings._replace_values_with_object(value)
            setting.append(value)
        else:
            logging.error(f'{setting_key} is not list and cannot be append')

    def remove(self, *args, value):
        """Remove the setting (only for array searched by name)"""
        setting = self._settings
        for setting_key in args:
            try:
                # If current setting is list of settings, search by name. Otherwise search by dict key
                if isinstance(setting, list):
                    setting = Settings._find_by_name(setting_key, setting)
                else:
                    setting = setting[setting_key]
            except KeyError:
                logging.error(f'{setting_key} is not defined in settings!')
                return None
        setting_to_remove = Settings._find_by_name(value['name'], setting)
        setting.remove(setting_to_remove)

    def load(self, filename: str):
            """ Load settings from YAML file"""
            self._default_filename = filename
            try:
                with open(filename, "r") as yamlfile:
                    self._settings = yaml.safe_load(yamlfile)
                    logging.info(f'Settings file {filename} successfully loaded')
                    Settings._replace_values_with_object(self._settings)
            except Exception as e:
                logging.error("Settings loading error: " + repr(e))

            try:
                with open('settings_comments.yaml', "r") as yamlfile:
                    self._settings_comments = yaml.safe_load(yamlfile)
                    logging.info('Comments file successfully loaded')
            except Exception as e:
                logging.error("Comments loading error: " + repr(e))

    def update(self, filename: str):
            """ Update current settings by settings from YAML file"""
            try:
                with open(filename, "r") as yamlfile:
                    new_settings = yaml.safe_load(yamlfile)
                    logging.info(f'Settings file {filename} successfully loaded')
                    Settings._update_object(self._settings, new_settings)
            except Exception as e:
                logging.error("Settings loading error: " + repr(e))

            try:
                with open('settings_comments.yaml', "r") as yamlfile:
                    self._settings_comments = yaml.safe_load(yamlfile)
                    logging.info('Comments file successfully loaded')
            except Exception as e:
                logging.error("Comments loading error: " + repr(e))

    def save(self, filename: str = None):
        """ Save settings to YAML file"""
        if filename is None:
            filename = self._default_filename
        try:
            with open(filename, "w") as yamlfile:
                settings_to_save = Settings._get_values(self._settings)
                yaml.safe_dump(settings_to_save, yamlfile)
                logging.info(f'Settings file {filename} successfully saved')
        except Exception as e:
            logging.error("Settings saving error: " + repr(e))
