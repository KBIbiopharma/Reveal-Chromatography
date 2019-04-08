from traits.api import Instance
from traitsui.api import BooleanEditor, Item, ModelView, VGroup, View

from app_common.traitsui.positive_int_editor import (
    PositiveIntEditor)
from app_common.traitsui.positive_float_editor import (
    PositiveFloatEditor)
from kromatography.model.solver import Solver


class SolverView(ModelView):
    """ View for Solver Parameters.
    """

    model = Instance(Solver)

    def default_traits_view(self):
        view = View(
            VGroup(
                Item("model.number_user_solution_points",
                     label="Number of Time Points in Solution"),
                Item("model.nthreads",
                     label="Number of Solver Threads"),
                Item("model.write_solution_all",
                     label="Save Solution for all Discretization Points",
                     editor=BooleanEditor()),
                Item("model.use_analytic_jacobian",
                     label="Use Analytic Jacobian",
                     editor=BooleanEditor()),
                label="Solver Setup", show_border=True
            ),
            VGroup(
                Item("model.time_integrator.abstol",
                     label="Absolute Yolerance in the Solution",
                     editor=PositiveFloatEditor()),
                Item("model.time_integrator.init_step_size",
                     label="Initial Step Size Factor",
                     editor=PositiveFloatEditor()),
                Item("model.time_integrator.max_steps",
                     label="Maximum Number of Timesteps",
                     editor=PositiveIntEditor()),
                Item("model.time_integrator.reltol",
                     label="Relative Tolerance in the Solution",
                     editor=PositiveFloatEditor()),
                label="Time Integrator Parameters", show_border=True
            ),
            VGroup(
                Item("model.schur_solver.gs_type",
                     label="Type of Gram-Schmidt Orthogonalization"),
                Item("model.schur_solver.max_krylov",
                     label="Size of the Iterative Linear SPGMR Solver"),
                Item("model.schur_solver.max_restarts",
                     label="Maximum Number of GMRES Restarts",
                     editor=PositiveIntEditor()),
                Item("model.schur_solver.schur_safety",
                     label="Schur Safety Factor",
                     editor=PositiveFloatEditor()),
                label="Schur Solver Parameters", show_border=True
            ),
        )
        return view

if __name__ == '__main__':
    # Build a model you want to visualize:
    solvertest = Solver()

    # Build model view, passing the model as a model and make a window for it:
    solver_model_view = SolverView(model=solvertest)
    solver_model_view.configure_traits()
