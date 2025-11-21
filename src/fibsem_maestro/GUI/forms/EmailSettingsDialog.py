from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from fibsem_maestro.tools.email_attention import send_email
from fibsem_maestro.settings import Settings

class EmailSettingsDialog(QDialog):
    def __init__(self, email_settings, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Email settings")

        self.layout = QVBoxLayout()

        self.label1 = QLabel("Password file:")
        self.entry_password_file = QLineEdit(self)
        self.entry_password_file.setText(email_settings['password_file'])  # Set default text for Entry 1

        self.label2 = QLabel("Receiver address")
        self.entry_receiver = QLineEdit(self)
        self.entry_receiver.setText(email_settings['receiver'])  # Set default text for Entry 2

        self.label3 = QLabel("Sender address")
        self.entry_sender = QLineEdit(self)
        self.entry_sender.setText(email_settings['sender'])  # Set default text for Entry 3

        self.test_button = QPushButton('Test')
        self.test_button.clicked.connect(self.test)

        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.accept)

        self.layout.addWidget(self.label1)
        self.layout.addWidget(self.entry_password_file)
        self.layout.addWidget(self.label2)
        self.layout.addWidget(self.entry_receiver)
        self.layout.addWidget(self.label3)
        self.layout.addWidget(self.entry_sender)
        self.layout.addWidget(self.test_button)
        self.layout.addWidget(self.ok_button)

        self.setLayout(self.layout)

    def save_settings(self):
        settings = Settings()
        settings.set('email', 'sender', value= self.entry_sender.text())
        settings.set('email', 'receiver', value=self.entry_receiver.text())
        settings.set('email', 'password_file', value=self.entry_password_file.text())

    def test(self):
        self.save_settings()
        if send_email("Maestro TEST", 'This is email test. Maestro is cool!'):
            QMessageBox.information(None, "Success", "The email has been successfully sent!")
        else:
            QMessageBox.critical(None, "Error", "An error occurred while sending the email!")