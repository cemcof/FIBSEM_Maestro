import importlib
import logging
import numpy as np
import time

from fibsem_maestro.autofunctions.sweeping import BasicInterleavedSweeping
from fibsem_maestro.image_criteria.criteria import Criterion
from fibsem_maestro.tools.support import Point, Image, ScanningArea, StagePosition
from fibsem_maestro.tools.image_tools import get_stripes
from fibsem_maestro.logger import Logger
from fibsem_maestro.settings import Settings
from fibsem_maestro.microscope_control.microscope import GlobalMicroscope
from autoscript_sdb_microscope_client.structures import GrabFrameSettings


class AutoFunction:
    def __init__(self, auto_function_name: str):
        """
        :param microscope: The microscope control instance.

        """
        # settings
        self.settings = Settings()
        self.auto_function_name = auto_function_name
        self._microscope = GlobalMicroscope().microscope_instance  # microscope control class
        self._sweeping = None  # sweeping class

        try:
            # Set sweeping and change-handler
            sweeping_strategy_setting = self.settings('autofunction', self.auto_function_name, 'sweeping_strategy',
                                                      return_object=True)
            # refresh self.sweeping_var and beam on every change!
            sweeping_strategy_setting.add_handler(self.sweeping_strategy_changed)
            self.sweeping_strategy_changed(sweeping_strategy_setting.value)
        except:
            logging.warning(f'Sweeping strategy in af {auto_function_name} not found')

        try:
            # focusing criterion class
            self._criterion = Criterion(self.settings('autofunction', self.auto_function_name, 'criterion_name'))
            # set the function called on resolution calculation (in separated thread)
            self._criterion.finalize_thread_func = self.get_image_finalize
        except:
            logging.warning(f'Criterion in af {auto_function_name} not found')


        # init criterion dict (array of focusing crit for each variable value)
        self._criterion_values = {}
        self.slice_number = None
        self.last_sweeping_value = None
        self.attempt = 1
        self.initial_af_value = None  # value before executing af
        self.final_af_value = None  # value after executing af
        self.best_criterion_value = None
        self.af_slice_number = None

        max_attempts_setting = self.settings('autofunction', self.auto_function_name, 'max_attempts',
                                             return_object=True)
        # refresh self.sweeping_var and beam on every change!
        max_attempts_setting.add_handler(self.max_attempts_changed)
        self.max_attempts = max_attempts_setting.value


    def sweeping_strategy_changed(self, value):
        sweeping_module = importlib.import_module('fibsem_maestro.autofunctions.sweeping')
        Sweeping = getattr(sweeping_module, value)  # Load correct sweeping class
        self._sweeping = Sweeping(self.auto_function_name)

    def max_attempts_changed(self, value):
        self.max_attempts = value

    def set_sweep(self):
        self._sweeping.set_sweep()


    def _initialize_criteria_dict(self):
        """
        Initializes the criterion values dictionary.

        :return: None
        """
        self._criterion_values = {i: [] for i in list(self._sweeping.sweep_inner(0))}

    def _prepare(self, image_for_mask=None):
        """ Update mask if needed and set the microscope """
        image_settings = self.settings('image', self.auto_function_name)
        # grab the image for masking if mask enabled
        if self._criterion.mask_used:
            self._criterion.mask.update_img(image_for_mask)
        self._microscope.apply_beam_settings(image_settings)  # apply resolution, li...

    def measure_resolution(self, image, slice_number=None, sweeping_value=None):
        # criterion calculation
        # run on separated thread - call self._get_image_finalize on the end of resolution calculation
        self._criterion(image, slice_number=slice_number, separate_thread=True, sweeping_value=sweeping_value)

    def wait_to_criterion_calculation(self):
        self._criterion.join_all_threads()

    def _get_image(self, value, slice_number=None):
        """
        Set the sweeping value, take image and measure criterion.
        :param value: The new value for the measure criterion.
        :return: None
        """
        # set value
        variable = self.settings('autofunction', self.auto_function_name, 'variable')
        logging.info(f'Autofunction setting {variable} to {value}')
        self.last_sweeping_value = value
        self._sweeping.value = value
        # grab image with defined settings (in self._image_settings). The settings are updated in self._prepare
        image = self._microscope.beam.grab_frame()
        self.measure_resolution(image, slice_number, sweeping_value=value)

    def get_image_finalize(self, resolution, slice_number, **kwargs):
        """ Finalizing function called on the end of resolution calculation thread"""
        # criterion can be None of not enough masked regions
        if resolution is not None:
            self._criterion_values[kwargs['sweeping_value']].append(resolution)
        else:
            logging.warning('Criterion omitted (not enough masked region)!')
        logging.info(f"Criterion value: {resolution}")

    def _evaluate(self, slice_number):
        """
        This method is used to evaluate the criteria and determine the best value. It also generates plots.
        """
        variable = self.settings('autofunction', self.auto_function_name, 'variable')
        self.wait_to_criterion_calculation()  # wait to complete all resolution calculations

        # convert list of criteria to mean values for each sweeping variable value
        for key, value_list in list(self._criterion_values.items()):
            self._criterion_values[key] = np.mean(value_list)  # average if more repetitions
        # remove items with NaN values
        self._criterion_values = {k: v for k, v in self._criterion_values.items() if not np.isnan(v)}

        print(f'Af values: {self._criterion_values}')

        try:
            if len(self._criterion_values) > 0:
                best_value = max(self._criterion_values, key=self._criterion_values.get)
                self._sweeping.value = best_value  # set best value
                self.final_af_value = best_value
                self.best_criterion_value = max(self._criterion_values.values())
                logging.info(f'Autofunction: {variable} = {best_value}. Criterion: {self.best_criterion_value}')
            else:
                logging.error('Autofunction fail!')
        except Exception as e:
            logging.error("Criterion for autofunction not calculated! " + repr(e))
            raise e

        Logger.create_log_af(self)

        # increment attempt counter if last slice also executed
        if self.af_slice_number is not None and slice_number is not None:
            if self.af_slice_number == slice_number - 1:
                self.attempt += 1
            else:
                self.attempt = 1
        self.af_slice_number = slice_number

    def check_firing(self, slice_number, image_resolution):
        """ Check if the firing condition is passed"""
        execute_slices = self.settings('autofunction', self.auto_function_name, 'execute_slices')
        execute_resolution = self.settings('autofunction', self.auto_function_name, 'execute_resolution')

        # number of slices execution
        if execute_slices > 0 and slice_number % execute_slices == 0:
            return True

        # number of slices execution
        if image_resolution is not None:
            if 0 < execute_resolution < image_resolution:
                return True

        return False

    def __call__(self, image_for_mask=None, slice_number=None):
        """
        :param image_for_mask: The image to be used for masking. Defaults to None.
        :return: True if the af process is finished, False if the process is not yet finished in step image mode.

        The __call__ method is used to execute the functionality of the class. It updates the mask image if needed and
        sets the microscope.
        It performs a sweeping process and evaluates the result.
        In both cases, it returns True if the process is finished and False if the process is not yet finished.
        """
        # Focusing on different area
        self.initial_af_value = self._sweeping.value
        self._initialize_criteria_dict()
        self.move_stage_x()
        self._prepare(image_for_mask)  # update mask image if needed and set microscope
        for i, (repetition, s) in enumerate(self._sweeping.sweep()):
            logging.info(f'Autofunction step no {i+1}')
            self._get_image(s, slice_number)
        self._evaluate(slice_number)
        self.move_stage_x(back=True)
        return True  # af finished

    def test(self):
        self.__call__(image_for_mask=None, slice_number=-1)

    def move_stage_x(self, back=False):
        """ Focusing on near area"""
        delta_x = self.settings('autofunction', self.auto_function_name, 'delta_x')

        x = 1 if back else -1
        # Move to focusing area
        if delta_x != 0:
            self._microscope.relative_position = StagePosition(x=delta_x * x)
            logging.info(f"Stage relative move for focusing. dx={delta_x * x}")

    @property
    def mask(self):
        """ Get mask object if used """
        if self._criterion.mask_used:
            return self._criterion.mask
        else:
            return None

    @property
    def criterion_values(self):
        return self._criterion_values

    @property
    def best_value(self):
        return


