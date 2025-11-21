from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QCheckBox
from fibsem_maestro.tools.email_attention import send_email
from fibsem_maestro.settings import Settings

class ErrorSettingsDialog(QDialog):
    def __init__(self, error_settings, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Error settings")

        self.layout = QVBoxLayout()

        self.label1 = QLabel("Error behaviour:")
        self.checkbox_email = QCheckBox(text='Email attention')
        self.checkbox_stop = QCheckBox(text='Stop acquisition')
        self.checkbox_exception = QCheckBox(text='Quit application')

        self.checkbox_email.setChecked('email' in error_settings)
        self.checkbox_stop.setChecked('stop' in error_settings)
        self.checkbox_exception.setChecked('exception' in error_settings)

        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.accept)

        self.layout.addWidget(self.label1)
        self.layout.addWidget(self.checkbox_email)
        self.layout.addWidget(self.checkbox_stop)
        self.layout.addWidget(self.checkbox_exception)
        self.layout.addWidget(self.ok_button)

        self.setLayout(self.layout)

    def save_settings(self):
        error_behaviour = []
        if self.checkbox_email.isChecked():
            error_behaviour.append('email')
        if self.checkbox_stop.isChecked():
            error_behaviour.append('stop')
        if self.checkbox_exception.isChecked():
            error_behaviour.append('exception')

        settings = Settings()
        settings.set('general', 'error_behaviour', value=error_behaviour)