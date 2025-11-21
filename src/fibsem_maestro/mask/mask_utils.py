import importlib
import logging

import numpy as np
from patchify import patchify, unpatchify
from scipy.ndimage import zoom, binary_fill_holes

from fibsem_maestro.tools.image_tools import center_padding, center_cropping


class ImageSizeConvertor:
    """ Converts image to different size (crop or/and pad)"""
    def __init__(self, image, target_size):
        self.image = image
        self.target_size = target_size

    def _padding(self, img):
        return center_padding(img, self.target_size)

    def _cropping(self, img):
        return center_cropping(img, self.target_size)

    def __call__(self):
        goal_image = self._padding(self.image) # padding if needed
        goal_image = self._cropping(goal_image)  # padding if needed
        return goal_image


class ImagePreparator:
    """ Prepare image for model prediction: downsampling + padding + patchify
    and unpack prediction segmented image to image format"""

    def __init__(self, patch_size, downsampling_factor, fill_holes):
        self.patch_size = patch_size
        self.downsampling_factor = downsampling_factor
        self.fill_holes = fill_holes
        self.original_shape = None
        self.original_padded_shape = None
        self.original_patches_shape = None

    def prepare_image_for_prediction(self, img):
        """ Input image -> prediction format"""
        self.original_shape = img.shape
        # downsampling
        input_image = zoom(img, 1 / self.downsampling_factor)

        # padding
        pad_height = self.patch_size[0] - (input_image.shape[0] % self.patch_size[0]) \
            if (input_image.shape[0] % self.patch_size[0]) != 0 else 0
        pad_width = self.patch_size[1] - (input_image.shape[1] % self.patch_size[1]) \
            if (input_image.shape[1] % self.patch_size[1]) != 0 else 0
        input_image = np.pad(input_image, ((0, pad_height), (0, pad_width)), mode='constant')
        self.original_padded_shape = input_image.shape

        # split to patches
        input_image = patchify(input_image, self.patch_size, step=self.patch_size[0])
        self.original_patches_shape = input_image.shape

        # merge patches to one axis
        input_image = input_image.reshape(-1, *input_image.shape[2:])[
            ..., np.newaxis]  # merge first two axis and add depth
        return input_image

    def get_mask_image_from_prediction(self, img):
        """ Predicted format -> Output image in file format"""
        # reshape back to image size
        output_image = img.reshape(self.original_patches_shape)
        output_image = unpatchify(output_image, self.original_padded_shape)
        output_image = zoom(output_image, self.downsampling_factor)  # upsampling
        output_image = output_image[0:self.original_padded_shape[0],
                       0:self.original_padded_shape[1]]
        # convert to binary
        output_image[output_image > 0.5] = 1
        output_image[output_image <= 0.5] = 0
        if self.fill_holes:
            output_image = binary_fill_holes(output_image)
        output_image = output_image.astype(np.uint8)
        return output_image


class TfModel(ImagePreparator):
    """ Load tensorflow model and execute it """
    def __init__(self, model_path, iterative_training, patch_size, downsampling_factor, fill_holes):
        super().__init__(patch_size, downsampling_factor, fill_holes)
        self.iterative_training = iterative_training
        self.model_path = model_path
        self.load_model()

    def load_model(self):
        try:
            module = importlib.import_module(self.model_path)
            self._model = module.load_model()
        except Exception as e:
            logging.error(f'Error in loading model {self.model_path}' + repr(e))
            self._model = None

    def predict(self, image):
        """ Predict segmentation from image """
        # convert image to the form suitable for prediction
        input_image = self.prepare_image_for_prediction(image)
        # predict mask
        predicted = self._model(input_image).numpy()[..., 1]
        # unpack mask to image format
        mask = self.get_mask_image_from_prediction(predicted)

        if self.iterative_training:
            mask_for_training = self.prepare_image_for_prediction(mask)
            self._model.fit(input_image, mask_for_training, {
                'epochs': 1,
                'batchSize': 16
            })

        return mask