class LineAutoFunction(AutoFunction):
    def __init__(self, auto_function_name: str):
        super().__init__(auto_function_name)
        self._line_focuses = {}
        self.line_focus_image = None

    def _estimate_line_time(self):
        dwell_time = self.settings('image', self.auto_function_name, 'dwell')
        line_integration = self.settings('image', self.auto_function_name, 'images_line_integration')
        resolution = self.settings('image', self.auto_function_name, 'resolution')
        imaging_area = ScanningArea.from_dict(self.settings('image', self.auto_function_name, 'imaging_area'))
        estimated_time = (dwell_time * line_integration
                          * resolution[0])
        if imaging_area.width > 0 and imaging_area.height > 0:
            estimated_time *= imaging_area.width
        return estimated_time

    def _variable_sweeping(self, line_time):
        """
        Performs line variable sweeping during scan for a given line time.

        :param line_time: the time it takes to acquire a single line of data
        :return: None
        """
        pre_imaging_delay = self.settings('autofunction', self.auto_function_name, 'pre_imaging_delay')
        keep_time = self.settings('autofunction', self.auto_function_name, 'keep_time')

        actual_repetition = -1
        for step, (repetition, s) in enumerate(self._sweeping.sweep()):
            self._sweeping.value = s  # set value
            # new segment
            if not repetition == actual_repetition:
                if repetition == 0:
                    self._microscope.beam.start_acquisition()
                logging.info(f'Autofunction sweep cycle {repetition}')
                actual_repetition = repetition
                # blank and wait
                self._microscope.total_blank()
                if step == 0:
                    time.sleep(pre_imaging_delay)
                time.sleep(keep_time * line_time)
                # unblank and wait
                self._microscope.total_unblank()

            time.sleep(keep_time * line_time)

        time.sleep(keep_time * line_time)  # ?
        self._microscope.beam.stop_acquisition()

    def _process_image(self, img):
        """
        It fills self._criterion_values based on given image with sweep value

        :param img: The image to be processed.
        :type img: numpy.ndarray
        :return: None
        """
        forbidden_sections = self.settings('autofunction', self.auto_function_name, 'forbidden_sections')
        steps = self.settings('autofunction', self.auto_function_name, 'sweeping_steps')
        separate_value = self.settings('autofunction', self.auto_function_name, 'stripes_separate_value')

        img = img.get8bit_clone()  # convert to 8b

        # convert to one-item list if only one section entered
        if isinstance(forbidden_sections, int):
            self.forbidden_sections = [forbidden_sections]

        sweeping_steps = steps
        for image_section_index, bin in get_stripes(img, separate_value=separate_value):
            if image_section_index not in self.forbidden_sections:
                logging.debug(f'Stripe length: {len(bin)}')
                bin = np.array_split(bin, sweeping_steps)  # split bins to equal parts the equal to focus_steps parts
                # go over all variable values
                for bin_index, variable in enumerate(self._sweeping.sweep_inner(image_section_index)):
                    # each line
                    for line_index in bin[bin_index]:
                        # Autofunction._get_image_finalize is called be event
                        # -> the resolution is appended to self._criterion_values
                        f = self._criterion(img, line_number=line_index, slice_number=self.slice_number,
                                            sweeping_value=variable)

                        if f is not None:
                            self._line_focuses[line_index] = f
                        else:
                            logging.warning('Criterion omitted due to not enough masked regions.')

    def _line_focus(self, slice_number):
        """
        Executes line focus operation.
        It starts scan with variable sweeping and evaluates results
        :return: None
        """
        # int line_focuses dict used for logging
        self._line_focuses = {}
        # line time estimation
        line_time = self._estimate_line_time()
        self._microscope.blank_screen()
        self._prepare()  # apply beam settings must be applied after change of scanning area that happened in blank_screen proceure
        # variable sweeping
        self._variable_sweeping(line_time)
        # get image
        self.line_focus_image = self._microscope.beam.get_image(crop_to_scanning_area=True)
        # calculate self._criterion_values
        self._process_image(self.line_focus_image)
        self._evaluate(slice_number)

    def __call__(self, image_for_mask=None, slice_number=None):
        """
        :param image_for_mask: The input image for creating a mask if needed.
        :return: True if the operation is successfully finished.

        """
        self.initial_af_value = self._sweeping.value
        self._initialize_criteria_dict()
        self.move_stage_x()  # focusing on different area
        self._prepare(image_for_mask)
        self._line_focus(slice_number)
        self.move_stage_x(back=True)
        return True  # af finished

    @property
    def line_focuses(self):
        return self._line_focuses


