import logging

import numpy as np

from fibsem_maestro.tools.image_tools import image_saturation_info, image_bit_dept_band
from fibsem_maestro.logger import Logger

class AutomaticContrastBrightness:
    def __init__(self, settings, microscope):
        self._settings_init(settings)
        self._microscope = microscope

    def _settings_init(self, acb_settings):
        self.acb_enabled = acb_settings['acb_enabled']
        self.mask_name = acb_settings['mask_name']
        self.allowed_saturation = acb_settings['allowed_saturation']
        self.allowed_minimal_band = acb_settings['allowed_minimal_band']
        self.p_increase_contrast = acb_settings['p_increase_contrast']
        self.p_decrease_contrast = acb_settings['p_decrease_contrast']
        self.p_brightness = acb_settings['p_brightness']
        self.acb_area = acb_settings['acb_area']

    def settings_init(self, settings):
        """ For global re-initialization of settings  (global settings always passed)"""
        self._settings_init(settings['contrast_brightness'])

    def decrease_contrast(self, decrease_value):
        d_contrast = decrease_value * self.p_decrease_contrast
        self._microscope.beam.contrast -= d_contrast
        return -d_contrast

    def increase_contrast(self, increase_value):
        d_contrast = increase_value * self.p_increase_contrast
        self._microscope.beam.contrast += d_contrast
        return d_contrast

    def decrease_brightness(self, decrease_value):
        d_brightness = decrease_value * self.p_brightness
        self._microscope.beam.brighness -= decrease_value * self.p_brightness
        return -d_brightness

    def increase_brightness(self, increase_value):
        d_brightness = increase_value * self.p_brightness
        self._microscope.beam.brighness += d_brightness
        return d_brightness

    def __call__(self, image):
        if self.acb_enabled:
            logging.info('ACB executed')

            # get statistics from image
            saturated, zeroed = image_saturation_info(image)
            image_band = image_bit_dept_band(image)

            # initial log parameters
            Logger.log_params['ACB-d_contrast'] = 0
            Logger.log_params['ACB-d_brightness'] = 0

            # too much saturation and zeoring - decrease contrast
            if saturated > self.allowed_saturation and zeroed > self.allowed_saturation:
                d_contrast = self.decrease_contrast(max(saturated-self.allowed_saturation, zeroed-self.allowed_saturation))
                logging.info(f'Contrast lowering needed. Saturated fraction: {saturated}, Zeroed fraction: {zeroed}. '
                             f'Decreased by {d_contrast}')
                Logger.log_params['ACB-d_contrast'] = d_contrast

            # too low contrast
            elif image_band < self.allowed_minimal_band:
                d_contrast = self.increase_contrast(1 - image_band)
                logging.info( f'Contrast increase needed. Used band: {image_band} is lower than allowed minimal band {self.allowed_minimal_band}.'
                              f'Increased by {d_contrast}')
                Logger.log_params['ACB-d_contrast'] = d_contrast

            # too high brightness
            elif saturated > self.allowed_saturation:
                d_brightness = self.decrease_brightness(saturated-self.allowed_saturation)
                logging.info(
                    f'Brightness lowering needed. Saturated fraction: {saturated} is higher than allowed saturation {self.allowed_saturation}.'
                    f'Decreased by {d_brightness}')

            # too low brightness
            elif zeroed > self.allowed_saturation:
                logging.info(f'Brightness increase needed. Zeroed fraction: {zeroed} is higher than allowed saturation {self.allowed_saturation}.'
                             f'')
                d_brightness = self.increase_brightness(saturated-self.allowed_saturation)
            # ok
            else:
                logging.info(f'Contrast, brightness OK. Saturated fraction: {saturated}, Zeroed fraction: {zeroed}, Used band: {image_band}.'
                             f'')

        else:
            logging.info('No acb executed')