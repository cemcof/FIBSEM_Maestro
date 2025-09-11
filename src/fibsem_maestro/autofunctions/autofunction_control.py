import importlib
import logging

from colorama import Fore

from fibsem_maestro.microscope_control.microscope import GlobalMicroscope
from fibsem_maestro.tools.email_attention import send_email
from fibsem_maestro.logger import Logger
from fibsem_maestro.settings import Settings


class AutofunctionControl:
    """ Initialize all autofunctions, it keep af queue and send emails """
    def __init__(self, masks=None):
        self.settings = Settings()
        self._microscope = GlobalMicroscope().microscope_instance

        self._masks = masks
        self.scheduler = []  # queue of autofunctions waiting to execute

        autofunction_settings = self.settings('autofunction', return_object=True)
        # list of all autofunctions objects
        self.autofunctions = [self._get_autofunction(idx, x) for idx, x in enumerate(autofunction_settings)]

    def _get_autofunction(self, idx, af_setting):
        # replace Autofunction class if changed
        af_setting['autofunction'].add_handler(self.autofunction_changed(idx))

        # select autofunction based on autofunction setting (settings.yaml)
        autofunction_module = importlib.import_module('fibsem_maestro.autofunctions.autofunction')
        Autofunction = getattr(autofunction_module, af_setting['autofunction'].value)
        return Autofunction(af_setting['name'].value)

    def autofunction_changed(self, idx):
        def autofunction_base_changed(value):
            autofunction_module = importlib.import_module('fibsem_maestro.autofunctions.autofunction')
            new_af = getattr(autofunction_module, value)
            self.autofunctions[idx] = new_af(self.autofunctions[idx].auto_function_name)
        return autofunction_base_changed

    def _email_attention(self):
        try:
            send_email("Maestro alert!", f"{self.active_autofunction.attempt} "
                       f"attempts of AF failed. Acquisition stopped!")
        except Exception as e:
            logging.error("Sending email error. " + repr(e))
        print(f"Number of focusing attempts exceeds allowed level ({self.active_autofunction.max_attempts}).")
        print("Perform manual inspection and press enter")
        input()

    def __call__(self, slice_number, image_resolution, image_for_mask=None):
        """
        Autofunctions handling.
        :param slice_number: the number of the current image slice
        :param image_resolution: the resolution of the image
        :param image_for_mask: an optional image used for masking
        :return: None
        """
        # check firing conditions of all autofunctions
        for af in self.autofunctions:
            # Add af to scheduler if condition passed
            if af.check_firing(slice_number, image_resolution):
                if af not in self.scheduler:
                    af.set_sweep()  # set sweeping base
                    self.scheduler.append(af)
                    logging.info(f'{af.auto_function_name} autofunction added to scheduler')
                else:
                    print(Fore.YELLOW, f'Autofunction {af.auto_function_name} already executed. It will not be added to the scheduler')

        # log active autofunctions
        Logger.log_params['active_af'] = [x.auto_function_name for x in self.scheduler]

        # any AF in scheduler in queue
        if len(self.scheduler) > 0:
            af = self.active_autofunction

            print(Fore.GREEN, f'Executed autofunction: {af.auto_function_name}. Attempt no {af.attempt}.')

            # if too much number of attempts, send email - is valid only for non-poke af. Poke is call by evaluate_image
            if af.attempt >= af.max_attempts:
                print(Fore.RED, f'Autofunction fail.')
                self._email_attention()
                self.remove_active_af()
                af.attempt = 1
            else:
                # run af
                if af(image_for_mask, slice_number=slice_number):  # run af
                    # if finished
                    self.remove_active_af()

    def remove_active_af(self):
        self.scheduler.pop(0)  # remove the finished af

    def get_autofunction(self, auto_function_name):
        if auto_function_name == 'none':
            return None
        else:
            return [dic for dic in self.autofunctions if dic.auto_function_name == auto_function_name][0]

    def test_af(self, name):
        """ Perform af test (af selected by name)"""
        self._microscope.beam = self._microscope.electron_beam
        af = self.get_autofunction(name)
        af.set_sweep()
        af.test()

    @ property
    def active_autofunction(self):
        if len(self.scheduler) > 0:
            return self.scheduler[0]
        else:
            return None
