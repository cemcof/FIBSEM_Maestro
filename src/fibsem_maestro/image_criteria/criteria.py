import importlib
import logging
from threading import Thread

import numpy as np

from fibsem_maestro.logger import Logger
from fibsem_maestro.settings import Settings


class Criterion:
    def __init__(self, criterion_name, mask=None):
        self.settings = Settings()
        self.criterion_name = criterion_name
        self.mask = mask

        self.pixel_size = None  # pixel size is measured from image
        self.tile_width_px = None  # tile width calculated from image size
        self.border_x = 0  # border width in pixels
        self.border_y = 0  # border height in pixels
        self.img_with_border = None  # Image without border
        self._threads = []  # threads list for criterion calculation in separated thread
        # function that is called on the end of separated thread (one argument - resolution)
        self.finalize_thread_func = None
        self.crit_images = None  # series of images to calculate criterion
        self.criterion_func = None
        self.final_regions_resolution = None
        self.final_resolution = None

        criterion_func_setting = self.settings('criterion_calculation', self.criterion_name, 'criterion',
                                               return_object=True)
        # refresh self.criterion_func on every change!
        criterion_func_setting.add_handler(self.criterion_changed)
        self.criterion_changed(criterion_func_setting.value)

        final_regions_resolution_setting = self.settings('criterion_calculation', self.criterion_name,
                                                         'final_regions_resolution', return_object=True)
        # refresh self.final_regions_resolution on every change!
        final_regions_resolution_setting.add_handler(self.final_regions_resolution_changed)
        self.final_regions_resolution_changed(final_regions_resolution_setting.value)

        final_resolution_setting = self.settings('criterion_calculation', self.criterion_name,
                                                 'final_resolution', return_object=True)
        # refresh self.final_resolution on every change!
        final_resolution_setting.add_handler(self.final_resolution_changed)
        self.final_resolution_changed(final_resolution_setting.value)

    def criterion_changed(self, value):
        criteria_module = importlib.import_module('fibsem_maestro.image_criteria.criteria_math')
        self.criterion_func = getattr(criteria_module, value)

    def final_regions_resolution_changed(self, value):
        self.final_regions_resolution = getattr(np, value)

    def final_resolution_changed(self, value):
        self.final_resolution = getattr(np, value)

    def _tiles_resolution(self, img, generate_map=False, return_best_tile=False, **kwargs):
        criterion_settings = self.settings('criterion_calculation', self.criterion_name)
        tile_size = self.settings('criterion_calculation', self.criterion_name, 'tile_size')

        if min(img.shape) == 1 or len(img.shape) == 1:  # line
            logging.debug('Line image does not support tiling')
            return self.criterion_func(img, criterion_settings)

        logging.info("Tiles resolution calculation...")
        # Apply resolution border to the acquired image
        if generate_map == False:
            self.img_with_border = self._crop_image_with_border(img)
        else:
            # do not apply bordering if resolution map needed
            self.img_with_border = img
            tiles_coordinates = self._generate_image_fractions(self.img_with_border, return_coordinates=True)
            resolution_map = np.zeros_like(self.img_with_border, dtype=np.float64)

        self.tile_size_px = int(tile_size / self.pixel_size)
        self.tile_size_px -= self.tile_size_px % 4  # must be divisible by 4

        # Get resolution of each tile and calculate final resolution
        res_arr = []

        # if tile size = 0, not apply tilling
        if tile_size == 0:
            tiles = [self.img_with_border]
        else:
            tiles = self. _generate_image_fractions(self.img_with_border)

        minimal_resolution = 1
        tile_img_best_res = None
        for tile_img in tiles:
            try:
                res = self.criterion_func(tile_img, criterion_settings)
                if generate_map:
                    coordinates_array = next(tiles_coordinates)
                    resolution_map[coordinates_array[0]:coordinates_array[0]+coordinates_array[2],
                    coordinates_array[1]:coordinates_array[1] + coordinates_array[3]] = res
                if res < minimal_resolution:
                    minimal_resolution = res
                    tile_img_best_res = tile_img

            except Exception as e:
                logging.warning("Resolution calculation error on current tile. " + repr(e))
                continue
            logging.info(f'Tile resolution: {res}')
            res_arr.append(res)

        logging.info(f'Image sectioned to {len(res_arr)} sections')

        if len(res_arr) == 0:
            logging.error("Resolution not computed")
            return 0
        else:
            res_arr = np.array(res_arr)
            res_arr = res_arr[~np.isnan(res_arr)]  # remove NaN
            final_res = self.final_resolution(res_arr)  # apply final function (like min)
            result = (final_res,)
            if generate_map:
                result = result + (resolution_map,)  # append result tuple
            if return_best_tile:
                result = result + (tile_img_best_res,)  # append result tuple
            return result

    @property
    def mask_used(self):
        return self.mask is not None

    def _generate_image_fractions(self, img, overlap=0, return_coordinates=False):
        """
        Generate image fractions (tiles) with optional overlap.

        Parameters:
            img (numpy.ndarray): The input image.
            overlap (float): Proportion of overlap between tiles (0 - no overlap, 1 - complete overlap).
            return_coordinates (bool): Whether to return tile coordinates.

        Yields:
            numpy.ndarray: A generated tile from the image.
            list: [x_start, y_start, tile_width, tile_height] if return_coordinates is True.
        """
        for x in np.arange(0, img.shape[0] - self.tile_size_px + 1, int(self.tile_size_px * (1 - overlap))):
            for y in np.arange(0, img.shape[1] - self.tile_size_px + 1, int(self.tile_size_px * (1 - overlap))):
                xi = int(x)
                yi = int(y)
                if return_coordinates:
                    yield [xi, yi, self.tile_size_px, self.tile_size_px]
                else:
                    yield img[xi: xi + self.tile_size_px, yi: yi + self.tile_size_px]

    def _crop_image_with_border(self, img, return_coordinates=False):
        """
        Crop an image based on a specified border size.

        Parameters:
            img (numpy.ndarray): The input image to be cropped.
            return_coordinates (bool): Whether to return the crop coordinates.

        Returns:
            numpy.ndarray: The cropped image.
            list: [x_start, y_start, cropped_width, cropped_height] if return_coordinates is True.
        """
        border = self.settings('criterion_calculation', self.criterion_name, 'border')

        self.border_x = int(img.shape[0] * border)
        self.border_y = int(img.shape[1] * border)

        if return_coordinates:
            return [self.border_x, self.border_y, img.shape[0] - 2 * self.border_x, img.shape[1] - 2 * self.border_y]
        else:
            cropped_img = img[self.border_x: self.border_x + img.shape[0] - 2 * self.border_x,
                              self.border_y: self.border_y + img.shape[1] - 2 * self.border_y]
            return cropped_img

    def __call__(self, image, line_number=None, slice_number=None, separate_thread=False, **kwargs):
        """
        It measures selected resolution criterion on image.
        It uses masking, tiling, border exclusion.

        line_number - if set, only one line is selected from mask image

        **kwargs - all kwargs will be passed to self.finalize_thread_func
        """


        self.pixel_size = image.pixel_size

        if line_number is not None:
            image = image[:, line_number]

        self.crit_images = [image]  # only one image if not masking

        if self.mask is not None:
            self.crit_images = self.mask.get_masked_images(image, line_number)

            if self.crit_images is None:
                logging.error('Not enough masked regions for resolution calculation - masking omitted!')
                self.crit_images = [image]  # calculate resolution on entire image

        if separate_thread:
            t = Thread(target=self._calculate, args=[slice_number], kwargs=kwargs)
            t.start()
            self._threads.append(t)
        else:
            resolution = self._calculate(slice_number, **kwargs)
            # log
            Logger.create_log_criterion(self, slice_number)
            return resolution

    def _calculate(self, slice_number, **kwargs):
        # resolution from different masked regions
        logging.info('Resolution calculation started')
        region_resolutions = []

        if 'generate_map' in kwargs and kwargs['generate_map'] == True:
            if 'return_best_tile' in kwargs and kwargs['return_best_tile'] == True:
                res, map, tile = self._tiles_resolution(self.crit_images[0], **kwargs)
            else:
                res, map = self._tiles_resolution(self.crit_images[0], **kwargs)

            region_resolutions.append(res)
        else:
            if 'return_best_tile' in kwargs and kwargs['return_best_tile'] == True:
                raise ValueError('Best tile is returned only with map generation')

            for i, image in enumerate(self.crit_images):
                # region resolution
                region_resolutions.append(self._tiles_resolution(image, **kwargs))

        region_resolutions = np.array(region_resolutions)
        region_resolutions = region_resolutions[~np.isnan(region_resolutions)]  # remove NaN
        resolution = float(self.final_regions_resolution(region_resolutions))
        # pointer to external function
        if self.finalize_thread_func is not None:
            self.finalize_thread_func(resolution, slice_number,  **kwargs)
        # log
        Logger.create_log_criterion(self, slice_number)

        result = (resolution,)
        if 'generate_map' in kwargs and kwargs['generate_map'] == True:
            result = result + (map,)
        if 'return_best_tile' in kwargs and kwargs['return_best_tile'] == True:
            result = result + (tile,)
        return result

    def join_all_threads(self):
        """ Wait until all resolution calculations are finished """
        [thread.join() for thread in self._threads]
        self._threads = []
