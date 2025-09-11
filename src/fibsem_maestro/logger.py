import logging
import os

import numpy as np
import yaml
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle

from fibsem_maestro.microscope_control.microscope import GlobalMicroscope
from fibsem_maestro.tools.support import fold_filename, ScanningArea
from fibsem_maestro.settings import Settings

settings = Settings()

def showimg(img):
    fig, ax = plt.subplots()
    ax.imshow(img.transpose(), cmap='gray')
    plt.tight_layout()
    plt.axis('off')
    return fig, ax

class BasicLogger:
    def __init__(self, slice_number, log_dir):
        self.filename = fold_filename(log_dir, slice_number)


class FibLog(BasicLogger):
    def __init__(self, fib, slice_number, log_dir):
        super().__init__(slice_number, log_dir)
        self.fib = fib

    def save_fib_images(self):
        try:
            if hasattr(self.fib, '_fiducial_image') and self.fib._fiducial_image is not None:
                self.save_image(self.fib._fiducial_image, 'fiducial.png')
            if hasattr(self.fib, '_fiducial_template') and self.fib._fiducial_template is not None:
                self.save_image(self.fib._fiducial_template, 'fiducial_template.png')
            if hasattr(self.fib, '_similarity_map') and self.fib._similarity_map is not None:
                self.save_image(self.fib._similarity_map, 'similarity_map.png')
            if hasattr(self.fib, '_subpixel_log') and self.fib._subpixel_log is not None:
                [y, y_gauss, y2, y_gauss2] = self.fib._subpixel_log
                plt.figure()
                plt.plot(y)
                plt.plot(y_gauss,'r')
                plt.savefig(os.path.join(self.filename,
                                         f'fib_subpixel_x.png'))
                plt.close()
                plt.figure()
                plt.plot(y2)
                plt.plot(y_gauss2, 'r')
                plt.savefig(os.path.join(self.filename,
                                         f'fib_subpixel_y.png'))
                plt.close()
        except Exception as e:
            logging.error('Milling log failed. ' +repr(e))

    def save_image(self, img, postfix):
        fig, _ = showimg(img)
        if not os.path.exists(self.filename):
            os.makedirs(self.filename, exist_ok=True)
        fig.savefig(os.path.join(self.filename,
                                 f'fib_{postfix}.png'))
        plt.close(fig)

class CriterionLog(BasicLogger):
    image_index = 1  # index that is incremented in each figure save (prevention of file rewrite)
    def __init__(self, criterion, slice_number, log_dir):
        super().__init__(slice_number, log_dir)
        self.criterion = criterion

        for i, image in enumerate(self.criterion.crit_images):
            self.save_log_subimage(image, i)  # Input image with drew tiles

    def tile_log_image(self, img):
        tile_size = settings('criterion_calculation', self.criterion.criterion_name, 'tile_size')
        """ Create image with inpaint rectangles that represent tiling"""
        fig, ax = showimg(img)
        # if tile size = 0, not apply tilling
        if tile_size > 0:
            tiles = self.criterion._generate_image_fractions(self.criterion.img_with_border, return_coordinates=True)
            # Create a Rectangle patch for each tile and add it to the axes
            for tile in tiles:
                rect = Rectangle((tile[0]+self.criterion.border_y, tile[1]+self.criterion.border_x), tile[2], tile[3],
                                         linewidth=1, edgecolor='r',
                                         facecolor='none')
                ax.add_patch(rect)
        return fig

    def save_log_subimage(self, image, index):
        """ Input image with drew tiles """
        # save log image only if it is not line
        if len(image.shape) == 2 and min(image.shape) > 1:
            fig = self.tile_log_image(image)
            try:
                fig.savefig(os.path.join(self.filename,f'criterion_{self.criterion.criterion_name}_image_{index}_({CriterionLog.image_index}).png'))
                plt.close(fig)
                CriterionLog.image_index += 1
            except:
                logging.error('Log image was not saved.')

