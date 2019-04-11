
from traits.api import register_factory
from traitsui.api import ModelView

from kromatography.ui.study_model_view import Study, StudyView
from kromatography.ui.resin_model_view import Resin, ResinView
from kromatography.ui.component_model_view import Component, ComponentView
from kromatography.ui.column_model_view import Column, ColumnView
from kromatography.ui.column_type_model_view import ColumnType, ColumnTypeView
from kromatography.ui.product_component_model_view import ProductComponent, \
    ProductComponentView

from kromatography.ui.chemical_model_view import Chemical, ChemicalView
from kromatography.ui.product_model_view import Product, ProductView
from kromatography.ui.system_model_view import System, SystemView
from kromatography.ui.system_type_model_view import SystemType, SystemTypeView
from kromatography.ui.solver_model_view import Solver, SolverView
from kromatography.ui.general_rate_model_view import (
    GeneralRateModel, GeneralRateModelView
)
from kromatography.ui.discretization_model_view import (
    Discretization, DiscretizationView
)
from kromatography.ui.steric_mass_action_model_view import(
    StericMassAction, StericMassActionModelView
)
from kromatography.ui.ph_dependent_steric_mass_action_model_view import(
    PhDependentStericMassAction, PhDependentStericMassActionModelView
)
from kromatography.ui.external_langmuir_model_view import (
    ExternalLangmuir, ExternalLangmuirView
)
from kromatography.ui.langmuir_model_view import Langmuir, LangmuirView
from kromatography.ui .method_model_view import Method, MethodModelView
from kromatography.ui.buffer_model_view import Buffer, BufferView
from kromatography.ui.solution_with_product_view import \
    SolutionWithProduct, SolutionWithProductView
from kromatography.ui.simulation_view import Simulation, SimulationView
from kromatography.ui.simulation_group_model_view import SimulationGroup, \
    SimulationGroupView
from kromatography.ui.brute_force_optimizer_model_view import \
    BruteForceOptimizer, BruteForceOptimizerView
from kromatography.ui.brute_force_optimizer_step_model_view import \
    BruteForceOptimizerStep, BruteForceOptimizerStepView


def register_all_data_views():
    """ Register all ModelView classes for all data models.
    """
    register_factory(StudyView, Study, ModelView)
    register_factory(ResinView, Resin, ModelView)
    register_factory(ComponentView, Component, ModelView)
    register_factory(ColumnView, Column, ModelView)
    register_factory(ColumnTypeView, ColumnType, ModelView)
    register_factory(ChemicalView, Chemical, ModelView)
    register_factory(ProductView, Product, ModelView)
    register_factory(GeneralRateModelView, GeneralRateModel, ModelView)
    register_factory(SystemView, System, ModelView)
    register_factory(SolverView, Solver, ModelView)
    register_factory(DiscretizationView, Discretization, ModelView)
    register_factory(SystemView, System, ModelView)
    register_factory(SystemTypeView, SystemType, ModelView)
    register_factory(StericMassActionModelView, StericMassAction, ModelView)
    register_factory(PhDependentStericMassActionModelView,
                     PhDependentStericMassAction, ModelView)
    register_factory(ExternalLangmuirView, ExternalLangmuir, ModelView)
    register_factory(LangmuirView, Langmuir, ModelView)
    register_factory(MethodModelView, Method, ModelView)
    register_factory(BufferView, Buffer, ModelView)
    register_factory(SolutionWithProductView, SolutionWithProduct, ModelView)
    register_factory(SimulationGroupView, SimulationGroup, ModelView)
    register_factory(SimulationView, Simulation, ModelView)
    register_factory(BruteForceOptimizerView, BruteForceOptimizer, ModelView)
    register_factory(BruteForceOptimizerStepView, BruteForceOptimizerStep,
                     ModelView)
    register_factory(ProductComponentView, ProductComponent, ModelView)