class StepAutoFunction(AutoFunction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._step_number = 0  # actual step
        self.sweep_list = None

        keep_trying_setting = self.settings('autofunction', self.auto_function_name, 'keep_trying',
                                             return_object=True)
        # refresh self.sweeping_var and beam on every change!
        keep_trying_setting.add_handler(self.keep_trying_setting_changed)
        self.keep_trying = keep_trying_setting.value

    def keep_trying_setting_changed(self, value):
        self.keep_trying = value

    def __call__(self, *args, **kwargs):
        """
        :param image_for_mask: The image to be used for masking. Defaults to None.
        :return: True if the af process is finished, False if the process is not yet finished in step image mode.

        The __call__ method is used to execute the functionality of the class. It updates the mask image if needed and
        sets the microscope.
        It performs a step-by-step process.
        In both cases, it returns True if the process is finished and False if the process is not yet finished.
        """
        # step image mode
        if self._step_number == 0:
            self.initial_af_value = self._sweeping.value
            self.sweep_list = list(self._sweeping.sweep())
            self._initialize_criteria_dict()
        repetition, value = self.sweep_list[self._step_number]  # select sweeping variable based on current step
        logging.info(f'Performing step autofocus no. {self._step_number+1}')
        self.last_sweeping_value = value
        self._sweeping.value = value  # set a new value!
        self._step_number += 1

    def _initialize_criteria_dict(self):
        self._criterion_values = {}

    def test(self):
        while True:
            self.wait_to_criterion_calculation()  # join threads
            self.__call__(image_for_mask=None, slice_number=-1)
            self._prepare()  # apply settings
            image = self._microscope.electron_beam.grab_frame()
            if self.evaluate_image(image, slice_number=-1):
                # evaluation finished
                break

    def evaluate_image(self, image, slice_number):
        # new thread -> goto self.
        imaging_area = ScanningArea.from_dict(self.settings('image', self.auto_function_name, 'imaging_area'))

        if imaging_area.width > 0 and imaging_area.height > 0:
            left_top, [width, height] = imaging_area.to_img_coordinates(image.shape)
            image = image[left_top.x:left_top.x+width, left_top.y:left_top.y+height]

        self.measure_resolution(image, slice_number=slice_number, sweeping_value=self.last_sweeping_value)

        if self._step_number >= len(self.sweep_list):
            self.wait_to_criterion_calculation()  # join threads
            logging.info(f'Step-by-step autofocus finished.')
            self._evaluate(slice_number)
            self._step_number = 0  # restart steps
            if self.keep_trying and not self.best_criterion_value == 0:  # if keep_trying activated and still improvement - no end
                self.set_sweep()  # set new sweep
                return False
            return True  # af finished
        else:
            return False  # not finished yet

    def get_image_finalize(self, resolution, slice_number, **kwargs):
        """ Finalizing function called on the end of resolution calculation thread"""
        # criterion can be None of not enough masked regions
        if resolution is not None:
            self._criterion_values[self._step_number] = (kwargs['sweeping_value'], resolution)
        else:
            logging.warning('Criterion omitted (not enough masked region)!')
        logging.info(f"Criterion value: {resolution}")

    def _evaluate(self, slice_number):
        """ Evaluate data from all steps. Calculate difference between base resolution and
        the resolution alternated image"""
        min_diff = self.settings('autofunction', self.auto_function_name, 'min_diff')

        result_dic = {i: [] for i in list(self._sweeping.sweep_inner(0))}  # keep only keys - values will be appended
        logging.info(f'AF criteria: {self._criterion_values}')
        start_i = min(self._criterion_values.keys())
        end_i = max(self._criterion_values.keys())
        for i in np.arange(start_i+1, end_i+1, step=2):  # (0,2,4... base resolution)
            sweep_value, sweep_resolution = self._criterion_values[i]
            _, base_resolution = self._criterion_values[i-1]

            # consider improvements > min_diff (fraction of base resolution)
            min_diff_value = min_diff * base_resolution
            if sweep_resolution - base_resolution > min_diff_value:
                result_dic[sweep_value].append(sweep_resolution - base_resolution)
            else:
                result_dic[sweep_value].append(-1)

        # initial sweep variable -> criterion 0 (no change)
        result_dic[self._criterion_values[start_i][0]].append(0)
        self._criterion_values = result_dic
        super()._evaluate(slice_number)

class ManufacturerAutoFunction(AutoFunction):
    def __init__(self, auto_function_name: str):
        super().__init__(auto_function_name)

    def set_sweep(self):
        pass

    def __call__(self, image_for_mask=None, slice_number=None):
        from autoscript_sdb_microscope_client.structures import (RunAutoFocusSettings, RunAutoStigmatorSettings,
                                                                 RunAutoLensAlignmentSettings, RunAutoSourceTiltSettings)
        from autoscript_sdb_microscope_client.enumerations import DetectorMode

        sweeping_var = self.settings('autofunction', self.auto_function_name, 'variable')
        dwell_time = self.settings('image', self.auto_function_name, 'dwell')
        line_integration = self.settings('image', self.auto_function_name, 'images_line_integration')
        imaging_area = ScanningArea.from_dict(self.settings('image', self.auto_function_name, 'imaging_area'))
        contrast = self.settings('image', self.auto_function_name, 'contrast')
        brightness = self.settings('image', self.auto_function_name, 'brightness')

        dwell_backup = self._microscope.electron_beam.dwell_time
        self._microscope.electron_beam.dwell_time = dwell_time

        if sweeping_var == 'electron_beam.working_distance':


            if imaging_area.width > 0 and imaging_area.height > 0:
                settings = RunAutoFocusSettings(reduced_area=imaging_area.to_as())
            else:
                settings = RunAutoFocusSettings()

            autofunction_fn = self._microscope._microscope.auto_functions.run_auto_focus
        elif sweeping_var == 'electron_beam.stigmator':
            settings = RunAutoStigmatorSettings(
                method='OngEtAl',
                dwell_time=dwell_time,
                resolution=self.settings('autofunction', self.auto_function_name, 'resolution'),
                horizontal_field_width = self.settings('autofunction', self.auto_function_name, 'horizontal_field_width'),
                reduced_area=imaging_area.to_as(),
                line_integration=line_integration
            )
            autofunction_fn = self._microscope._microscope.auto_functions.run_auto_stigmator
        elif sweeping_var == 'electron_beam.lens_alignment':
            if imaging_area.width > 0 and imaging_area.height > 0:
                settings = RunAutoLensAlignmentSettings(reduced_area=imaging_area.to_as(),
                                                        dwell_time=dwell_time,
                                                        resolution=self.settings('autofunction', self.auto_function_name, 'resolution'),
                                                        line_integration=line_integration)
            else:
                settings = RunAutoLensAlignmentSettings(dwell_time=dwell_time,
                                                        resolution=self.settings('autofunction', self.auto_function_name, 'resolution'),
                                                        line_integration=line_integration)

            autofunction_fn = self._microscope._microscope.auto_functions.run_auto_lens_alignment
        elif sweeping_var == 'electron_beam.source_tilt':
            settings = RunAutoSourceTiltSettings(contrast=contrast,
                                                 brightness=brightness,
                                                 dwell_time=dwell_time,
                                                 method="Volumescope")
            autofunction_fn = self._microscope._microscope.auto_functions.run_auto_source_tilt
        else:
            raise Exception(f'Unknown variable for {sweeping_var} for manufacturer autofunction.')

        self.move_stage_x()  # focusing on different area

        if sweeping_var == 'electron_beam.source_tilt':
            detector_backup = self._microscope._microscope.detector.type.value
            detector_mode_backup = self._microscope._microscope.detector.mode.value
            self._microscope._microscope.detector.type.value = 'TLD'
            self._microscope._microscope.detector.mode.value = DetectorMode.SECONDARY_ELECTRONS

        logging.info(f'Performing manufacturer autofunction - {sweeping_var}')

        autofunction_fn(settings)

        if sweeping_var == 'electron_beam.source_tilt':
            self._microscope._microscope.detector.type.value = detector_backup
            self._microscope._microscope.detector.mode.value = detector_mode_backup
        self._microscope.electron_beam.dwell_time = dwell_backup

        self.move_stage_x(back=True)

        # increment attempt counter if last slice also executed
        if self.af_slice_number is not None and slice_number is not None:
            if self.af_slice_number == slice_number - 1:
                self.attempt += 1
            else:
                self.attempt = 1
        self.af_slice_number = slice_number

        return True  # af finished