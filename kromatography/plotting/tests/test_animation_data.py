from unittest import TestCase

from kromatography.plotting.animation_data import AnimationData, \
    _build_animation_data_from_sim
from kromatography.utils.testing_utils import \
    load_default_experiment_simulation


class TestAnimationData(TestCase):

    def setUp(self):
        _, self.sim = load_default_experiment_simulation()

    def test_build_animation(self):
        for i in range(3):
            anim_data = _build_animation_data_from_sim(self.sim, i)
            self.assertIsInstance(anim_data, AnimationData)

        with self.assertRaises(IndexError):
            _build_animation_data_from_sim(self.sim, 4)
