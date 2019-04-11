from os.path import dirname, join
from unittest import TestCase

from app_common.apptools.script_runner.python_script_runner import \
    PythonScriptRunError

from kromatography.app.krom_app import instantiate_app
from kromatography.tools.python_script_runner import \
    PythonScriptRunner

HERE = dirname(__file__)

SPLASH_DURATION = 0.1

EXPECTED_CONTEXT_ENTRIES = ["app", "task", "study", "user_datasource",
                            "study_datasource",  "__name__"]


class TestPythonScriptRunner(TestCase):

    def setUp(self):
        self.filepath = join(HERE, "data", "no_gui_script.py")
        self.code = open(self.filepath).read()
        # TODO: Contribute a task for more realistic script context
        self.app = instantiate_app(
            splash_duration=SPLASH_DURATION, verbose=False
        )

    def test_script_cant_run_without_app(self):
        script = PythonScriptRunner(code=self.code)
        with self.assertRaises(ValueError):
            script.run()

    def test_script_no_context_without_app(self):
        script = PythonScriptRunner(code=self.code)
        with self.assertRaises(ValueError):
            getattr(script, "context")

    def test_context_content(self):
        script = PythonScriptRunner(code=self.code, app=self.app)
        for key in EXPECTED_CONTEXT_ENTRIES:
            self.assertIn(key, script.context)

        self.assertIs(script.context["app"], self.app)
        self.assertIs(script.context["user_datasource"], self.app.datasource)

    def test_app_runs_no_gui_script(self):
        script = PythonScriptRunner(code=self.code, app=self.app)
        output = script.run()
        self.assertIsInstance(output, str)

    def test_output_from_run(self):
        script = PythonScriptRunner(code="print('ABCDE')", app=self.app)
        output = script.run()
        self.assertEqual(output, 'ABCDE\n')

    def test_app_raises_on_bad_code(self):
        code = "BAD CODE THAT CAN'T RUN"
        script = PythonScriptRunner(code=code, app=self.app)
        with self.assertRaises(PythonScriptRunError):
            script.run()
