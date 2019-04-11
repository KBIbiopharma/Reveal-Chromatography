from traits.api import HasStrictTraits, Instance, List, Str
from traitsui.api import Item, EnumEditor, Label, ListStrEditor, \
    OKCancelButtons

from kromatography.model.study import Study
from .krom_view import KromView


class BaseSimulationSelector(HasStrictTraits):
    """ Base class to support selecting 1 or more simulations from a study.
    """
    #: Study containing the simulations to choose from
    study = Instance(Study)

    # List of available Simulation names to choose from
    simulation_names_available = List(Str)

    # List of available SimulationGroup names to choose from
    simulation_group_names_available = List(Str)

    title = Str("Select Simulation(s)")

    def _simulation_names_available_default(self):
        return [sim.name for sim in self.study.simulations]

    def _simulation_group_names_available_default(self):
        return [group.name
                for group in self.study.analysis_tools.simulation_grids]


class SimulationSelector(BaseSimulationSelector):
    """ Selector for a set of Simulations and SimulationGroups from a study.

    Flexible title and description since it is used for multiple tools:
    """
    #: List of simulation names selected
    simulations_selected = List(Str)

    #: Title of the window
    title = Str("Select Simulations")

    #: Text displayed above the simulation selector, to guide user:
    description = Str('To select more than 1 simulation, press the Ctrl key:')

    def default_traits_view(self):
        view = KromView(
            Label(self.description),
            Item(
                "simulation_names_available",
                editor=ListStrEditor(selected="simulations_selected",
                                     multi_select=True, editable=False),
                show_label=False),
            buttons=OKCancelButtons,
            title=self.title
        )
        return view


class SingleSimulationSelector(BaseSimulationSelector):
    """ Class to support select a single simulation from a study.
    """
    #: List of simulation names selected
    simulation_selected = Str

    title = Str("Select Simulation")

    def default_traits_view(self):
        editor = EnumEditor(values=self.simulation_names_available)

        view = KromView(
            Item("simulation_selected", editor=editor, show_label=False,
                 style="custom"),
            buttons=OKCancelButtons,
            title=self.title
        )
        return view


class SingleSimulationGroupSelector(BaseSimulationSelector):
    """ Class to support select a single SimulationGroup from a study.
    """
    simulation_group_selected = Str

    title = Str("Select Simulation Group")

    def default_traits_view(self):
        editor = EnumEditor(values=self.simulation_group_names_available)

        view = KromView(
            Item("simulation_group_selected", editor=editor, show_label=False,
                 style="custom"),
            buttons=OKCancelButtons,
            title=self.title
        )
        return view


class RanSimulationChooser(SingleSimulationSelector):
    """ Class to support select an already ran simulation from a study.
    """
    def _simulation_names_available_default(self):
        """ Filter out simulations that haven't been run."""
        return [sim.name for sim in self.study.simulations
                if sim.output is not None]
