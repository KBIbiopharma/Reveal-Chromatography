from unittest import TestCase

from traits.api import HasTraits
from traitsui.ui import UI

from app_common.apptools.testing_utils import temp_bringup_ui_for

from kromatography.utils.traitsui_utils import _NameEditor, prompt_for_new_name


class TestNameEditor(TestCase):

    def test_bring_up(self):
        obj = _NameEditor(old_name="blah")
        with temp_bringup_ui_for(obj):
            pass

    def test_default_new_name(self):
        obj = _NameEditor(old_name="blah")
        self.assertEqual(obj.new_name, "blah")


class TestPromptForNewName(TestCase):
    def test_trigger_name_editor_dialog(self):
        class Obj(HasTraits):
            name = "blah"

        ui = prompt_for_new_name(Obj(), kind=None)
        self.assertIsInstance(ui, UI)
