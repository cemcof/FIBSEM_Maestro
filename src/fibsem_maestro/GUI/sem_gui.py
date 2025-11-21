import logging
import math

from PySide6.QtCore import QRect

from fibsem_maestro.GUI.image_label import create_image_label
from fibsem_maestro.microscope_control.autoscript_control import AutoscriptMicroscopeControl
from fibsem_maestro.microscope_control.microscope import GlobalMicroscope
from fibsem_maestro.tools.dirs_management import findfile
from gui_tools import populate_form, serialize_form, get_module_members, change_setting_gui
from fibsem_maestro.tools.support import Image, Point, ScanningArea
from image_label_manger import ImageLabelManagers
from fibsem_maestro.settings import Settings


class SemGui:
    def __init__(self, window, serial_control):
        self.window = window
        # selected imaging settings
        self.serial_control = serial_control  # needed for image get and running flag
        self.microscope = GlobalMicroscope().microscope_instance
        self.settings = Settings()

        self.populate_form()
        self.build_connections()

        self.window.imageLabel = create_image_label(self.window.semVerticalLayout)

        # add image label to the manager (for multiple image labels control)
        ImageLabelManagers.sem_manager.add_image(self.window.imageLabel)

    def build_connections(self):
        self.window.getImagePushButton.clicked.connect(self.getImagePushButton_clicked)
        self.window.setImagingPushButton.clicked.connect(self.setImagingPushButton_clicked)
        self.window.testImagingPushButton.clicked.connect(self.testImagingPushButton_clicked)
        self.window.alignedImagingDirectionPushButton.clicked.connect(self.alignedImagingDirectionPushButton_clicked)
        self.window.alignedSampleSurfacePushButton.clicked.connect(self.alignedSampleSurfacePushButton_clicked)

    def populate_form(self):
        imaging_name = self.settings('acquisition', 'image_name')
        image_settings, image_settings_comment = self.settings('image', imaging_name, return_comment=True)
        criterion_name = self.settings('acquisition', 'criterion_name')
        criterion_settings, criterion_settings_comment = self.settings('criterion_calculation', criterion_name,  return_comment=True)
        acquisition_settings, acquisition_settings_comment = self.settings('acquisition', return_comment=True)
        mask_settings = self.settings('mask')

        populate_form(acquisition_settings, layout=self.window.semFormLayout,
                      specific_settings={'image_name':None, 'criterion_name':None},
                      comment=acquisition_settings_comment)
        populate_form(image_settings, layout=self.window.imageSettingsFormLayout,
                      specific_settings={'name':None, 'criterion_name':None, 'imaging_area':None},
                      comment=image_settings_comment)

        masks = ['none', *[x['name'] for x in mask_settings]]  # none + masks defined in settings
        criteria = get_module_members('fibsem_maestro.image_criteria.criteria_math', 'func')
        populate_form(criterion_settings, layout=self.window.imageCriterionFormLayout,
                      specific_settings={'name': None, 'mask_name': masks, 'criterion': criteria},
                      comment=criterion_settings_comment)

    def serialize_layout(self):
        imaging_name = self.settings('acquisition', 'image_name')
        criterion_name = self.settings('acquisition', 'criterion_name')

        serialize_form(self.window.semFormLayout, ['acquisition'])
        serialize_form(self.window.imageSettingsFormLayout, ['image', imaging_name])
        serialize_form(self.window.imageCriterionFormLayout, ['criterion_calculation', criterion_name])

    def getImagePushButton_clicked(self):
        # if acquisition running -> get last image
        dirs_output_images = self.settings('dirs', 'output_images')

        if hasattr(self.microscope, 'is_virtual'):
            from autoscript_sdb_microscope_client.structures import AdornedImage
            # image = Image.from_as(AdornedImage.load('/home/cemcof/Downloads/cell.tif'))
            image = Image.from_as(AdornedImage.load('img.tif'))
        elif self.serial_control.running:
            _, img_filename = findfile(dirs_output_images)
            # load image if AS is used
            if isinstance(self.microscope, AutoscriptMicroscopeControl):
                from autoscript_sdb_microscope_client.structures import AdornedImage
                image = Image.from_as(AdornedImage.load(img_filename))
            else:
                raise NotImplementedError('Image loading of non-autoscript type is not implemented')
        else:
            image = self.microscope.electron_beam.get_image()

        ImageLabelManagers.sem_manager.update_image(image)

    def setImagingPushButton_clicked(self):
        """ Set imaging on selected area """
        extended_resolution = self.settings('acquisition', 'extended_resolution')
        imaging_name = self.settings('acquisition', 'image_name')

        if self.window.imageLabel.image is not None:
            pixel_size = self.window.imageLabel.image.pixel_size
            img_shape = self.window.imageLabel.image.shape

            if extended_resolution:
                shift, fov = self.window.imageLabel.get_selected_area().to_meters(img_shape, pixel_size)  # drew image
                # shift leftop to image center
                shift = shift - Point((img_shape[0]//2)*pixel_size, (img_shape[1]//2)*pixel_size)
                # shift center to image center
                shift = shift + Point(fov[0]/2, fov[1]/2)
                # correct direction of beam shift with respect to image location
                shift = shift * self.microscope.electron_beam.image_to_beam_shift
                # apply shift and fov change
                self.microscope.add_beam_shift_with_verification(shift)
                change_setting_gui(self.window.imageSettingsFormLayout, 'field_of_view', fov)  # change in GUI
                # Zero scanning area
                self.settings.set('image', imaging_name, 'imaging_area', value=ScanningArea(Point(0,0),0,0).to_dict())
            else:
                fov = [img_shape[0] * pixel_size, img_shape[1] * pixel_size]
                change_setting_gui(self.window.imageSettingsFormLayout, 'field_of_view', fov)  # change in GUI
                imaging_area = self.window.imageLabel.get_selected_area()
                self.settings.set('image', imaging_name, 'imaging_area', value=imaging_area.to_dict())

             # save beam shift to microscope_settings.yaml
            self.serial_control.save_sem_settings()  # save microscope settings to file
            self.window.imageLabel.rect = QRect()  # clear the rectangle
            self.testImagingPushButton_clicked()
        else:
            logging.warning('No image selected')

    def testImagingPushButton_clicked(self):
        """Acquire image and show im imageLabel"""
        # save actual settings
        self.serialize_layout()

        imaging_name = self.settings('acquisition', 'image_name')
        image_settings = self.settings('image', imaging_name)

        # Load microscope settings from file
        self.serial_control.load_sem_settings()
        applied_images_settings = image_settings

        # Fast scan checkbox reduces dwell or LI
        if self.window.fastScanCheckBox.isChecked():
            if applied_images_settings['dwell'] > 200e-9:
                applied_images_settings['dwell'] = 200e-9
            if applied_images_settings['images_line_integration'] > 1:
                applied_images_settings['images_line_integration'] //= 2

        # Apply settings and grab image
        self.microscope.apply_beam_settings(applied_images_settings)

        if self.window.fastScanCheckBox.isChecked():
            while self.microscope.beam.resolution[0] * self.microscope.beam.resolution[1] > 25165824:
                new_res = [self.microscope.beam.resolution[0] // 2,
                           self.microscope.beam.resolution[1] // 2]
                self.microscope.beam.resolution = new_res

        image = self.microscope.electron_beam.grab_frame()
        ImageLabelManagers.sem_manager.update_image(image)  # update SEM image in all connected ImageLabels

    def alignedImagingDirectionPushButton_clicked(self):
        self.window.apply_settings()  # GUI -> SETTINGS (also in fib_gui for slice distance)
        slice_distance = self.settings('milling', 'slice_distance')
        imaging_angle = 38
        # calculate incremen ts
        wd_increment = slice_distance / math.sin(math.radians(imaging_angle))  # z correction
        y_increment = 0

        self.settings.set('acquisition', 'wd_correction', value=wd_increment)
        self.settings.set('acquisition', 'y_correction', value=y_increment)
        self.window.populate_forms()  # SETTINGS -> GUI

    def alignedSampleSurfacePushButton_clicked(self):
        self.serialize_layout()  # GUI -> SETTINGS (also in fib_gui for slice distance)
        slice_distance = self.settings('milling', 'slice_distance')
        imaging_angle = 38
        # calculate increments
        wd_increment = slice_distance  # z correction
        y_increment = -math.tan(math.radians(imaging_angle)) * slice_distance

        self.settings.set('acquisition', 'wd_correction', value=wd_increment)
        self.settings.set('acquisition', 'y_correction', value=y_increment)
        self.window.populate_forms()  # SETTINGS -> GUI
