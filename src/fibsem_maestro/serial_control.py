import concurrent.futures
import logging
import os

from PySide6.QtCore import QThreadPool
from colorama import Fore, init as colorama_init

from fibsem_maestro.GUI.worker import Worker
from fibsem_maestro.autofunctions.autofunction import StepAutoFunction
from fibsem_maestro.autofunctions.autofunction_control import AutofunctionControl
from fibsem_maestro.contrast_brightness.automatic_contrast_brightness import AutomaticContrastBrightness
from fibsem_maestro.error_handler import ErrorHandler
from fibsem_maestro.image_criteria.criteria import Criterion
from fibsem_maestro.mask.masking import MaskingModel
from fibsem_maestro.drift_correction.template_matching import TemplateMatchingDriftCorrection
from fibsem_maestro.microscope_control.microscope import GlobalMicroscope, create_microscope
from fibsem_maestro.microscope_control.settings import load_settings, save_settings
from fibsem_maestro.milling.milling import Milling
from fibsem_maestro.tools.dirs_management import make_dirs
from fibsem_maestro.tools.email_attention import send_email
from fibsem_maestro.tools.support import Point
from fibsem_maestro.logger import Logger
from fibsem_maestro.settings import Settings

colorama_init(autoreset=True)  # colorful console

class StoppingFlag:
    def __init__(self):
        self._stopping_flag = False
        self.microscope = GlobalMicroscope().microscope_instance
    def __call__(self):
        if self._stopping_flag:
            logging.warning('Stopping executed')
            self.microscope.electron_beam.stop_acquisition()
            self.microscope.ion_beam.stop_acquisition()
            self._stopping_flag = False
            return True
        else:
            return False

    @property
    def stopping_flag(self):
        return self._stopping_flag

    @stopping_flag.setter
    def stopping_flag(self, value):
        self._stopping_flag = value


