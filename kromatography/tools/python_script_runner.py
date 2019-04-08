from os.path import basename, splitext

from app_common.apptools.script_runner.python_script_runner import \
    PythonScriptRunner as BasePythonScriptRunner


class PythonScriptRunner(BasePythonScriptRunner):
    """ Customized version of the script running, controlling the context it is
    run in.
    """
    def _context_default(self):
        # Build the context from globals and then update with above so that the
        # above is guarantied to be un-modified.
        context = super(PythonScriptRunner, self)._context_default()

        # This test is only done to allow non-gui tests run scripts that don't
        # modify the GUI.
        if self.task:
            active_study = self.task.project.study
            study_ds = active_study.study_datasource
        else:
            active_study = None
            study_ds = None

        script_name = basename(self.path)
        mod_name = "kromatography.python_scripts." + splitext(script_name)[0]
        supp_context = {"user_datasource": self.app.datasource,
                        # Task and study from current active_task
                        "task": self.task, "study": active_study,
                        "study_datasource": study_ds,
                        "__name__": mod_name}
        context.update(supp_context)
        return context
