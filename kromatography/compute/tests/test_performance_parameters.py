from unittest import TestCase

from traits.api import TraitError
from scimath.units.api import UnitArray, UnitScalar, unit_parser

from kromatography.utils.assertion_utils import assert_unit_scalar_almost_equal
from kromatography.compute.performance_parameters import \
    calculate_component_concentrations, calculate_pool_volume, \
    calculate_start_stop_collect, calculate_step_yield
from kromatography.model.solution_with_product import SolutionWithProduct
from kromatography.model.x_y_data import XYData
from kromatography.model.method_step import MethodStep
from kromatography.model.tests.example_model_data import (
    COLUMN_TYPE_DATA, COLUMN_DATA, RESIN_DATA, PRODUCT_DATA, Prod001_comp1,
    Prod001_comp2, Prod001_comp3
)
from kromatography.model.api import Column, ColumnType, Product, Resin
from kromatography.model.collection_criteria import CollectionCriteria
from kromatography.utils.app_utils import initialize_unit_parser

initialize_unit_parser()


class TestComputeStartStopCollect(TestCase):
    def setUp(self):
        # Build a fake peak
        x = range(5)
        y = [0., 1., 2., 1., 0.]
        self.data = XYData(x_data=x, y_data=y, name="sample data",
                           x_metadata={"units": "seconds"})

        # Build a fake double peak
        x = range(10)
        y = [0., 1., 2., 1., 0., 0., 1., 2., 1., 0.]
        self.data_2peaks = XYData(x_data=x, y_data=y, name="sample data",
                                  x_metadata={"units": "seconds"})

        self.step_start = UnitScalar(0/60., units="minute")
        self.step_stop = UnitScalar(4/60., units="minute")

    def test_compute_start_collect_time_fixed_abs(self):
        coll_criteria = CollectionCriteria(
            name="Test collec crit",
            start_collection_target=0.5,
            start_collection_type="Fixed Absorbance",
            stop_collection_target=1.5,
            stop_collection_type="Fixed Absorbance",
        )
        self.assertEqual(coll_criteria.start_collection_while, "Ascending")
        self.assertEqual(coll_criteria.stop_collection_while, "Descending")
        collections = calculate_start_stop_collect(
            self.data, coll_criteria, self.step_start, self.step_stop
        )
        start_time, start_idx, stop_time, stop_idx = collections
        self.assertEqual(start_time, UnitScalar(1./60., units="minute"))
        self.assertEqual(start_idx, 1)
        self.assertEqual(stop_time, UnitScalar(3./60., units="minute"))
        self.assertEqual(stop_idx, 3)

    def test_compute_start_collect_time_fixed_abs_searching_too_far(self):
        coll_criteria = CollectionCriteria(
            name="Test collec crit",
            start_collection_target=0.5,
            start_collection_type="Fixed Absorbance",
            stop_collection_target=1.5,
            stop_collection_type="Fixed Absorbance",
        )
        # These times are larger than the end of the dataset
        step_start = UnitScalar(5/60., units="minute")
        step_stop = UnitScalar(6/60., units="minute")
        with self.assertRaises(ValueError):
            calculate_start_stop_collect(self.data, coll_criteria, step_start,
                                         step_stop)

    def test_compute_start_collect_time_fixed_abs_start_descending(self):
        coll_criteria = CollectionCriteria(
            name="Test collec crit",
            start_collection_target=1.5,
            start_collection_type="Fixed Absorbance",
            start_collection_while="Descending",
            stop_collection_target=0.5,
            stop_collection_type="Fixed Absorbance",
        )
        self.assertEqual(coll_criteria.stop_collection_while, "Descending")

        collections = calculate_start_stop_collect(
            self.data, coll_criteria, self.step_start, self.step_stop
        )
        start_time, start_idx, stop_time, stop_idx = collections
        self.assertEqual(start_time, UnitScalar(3./60., units="minute"))
        self.assertEqual(start_idx, 3)
        self.assertEqual(stop_time, UnitScalar(4./60., units="minute"))
        self.assertEqual(stop_idx, 4)

    def test_compute_start_collect_time_fixed_abs_stop_before_start(self):
        coll_criteria = CollectionCriteria(
            name="Test collec crit",
            start_collection_target=0.5,
            start_collection_type="Fixed Absorbance",
            start_collection_while="Descending",
            stop_collection_target=1.5,
            stop_collection_type="Fixed Absorbance",
        )
        self.assertEqual(coll_criteria.stop_collection_while, "Descending")

        collections = calculate_start_stop_collect(
            self.data, coll_criteria, self.step_start, self.step_stop
        )
        start_time, start_idx, stop_time, stop_idx = collections
        self.assertGreater(start_time, stop_time)

    def test_compute_stop_collect_time_fixed_abs_stop_ascending(self):
        coll_criteria = CollectionCriteria(
            name="Test collec crit",
            start_collection_target=0.5,
            start_collection_type="Fixed Absorbance",
            stop_collection_while="Ascending",
            stop_collection_target=1.5,
            stop_collection_type="Fixed Absorbance",
        )
        self.assertEqual(coll_criteria.start_collection_while, "Ascending")

        collections = calculate_start_stop_collect(
            self.data, coll_criteria, self.step_start, self.step_stop
        )
        start_time, start_idx, stop_time, stop_idx = collections
        self.assertEqual(start_time, UnitScalar(1. / 60., units="minute"))
        self.assertEqual(start_idx, 1)
        self.assertEqual(stop_time, UnitScalar(2. / 60., units="minute"))
        self.assertEqual(stop_idx, 2)

    def test_compute_stop_collect_time_fixed_abs_stop_before_start_2(self):
        coll_criteria = CollectionCriteria(
            name="Test collec crit",
            start_collection_target=1.5,
            start_collection_type="Fixed Absorbance",
            stop_collection_while="Ascending",
            stop_collection_target=0.5,
            stop_collection_type="Fixed Absorbance",
        )
        self.assertEqual(coll_criteria.start_collection_while, "Ascending")

        collections = calculate_start_stop_collect(
            self.data, coll_criteria, self.step_start, self.step_stop
        )
        start_time, start_idx, stop_time, stop_idx = collections
        self.assertGreater(start_time, stop_time)

    def test_compute_start_collect_time_fixed_abs_double_peak(self):
        coll_criteria = CollectionCriteria(
            name="Test collec crit",
            start_collection_target=0.5,
            start_collection_type="Fixed Absorbance",
            stop_collection_target=1.5,
            stop_collection_type="Fixed Absorbance",
        )

        step_start = UnitScalar(5/60., units="minute")
        step_stop = UnitScalar(10/60., units="minute")
        collections = calculate_start_stop_collect(
            self.data_2peaks, coll_criteria, step_start, step_stop
        )
        start_time, start_idx, stop_time, stop_idx = collections
        self.assertEqual(start_time, UnitScalar(6./60., units="minute"))
        self.assertEqual(start_idx, 6)
        self.assertEqual(stop_time, UnitScalar(8./60., units="minute"))
        self.assertEqual(stop_idx, 8)

    def test_compute_start_collect_time_ppm_stop(self):
        coll_criteria = CollectionCriteria(
            name="Test collec crit",
            start_collection_target=0.5,
            start_collection_type="Fixed Absorbance",
            stop_collection_target=60,
            stop_collection_type="Percent Peak Maximum",
        )
        collections = calculate_start_stop_collect(
            self.data, coll_criteria, self.step_start, self.step_stop
        )
        start_time, start_idx, stop_time, stop_idx = collections
        self.assertEqual(start_time, UnitScalar(1./60., units="minute"))
        self.assertEqual(start_idx, 1)
        self.assertEqual(stop_time, UnitScalar(3./60., units="minute"))
        self.assertEqual(stop_idx, 3)

    def test_compute_start_collect_time_ppm(self):
        coll_criteria = CollectionCriteria(
            name="Test collec crit",
            start_collection_target=40,
            start_collection_type="Percent Peak Maximum",
            stop_collection_target=60,
            stop_collection_type="Percent Peak Maximum",
        )
        collections = calculate_start_stop_collect(
            self.data, coll_criteria, self.step_start, self.step_stop
        )
        start_time, start_idx, stop_time, stop_idx = collections
        self.assertEqual(start_time, UnitScalar(1. / 60., units="minute"))
        self.assertEqual(start_idx, 1)
        self.assertEqual(stop_time, UnitScalar(3. / 60., units="minute"))
        self.assertEqual(stop_idx, 3)

    def test_compute_start_collect_time_wrong_type(self):
        with self.assertRaises(TraitError):
            CollectionCriteria(
                name="Test collec crit",
                start_collection_target=0.5,
                start_collection_type="BAD TYPE",
                stop_collection_target=60,
                stop_collection_type="Percent Peak Maximum",
            )

    def test_compute_stop_collect_time_wrong_type(self):
        with self.assertRaises(TraitError):
            CollectionCriteria(
                name="Test collec crit",
                start_collection_target=0.5,
                start_collection_type="Percent Peak Maximum",
                stop_collection_target=60,
                stop_collection_type="BAD TYPE",
            )


