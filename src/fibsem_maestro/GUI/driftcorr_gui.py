import logging
import typing

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QMessageBox

from fibsem_maestro.microscope_control.microscope import GlobalMicroscope
from fibsem_maestro.GUI.gui_tools import serialize_form, populate_form, get_module_members
from fibsem_maestro.GUI.image_label import ImageLabel, create_image_label
from image_label_manger import ImageLabelManagers
from fibsem_maestro.tools.support import ScanningArea
from fibsem_maestro.settings import Settings

class DriftCorrGui:
    def __init__(self, window, serial_control):
        self.window = window
        self.settings = Settings()
        self.build_connections()
        self.serial_control = serial_control
        self.microscope = GlobalMicroscope().microscope_instance

        self.populate_form()

        self.window.driftcorrImageLabel = create_image_label(self.window.driftcorrVerticalLayout)

        driftcorr_areas_settings = self.settings('drift_correction', 'driftcorr_areas')
        self.driftcorr_areas = DriftCorrAreas(driftcorr_areas_settings,
                                              image_label=self.window.driftcorrImageLabel,
                                              settings_chain=['drift_correction', 'driftcorr_areas'])
        # add image label to the manager (for multiple image labels control)
        ImageLabelManagers.sem_manager.add_image(self.window.driftcorrImageLabel)

    def build_connections(self):
        self.window.addDriftCorrPushButton.clicked.connect(self.addDriftCorrPushButton_clicked)
        self.window.removeDriftCorrPushButton.clicked.connect(self.removeDriftCorrPushButton_clicked)
        self.window.updateDriftCorrPushButton.clicked.connect(self.updateDriftCorrPushButton_clicked)
        self.window.testDriftCorrPushButton.clicked.connect(self.testDriftCorrPushButton_clicked)
        self.window.driftCorrUpdateImagePushButton.clicked.connect(self.driftCorrUpdateImagePushButton_clicked)

    def populate_form(self):
        driftcorr_areas_settings, driftcorr_areas_comments = self.settings('drift_correction', return_comment=True)
        driftcorr_methods = get_module_members('fibsem_maestro.drift_correction', 'mod')
        driftcorr_imaging_settings = self.settings('image','driftcorr')

        populate_form(driftcorr_areas_settings, layout=self.window.driftCorrFormLayout,
                      specific_settings={'type': driftcorr_methods, 'driftcorr_areas': None},
                      comment=driftcorr_areas_comments)

        populate_form(driftcorr_imaging_settings, layout=self.window.driftCorrImagingFormLayout,
                      specific_settings={'name': None})

    def serialize_layout(self):
        serialize_form(self.window.driftCorrFormLayout, ['drift_correction'])
        serialize_form(self.window.driftCorrImagingFormLayout, ['image', 'driftcorr'])

    def addDriftCorrPushButton_clicked(self):
        new_driftcorr_area = self.window.driftcorrImageLabel.get_selected_area()
        if new_driftcorr_area.width > 0 and new_driftcorr_area.height > 0:  # from some reason, addDriftCorrPushButton_clicked is called twice!
            self.driftcorr_areas.add(new_driftcorr_area)
            # # update view
            self.window.driftcorrImageLabel.rect = QRect()  # clear the drawing rectangle
            self.window.driftcorrImageLabel.update()

    def removeDriftCorrPushButton_clicked(self):
        self.driftcorr_areas.clear()
        self.window.driftcorrImageLabel.update()

    def updateDriftCorrPushButton_clicked(self):
        self.serialize_layout()  # save current gui settings
        self.serial_control.update_driftcorr_areas(self.window.driftcorrImageLabel.image)
        QMessageBox.information(None, 'Drift correction', 'Drift correction areas updated.')

    def testDriftCorrPushButton_clicked(self):
        self.serialize_layout()  # save current gui settings
        self.serial_control.test_driftcorr_areas()

    def driftCorrUpdateImagePushButton_clicked(self):
        applied_images_settings =  self.settings('image', 'driftcorr')
        # save actual settings
        self.serialize_layout()

        # switch to ebeam
        self.microscope.beam = self.microscope.electron_beam
        # Apply settings and grab image
        self.microscope.apply_beam_settings(applied_images_settings)

        image = self.microscope.electron_beam.grab_frame()
        ImageLabelManagers.sem_manager.update_image(image)  # update SEM image in all connected ImageLabels

class DriftCorrAreas:
    def __init__(self, driftcorr_areas: typing.List[dict], image_label: ImageLabel, settings_chain: list):
        self.image_label = image_label
        self.settings_chain = settings_chain
        self.settings = Settings()
        self._data = []
        try:
            [self.add(ScanningArea.from_dict(x)) for x in driftcorr_areas]
        except Exception as e:
            logging.error(f'Conversion of {driftcorr_areas} to scanning areas failed! All areas are omitted. ' + repr(e))
            raise Exception(e)

    def add(self, value: ScanningArea):
        self._data.append(value)
        self.image_label.rects_to_draw.append((value, (255, 0, 255)))
        self.settings.set(*self.settings_chain, value=self.to_dict())

    def get(self, index: int) -> ScanningArea:
        return self._data[index]

    def clear(self):
        self._data = []
        self.image_label.rects_to_draw = []
        self.settings.set(*self.settings_chain, value=self._data)

    def to_dict(self) -> typing.List[dict]:
        return [x.to_dict() for x in self._data]
