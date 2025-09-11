import logging

from fibsem_maestro.tools.email_attention import send_email
from fibsem_maestro.settings import Settings

class ErrorHandler:
    def __init__(self, stopping_flag):
        self.settings = Settings()
        self.stopping_flag = stopping_flag

    def __call__(self, exception):
        error_behaviour_settings = self.settings('general', 'error_behaviour')

        if 'email' in error_behaviour_settings:
            try:
                send_email('Maestro - acquisition error', repr(exception))
            except Exception as e:
                logging.error('Email sending error! ' + repr(e))
        if 'stop' in error_behaviour_settings:
            self.stopping_flag.stopping_flag = True
        if 'exception' in error_behaviour_settings:
            raise RuntimeError('Acquisition error! ' + repr(exception))