import logging

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QInputDialog

from fibsem_maestro.GUI.image_label import create_image_label
from image_label_manger import ImageLabelManagers
from fibsem_maestro.tools.support import ScanningArea, Point
from fibsem_maestro.microscope_control.autoscript_control import BeamControl
from gui_tools import populate_form, serialize_form, confirm_action_dialog, get_module_members, get_setters
from fibsem_maestro.settings import Settings


class AutofunctionsGui:
    def __init__(self, window, serial_control):
        self.window = window
        self.serial_control = serial_control  # needed for af init and Test
        self.settings = Settings()
        self.build_connections()

        self.window.autofunctionsImageLabel = create_image_label(self.window.autofunctionsVerticalLayout)
        # add image label to the manager (for multiple image labels control)
        ImageLabelManagers.sem_manager.add_image(self.window.autofunctionsImageLabel)

        self.selected_af = None
        self._af_area = ScanningArea(Point(0,0),0,0)
        self.autofunctionComboBox_fill()
        self.af_set()

        self.window.autofunctionsImageLabel.rects_to_draw.append((self.af_area, (0, 255, 0)))

    def autofunctionComboBox_fill(self):
        self.window.autofunctionComboBox.clear()
        af_names = [af['name'] for af in self.settings('autofunction')]
        self.window.autofunctionComboBox.addItems(af_names)

    def build_connections(self):
        self.window.cloneAutofunctionPushButton.clicked.connect(self.cloneAutoFunctionPushButton_clicked)
        self.window.removeAutofunctionPushButton.clicked.connect(self.removeAutofunctionPushButton_clicked)
        self.window.setAfAreaPushButton.clicked.connect(self.setAfAreaPushButton_clicked)
        self.window.autofunctionComboBox.currentIndexChanged.connect(self.autofunctionComboBox_changed)
        self.window.testAfPushButton.clicked.connect(self.testAfPushButton_clicked)

    def serialize_layout(self):
        """ Save GUI to Settings"""
        criterion_name = self.settings('autofunction', self.selected_af, 'criterion_name')
        image_name = self.settings('autofunction', self.selected_af, 'image_name')
        serialize_form(self.window.autofunctionFormLayout, ['autofunction', self.selected_af])
        serialize_form(self.window.autofunctionCriteriumFormLayout, ['criterion_calculation', criterion_name])
        serialize_form(self.window.autofunctionImagingFormLayout, ['image', image_name])

    def cloneAutoFunctionPushButton_clicked(self):
        text, ok = QInputDialog.getText(self.window, "New autofunction", "Autofunction name: ")

        if ok:
            new_af = dict(self.settings('autofunction', self.selected_af))  # copy dict
            new_af['name'] = text
            new_af['criterion_name'] = text
            new_af['image_name'] = text

            new_crit = dict(self.settings('criterion_calculation', self.selected_af))
            new_crit['name'] = text

            new_image = dict(self.settings('image', self.selected_af))
            new_image['name'] = text

            self.settings.append('autofunction', value=new_af)
            self.settings.append('criterion_calculation', value=new_crit)
            self.settings.append('image', value=new_image)
            self.serialize_layout()
            self.autofunctionComboBox_fill()
            self.window.autofunctionComboBox.setCurrentText(text)
            self.serial_control.initialize_autofunctions()  # autofunctions must be completely reinitalized


    def removeAutofunctionPushButton_clicked(self):
        if len(self.settings('autofunction')) > 1:
            if confirm_action_dialog():
                criterion_name = self.settings('autofunction', self.selected_af, 'criterion_name')
                image_name = self.settings('autofunction', self.selected_af, 'image_name')

                criterion = self.settings('criterion_calculation', criterion_name)
                imaging = self.settings('image', image_name)
                af = self.settings('autofunction', self.selected_af)

                self.settings.remove('criterion_calculation', value=criterion)
                self.settings.remove('image', value=imaging)
                self.settings.remove('autofunction', value=af)

                self.autofunctionComboBox_fill()
                self.window.autofunctionComboBox.setCurrentIndex(0)
                self.serial_control.initialize_autofunctions()  # autofunctions must be completely reinitalized


    def setAfAreaPushButton_clicked(self):
        if self.window.autofunctionsImageLabel.image is not None:
            self.af_area = self.window.autofunctionsImageLabel.get_selected_area()
            self.settings.set('image', self.selected_af, 'imaging_area', value = self.af_area.to_dict())
            # update view
            self.af_set()
        else:
            logging.warning('Autofocus area not set because image is not loaded!')

    def autofunctionComboBox_changed(self):
        self.af_set()

    def testAfPushButton_clicked(self):
        self.serialize_layout()
        self.serial_control.test_af(self.selected_af)

    def af_set(self):
        """ Autofunction selected by combo-box -> update all"""
        mask_settings = self.settings('mask')

        selected_af_text = self.window.autofunctionComboBox.currentText()

        if selected_af_text == '':
            return

        self.selected_af = selected_af_text

        # items for combo boxes
        # list of available autofunctions (only names)
        autofunctions = get_module_members('fibsem_maestro.autofunctions.autofunction', 'class')
        masks = ['none', *[x['name'] for x in mask_settings]]  # none + masks defined in settings
        sweepings = get_module_members('fibsem_maestro.autofunctions.sweeping', 'class')
        # all possible electron and ions setters
        sweeping_variables = ['electron_beam.' + x for x in get_setters(BeamControl)] + ['ion_beam.' + x for x in get_setters(BeamControl)]
        criteria = get_module_members('fibsem_maestro.image_criteria.criteria_math', 'func')

        af_settings, af_settings_comments = self.settings('autofunction', self.selected_af, return_comment=True)
        populate_form(af_settings, layout=self.window.autofunctionFormLayout,
                      specific_settings={'name': None, 'criterion_name': None, 'image_name': None,
                                         'autofunction': autofunctions, 'mask_name': masks,  # list is shown as combobox
                                         'sweeping_strategy': sweepings, 'variable': sweeping_variables },
                      comment=af_settings_comments)

        image_settings, image_settings_comments = self.settings('image', self.selected_af, return_comment=True)
        populate_form(image_settings, layout=self.window.autofunctionImagingFormLayout,
                      specific_settings={'name': None, 'imaging_area': None},
                      comment=image_settings_comments)

        criterion_settings, criterion_settings_comments = self.settings('criterion_calculation', self.selected_af, return_comment=True)
        populate_form(criterion_settings, layout=self.window.autofunctionCriteriumFormLayout, specific_settings={'name': None, 'mask_name': masks,
                                                                                                                 'criterion': criteria},
                      comment=criterion_settings_comments)
        imaging_area = self.settings('image', self.selected_af, 'imaging_area')
        self.af_area = ScanningArea.from_dict(imaging_area)
        self.window.autofunctionsImageLabel.rect = QRect()  # clear the drawing rectangle
        self.window.autofunctionsImageLabel.update()

    @property
    def af_area(self):
        return self._af_area

    @af_area.setter
    def af_area(self, value):
        self._af_area.update(value)  # update af area
