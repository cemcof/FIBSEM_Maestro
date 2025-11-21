import logging
import os

from fibsem_maestro.tools.support import fold_filename


class MaskDriftCorrection:
    """ Drift correction keep the center of masked blob in the center of FoV"""
    def __init__(self, mask, microscope, logging_dict, log_dir=None):
        assert mask is not None, 'Mask not found. Drift correction failed.'

        self._mask = mask
        self._microscope = microscope
        self.logging_dict = logging_dict
        self.log_dir = log_dir

    def __call__(self, slice_number=None):
        # get center of blob
        self.current_position = self._mask.get_center()
        # get center of mask image
        center = self._mask.image_ceter
        pixel_size = self._mask.image_pixel_size
        if self.current_position is not None:
            shift_x = (center[0] - self.current_position[0]) * pixel_size
            shift_y = (center[1] - self.current_position[1]) * pixel_size
            self.logging_dict[f"shift_x"] = shift_x
            self.logging_dict[f"shift_y"] = shift_y
            self._save_log_images(slice_number)
        else:
            logging.warning('The position in mask drift correction is not defined!')


    @property
    def mask(self):
        return self._mask

    def _save_log_images(self, slice_number):
        mask_filename = fold_filename(self.log_dir, slice_number, postfix="drift_correction")
        self.mask.save_log_images(mask_filename)
