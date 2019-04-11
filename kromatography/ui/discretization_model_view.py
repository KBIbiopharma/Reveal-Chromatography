from traits.api import Instance
from traitsui.api import Item, ModelView, VGroup, View


from app_common.traitsui.positive_int_editor import (
    PositiveIntEditor)
from app_common.traitsui.positive_float_editor import (
    PositiveFloatEditor)

from kromatography.model.discretization import Discretization


class DiscretizationView(ModelView):
    """ View for the Discretization Parameters.
    """

    # -------------------------------------------------------------------------
    # ModelView interface
    # -------------------------------------------------------------------------

    model = Instance(Discretization)

    def default_traits_view(self):

        view = View(
            VGroup(
                Item("model.ncol", label="Number of Column Discretization "
                                         "Points",
                     editor=PositiveIntEditor()),
                Item("model.npar", label="Number of Bead Discretization "
                                         "Points",
                     editor=PositiveIntEditor()),
                Item("model.par_disc_type", label="Bead Discretization "
                                                  "Scheme"),
                label="Discretization Parameters", show_border=True
            ),
            VGroup(
                Item("model.weno.boundary_model", label="WENO Boundary "
                                                        "Model"),
                Item("model.weno.weno_eps", label="WENO Epsilon",
                     editor=PositiveFloatEditor()),
                Item("model.weno.weno_order", label="WENO Order"),
                label="WENO Parameters", show_border=True,
            ),
        )
        return view


if __name__ == '__main__':

    # Build a model you want to visualize:
    model = Discretization()

    # Build model view, passing the model as a model and make a window for it:
    discretization_model_view = DiscretizationView(model=model)
    discretization_model_view.configure_traits()
