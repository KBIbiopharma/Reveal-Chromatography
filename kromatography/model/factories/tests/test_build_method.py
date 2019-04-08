
from unittest import TestCase
from contextlib import contextmanager

from kromatography.model.factories.method import build_sim_method_from_method
from kromatography.model.tests.sample_data_factories import make_sample_study2
from kromatography.model.method import Method
from kromatography.model.solution import Solution


class TestBuildSimMethodFromMethod(TestCase):

    @classmethod
    def setUpClass(cls):
        real_study = make_sample_study2(add_transp_bind_models=True)
        real_exp = real_study.search_experiment_by_name('Run_1')

        cls.source_method = real_exp.method

        cls.first_simulated_step = "Load"
        cls.last_simulated_step = "Strip"

    def test_build_sim_method(self):
        method = build_sim_method_from_method(self.source_method,
                                              self.first_simulated_step,
                                              self.last_simulated_step)

        self.assertValidMethod(method)

    def test_build_sim_method_custom_initial_buffer(self):
        pre_equil_step = self.source_method.method_steps[1]
        pre_equil_buffer = pre_equil_step.solutions[0]

        method = build_sim_method_from_method(
            self.source_method, self.first_simulated_step,
            self.last_simulated_step, initial_buffer=pre_equil_buffer
        )

        self.assertValidMethod(method)

    def test_inverted_start_stop_fails(self):
        first_simulated_step = "Strip"
        last_simulated_step = "Load"
        with self.assertRaises(ValueError):
            build_sim_method_from_method(self.source_method,
                                         first_simulated_step,
                                         last_simulated_step)

    def test_build_sim_method_from_short_method_fail(self):
        self.source_method.method_steps = self.source_method.method_steps[2:]
        # This has to fail because no step before the first simulated step and
        # no initial buffer specified.
        with self.assertRaises(ValueError):
            build_sim_method_from_method(
                self.source_method, self.first_simulated_step,
                self.last_simulated_step
            )

    def test_build_sim_method_from_short_method(self):
        equil_step = self.source_method.method_steps[1]
        equil_buffer = equil_step.solutions[0]
        # strip out pre-equil and equil steps and make sure we can still build
        # the sim.
        with self.remove_n_steps_source_method():
            method = build_sim_method_from_method(
                self.source_method, self.first_simulated_step,
                self.last_simulated_step, initial_buffer=equil_buffer
            )
            self.assertValidMethod(method, init_buffer_auto_set=False)

    def test_build_1step_method(self):
        """ Test that a simulation method can be built from a method containing
        just the method steps simulated.
        """
        equil_step = self.source_method.method_steps[1]
        equil_buffer = equil_step.solutions[0]
        first_simulated_step = "Load"
        last_simulated_step = first_simulated_step
        method = build_sim_method_from_method(
            self.source_method, first_simulated_step, last_simulated_step,
            initial_buffer=equil_buffer
        )
        self.assertValidMethod(method, num_steps=1, fstep=first_simulated_step,
                               lstep=last_simulated_step, test_pooling=False)

    # Utilities ---------------------------------------------------------------

    @contextmanager
    def remove_n_steps_source_method(self, n=2):
        removed_steps = self.source_method.method_steps[:n]
        self.source_method.method_steps = self.source_method.method_steps[n:]
        self.source_method.collection_step_number -= n
        yield
        self.source_method.method_steps = removed_steps + \
            self.source_method.method_steps
        self.source_method.collection_step_number += n

    def assertValidMethod(self, method, num_steps=4, fstep="", lstep="",
                          init_buffer_auto_set=True, test_pooling=True):
        """ Make sure the provided method has the right nature, steps, and
        initial buffer.
        """
        if not fstep:
            fstep = self.first_simulated_step

        if not lstep:
            lstep = self.last_simulated_step

        self.assertIsInstance(method, Method)
        self.assertEqual(len(method.method_steps), num_steps)
        self.assertEqual(method.method_steps[0].step_type, fstep)
        self.assertEqual(method.method_steps[-1].step_type, lstep)
        self.assertIsInstance(method.initial_buffer, Solution)
        self.assertEqual(method.initial_buffer.name, 'Equil_Wash_1')
        self.assertEqual(method.collection_step_number, 2)
        if test_pooling:
            pooling_step = method.method_steps[method.collection_step_number]
            self.assertEqual(pooling_step.step_type, "Gradient Elution")

        if init_buffer_auto_set:
            _, first_step_idx = self.source_method.get_step_of_name(
                fstep, collect_step_num=True
            )
            init_step = self.source_method.method_steps[first_step_idx - 1]
            self.assertIn(method.initial_buffer, init_step.solutions)
