import argparse
import logging

import shutil
import sys
import os

current_directory = os.path.dirname(os.path.abspath(__file__))
parent_directory = os.path.dirname(current_directory)
parent_directory = os.path.dirname(parent_directory)
print(f'Content root: {parent_directory}')
sys.path.append(parent_directory)

from fibsem_maestro.GUI.driftcorr_gui import DriftCorrGui
from fibsem_maestro.GUI.forms.ErrorSettingsDialog import ErrorSettingsDialog

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog
)
from PySide6.QtCore import QCoreApplication

from fibsem_maestro import version
from fibsem_maestro.GUI.forms.EmailSettingsDialog import EmailSettingsDialog
from fibsem_maestro.GUI.image_label_manger import ImageLabelManagers
from fib_gui import FibGui
from fibsem_maestro.GUI.forms.FIBSEM_Maestro_GUI import Ui_MainWindow
from fibsem_maestro.serial_control import SerialControl
from fibsem_maestro.tools.dirs_management import findfile
from sem_gui import SemGui
from autofunctions_gui import AutofunctionsGui
from acb_gui import AcbGui
from fibsem_maestro.logger import Logger
from fibsem_maestro.settings import Settings

default_settings_yaml_path = 'settings.yaml'  # default yaml settings

class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(QCoreApplication.translate("MainWindow", f"FIBSEM_Maestro v {version.VERSION}", None))
        self.settings = Settings()
        self.build_connections()
        # create and configure SerialControl
        self.sem_gui = SemGui(self, serial_control)
        self.fib_gui = FibGui(self, serial_control)
        self.autofunctions_gui = AutofunctionsGui(self, serial_control)
        self.driftcorr_gui = DriftCorrGui(self, serial_control)
        #self.acb_gui = AcbGui(self, serial_control)
        self.tabAcb.setEnabled(False)  # !!!
        ImageLabelManagers.sem_manager.clear()  # clear image label managers

        # register events
        serial_control.event_acquisition_start.append(self.acquisition_start_event_handler)
        serial_control.event_acquisition_stop.append(self.acquisition_stop_event_handler)

    def build_connections(self):
        self.actionAbout.triggered.connect(self.about_clicked)
        self.runPushButton.clicked.connect(self.runPushButton_clicked)
        self.stopPushButton.clicked.connect(self.stopPushButton_clicked)
        self.actionLoadSettings.triggered.connect(self.actionLoad_clicked)
        self.actionSaveSettings.triggered.connect(self.actionSave_clicked)
        self.actionSaveSettingsAs.triggered.connect(self.actionSaveAs_clicked)
        self.actionEmail.triggered.connect(self.actionEmail_clicked)
        self.actionErrorActions.triggered.connect(self.actionError_clicked)
        self.actionEnable_buttons.triggered.connect(self.actionEnable_buttons_clicked)

    def about_clicked(self):
        QMessageBox.about(
            self,
            "About FIBSEM_Maestro",
            f"<p>FIBSEM_Maestro v{version.VERSION}</p>"
            "<p>Pavel Krepelka</p>"
            "<p>CEITEC MU - Cryo-electron microscopy core facility</p>"
            "<p>pavel.krep@gmail.com</p>",
        )

    def runPushButton_clicked(self):
        self.apply_settings()
        dirs_output_images = self.settings('dirs', 'output_images')
        max_slice, _ = findfile(dirs_output_images)  # find the highest already acquired index
        serial_control.run(max_slice + 1)

    def stopPushButton_clicked(self):
        serial_control.stop()

    def actionSave_clicked(self):
        self.apply_settings()

    def actionSaveAs_clicked(self):
        self.apply_settings()
        file, _ = QFileDialog.getSaveFileName(self, 'Save settings file', '', 'YAML Files (*.yaml)')
        if file:
            shutil.copy(settings_yaml_path, file)

    def actionLoad_clicked(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Load settings file', '', 'YAML Files (*.yaml)')
        if file:
            shutil.copy(file, settings_yaml_path)
            settings.update(settings_yaml_path)  #
            self.populate_forms()

    def actionEmail_clicked(self):
        email_settings = self.settings('email')
        dialog = EmailSettingsDialog(email_settings)
        if dialog.exec():
            dialog.save_settings()  # save settings to dict
            # save to settings
            settings.save()

    def actionError_clicked(self):
        error_settings = self.settings('general', 'error_behaviour')
        dialog = ErrorSettingsDialog(error_settings)
        if dialog.exec():
            dialog.save_settings()  # save settings to dict
            # save to settings
            settings.save()

    def actionEnable_buttons_clicked(self):
        self.runPushButton.setEnabled(True)
        self.stopPushButton.setEnabled(True)
        serial_control.running = False

    def closeEvent(self, event):
        """ Form closing event """
        self.apply_settings()  # save on form closing

    def acquisition_start_event_handler(self):
        self.runPushButton.setEnabled(False)
        self.stopPushButton.setEnabled(True)

    def acquisition_stop_event_handler(self):
        self.runPushButton.setEnabled(True)
        self.stopPushButton.setEnabled(False)

    def apply_settings(self):
        # GUI -> settings var
        if hasattr(self, 'sem_gui'):  # can be called in initialization, that is why some components may not exist
            self.sem_gui.serialize_layout()
        if hasattr(self, 'fib_gui'):
            self.fib_gui.serialize_layout()
        if hasattr(self, 'autofunctions_gui'):
            self.autofunctions_gui.serialize_layout()
        if hasattr(self, 'driftcorr_gui'):
            self.driftcorr_gui.serialize_layout()
        # if hasattr(self, 'acb_gui'):
        #     self.acb_gui.serialize_layout()

        settings.save()

    def populate_forms(self):
        # settings var -> GUI
        if hasattr(self, 'sem_gui'):  # can be called in initialization, that is why some components may not exist
            self.sem_gui.populate_form()
        if hasattr(self, 'fib_gui'):
            self.fib_gui.populate_form()
        if hasattr(self, 'autofunctions_gui'):
            self.autofunctions_gui.af_set()
        if hasattr(self, 'driftcorr_gui'):
            self.driftcorr_gui.populate_form()
        # if hasattr(self, 'acb_gui'):
        #     self.acb_gui.populate_form()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    parser = argparse.ArgumentParser(description="FIBSEM_Maestro v"+version.VERSION)
    parser.add_argument('-p', action="store", dest="default_folder", type=str, required=False,
                        help="Default project folder path")
    parser.add_argument('--virtual', action="store_true",
                        help="Virtual mode (without connection to microscope)")
    args = parser.parse_args()


    # folder path as argument
    if args.default_folder:
        folder_path = args.default_folder
    else:
        folder_path = QFileDialog.getExistingDirectory(None, 'Select Project Folder')

    if folder_path:  # If directory string is not empty
        settings_yaml_path = os.path.join(folder_path, 'settings.yaml')
        # if settings file does not exist - copy default
        if not os.path.exists(settings_yaml_path):
            shutil.copy(default_settings_yaml_path, settings_yaml_path)

        # enables virtual mode
        if args.virtual:
            pass
            # TODO: control virtual mode

        # settings must be loaded before Logger
        settings = Settings()
        settings.load(settings_yaml_path)

        serial_control = SerialControl()
        serial_control.change_dir_settings(folder_path)  # change dirs settings to correct project folder
        settings.save()

        # turn on initial logging (to the execute folder)
        Logger.init(None)

        win = Window()
        win.show()
        sys.exit(app.exec())