class TemplateMatchingLog(BasicLogger):
    def __init__(self, template_matching, slice_number, log_dir):
        super().__init__(slice_number, log_dir)
        self.template_matching = template_matching
        self.template_matching_log = self.template_matching_log_image()
        self.template_matching_filename = self.filename+'template_matching.png'
        self.similarities = []

    def template_matching_log_image(self):
        areas = settings('drift_correction', 'driftcorr_areas')
        fig, ax = showimg(self.template_matching.template_matching_image)

        for i in range(len(areas)):
            original = ScanningArea.from_dict(areas[i]).to_img_coordinates(
                self.template_matching.template_matching_image.shape)
            new_area = self.template_matching.templates_positions[i]

            # Create a Rectangle patch (original location of templates)
            rect = Rectangle((original[0].x, original[0].y), original[1][0], original[1][1], linewidth=1,
                             edgecolor='r', facecolor='none', alpha=0.5)
            # Add the patch to the Axes
            ax.add_patch(rect)
            # Create a Rectangle patch (found location)
            rect = Rectangle((new_area[0], new_area[1]), new_area[2], new_area[3], linewidth=1,
                             edgecolor='b', facecolor='none', alpha=0.5)
            ax.add_patch(rect)
        return fig

    def save_curve_image(self):
        self.template_matching_log.savefig(self.template_matching_filename)
        plt.close(self.template_matching_log)

        if self.template_matching.heat_map is not None:
            for i, heat_map in enumerate(self.template_matching.heat_map):
                fig, _ = showimg(heat_map)
                fig.savefig(self.filename+f'template_matching_heatmap{i}.png')
                plt.close(fig)

class AutofocusLog(BasicLogger):
    def __init__(self, af, slice_number, log_dir):
        # af - Autofunction object
        super().__init__(slice_number, log_dir, )
        self.af = af
        self.af_name = af.auto_function_name
        if len(self.af.criterion_values) > 0:
            self.curve = self.curve_image()  # image variable vs criterion

            self.curve_image_filename = os.path.join(self.filename, self.af_name, 'af_curve.png')
            os.makedirs(os.path.join(self.filename, self.af_name), exist_ok=True)
            self.curve.savefig(self.curve_image_filename)  # save image to file
            plt.close(self.curve)

            if hasattr(af, 'line_focus_image'):  # af is LineAutoFunction
                self.line_image = self.line_focus_image()  # on the fly focusing image
                if self.line_image is not None:
                    self.line_image_filename = os.path.join(self.filename, self.af_name, '_line_focus.png')
                    self.line_image.savefig(self.line_image_filename)
                    plt.close(self.line_image)

            self.initial_value = self.af.initial_af_value
            self.final_value = self.af.final_af_value

    def curve_image(self):
        """
        Display the AF curve.

        :return: The figure object representing the AF curve plot.
        """
        swept_values = list(self.af.criterion_values.keys())
        criterion_values = list(self.af.criterion_values.values())
        maxi = np.argmax(criterion_values)  # maximal value of criterion

        fig = plt.figure()
        plt.plot(swept_values, criterion_values, 'r.')

        plt.axvline(x=swept_values[int(np.ceil(len(swept_values) / 2))], color='lightblue')  # make horizontal line in the middle (last value)
        plt.axvline(x=swept_values[maxi], color='b')  # make horizontal line on the position of maximal value

        plt.tight_layout()
        plt.title('Focus criterion')
        return fig

    def line_focus_image(self):
        """
        :param img: Image array
        :return: Figure object

        Displays an image with a line plot overlay representing focus values.

        The method takes an image array and plots a line representation of focus values
        on top of the image. The focus values are scaled to fit within the visible range
        of the image.
        """
        # convert dict_values to np.array
        values_y = np.array(list(self.af.line_focuses.values()))
        if len(values_y) == 0:
            logging.error("AF values missing - the AF image cannot be plotted")
            return None
        else:
            scale = self.af.line_focus_image.shape[1] / max(values_y)  # scale values to visible range
            values_x = list(self.af.line_focuses.keys())
            fig, _ = showimg(self.af.line_focus_image)
            plt.axis('off')
            plt.plot(values_y * scale, values_x, c='r')
            plt.tight_layout()
            plt.title('Line focus plot')
            return fig

