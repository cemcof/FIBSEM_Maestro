import importlib
import logging
import inspect
import numpy as np
import io
from PIL import Image
from PySide6.QtGui import QImage, QPixmap, QTransform

from PySide6.QtWidgets import QLabel, QLineEdit, QFormLayout, QMessageBox, QComboBox, QCheckBox

from fibsem_maestro.settings import Settings

settings = Settings()


def populate_form(settings, layout=None, specific_settings={}, comment=None):
    """ Populate layout by settings.
    specific_settings - dict of non-textbox settings
      - None - omit
      - List - combo box """

    # sort by settings keys - in order to keep the same layout
    ordered_settings = dict(sorted(settings.items()))

    # clear layouts
    clear_layout(layout)

    for s in ordered_settings:
        widget = None

        if s in specific_settings:
            if isinstance(specific_settings[s], list):
                widget = QComboBox()
                widget.addItems(specific_settings[s])
                widget.setCurrentText(ordered_settings[s])
        else:
            value = ordered_settings[s]
            widget = create_setting_gui(value)  # create widget
            set_setting_gui(widget, value)  # set widget

        if widget is not None:
            widget.settings_name = s
            label = QLabel(s)
            if comment is not None:
                if s in comment.keys():
                    widget.setToolTip(comment[s])
                    label.setToolTip(comment[s])
            layout.addRow(label, widget)

def iter_settings_gui(layout: QFormLayout):
    """

    To iterate through a given QFormLayout and yield settings widgets.

    Parameters:
        layout: QFormLayout - The QFormLayout to iterate through.

    Yields:
        widgets with a 'settings_name' attribute found in the specified layout.

    """
    for i in range(layout.rowCount()):
        field_item = layout.itemAt(i, QFormLayout.FieldRole)
        if field_item is not None:
            widget = field_item.widget()
            if hasattr(widget, 'settings_name'):
                yield widget

def create_setting_gui(value):
    if isinstance(value, bool):
        return QCheckBox()
    else:
        return QLineEdit()

def set_setting_gui(widget, value):
    # bool
    if isinstance(value, bool):
        widget.setChecked(value)
    # scalar
    elif isinstance(value, (int, float, str)):
        widget.setText(f'{value}')
    # array
    elif isinstance(value, list):
        widget.setText('')
        for i, v in enumerate(value):
            if i == 0:
                widget.setText(widget.text() + f'{v}')
            else:
                widget.setText(widget.text() + f',{v}')
    elif isinstance(value, dict):
        for k, v in value.items():
            widget.setText(widget.text() + f'{k}:{v},')
    else:
        raise ValueError(f'Settings has invalid format!')


def get_setting_gui(widget):
    """
    Function to extract settings value from different types of PyQt5 widgets.
    Accepts float, str, [floats separated by ,], boolean
    Parameters:
        widget: PyQt5 widget - The input widget to extract the value from.

    Returns:
        The extracted settings value from the widget.

    Raises:
        ValueError: If the settings value has an invalid format.
    """
    if isinstance(widget, QComboBox):
        str_value = widget.currentText()
    else:
        str_value = widget.text()

    if isinstance(widget, QCheckBox):
        value = widget.isChecked()
    else:
        try:
            value = int(str_value)
        except ValueError:
            try:
                value = float(str_value)
            except ValueError:
                try:
                    if ',' in str_value:
                        # string value with ','
                        parts = str_value.split(',')
                        value = [float(v) for v in parts]
                    else:
                        # string value
                        value = str_value
                except ValueError:
                    raise ValueError(f'Settings "{str_value}" has invalid format!')
    return value


def change_setting_gui(layout: QFormLayout, setting: str, new_value):
    for widget in iter_settings_gui(layout):
        if widget.settings_name == setting:
            set_setting_gui(widget, new_value)

def serialize_form(layout: QFormLayout, setting):
    """ Set setting in settings class based on layout """
    for widget in iter_settings_gui(layout):
        value = get_setting_gui(widget)
        settings_name = widget.settings_name
        setting_t = tuple(setting + [settings_name])
        settings.set(*setting_t, value=value)

def confirm_action_dialog():
    msgBox = QMessageBox()
    msgBox.setWindowTitle("Confirmation")
    msgBox.setText("Are you sure?")
    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    return msgBox.exec()


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()


def get_module_members(module_path: str, member_type: str):
    """
    Retrieve a list of class names or function names from a module at the given module path.

    Args:
        module_path (str): The Python path of the module to inspect
        member_type (str): The type of members to return, either 'class' to return classes, 'mod' to return modules or 'func' to return functions.

    Returns:
        List[str]: A list of member names of the specified member_type from the module at module_path.

    Raises:
        ValueError: If member_type is not either 'class' or 'func', it raises ValueError with relevant information.
    """
    if member_type == 'class':
        inspect_member = inspect.isclass
    elif member_type == 'func':
        inspect_member = inspect.isfunction
    elif member_type == 'mod':
        inspect_member = inspect.ismodule
    else:
        raise ValueError(f'Unknown member type: {member_type}')
    imported_module = importlib.import_module(module_path)
    members = inspect.getmembers(imported_module, inspect_member)
    if member_type == 'mod':
        return [m[0] for m in members]
    else:
        return [m[0] for m in members if m[1].__module__ == imported_module.__name__]


def get_setters(cls):
    """
    Retrieves all setters defined in the given class.

    Args:
        cls (class): The class to investigate.

    Returns:
        List[str]: A list of setters' names defined in the class.
    """
    return [name for name, value in inspect.getmembers(cls) if isinstance(value, property) and value.fset is not None]


def get_pixmap(image, transpose = False):
    img = np.ascontiguousarray(image)
    pil_img = Image.fromarray(img)
    buf = io.BytesIO()
    pil_img.save(buf, format='PNG')
    qimg = QImage()
    qimg.loadFromData(buf.getvalue(), format='PNG')
    if transpose:
        qimg = qimg.mirrored(True, False)
    pixmap = QPixmap.fromImage(qimg)
    if transpose:
        transform = QTransform().rotate(-90)
        pixmap = pixmap.transformed(transform)
    return pixmap