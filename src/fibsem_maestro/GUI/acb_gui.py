from PySide6.QtCore import QRect

from fibsem_maestro.GUI.gui_tools import serialize_form, populate_form
from fibsem_maestro.GUI.image_label import create_image_label
from image_label_manger import ImageLabelManagers
from fibsem_maestro.tools.support import ScanningArea, Point


class AcbGui:
    def __init__(self, window, serial_control):
        self.window = window
        self.contrast_brightness_settings = serial_control.contrast_brightness_settings
        self.mask_settings = serial_control.mask_settings
        self._acb_area = ScanningArea(Point(0,0),0,0)

        self.populate_form()
        self.acb_area = ScanningArea.from_dict(self.contrast_brightness_settings['acb_area'])

        self.build_connections()

        self.window.acbImageLabel = create_image_label(self.window.acbVerticalLayout_2)
        # add image label to the manager (for multiple image labels control)
        ImageLabelManagers.sem_manager.add_image(self.window.acbImageLabel)

        self.window.acbImageLabel.rects_to_draw.append((self.acb_area, (0, 0, 255)))

    def build_connections(self):
        self.window.setAcbPushButton.clicked.connect(self.setAcbPushButton_clicked)

    def populate_form(self):
        masks = ['none', *[x['name'] for x in self.mask_settings]]
        populate_form(self.contrast_brightness_settings, layout=self.window.acbFormLayout,
                      specific_settings={'mask_name': masks, 'acb_area': None})

    def serialize_layout(self):
        serialize_form(self.window.acbFormLayout, self.contrast_brightness_settings)

    def setAcbPushButton_clicked(self):
        self.acb_area = self.window.acbImageLabel.get_selected_area()
        self.contrast_brightness_settings['acb_area'] = self.acb_area.to_dict()
        # update view
        self.window.acbImageLabel.rect = QRect()  # clear the drawing rectangle
        self.window.acbImageLabel.update()


    @property
    def acb_area(self):
        return self._acb_area

    @acb_area.setter
    def acb_area(self, value):
        self._acb_area.update(value)  # update af area