class Logger:
    logging_file_handler = None
    log_params = {}
    _electron = None
    _ion = None
    _microscope = None
    yaml_log_filaname = None
    _slice_number = None
    log_criteria = []
    log_fib = None
    log_template_matching = None

    @staticmethod
    def init(slice_number):
        log_dir = settings('dirs', 'log')

        # remove previous file logger
        if Logger.logging_file_handler is not None:
            Logger.logger.removeHandler(Logger.logging_file_handler)

        Logger._microscope = GlobalMicroscope().microscope_instance
        Logger._slice_number = slice_number

        if Logger._microscope is not None:
            Logger._electron = Logger._microscope.electron_beam
            Logger._ion = Logger._microscope.ion_beam

        # make dir
        os.makedirs(fold_filename(log_dir, slice_number), exist_ok=True)
        # python logger settings
        log_filename = fold_filename(log_dir, slice_number, 'app.log')
        Logger.yaml_log_filaname = fold_filename(log_dir, slice_number, 'log_dict.yaml')
        log_level = settings('general', 'log_level')

        Logger.logger = logging.getLogger()  # Create a logger object.
        fmt = '%(asctime)s: %(module)s - %(levelname)s - %(message)s'
        Logger.logger_formatter = logging.Formatter(fmt)
        Logger.logging_file_handler = logging.FileHandler(log_filename)  # Configure the logger to write into a file
        Logger.logging_file_handler.setFormatter(Logger.logger_formatter)
        Logger.logger.addHandler(Logger.logging_file_handler)  # Add the handler to the logger object
        Logger.logger.setLevel(log_level)
        logging.debug('Logging handler added')
        Logger.fib_fiducial_template_image = None  # fiducial template for milling
        Logger.fib_fiducial_image = None  # image of milling fiducial
        Logger.fib_similarity_map = None  # template matching map for fiducial drift measurement

        Logger.log_af = None  # autofunction log
        Logger.log_template_matching = None # template matching log
        Logger.log_criteria = []

    # @staticmethod
    # def generate_report(slice_number):
    #     log_dir = settings('dirs', 'log')
    #
    #     # Create the Jinja2 environment and specify the directory of templates
    #     env = Environment(loader=FileSystemLoader('html_template'))
    #
    #     # Load the template from the environment
    #     template = env.get_template('slice_report.html')
    #
    #     # Define our data to insert into the template
    #     data = {'slice_number': slice_number,
    #             'current_time': datetime.now(),
    #             'log_fib': Logger.log_fib}
    #
    #     if hasattr(Logger.log_fib.fib, '_fiducial_template'):
    #         data['fib_fiducial_template_image'] = Logger.log_fib.fib._fiducial_template
    #     if hasattr(Logger.log_fib.fib, '_fiducial_image'):
    #         data['fib_fiducial_image'] = Logger.log_fib.fib._fiducial_image
    #     if hasattr(Logger.log_fib.fib, '_similarity_map'):
    #         data['fib_similarity_map'] = Logger.log_fib.fib._similarity_map
    #         data['fib_similarity'] = Logger.log_fib.fib._similarity
    #         data['mill_position'] = Logger.log_fib.fib.position
    #
    #     data.update(Logger.log_params)
    #
    #     data['slice_filename'] =
    #
    #     # Render the template with the data
    #     output = template.render(data=data)
    #
    #     filename = fold_filename(log_dir, slice_number, 'log_dict.yaml')
    #     # Save the output to a new HTML file
    #     with open(filename, 'w') as file:
    #         file.write(output)


    @staticmethod
    def log_microscope_settings():
        Logger.log_params['electron_wd'] = Logger._electron.working_distance
        Logger.log_params['electron_beam_shift_x'] = Logger._electron.beam_shift_x
        Logger.log_params['electron_beam_shift_y'] = Logger._electron.beam_shift_y
        Logger.log_params['electron_stigmator_x'] = Logger._electron.stigmator_x
        Logger.log_params['electron_stigmator_y'] = Logger._electron.stigmator_y
        Logger.log_params['electron_contrast'] = Logger._electron.detector_contrast
        Logger.log_params['electron_brightness'] = Logger._electron.detector_brightness
        position = Logger._microscope.position
        Logger.log_params['stage_x'] = position.x
        Logger.log_params['stage_y'] = position.y
        Logger.log_params['stage_z'] = position.z
        Logger.log_params['ion_beam_shift_x'] = Logger._ion.beam_shift_x
        Logger.log_params['ion_beam_shift_y'] = Logger._ion.beam_shift_y

    @staticmethod
    def save_log(slice_number=None):
        """Save yaml dict log to file"""
        log_dir = settings('dirs', 'log')
        if slice_number is None:
            filename = Logger.yaml_log_filaname
        else:
            filename = fold_filename(log_dir, slice_number, 'log_dict.yaml')

        with open(filename, 'w') as f:
            yaml.dump(Logger.log_params, f, default_flow_style=False)

    @staticmethod
    def create_log_af(af):
        log_dir = settings('dirs', 'log')
        Logger.log_af = AutofocusLog(af, Logger._slice_number, log_dir)

    @staticmethod
    def create_log_template_matching(tm):
        log_dir = settings('dirs', 'log')
        Logger.log_template_matching = TemplateMatchingLog(tm, Logger._slice_number, log_dir)

    @staticmethod
    def create_log_criterion(crit, slice_number=None):
        if slice_number is None:
            slice_number = Logger._slice_number

        log_dir = settings('dirs', 'log')
        Logger.log_criteria.append(CriterionLog(crit, slice_number, log_dir))

    @staticmethod
    def create_log_fib(fib):
        log_dir = settings('dirs', 'log')
        Logger.log_fib = FibLog(fib, Logger._slice_number, log_dir)
