""" Following the first script, this one creates objects that have more
realistic attributes. This script requires to be run in a project that contains
at least 1 experiment.
"""
from kromatography.model.api import Product, ProductComponent
from kromatography.utils.chromatography_units import UnitScalar
from kromatography.model.factories.simulation import build_simulation_from_experiment
from kromatography.model.binding_model import PhDependentStericMassAction

# Now making a new product with components in it:
comp1 = ProductComponent(name="Comp1", molecular_weight=UnitScalar(18.8, units="kg/mol"),
                         extinction_coefficient=UnitScalar(0.75, units="(AU * L)/(cm * g)"))
comp2 = ProductComponent(name="Comp2", molecular_weight=UnitScalar(18.8, units="kg/mol"),
                         extinction_coefficient=UnitScalar(0.75, units="(AU * L)/(cm * g)"))
# To measure the component concentration, we need a corresponding assay and
# expression
assays = ["CEX_comp1", "CEX_comp2"]
product_component_concentration_exps = ["product_concentration * CEX_comp1 / 100",
                                        "product_concentration * CEX_comp2 / 100"]
new_prod = Product(name="PROD003", product_type="Mab",
                   product_components=[comp1, comp2],
                   product_component_concentration_exps=product_component_concentration_exps,
                   product_component_assays=assays)
user_datasource.set_object_of_type("products", new_prod)
user_datasource.set_object_of_type("product_components", comp1)
user_datasource.set_object_of_type("product_components", comp2)

print("Current Study contains {} experiments".format(len(study.experiments)))

# Create a new simulation from an existing experiment:
exp = study.experiments[0]
# Let's give it a pH dependent binding model, leaving the rest as defaults.
# Note: +1 because binding models need 1 component for the cation component
ph_binding = PhDependentStericMassAction(num_prod_comp=exp.product.num_components,
                                         name="New binding")
new_sim = build_simulation_from_experiment(exp, binding_model=ph_binding)
study.add_simulations(new_sim)

# Open the new product in the central pane:
task.edit_object_in_central_pane(new_prod)
task.edit_object_in_central_pane(new_sim)
