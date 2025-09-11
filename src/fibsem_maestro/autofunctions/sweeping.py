import logging
import numpy as np

from fibsem_maestro.settings import Settings
from fibsem_maestro.microscope_control.microscope import GlobalMicroscope

class BasicSweeping:
    """
    Class for basic linear sweeping of any Microscope attribute.
    """
    def __init__(self, autofunction_name):
        self._microscope = GlobalMicroscope().microscope_instance
        self.autofunction_name = autofunction_name
        self.settings = Settings()
        self._base = None  # initial sweeping variable
        self._beam = None
        self._sweeping_var = None

        sweeping_var_setting = self.settings('autofunction', self.autofunction_name,
                                             'variable', return_object=True)
        # refresh self.sweeping_var and beam on every change!
        sweeping_var_setting.add_handler(self.sweeping_var_changed)
        self.sweeping_var_changed(sweeping_var_setting.value)

    def sweeping_var_changed(self, sweeping_var_value):
        beam, sweep_value = sweeping_var_value.split('.')
        self._beam = getattr(self._microscope, beam)
        self._sweeping_var = sweep_value

    @property
    def value(self):
        """ Get sweeping variable """
        return getattr(self._beam, self._sweeping_var)

    @value.setter
    def value(self, value):
        """ Set sweeping variable """
        setattr(self._beam, self._sweeping_var, value)

    def set_sweep(self):
        """ Set sweeping start point """
        self._base = self.value

    def define_sweep_space(self, repetition):
        # ensure zig zag manner
        range = self.settings('autofunction', self.autofunction_name, 'sweeping_range')
        steps = int(self.settings('autofunction', self.autofunction_name, 'sweeping_steps'))

        if repetition % 2 == 0:
            sweep_space = np.linspace(self._base + range[0], self._base + range[1],
                                      steps)  # self.range[0] is negative
        else:
            sweep_space = np.linspace(self._base + range[1], self._base + range[0], steps)
        return sweep_space

    def sweep_inner(self, repetition):
        """ Basic sweeping"""
        sweep_space = self.define_sweep_space(repetition)
        limits = self._beam.limits(self._sweeping_var)
        for s in sweep_space:
            if limits[0] < s < limits[1]:
                yield s
            else:
                logging.warning(f'Sweep of {self._sweeping_var} is out of range ({s}')
                # return limit value
                yield limits[0] if s < limits[0] else limits[1]

    def sweep(self):
        """
        Performs a sweep of a variable within specified limits.

        :return: A generator object that yields values within the specified limits.
        :rtype: generator object
        """
        total_cycles = int(self.settings('autofunction', self.autofunction_name, 'sweeping_total_cycles'))

        for repetition in range(total_cycles):
            logging.info(f'Sweep cycle {repetition} of {total_cycles}')
            for s in self.sweep_inner(repetition):
                yield repetition, s


class BasicInterleavedSweeping(BasicSweeping):
    """ Basic sweeping interleaved by base sweeping values (Chans method)"""
    def define_sweep_space(self, *args, **kwargs):
        # if no of steps is odd -> remove 1. The base wd must be excluded
        range = self.settings('autofunction', self.autofunction_name, 'sweeping_range')
        steps = int(self.settings('autofunction', self.autofunction_name, 'sweeping_steps'))

        if steps % 2 == 1:
            steps -= 1

        sweep_space = np.linspace(self._base + range[0], self._base + range[1], steps)  # self.range[0] is negative
        interleave = np.ones(len(sweep_space)) * self._base
        # Merge arrays in interleaved fashion
        merged_arr = np.dstack((interleave, sweep_space)).reshape(-1)
        return merged_arr

#
# class SpiralSweeping(BasicSweeping):
#     def __init__(self, microscope, settings):
#         super().__init__(microscope, settings)
#         self.step_per_cycle = int(settings['sweeping_steps'])
#         self.cycles = int(settings['sweeping_spiral_cycles'])
#
#     def sweep_inner(self, repetition):
#         """ Basic sweeping"""
#         if repetition % 2 == 0:
#             sweep_space = np.arange(self.steps)
#         else:
#             sweep_space = np.arange(self.steps)[::-1]
#
#         for s in sweep_space:
#             cycle_no = s // self.step_per_cycle  # cycle number
#             step_no = s % self.step_per_cycle  # step number in the cycle
#             radius = (self.range / self.cycles) * (cycle_no + 1)  # avoid zero radius
#             angle = (2 * np.pi / self.step_per_cycle) * step_no
#
#             if cycle_no % 2 == 1:  # add angle shift for better covering
#                 angle += (2 * np.pi / self.step_per_cycle) / 2
#
#             x = np.cos(angle) * radius
#             y = np.sin(angle) * radius
#
#             value = self._base + Point(x, y)
#             value_r = math.sqrt(value.x ** 2 + value.y ** 2)  # distance from zero (radius)
#
#             if value_r < self.max_limits:
#                 yield value
#             else:
#                 logging.warning(f'Sweep of {self.sweeping_var} is out of range ({s}')
#
#     def sweep(self):
#         """
#         Perform a sweeping motion in a spiral pattern, generating a sequence of points.
#
#         :return: A generator that yields the points of the sweeping motion.
#         """
#         for repetition in range(self.total_cycles):
#             for r in self.sweep_inner(repetition):
#                 yield r
