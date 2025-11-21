# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 10:31:42 2024

@author: pavel
"""

# Gmail setting:
# https://stackoverflow.com/questions/10147455/how-to-send-an-email-with-gmail-as-provider-using-python/27515833#27515833

import os
import smtplib
import logging
from fibsem_maestro.settings import Settings


def send_email(subject, text):
    settings = Settings()
    sender = settings('email', 'sender')
    receiver = settings('email', 'receiver')
    password_file = settings('email', 'password_file')

    if os.path.exists(password_file):
        with open(password_file) as f:
            password = f.readline()
    else:
        print(f"{password_file} not found.")
        return False

    if sender is not None and receiver is not None:
        print("Sending email.")
        try:
            smtpserver = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            smtpserver.ehlo()
            smtpserver.login(sender, password)

            # Test send mail
            email_text = f'Subject: {subject}\n\n {text}'
            smtpserver.sendmail(sender, receiver, email_text)

            # Close the connection
            smtpserver.close()
            print('Email sent!')
            return True
        except Exception as e:
            logging.error('Email error. ' + repr(e))
            return False
