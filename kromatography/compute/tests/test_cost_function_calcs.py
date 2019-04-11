import unittest
import numpy as np

from kromatography.compute.cost_function_calcs import \
    calc_peak_center_of_mass, calc_peak_timing, calc_trailing_slope, \
    find_index_of_first_value_below


class Test(unittest.TestCase):

    def setUp(self):
        # Rectangle peak:
        self.rect_x = np.array([0., 0., 1., 1.])
        self.rect_y = np.array([0., 1., 1., 0.])

        # Triangle peak:
        self.trian_y = np.array([0., 1., 2., 3., 2., 1., 0.])
        self.trian_x = np.arange(len(self.trian_y))

        # Triangle2 peak:
        self.trian_y2 = np.array([0., 0.5, 1., 1.5, 1., 0.5, 0.])
        self.trian_x2 = np.arange(len(self.trian_y))

    def test_calc_peak_center_of_mass(self):
        x_peak_com = calc_peak_center_of_mass(self.rect_x, self.rect_y)
        self.assertAlmostEqual(x_peak_com, 0.5)

        x_peak_com = calc_peak_center_of_mass(self.trian_x, self.trian_y)
        self.assertAlmostEqual(x_peak_com, 3.)

    def test_calc_peak_timing(self):
        x_peak = calc_peak_timing(self.trian_x, self.trian_y)
        self.assertAlmostEqual(x_peak, 3.)

        # Returns the first value at which the peak is reached...
        x_peak = calc_peak_timing(self.rect_x, self.rect_y)
        self.assertAlmostEqual(x_peak, 0.)

    def test_calc_trailing_slope(self):
        slope = calc_trailing_slope(self.trian_x, self.trian_y,
                                    low_trigger_fraction=0.5,
                                    high_trigger_fraction=1.)
        self.assertAlmostEqual(slope, -1.)

        slope = calc_trailing_slope(self.trian_x2, self.trian_y2,
                                    low_trigger_fraction=0.5,
                                    high_trigger_fraction=1.)
        self.assertAlmostEqual(slope, -0.5)

        # Returns 0 when the low fraction is not reached before the end
        x_peak = calc_peak_timing(self.rect_x, self.rect_y)
        self.assertAlmostEqual(x_peak, 0.)

    def test_find_index_of_first_value_below(self):
        loc = find_index_of_first_value_below(self.trian_y, 3, +1, 2.9)
        self.assertEqual(loc, 4)

        # Larger step forward:
        loc = find_index_of_first_value_below(self.trian_y, 3, +2, 2.9)
        self.assertEqual(loc, 5)

        # It is below or equal, so less than 3 is reached at 3:
        loc = find_index_of_first_value_below(self.trian_y, 3, +1, 3)
        self.assertEqual(loc, 3)

        # Stepping backward:
        loc = find_index_of_first_value_below(self.trian_y, 3, -1, 2.9)
        self.assertEqual(loc, 2)

        # Large step backward:
        loc = find_index_of_first_value_below(self.trian_y, 3, -2, 2.9)
        self.assertEqual(loc, 1)