class SerialControl:
    def __init__(self):
        self._stopping_flag = False
        self.image = None  # actual image
        self.image_resolution = 0  # initial image resolution = 0 # initial image res
        self.future = None  # thread for acquisition running
        self.settings = Settings()

        self._microscope = self.initialize_microscope()
        self._electron = self._microscope.electron_beam

        self.stopping = StoppingFlag()
        self.error_handler = ErrorHandler(self.stopping)
        # events
        self.event_acquisition_start = []
        self.event_acquisition_stop = []

        #self._masks = self.initialize_masks()
        self._milling = self.initialize_milling()
        self._autofunctions = self.initialize_autofunctions()
        #self._acb = self.initialize_acb()
        self._criterion_resolution = self.initialize_criterion_resolution()
        self._criterion_resolution.finalize_thread_func = self.finalize_calculate_resolution
        self._drift_correction = self.initialize_drift_correction()

        self.threadpool = QThreadPool()
        self.running = False

    def initialize_microscope(self):
        """ microscope init"""
        try:
            # return the right class and call initializer
            microscope = create_microscope()()
            GlobalMicroscope().microscope_instance = microscope  # set the global instance

            print(Fore.YELLOW + 'Microscope initialized')
        except Exception as e:
            logging.error("Microscope initialization failed! "+repr(e))
            raise RuntimeError('Microscope initialization failed!') from e
        return microscope

    def initialize_milling(self):
        """ Slicing init """
        try:
            milling = Milling()
            print(Fore.YELLOW +'Milling initialized')
        except Exception as e:
            logging.error("Milling initialization failed! " + repr(e))
            raise RuntimeError("Milling initialization failed!") from e
        return milling

    def initialize_masks(self):
        """ Masking init """
        # try:
        #     # init all masks
        #     masks = [MaskingModel(m) for m in self.mask_settings]
        # except Exception as e:
        #     logging.error("Mask loading failed!" + repr(e))
        #     raise RuntimeError("Mask loading failed!") from e
        # return masks

    def initialize_autofunctions(self):
        """ autofunction init """
        try:
            autofunctions = AutofunctionControl()  #masks=self._masks
            print(Fore.YELLOW + f'Autofunctions found: {[x.auto_function_name for x in autofunctions.autofunctions]}')
        except Exception as e:
            logging.error("Autofunction initialization failed! "+repr(e))
            raise RuntimeError('"Autofunction initialization failed!') from e
        self._autofunctions = autofunctions # needed for initialize from different place then self.__init__
        return autofunctions

    def initialize_acb(self):
        """ Auto contrast-brightness init """
        # try:
        #     acb = AutomaticContrastBrightness()
        #     print(Fore.YELLOW + 'ACB initialized')
        # except Exception as e:
        #     logging.error("ACB initialization failed! " + repr(e))
        #     raise RuntimeError("ACB initialization failed!") from e
        # return acb

    def initialize_criterion_resolution(self):
        """ Resolution measurement init """
        criterion_name = self.settings('acquisition', 'criterion_name')

        # criterion of resolution calculation of final image - it uses parameters from criterion_calculation settings
        try:
            # mask = find_in_objects(self.actual_criterion['mask_name'], self._masks)
            criterion_resolution = Criterion(criterion_name)  # mask=mask
            print(Fore.YELLOW + f'Image resolution criterion: {criterion_resolution.criterion_name}')
        except Exception as e:
            logging.error("Initialization of resolution criteria failed! " + repr(e))
            raise RuntimeError("Initialization of resolution criteria failed!") from e
        return criterion_resolution

    def initialize_drift_correction(self):
        dc_type = self.settings('drift_correction', 'type')

        """" drift correction init """
        if dc_type == 'template_matching':
            try:
                drift_correction = TemplateMatchingDriftCorrection()
            except Exception as e:
                logging.error("Initialization of template matching failed! " + repr(e))
                raise RuntimeError("Initialization of template matching failed!") from e
        else:
            drift_correction = None
            print(Fore.RED + 'No drift correction found')
        return drift_correction

    def check_af_on_acquired_image(self, slice_number):
        # autofunction on acquired image
        aaf = self._autofunctions.active_autofunction
        if aaf is not None and isinstance(aaf, StepAutoFunction):
            logging.info(f'Autofunction on acquired image invoked! {aaf.auto_function_name}')
            if aaf.evaluate_image(self.image, slice_number=slice_number):
                # here, the attempts should be tested but poke do not comply attempts
                self._autofunctions.remove_active_af()  # remove if finished

    def wait_for_af_criterion_calculation(self):
        aaf = self._autofunctions.active_autofunction
        if aaf is not None and isinstance(aaf, StepAutoFunction):
            aaf.wait_to_criterion_calculation()

    def finalize_calculate_resolution(self, resolution, slice_number, **kwargs):
        """ Thread on the end of imaging (parallel with milling)"""
        self.image_resolution = resolution
        Logger.log_params['resolution'] = self.image_resolution
        print(Fore.GREEN + f'Calculated resolution: {self.image_resolution}')

        Logger.save_log(slice_number)  # save log dict

    def milling(self, slice_number):
        """ Cut slice (with drift correction by fiducial)  """
        try:
            self._milling(slice_number)
        except Exception as e:
            logging.error('Milling error'+repr(e))
            print(Fore.RED + 'Milling failed')
            self.error_handler(e)

    def calculate_resolution(self, slice_number):
        """ Calculate resolution """
        try:
            # go to self.finalize_calculate_resolution on thread finishing
            self.image_resolution = self._criterion_resolution(self.image, slice_number=slice_number,
                                                               separate_thread=True)
        except Exception as e:
            logging.error('Image resolution calculation error. Setting resolution to 0.'+repr(e))
            print(Fore.RED + 'Resolution measurement failed')
            self.image_resolution = 0
            self.error_handler(e)

    def correction(self):
        """ WD and Y correction"""
        wd_correction = self.settings('acquisition', 'wd_correction')
        y_correction = self.settings('acquisition', 'y_correction')
        additive_beam_shift = self.settings('general', 'additive_beam_shift')
        # WD increment
        try:
            logging.info('WD increment: '+str(wd_correction))
            self._electron.working_distance += wd_correction
            print(Fore.GREEN + 'WD correction applied. '+str(wd_correction))
        except Exception as e:
            logging.error('Working distance settings failed! '+repr(e))
            print(Fore.RED + 'Working distance settings failed!')
            self.error_handler(e)

        # y correction + beam shift
        try:
            logging.info('Y correction: '+str(y_correction))
            delta_bs = Point(additive_beam_shift[0],additive_beam_shift[1]) + Point(0, y_correction)
            self._microscope.add_beam_shift_with_verification(delta_bs)  # check y_increment direction
            print(Fore.GREEN + 'Y correction applied. '+str(delta_bs.to_dict()))
        except Exception as e:
            logging.error('Y correction failed! '+repr(e))
            print(Fore.RED + 'Y correction failed!')
            self.error_handler(e)

    def autofunction(self, slice_number):
        """" Autofunctions handling """
        try:
            self._autofunctions(slice_number, self.image_resolution)
            if len(self._autofunctions.scheduler) == 0:
                print(Fore.GREEN + 'The autofunction queue is empty.')
            else:
                print(Fore.YELLOW + f'Waiting autofunctions: {[x.auto_function_name for x in self._autofunctions.scheduler]}')
        except Exception as e:
            logging.error('Autofunction error. '+repr(e))
            print(Fore.RED + 'Autofunction error!')
            self.error_handler(e)

    def auto_contrast_brightness(self, slice_number):
        try:
            self._autofunctions(slice_number, self.image_resolution)
            if len(self._autofunctions.scheduler) == 0:
                print(Fore.GREEN + 'The autofunction queue is empty.')
            else:
                print(Fore.YELLOW + f'Waiting autofunctions: {[x.name for x in self._autofunctions.scheduler]}')
        except Exception as e:
            logging.error('Autofunction error. ' + repr(e))
            print(Fore.RED + 'Autofunction error!')
            self.error_handler(e)

    def acquire(self, slice_number):
        """ Acquire and save image """
        try:
            self.image = self._microscope.acquire_image(slice_number)
            print(Fore.GREEN + 'Image acquired')
        except Exception as e:
            logging.error('Image acquisition error. '+repr(e))
            print(Fore.RED + 'Image acquisition failed!')
            self.error_handler(e)

    def drift_correction(self, slice_number):
        """ Drift correction handling """
        if self._drift_correction is not None:
            try:
                delta = self._drift_correction(self.image, slice_number)
                # it is drift correction based on masking
                if delta is not None:
                    print(Fore.GREEN + 'Drift correction applied. ' + str(delta.to_dict()))
            except Exception as e:
                logging.error('Drift correction error. ' + repr(e))
                print(Fore.RED + 'Application of drift correction failed!')
                self.error_handler(e)

    def load_sem_settings(self):
        """ Load microscope settings from file and set microscope """
        sem_settings_dir = self.settings('dirs', 'project')
        sem_settings_file = self.settings('general', 'sem_settings_file')
        # set microscope
        try:
            logging.info('Microscope setting loading')
            load_settings(microscope=self._microscope, path=os.path.join(sem_settings_dir, sem_settings_file))
            self._microscope.beam = self._electron  # set electron as default beam
            print(Fore.GREEN + 'Microscope settings applied')
        except Exception as e:
            logging.error('Loading of microscope settings failed! ' + repr(e))
            print(Fore.RED + 'Application of microscope settings failed!')
            self.error_handler(e)

    def save_sem_settings(self):
        sem_settings_dir = self.settings('dirs', 'project')
        sem_settings_file = self.settings('general', 'sem_settings_file')
        variables_to_save = self.settings('general', 'variables_to_save')

        """ Save microscope settings from file from microscope """
        settings_to_save = variables_to_save
        try:
            save_settings(microscope=self._microscope,
                          settings=settings_to_save,
                          path=os.path.join(sem_settings_dir, sem_settings_file))
            print(Fore.GREEN + 'Microscope settings saved')
        except Exception as e:
            logging.error('Microscope settings saving error! ' + repr(e))
            print(Fore.RED + 'Microscope settings saving failed!')
            self.error_handler(e)

    def stop(self):
        self.stopping.stopping_flag = True

    def run(self, start_slice_number):
        if not self.running:
            # init
            self._autofunctions.scheduler = []
            for af in self._autofunctions.autofunctions:
                if hasattr(af, '_step_number'):
                    af._step_number = 0

            # fire start event
            for event_start in self.event_acquisition_start:
                event_start()
            worker = Worker(self.run_async, start_slice_number)
            # fire stop event
            for event_stop in self.event_acquisition_stop:
                worker.signals.finished.connect(event_stop)  # connect finished signal to a slot
            self.threadpool.start(worker)
            #self.run_async(start_slice_number)
        else:
            logging.warning('Acquisition already running! Attempt to stop')
            self.stop()

    def run_async(self, start_slice_number):
        slice_number = start_slice_number
        self.running = True
        while self.cycle(slice_number):
            self.running = True
            logging.info(f'---Slice {slice_number} completed ---')
            slice_number += 1
        self.running = False

    def sputter(self):
        sputtering_enabled = self.settings('acquisition', 'sputter')
        if sputtering_enabled:
            from fibsem_maestro.sputter_biohydra import sputter
            try:
                sputtering_grid = self.settings('acquisition', 'sputter_grid')
                sputter(sputtering_grid, self.microscope._microscope)
                print(Fore.GREEN + 'Sputtering completed!')
            except Exception as e:
                logging.error('Sputtering error ' + repr(e))
                print(Fore.RED + 'Sputtering failed!')
                self.error_handler(e)

    def sputter_restore(self):
        sputtering_enabled = self.settings('acquisition', 'sputter')
        if sputtering_enabled:
            from fibsem_maestro.sputter_biohydra import sputter_restore
            try:
                sputter_restore()
                print(Fore.GREEN + 'Sputtering restored!')
            except Exception as e:
                logging.error('Sputtering restore error ' + repr(e))
                print(Fore.RED + 'Sputtering restore failed!')
                self.error_handler(e)

    def cycle(self, slice_number):
        imaging_enabled = self.settings('acquisition', 'imaging_enabled')
        resolution_threshold = self.settings('acquisition', 'resolution_threshold')
        print(Fore.YELLOW + f'Current slice number: {slice_number}')
        logging.info(f'Current slice number: {slice_number}')

        Logger.init(slice_number)

        self._microscope.beam = self._microscope.ion_beam  # switch to ions
        self.milling(slice_number)  # FIB milling (slicing)
        if self.stopping():
            return False

        if imaging_enabled:
            # wait for resolution calculation if needed anf AF main imaging criterion calculation
            self._criterion_resolution.join_all_threads()
            self.wait_for_af_criterion_calculation()

            if self.image_resolution is not None:
                if self.image_resolution > resolution_threshold:
                    try:
                        send_email("Maestro alert!",
                                   f"Resolution {self.image_resolution} is too bad! (>{resolution_threshold})"
                                   f"Acquisition stopped!")
                    except Exception as e:
                        logging.error("Sending email error. " + repr(e))

                    print(f"Resolution {self.image_resolution} is too bad. (>{resolution_threshold})")
                    print("Perform manual inspection and press enter")
                    input()

            if self.stopping():
                return False

            self.sputter()

            if self.stopping():
                return False

            self._microscope.beam = self._microscope.electron_beam  # switch to electrons
            self.load_sem_settings()  # load settings and set microscope
            if self.stopping():
                return False
            self.correction()  # wd and y correction
            if self.stopping():
                return False

            self.drift_correction(slice_number)  # drift correction
            if self.stopping():
                return False

            self.autofunction(slice_number)  # auto-functions handling
            if self.stopping():
                return False
            Logger.log_microscope_settings()  # save microscope settings
            self.acquire(slice_number)  # acquire image
            if self.stopping():
                return False
            self.check_af_on_acquired_image(slice_number)  # check if the autofunction on main_imaging is activated
            if self.stopping():
                return False
            # self.drift_correction(slice_number)  # drift correction
            # if self.stopping():
            #      return False

           # self.auto_contrast_brightness(slice_number)
            if self.stopping():
                return False
            # resolution calculation
            self.calculate_resolution(slice_number)

            self.save_sem_settings()

            self.sputter_restore()
            if self.stopping():
                return False
        else:
            Logger.log_microscope_settings()  # save microscope settings
            print(Fore.RED + 'Imaging skipped!')
            logging.warning('Imaging skipped because imaging is disabled in configuration!')
        return True

    def change_dir_settings(self, new_dir):
        self.settings.set('dirs', 'project', value=new_dir)
        self.settings.set('dirs', 'output_images', value = os.path.join(new_dir, 'images'))
        self.settings.set('dirs', 'log', value = os.path.join(new_dir, 'logs'))
        self.settings.set('dirs', 'template_matching', value=os.path.join(new_dir, 'template_matching'))

        # make dirs if needed
        make_dirs(self.settings('dirs'))

    def test_af(self, name):
        self._autofunctions.test_af(name)

    def milling_init(self):
        self._milling.milling_init()

    def milling_load(self):
        # Load fib settings
        self._milling.load_settings()

    def update_driftcorr_areas(self, image):
        self._drift_correction.update_templates(image)

    def test_driftcorr_areas(self):
        self._drift_correction.test()

    def milling_reset(self):
        self._milling.reset_position()

    @property
    def microscope(self):
        return self._microscope
