from unittest import TestCase

from app_common.apptools.testing_utils import temp_bringup_ui_for

from kromatography.tools.preferences_view import \
    RevealChromatographyPreferenceView
from kromatography.utils.app_utils import get_preferences


class TestPreferencesView(TestCase):
    def setUp(self):
        self.prefs = get_preferences()

    def test_bring_up(self):
        view = RevealChromatographyPreferenceView(model=self.prefs)
        with temp_bringup_ui_for(view):
            pass
