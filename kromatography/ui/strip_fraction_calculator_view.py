""" Assistant to display and override Experiments' strip fractions.
"""
from scimath.units.api import UnitScalar
from traits.api import HasStrictTraits, Instance, Property, Str
from traitsui.api import Action, Handler, HGroup, Item, Label, Spring, VGroup

from kromatography.model.api import SolutionWithProduct
from app_common.traitsui.unit_scalar_editor import \
    UnitScalarEditor
from kromatography.utils.traitsui_utils import KromView
from kromatography.compute.strip_fraction_calculator import \
    StripFractionCalculator


ResetButton = Action(name='Reset all', action="do_reset",
                     toolip="Reset all experiment parameters.")

ApplyButton = Action(name='Apply', action="do_apply")


class StripFractionCalculatorHandler(Handler):
    """ Controller for the StripFractionCalculatorEditor, controlling the
    custom buttons.
    """
    def do_apply(self, info):
        strip_mass_fraction = info.object.model.strip_mass_fraction
        info.object.model.experim.strip_mass_fraction = strip_mass_fraction

        # Close the window
        info.ui.dispose()

    def do_reset(self, info):
        calculator = info.object.model
        calculator.reset = True

    def close(self, info, is_ok, skip_reset=False):
        """ Closing the window or Cancel button requested. Reset the model.
        """
        if not skip_reset:
            self.do_reset(info)

        return super(StripFractionCalculatorHandler, self).close(info, is_ok)


class StripFractionCalculatorView(HasStrictTraits):
    """ Editor for interactive computation of the strip fraction in experiment.
    """
    model = Instance(StripFractionCalculator)

    # Data that will be affected by the tool

    #: Solution that will be modified by the tool is Apply button is pressed
    _load_solution = Property(Instance(SolutionWithProduct),
                              depends_on="model")

    #: Name of the solution that will be modified
    _load_solution_name = Property(Str, depends_on="_load_solution")

    #: Current value of the strip fraction as specified on corresponding load
    _current_strip_mass_fraction = Property(Instance(UnitScalar),
                                            depends_on="_load_solution")

    def default_traits_view(self):
        landing_text = r"Strip contribution estimation for Experiment " \
                       r"'<i>{}</i>' (load '<i>{}</i>'), from the specified " \
                       r"load concentration, method step <br>start times and "\
                       r"estimated product extinction coefficient:"
        landing_text = landing_text.format(self.model.experim.name,
                                           self._load_solution_name)
        formula = "strip_fraction = 1 - mass_eluting_before_strip / " \
                  "loaded_mass"

        view = KromView(
            VGroup(
                VGroup(
                    Label(landing_text),
                    HGroup(
                        Spring(),
                        Label(formula),
                        Spring(),
                    ),
                    show_border=True
                ),
                VGroup(
                    HGroup(
                        VGroup(
                            Item("object.model.load_concentration",
                                 editor=UnitScalarEditor()),
                            Item("object.model.loaded_volume",
                                 editor=UnitScalarEditor())
                        ),
                        Spring(),
                        VGroup(
                            Spring(),
                            Item("object.model.loaded_mass",
                                 editor=UnitScalarEditor(),
                                 style="readonly"),
                            Spring(),
                        ),
                    ),
                    show_border=True, label="Product loaded into the column"
                ),
                HGroup(
                    VGroup(
                        Item("object.model.product_ext_coeff",
                             editor=UnitScalarEditor(),
                             label="Est. product extinction coef."),
                        Item("object.model.load_start",
                             label="Load start time",
                             editor=UnitScalarEditor()),
                        Item("object.model.strip_start",
                             label="Strip start time",
                             editor=UnitScalarEditor()),
                    ),
                    Spring(),
                    VGroup(
                        Spring(),
                        Item("object.model.integrated_mass_before_strip",
                             label="Mass eluting before strip",
                             editor=UnitScalarEditor(), style="readonly"),
                        Spring()
                    ),
                    show_border=True, label="Product recovered before Strip"
                ),
                HGroup(
                    Spring(),
                    Item("object.model.strip_mass_fraction",
                         editor=UnitScalarEditor(),
                         label="Proposed Strip Mass Fraction"),
                    Item("_current_strip_mass_fraction",
                         editor=UnitScalarEditor(), style="readonly",
                         label="Current Strip Mass Fraction"),
                    Spring()
                ),
            ),
            title="Strip Fraction Estimation Assistant",
            buttons=[ResetButton, ApplyButton],
            handler=StripFractionCalculatorHandler(),
        )
        return view

    def _get__load_solution(self):
        return self.model.experim.method.load.solutions[0]

    def _get__load_solution_name(self):
        return self._load_solution.name

    def _get__current_strip_mass_fraction(self):
        return self._load_solution.strip_mass_fraction
