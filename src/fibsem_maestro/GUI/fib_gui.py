from PySide6.QtWidgets import QMessageBox

from fibsem_maestro.GUI.gui_tools import populate_form, serialize_form
from fibsem_maestro.GUI.image_label import create_image_label
from fibsem_maestro.tools.support import Image, ScanningArea, Point
from fibsem_maestro.settings import Settings
from fibsem_maestro.microscope_control.microscope import GlobalMicroscope

class FibGui:
    def __init__(self, window, serial_control):
        self.window = window
        self.serial_control = serial_control
        self.microscope = GlobalMicroscope().microscope_instance
        self.settings = Settings()

        self.populate_form()
        self.build_connections()

        self._fiducial_area = ScanningArea(Point(0,0),0,0)
        self._extended_fiducial_area = ScanningArea(Point(0,0),0,0)
        self._milling_area = ScanningArea(Point(0,0),0,0)
        self._milling_mark = ScanningArea(Point(0, 0), 0, 0)

        self.window.fibImageLabel = create_image_label(self.window.fibVerticalLayout)
        self.window.fibImageLabel.rects_to_draw.append((self._fiducial_area, (255, 0, 0))) # RGB color
        self.window.fibImageLabel.rects_to_draw.append((self._extended_fiducial_area, (130, 150, 11)))  # RGB color
        self.window.fibImageLabel.rects_to_draw.append((self._milling_area, (0, 0, 255)))  # RGB color
        self.window.fibImageLabel.rects_to_draw.append((self._milling_mark, (30, 30, 255)))  # RGB color

    def build_connections(self):
        self.window.getFibImagePushButton.clicked.connect(self.getFibImagePushButton_clicked)
        self.window.setFibFiducialPushButton.clicked.connect(self.setFibFiducialPushButton_clicked)
        self.window.setFibAreaPushButton.clicked.connect(self.setFibAreaPushButton_clicked)
        self.window.makeSlicePushButton.clicked.connect(self.makeSlicePushButton_clicked)
        self.window.loadFibSettingsPushButton.clicked.connect(self.loadFibSettingsPushButton_clicked)

    def populate_form(self):
        fib_settings, fib_settings_comments = self.settings('milling', return_comment=True)

        populate_form(fib_settings, layout=self.window.fibFormLayout,
                      specific_settings={'variables_to_save':None,'settings_file':None,'fiducial_area':None,
                                         'milling_area':None},
                      comment=fib_settings_comments)

    def serialize_layout(self):
        serialize_form(self.window.fibFormLayout, ['milling'])

    def getFibImagePushButton_clicked(self):
        fiducial_area = self.settings('milling', 'fiducial_area')
        milling_area = self.settings('milling', 'milling_area')

        if hasattr(self.microscope, 'is_virtual'):
            raise NotImplementedError('Load image in virtual mode')
            from autoscript_sdb_microscope_client.structures import AdornedImage
            #image = Image.from_as(AdornedImage.load('/home/cemcof/Downloads/cell.tif'))
            #image = Image.from_as(AdornedImage.load('D:\ceitec_data\ins - fccb\data\raw\slice_00547_(0).tif'))

        if self.serial_control.running:
            QMessageBox.critical(None, 'FIB image', 'Cannot take image in running job.')
        else:
            image = self.microscope.ion_beam.get_image()
            self.window.fibImageLabel.setImage(image)
            self.fiducial_area = ScanningArea.from_dict(fiducial_area)
            self.milling_area = ScanningArea.from_dict(milling_area)


    def setFibFiducialPushButton_clicked(self):
        self.serialize_layout()  # update fib_settings (fiducial_margin)
        self.window.fibImageLabel.reset_zoom_pan()
        selected_area = self.window.fibImageLabel.get_selected_area()
        if selected_area is not None and selected_area.width > 0 and selected_area.height > 0:
            self.fiducial_area = self.window.fibImageLabel.get_selected_area()
            self.settings.set('milling', 'fiducial_area', value=self.fiducial_area.to_dict())

        self.serial_control.milling_init()

    def setFibAreaPushButton_clicked(self):
        selected_area = self.window.fibImageLabel.get_selected_area()
        if selected_area is not None and selected_area.width > 0 and selected_area.height > 0:
            self.serialize_layout()  # update fib_settings (direction)
            self.window.fibImageLabel.reset_zoom_pan()
            self.milling_area = selected_area
            # update settings (not in layout)
            self.settings.set('milling', 'milling_area', value=self.milling_area.to_dict())

    def makeSlicePushButton_clicked(self):
        self.serialize_layout()
        self.serial_control.milling(slice_number=-1)

    def loadFibSettingsPushButton_clicked(self):
        self.serial_control.milling_load()

    @property
    def milling_area(self):
        return self._milling_area


    @milling_area.setter
    def milling_area(self, value):
        direction = self.settings('milling', 'direction')

        self._milling_area.update(value)
        # update milling area mark
        img_shape = self.window.fibImageLabel.image.shape
        # milling area marker
        pos, size = self._milling_area.to_img_coordinates(img_shape)
        direction = direction
        # position of direction mark
        if direction > 0:
            pos.y += 10  # move in y
        else:
            pos.y += size[1] - 20
        self._milling_mark.update(ScanningArea.from_image_coordinates(img_shape, pos.x, pos.y, 10, 10))
        self.serial_control.milling_reset()  # reset position

    @property
    def fiducial_area(self):
        return self._fiducial_area

    @fiducial_area.setter
    def fiducial_area(self, value):
        fiducial_margin = self.settings('milling', 'fiducial_margin')

        self._fiducial_area.update(value)  # update fiducial
        # update extended fiducial area
        pixel_size = self.window.fibImageLabel.image.pixel_size
        img_shape = self.window.fibImageLabel.image.shape
        border = fiducial_margin
        left_top, size = self._fiducial_area.to_meters(img_shape, pixel_size)
        """ Calculate and show the extended fiducial area (fiducial area + border)"""
        extended_fiducial_area = ScanningArea.from_meters(img_shape, pixel_size, left_top.x-border, left_top.y-border,
                                                 size[0]+2*border, size[1]+2*border)  # update extended fiducial area
        self._extended_fiducial_area.update(extended_fiducial_area)