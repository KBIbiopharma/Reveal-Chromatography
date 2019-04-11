""" Assistant to display and override Experiments' strip fractions.
"""
from traits.api import HasStrictTraits, Instance, List
from traitsui.api import Action, Handler, Item, InstanceEditor, Tabbed, VGroup

from kromatography.model.api import Experiment
from kromatography.utils.traitsui_utils import KromView
from kromatography.compute.strip_fraction_calculator import \
    StripFractionCalculator
from kromatography.ui.strip_fraction_calculator_view import \
    StripFractionCalculatorView


ResetAllButton = Action(name='Reset All', action="do_reset")

ApplyAllButton = Action(name='Apply All', action="do_apply")


class MultiExpStripFractionCalculatorHandler(Handler):
    """ Controller for the StripFractionCalculatorEditor, controlling the
    custom buttons.
    """
    def do_apply(self, info):
        view = info.object
        for experim, calc in zip(view.target_experiments,
                                 view.fraction_calculators):
            experim.strip_mass_fraction = calc.strip_mass_fraction

        # Close the window
        res = self.close(info, True, skip_reset=True)
        self._on_close(info, skip_reset=True)
        return res

    def _on_close(self, info, skip_reset=False):
        """ Handles a "Close" request.
        """
        ready_to_close = ((info.ui.owner is not None) and
                          self.close(info, True, skip_reset=skip_reset))
        if ready_to_close:
            info.ui.owner.close()

    def do_reset(self, info):
        for calculator in info.object.fraction_calculators:
            calculator.reset = True

    def close(self, info, is_ok, skip_reset=False):
        """ Closing the window or Cancel button requested. Reset the model.
        """
        if not skip_reset:
            self.do_reset(info)

        return super(MultiExpStripFractionCalculatorHandler, self).close(info,
                                                                         is_ok)


class MultiExpStripFractionCalculatorView(HasStrictTraits):
    """ Editor for interactive computation of strip fraction for a list of
    experiments.
    """
    #: List of experiments to build strip fraction calculators for
    target_experiments = List(Instance(Experiment))

    #: List of strip fraction calculators for each target experiment
    fraction_calculators = List(Instance(StripFractionCalculator))

    def default_traits_view(self):
        view_items = []
        for i, calc in enumerate(self.fraction_calculators):
            calc_name = "_calc_view_{}".format(i)
            self.add_trait(calc_name, Instance(StripFractionCalculatorView))
            calc_view = StripFractionCalculatorView(model=calc)
            self.trait_set(**{calc_name: calc_view})

            view_item = VGroup(
                Item(calc_name, editor=InstanceEditor(),
                     style="custom", show_label=False),
                label=calc.experim.name
            )
            view_items.append(view_item)

        view = KromView(
            Tabbed(*view_items),
            title="Strip Fraction Estimation Assistant",
            buttons=[ResetAllButton, ApplyAllButton],
            handler=MultiExpStripFractionCalculatorHandler(),
        )
        return view

    def _target_experiments_changed(self):
        self.fraction_calculators = [StripFractionCalculator(experim=exp)
                                     for exp in self.target_experiments]