class TestComputePerformanceParameters(TestCase):
    def setUp(self):
        #: Build a fake peak:
        # times is in seconds
        x = range(5)
        y = [0., 1., 2., 1., 0.]
        self.data = XYData(x_data=x, y_data=y, name="sample data")

        column_type = ColumnType(**COLUMN_TYPE_DATA)
        resin = Resin(**RESIN_DATA)
        self.column = Column(column_type=column_type, resin=resin,
                             **COLUMN_DATA)
        self.column.volume = UnitScalar(100., units="liter")

    def test_calculate_pool_volume(self):
        start_collect_time = UnitScalar(1, units="minute")
        stop_collect_time = UnitScalar(2, units="minute")
        flow_rate = UnitScalar(100, units="liter/minute")
        vol = calculate_pool_volume(start_collect_time, stop_collect_time,
                                    flow_rate, self.column)
        assert_unit_scalar_almost_equal(vol, UnitScalar(1, units="CV"))

    def test_calculate_pool_volume_no_time(self):
        start_collect_time = UnitScalar(1, units="minute")
        stop_collect_time = UnitScalar(1, units="minute")
        flow_rate = UnitScalar(3, units="m**3/minute")
        vol = calculate_pool_volume(start_collect_time, stop_collect_time,
                                    flow_rate, self.column)
        assert_unit_scalar_almost_equal(vol, UnitScalar(0.0, units="CV"))

    def test_calculate_step_yield(self):
        pool_concentration = UnitScalar(1, units="g/liter")
        pool_volume = UnitScalar(1, units="CV")
        step_volume = UnitScalar(1, units="CV")
        step_flow_rate = UnitScalar(100, units="liter/minute")
        sols = [SolutionWithProduct(product_concentration=pool_concentration,
                                    name="Sol")]
        load_step = MethodStep(step_type="Load", name="Load", solutions=sols,
                               flow_rate=step_flow_rate, volume=step_volume)
        step_yield = calculate_step_yield(pool_concentration, pool_volume,
                                          load_step)
        assert_unit_scalar_almost_equal(step_yield, UnitScalar(100, units="%"))

        pool_concentration09 = UnitScalar(0.9, units="g/liter")
        step_yield = calculate_step_yield(pool_concentration09, pool_volume,
                                          load_step)
        assert_unit_scalar_almost_equal(step_yield, UnitScalar(90, units="%"))

        pool_volume = UnitScalar(0.9, units="CV")
        step_yield = calculate_step_yield(pool_concentration, pool_volume,
                                          load_step)
        assert_unit_scalar_almost_equal(step_yield, UnitScalar(90, units="%"))

    def test_calculate_component_concentrations(self):
        comp_absorb_data = {"Acidic_1_Sim": self.data,
                            "Acidic_2_Sim": self.data,
                            "Native_Sim": self.data}
        comps = [Prod001_comp1, Prod001_comp2, Prod001_comp3]
        product = Product(product_components=comps, **PRODUCT_DATA)
        start_collect_idx, stop_collect_idx = 1, 3
        comp_conc = calculate_component_concentrations(
            product, comp_absorb_data, start_collect_idx, stop_collect_idx
        )
        self.assertIsInstance(comp_conc, UnitArray)
        self.assertEqual(comp_conc.units, unit_parser.parse_unit("g/liter"))
        # All the same value since all the same XYdata
        for concentration in comp_conc:
            self.assertEqual(concentration, comp_conc[0])
