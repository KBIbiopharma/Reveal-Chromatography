from unittest import TestCase
from os.path import dirname, join
from numpy import isnan

from scimath.units.api import UnitScalar
from app_common.scimath.assertion_utils import assert_unit_scalar_almost_equal
from app_common.scimath.units_utils import has_mass_units
from app_common.apptools.testing_utils import temp_bringup_ui_for

import kromatography
from kromatography.io.study import load_study_from_excel
from kromatography.model.mass_balance_analyzer import MassBalanceAnalyzer
from kromatography.utils.string_definitions import UV_DATA_KEY
from kromatography.utils.app_utils import initialize_unit_parser
from kromatography.model.tests.sample_data_factories import \
    make_sample_experiment2
from kromatography.utils.chromatography_units import column_volumes
from kromatography.utils.testing_utils import io_data_path
from kromatography.io.api import load_object

initialize_unit_parser()


class TestMassBalanceAnalyzerView(TestCase):

    def setUp(self):
        fname = "PROD001_Example_Pulse_Injection_Study.xlsx"
        folder = join(dirname(kromatography.__file__), "data", "tutorial_data")
        fpath = join(folder, fname)
        pulse_study = load_study_from_excel(fpath, allow_gui=False)
        self.exp = pulse_study.search_experiment_by_name("Run_1")
        # Multi-component product experiment
        self.exp2 = make_sample_experiment2()

    def test_bring_up_pulse_inj_exp(self):
        mba = MassBalanceAnalyzer(target_experiment=self.exp)
        with temp_bringup_ui_for(mba):
            pass

    def test_bring_up_ge_exp(self):
        mba = MassBalanceAnalyzer(target_experiment=self.exp2)
        with temp_bringup_ui_for(mba):
            pass


class TestMassBalanceAnalyzer(TestCase):

    @classmethod
    def setUpClass(cls):
        folder = join(dirname(kromatography.__file__), "data", "tutorial_data")
        cls.pulse_akta = join(folder, "47cm_hr.asc")
        # Originally stored in PROD001_Example_Pulse_Injection_Study.xlsx
        fname = io_data_path("prod1_pulse_run2_experiment.chrom")
        cls.exp = load_object(fname)[0]

        # Multi-component product experiment
        cls.exp2 = make_sample_experiment2()

    def setUp(self):
        self.load_volume = UnitScalar(0.0635/8.03, units="CV")
        self.load_concentration = UnitScalar(8.03, units="g/L")

    def test_create_no_exp(self):
        with self.assertRaises(ValueError):
            MassBalanceAnalyzer()

    def test_create_ge_exp(self):
        # Can create the analyzer with a gradient elution experiment, but can't
        # analyze:
        mba = MassBalanceAnalyzer(target_experiment=self.exp2)
        with self.assertRaises(ValueError):
            mba.analyze()

    def test_create_pass_exp_only(self):
        mba = MassBalanceAnalyzer(target_experiment=self.exp)
        self.assertIsInstance(mba, MassBalanceAnalyzer)
        self.assertIsNotNone(mba.continuous_data)
        self.assert_initial_state(mba)

    def test_create_pass_exp_and_cont_data_separately(self):
        # Remove the continuous data and pass it separately
        data = self.exp.output.continuous_data.pop(UV_DATA_KEY)
        try:
            mba = MassBalanceAnalyzer(target_experiment=self.exp,
                                      continuous_data=data)
            self.assertIsInstance(mba, MassBalanceAnalyzer)
            self.assert_initial_state(mba)
        finally:
            self.exp.output.continuous_data[UV_DATA_KEY] = data

    def test_compute_mass_from_method(self):
        mba = MassBalanceAnalyzer(target_experiment=self.exp)
        method_mass = mba.loaded_mass_from_method()
        self.assertTrue(has_mass_units(method_mass))

    def test_compute_mass_from_uv(self):
        mba = MassBalanceAnalyzer(target_experiment=self.exp)
        method_mass = mba.loaded_mass_from_uv()
        self.assertTrue(has_mass_units(method_mass))

    def test_compute_loaded_vol_to_balance_no_analysis(self):
        mba = MassBalanceAnalyzer(target_experiment=self.exp)
        # Raises error because analysis not done:
        with self.assertRaises(TypeError):
            mba.compute_loaded_vol()

    def test_compute_concentration_to_balance_no_analysis(self):
        mba = MassBalanceAnalyzer(target_experiment=self.exp)
        # Raises error because analysis not done:
        with self.assertRaises(TypeError):
            mba.compute_concentration()

    def test_analyze_method_and_akta_not_aligned(self):
        # The akta file contains data corresponding to the Load step and on,
        # so with this information, the data is not aligned, because the Equil
        # step duration isn't skipped:
        self.exp.method.offline_steps = []
        mba = MassBalanceAnalyzer(target_experiment=self.exp)
        self.assert_initial_state(mba)
        mba.analyze()
        self.assert_analyzed_state(mba, aligned=False)

    def test_analyze_method_and_akta_aligned(self):
        # The akta file contains data corresponding to the Load step and on,
        # so with this information, the data is aligned:
        self.exp.method.offline_steps = ["Equilibration"]
        # That data is only aligned at the 5% mark:
        mba = MassBalanceAnalyzer(target_experiment=self.exp,
                                  balance_threshold=0.05)
        self.assert_initial_state(mba)
        mba.analyze()
        self.assert_analyzed_state(mba, aligned=True)

    # Assertion utilities -----------------------------------------------------

    def assert_initial_state(self, mba):
        self.assertIsInstance(mba.balance_threshold, float)
        self.assertGreater(mba.balance_threshold, 0.)
        assert_unit_scalar_almost_equal(mba.current_volume,
                                        self.load_volume)
        assert_unit_scalar_almost_equal(mba.current_concentration,
                                        self.load_concentration)
        self.assertFalse(mba.balanced)

    def assert_analyzed_state(self, mba, aligned=False):
        self.assertIsInstance(mba.balance_threshold, float)
        self.assertGreater(mba.balance_threshold, 0.)
        assert_unit_scalar_almost_equal(mba.current_volume,
                                        self.load_volume)
        assert_unit_scalar_almost_equal(mba.current_concentration,
                                        self.load_concentration)
        # We know this file is balanced
        self.assertIsInstance(mba.mass_from_method, UnitScalar)
        self.assertFalse(isnan(mba.mass_from_method))
        self.assertIsInstance(mba.mass_from_uv, UnitScalar)
        self.assertFalse(isnan(mba.mass_from_uv))
        if aligned:
            self.assertTrue(mba.balanced)
        else:
            self.assertFalse(mba.balanced)

        # Can compute what values are needed to balance the data:
        new_vol = mba.compute_loaded_vol(tgt_units=column_volumes)
        self.assertEqual(new_vol.units.label, "CV")
        if aligned:
            self.assertAlmostEqual(float(new_vol), float(self.load_volume),
                                   places=4)

        new_conc = mba.compute_concentration()
        self.assertEqual(new_conc.units.label, "g/L")
        if aligned:
            self.assertAlmostEqual(float(new_conc),
                                   float(self.load_concentration), places=1)
