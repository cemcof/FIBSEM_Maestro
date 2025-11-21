import math
import re

import numpy
import numpy as np


class Point:
    def __init__(self, x=0, y=0):
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, x):
        self._x = x

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, y):
        self._y = y

    @staticmethod
    def from_point_as(point_as):
        """Create a Point instance from a AS Point instance."""
        return Point(x=point_as.x, y=point_as.y)

    def to_array(self):
        return [self.x, self.y]

    def to_dict(self):
        return vars(self)

    def __mul__(self, other):
        if isinstance(other, Point):
            return Point(self.x * other.x, self.y * other.y)
        if isinstance(other, (float, int)):
            return Point(self.x * other, self.y * other)
        elif isinstance(other, (list, tuple)):
            return Point(self.x * other[0], self.y * other[1])
        else:
            return TypeError("Unsupported operand type")

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        else:
            raise TypeError("Unsupported operand type")

    def __sub__(self, other):
        if isinstance(other, Point):
            return Point(self.x - other.x, self.y - other.y)
        else:
            raise TypeError("Unsupported operand type")

    def __str__(self):
        return f"Point({self.x}, {self.y})"

    @classmethod
    def from_str(cls, point_string):
        # Extract the coordinates from the string
        x, y = map(float, point_string[6:-1].split(', '))
        return cls(x, y)


class StagePosition:
    """
    Class representing the stage position
    Rotation and tilt is in deg
    """

    def __init__(self, x=0.0, y=0.0, z=0.0, rotation=0.0, tilt=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.rotation = rotation
        self.tilt = tilt

    @staticmethod
    def from_stage_position_as(stage_position_as):
        """Create a StagePosition instance from a AS StagePosition instance."""
        return StagePosition(x=stage_position_as.x, y=stage_position_as.y, z=stage_position_as.z,
                             rotation=math.degrees(stage_position_as.r),
                             tilt=math.degrees(stage_position_as.t))

    def to_stage_position_as(self):
        """Convert StagePosition to AS StagePosition instance."""
        from autoscript_sdb_microscope_client.structures import StagePosition as StagePositionAS
        stage_dict = self.to_dict()
        stage_dict['r'] = math.radians(stage_dict['rotation'])
        stage_dict['t'] = math.radians(stage_dict['tilt'])
        del stage_dict['rotation']
        del stage_dict['tilt']
        return StagePositionAS(**stage_dict, coordinate_system="Specimen")

    def to_dict(self):
        return vars(self)

    def to_xy(self):
        return self.x, self.y

    def __str__(self):
        return f"StagePosition({self.x}, {self.y}, {self.z}, {self.rotation}, {self.tilt})"

    @classmethod
    def from_str(cls, point_string):
        # Extract the coordinates from the string
        x, y, z, r ,t = map(float, point_string[14:-1].split(', '))
        return cls(x, y, z, r, t)


class Image(np.ndarray):
    def __new__(cls, image, pixel_size):
        obj = np.asarray(image.data).view(cls)
        obj.pixel_size = pixel_size
        return obj

    def get8bit_clone(self):
        """ Get 8 bit version of self"""
        pixel_size = self.pixel_size
        output = self.copy()
        if np.max(output) > 255:
            output = output / np.max(output) * 255
        output = np.ascontiguousarray(np.uint8(output))
        return Image(output, pixel_size)

    def transpose(self, __axes=None):
        # ascontiguousarray needed for QPixmap
        return Image(np.ascontiguousarray(self.T), self.pixel_size)

    @staticmethod
    def from_as(adorned_image):
        pixel_size = adorned_image.metadata.binary_result.pixel_size.x
        image = Image(np.asarray(adorned_image.data), pixel_size)
        return image.transpose()

    def __array_finalize__(self, obj):
        if obj is None: return
        self.pixel_size = getattr(obj, 'pixel_size', None)

    @property
    def height(self):
        return self.shape[1]

    @property
    def width(self):
        return self.shape[0]

    def __getitem__(self, index):
        result = super(Image, self).__getitem__(index)
        if type(result) is Image:
            return result
        else:
            return Image(result, self.pixel_size)


class ScanningArea:
    def __init__(self, leftop: Point, width: float, height: float):
        """ Area defined as the fraction (center of the image = 0.5)"""
        self.leftop = leftop
        self.width = width
        self.height = height

    def update(self, scanning_area):
        self.leftop = scanning_area.leftop
        self.width = scanning_area.width
        self.height = scanning_area.height

    def to_as(self):
        from autoscript_sdb_microscope_client.structures import Rectangle
        """ Convert the coordinates to AS coordinates """
        return Rectangle(left=self.leftop.x, top=self.leftop.y, width=self.width, height=self.height)

    def to_img_coordinates(self, img_shape):
        """
        Calculate the coordinates of an object in an image based on its relative position and size.

        :param img_shape: The shape of the image as a tuple (height, width).
        :type img_shape: tuple
        :return: The left top coordinates of the object and its size as a tuple.
        :rtype: tuple
        """
        leftop_pix = self.leftop * img_shape
        width_pix = img_shape[0] * self.width
        height_pix = img_shape[1] * self.height
        left_top = [int(leftop_pix.x), int(leftop_pix.y)]
        return Point(*left_top), [int(width_pix), int(height_pix)]

    def to_meters(self, img_shape, pixel_size):
        """ Calculate the coordinates of an object in a real size (with known pixel_size) based on its relative position and size."""
        left_top, [width_pix, height_pix] = self.to_img_coordinates(img_shape)
        return Point(left_top.x * pixel_size, left_top.y * pixel_size), [width_pix * pixel_size, height_pix * pixel_size]

    def to_dict(self):
        return {'x': self.leftop.x, 'y': self.leftop.y, 'width': self.width, 'height': self.height}

    def __str__(self):
        return f"ScanningArea({self.leftop.x}, {self.leftop.y}, {self.width}, {self.height})"

    @staticmethod
    def from_str(point_string):
        # Extract the coordinates from the string
        # Remove label 'ScanningArea'
        x, y, w, h = map(float, point_string[13:-1].split(', '))
        return ScanningArea(Point(x, y), w, h)

    @staticmethod
    def from_image_coordinates(img_shape, left, top, width, height):
        """ Extract the coordinates from position in image"""
        ratio_x = left / img_shape[0]
        ratio_y = top / img_shape[1]
        ratio_w = width / img_shape[0]
        ratio_h = height / img_shape[1]
        return ScanningArea(Point(ratio_x, ratio_y), ratio_w , ratio_h)

    @staticmethod
    def from_meters(img_shape, pixel_size, left, top, width, height):
        return ScanningArea.from_image_coordinates(img_shape,
                                                   int(left/pixel_size),
                                                   int(top/pixel_size),
                                                   int(width/pixel_size),
                                                   int(height/pixel_size))
    @staticmethod
    def from_dict(d):
        return ScanningArea(Point(d['x'], d['y']), d['width'] , d['height'])

    @staticmethod
    def from_as(d):
        return ScanningArea(Point(d.left, d.top), d.width, d.height)



def fold_filename(log_dir, slice_number, postfix=""):
    """return: log_dir+slice_number+postfix"""
    if slice_number is None:
        slice_number = -1
    filename = log_dir + f'/{slice_number:05}/{postfix}'
    return filename
