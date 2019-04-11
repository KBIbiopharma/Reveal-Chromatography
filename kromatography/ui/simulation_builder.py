import logging

from traits.api import Enum, HasStrictTraits, Instance, List, Property, Str
from traitsui.api import EnumEditor

from kromatography.model.data_source import DataSource
from kromatography.model.discretization import DISCRETIZATION_TYPES
from kromatography.model.solver import SOLVER_TYPES

logger = logging.getLogger(__name__)


class SimulationBuilder(HasStrictTraits):
    """ Base class to build a simulation from datasource or experiment.
    """
    #: Name of the future simulation
    simulation_name = Str("New Simulation")

    #: Target study datasource w/ custom objects (solutions, binding, ...)
    study_datasource = Instance(DataSource)

    #: Name of the first simulated step
    first_simulated_step_name = Enum(values="step_names")

    #: Name of the last simulated step
    last_simulated_step_name = Enum(values="step_names")

    #: List of all the names of the steps in the source method
    step_names = Property(depends_on="method")

    #: Name of the solution the resin was in at the start of the simulation
    initial_buffer_name = Enum(values="all_buffers")

    #: All buffers to pick from for the initial condition state:
    all_buffers = List

    #: Solution that the resin is in at the start of the simulation
    initial_buffer = Property(depends_on="initial_buffer_name")

    #: Name of the transport model to use in the simulation
    transport_model_name = Str

    #: Instance of the TransportModel the output simulation should get
    transport_model = Property(depends_on="transport_model_name")

    #: Name of the binding model to use in the simulation
    binding_model_name = Str

    #: Instance of the BindingModel the output simulation should get
    binding_model = Property(depends_on="binding_model_name")

    #: Type of solver to create the simulation with
    solver_type = Enum(SOLVER_TYPES)

    #: Type of discretization model to build the simulation from
    discretization_type = Enum(DISCRETIZATION_TYPES)

    # Private interface -------------------------------------------------------

    def _build_enum_editor_for_type(self, type_id):
        """ Retrieve all possible value names for the given type. """
        all_model_names = self._build_list_objects_for_type(type_id)
        editor = EnumEditor(values=all_model_names)
        return editor

    def _build_list_objects_for_type(self, type_id):
        datasource = self._get_datasource(type_id)
        all_model_names = datasource.get_object_names_by_type(type_id)
        return all_model_names

    def _get_datasource(self, type_id):
        """ Depending on the type of data to store or access, return the
        appropriate datasource.
        """
        if type_id == "products":
            datasource = self.datasource
        else:
            datasource = self.study_datasource
        return datasource

    def _get_object_clone_from_name(self, type_id, object_name):
        """ Make a clone of the default object in the appropriate datasource
        for the object type and name.
        """
        if not object_name:
            return None

        ds = self._get_datasource(type_id)
        obj = ds.get_object_of_type(type_id, object_name)
        clone = obj.clone_traits(copy="deep")
        return clone

    # Trait initializations ---------------------------------------------------

    def _all_buffers_default(self):
        return [""] + self._build_list_objects_for_type("buffers")

    def _transport_model_name_default(self):
        if self.study_datasource and self.study_datasource.transport_models:
            return self.study_datasource.transport_models[0].name
        else:
            return ""

    def _binding_model_name_default(self):
        if self.study_datasource and self.study_datasource.transport_models:
            return self.study_datasource.binding_models[0].name
        else:
            return ""

    # Property getters/setters ------------------------------------------------

    def _get_initial_buffer(self):
        if not self.initial_buffer_name:
            return None
        else:
            return self._get_object_clone_from_name("buffers",
                                                    self.initial_buffer_name)

    def _get_transport_model(self):
        return self._get_object_clone_from_name("transport_models",
                                                self.transport_model_name)

    def _get_binding_model(self):
        return self._get_object_clone_from_name("binding_models",
                                                self.binding_model_name)
