""" Example data for all the data models for testing.
"""

from scimath.units.unit_scalar import UnitArray, UnitScalar
from scimath.units.dimensionless import percent

from kromatography.model.buffer import Buffer
from kromatography.model.chemical import Chemical
from kromatography.model.collection_criteria import CollectionCriteria
from kromatography.model.component import Component
from kromatography.model.product import Product
from kromatography.model.product_component import ProductComponent
from kromatography.model.method_step import MethodStep
from kromatography.model.solution_with_product import SolutionWithProduct
from kromatography.utils.chromatography_units import (
    column_volumes, cm_per_hr, extinction_coefficient_unit, fraction,
    gram_per_liter, gram_per_milliliter, gram_per_mol, assay_unit,
    kg_per_liter, mS_per_cm, milli_molar, milliliter, ml_per_min, molar
)
from kromatography.model.factories.product import add_strip_to_product


RESIN_DATA = {
    'lot_id': 'Lot123456',
    'name': 'Fractogel-SO3 (M)',
    'ligand': 'SO2',
    'resin_type': 'CEX',
    'average_bead_diameter': UnitScalar(65.0, units='um'),
    'ligand_density': UnitScalar(75.0, units=milli_molar),
    'settled_porosity': UnitScalar(0.42, units=fraction),
}

# Chemical components
COMPONENT_DATA = {
    'name': 'Sodium',
    'charge': UnitScalar(1, units='1'),
    'pKa': UnitScalar(0.0, units='1')
}

COMPONENT2_DATA = {
    'name': 'Chloride',
    'charge': UnitScalar(-1, units='1'),
    'pKa': UnitScalar(0.0, units='1')
}

COMPONENT3_DATA = {
    'name': 'Acetate',
    'charge': UnitScalar(-1, units='1'),
    'pKa': UnitScalar(4.73, units='1')
}

CHEMICAL_DATA = {
    'name': 'Sodium Chloride',
    'component_list': [Component(**COMPONENT_DATA),
                       Component(**COMPONENT2_DATA)],
    'component_atom_counts': [1, 1],
    'state': 'Solid',
    'molecular_weight': UnitScalar(58.44, units=gram_per_mol)
}

CHEMICAL2_DATA = {
    'name': 'Sodium Acetate',
    'component_list': [Component(**COMPONENT_DATA),
                       Component(**COMPONENT3_DATA)],
    'component_atom_counts': [1, 1],
    'state': 'Solid',
    'molecular_weight': UnitScalar(82.02, units=gram_per_mol)
}

CHEMICAL3_DATA = {
    'name': 'Acetic Acid',
    'component_list': [Component(**COMPONENT3_DATA)],
    'component_atom_counts': [1],
    'state': 'Liquid',
    'molecular_weight': UnitScalar(60.05, units=gram_per_mol)
}

CHEMICAL4_DATA = {
    'name': 'Sodium Hydroxide',
    'component_list': [Component(**COMPONENT_DATA)],
    'component_atom_counts': [1],
    'state': 'Liquid',
    'molecular_weight': UnitScalar(40.0, units=gram_per_mol)
}

COLUMN_TYPE_DATA = {
    "name": "Axichrom 100",
    "manufacturer_name": "Axichrom 100",
    "manufacturer": "GE",
    "diameter": UnitScalar(100, units="cm"),
    "bed_height_range": UnitArray([10., 30.], units="cm"),
    "bed_height_adjust_method": "Hydraulic"
}

COLUMN_DATA = {
    "name": "CP_001",
    "column_lot_id": "CP_001",
    "bed_height_actual": UnitScalar(20.0, units="cm"),
    "compress_factor": UnitScalar(1.18, units=""),
    "hetp": UnitScalar(0.05, units="cm"),
    "hetp_asymmetry": UnitScalar(100, units=""),
}

PRODUCT_DATA = {
    'name': 'Prod001',
    'product_type': 'Globular',
    'product_component_assays': ['CEX_Acidic_2', 'CEX_Acidic_1', 'CEX_Native'],
    'product_component_concentration_exps': [
        'product_concentration * CEX_Acidic_2 / 100',
        'product_concentration * CEX_Acidic_1 / 100',
        'product_concentration * CEX_Native / 100'
    ],
    'impurity_names': ['Host_Cell_Proteins', 'DNA'],
    'impurity_assays': ['HCP_Elisa', 'DNA_Pico_Green'],
    'impurity_concentration_exps': [
        'product_concentration * HCP_Elisa / 1000',
        'product_concentration * DNA_Pico_Green / 1000'
    ],
    'pI': UnitScalar(7.52, units='1'),
    'amino_acids': ['Histidine', 'Cysteine'],
    'amino_acid_numbers': [10, 2]
}

# 3 ProductComponents for this product:
ACIDIC_1_PRODUCT_COMPONENT_DATA = {
    'target_product': 'Prod001',
    'name': 'Acidic_1',
    'molecular_weight': UnitScalar(18.8, units=gram_per_mol),
    'extinction_coefficient': UnitScalar(0.75,
                                         units=extinction_coefficient_unit),
}

ACIDIC_2_PRODUCT_COMPONENT_DATA = {
    'target_product': 'Prod001',
    'name': 'Acidic_2',
    'molecular_weight': UnitScalar(18.8, units=gram_per_mol),
    'extinction_coefficient': UnitScalar(0.75,
                                         units=extinction_coefficient_unit),
}

NATIVE_PRODUCT_COMPONENT_DATA = {
    'target_product': 'Prod001',
    'name': 'Native',
    'molecular_weight': UnitScalar(18.8, units=gram_per_mol),
    'extinction_coefficient': UnitScalar(0.75,
                                         units=extinction_coefficient_unit),
}

Prod001_comp1 = ProductComponent(**ACIDIC_1_PRODUCT_COMPONENT_DATA)
Prod001_comp2 = ProductComponent(**ACIDIC_2_PRODUCT_COMPONENT_DATA)
Prod001_comp3 = ProductComponent(**NATIVE_PRODUCT_COMPONENT_DATA)

Prod001 = Product(product_components=[Prod001_comp1, Prod001_comp2,
                                      Prod001_comp3], **PRODUCT_DATA)

Prod001_with_strip, Prod001_strip = add_strip_to_product(Prod001)

PRODUCT_DATA2 = {
    'name': 'Mab001',
    'product_type': 'MAB',
    'product_component_assays': ['CEX_Acidic', 'CEX_Main', 'CEX_Basic',
                                 'SEC_Monomer', 'SEC_Dimer'],
    'product_component_concentration_exps': [
        'product_concentration * SEC_Monomer * CEX_Acidic / 10000',
        'product_concentration * SEC_Monomer * CEX_Main / 10000',
        'product_concentration * SEC_Monomer * CEX_Basic / 10000',
        'product_concentration * SEC_Dimer / 100'
    ],
    'impurity_names': ['Host_Cell_Proteins', 'DNA'],
    'impurity_assays': ['HCP_Elisa', 'DNA_Pico_Green'],
    'impurity_concentration_exps': [
        'product_concentration * HCP_Elisa',
        'product_concentration * DNA_Pico_Green'
    ],
    'pI': UnitScalar(8.52, units='1'),
    'amino_acids': ['Histidine', 'Cysteine'],
    'amino_acid_numbers': [10, 2]
}

# 4 ProductComponents for this product:

ACIDIC_Monomer_PRODUCT_COMPONENT_DATA = {
    'target_product': 'Mab001',
    'name': 'Acidic_Monomer',
    'molecular_weight': UnitScalar(150.0, units=gram_per_mol),
    'extinction_coefficient': UnitScalar(1.5,
                                         units=extinction_coefficient_unit)
}

BASIC_Monomer_PRODUCT_COMPONENT_DATA = {
    'target_product': 'Mab001',
    'name': 'Basic_Monomer',
    'molecular_weight': UnitScalar(150.0, units=gram_per_mol),
    'extinction_coefficient': UnitScalar(1.5,
                                         units=extinction_coefficient_unit)
}

NEUTRAL_Monomer_PRODUCT_COMPONENT_DATA = {
    'target_product': 'Mab001',
    'name': 'Neutral_Monomer',
    'molecular_weight': UnitScalar(150.0, units=gram_per_mol),
    'extinction_coefficient': UnitScalar(1.5,
                                         units=extinction_coefficient_unit)
}

DIMER_PRODUCT_COMPONENT_DATA = {
    'target_product': 'Mab001',
    'name': 'Dimer',
    'molecular_weight': UnitScalar(300.0, units=gram_per_mol),
    'extinction_coefficient': UnitScalar(1., units=extinction_coefficient_unit)
}

Mab001_comp1 = ProductComponent(**ACIDIC_Monomer_PRODUCT_COMPONENT_DATA)
Mab001_comp2 = ProductComponent(**BASIC_Monomer_PRODUCT_COMPONENT_DATA)
Mab001_comp3 = ProductComponent(**NEUTRAL_Monomer_PRODUCT_COMPONENT_DATA)
Mab001_comp4 = ProductComponent(**DIMER_PRODUCT_COMPONENT_DATA)


PRODUCT_DATA_LIST_LENGTHS_BAD = {
    'name': 'Prod001',
    'product_type': 'Globular',
    'product_component_concentration_exps': [
        'product_concentration * CEX_Acidic_2 / 100',
        'product_concentration * CEX_Acidic_1 / 100',
        'product_concentration * CEX_Native / 100'
    ],
    'product_component_assays': ['CEX_Acidic_2', 'CEX_Acidic_1', 'CEX_Native'],
    'impurity_names': ['Host_Cell_Proteins', 'DNA'],
    'impurity_assays': ['HCP Elisa', 'DNA Pico Green'],
    'impurity_concentration_exps': [
        'product_concentration * HCP_Elisa / 1000',
        'product_concentration * DNA_Pico_Green / 1000'
    ],
    'pI': UnitScalar(7.52, units='1'),
    'amino_acids': ['Histidine', 'Cysteine'],
    'amino_acid_numbers': [10, 2]
}

PRODUCT_DATA_EXPRESSION_BAD_VAR = {
    'name': 'Mab001',
    'product_type': 'MAB',
    'product_component_assays': ['CEX_Acidic',
                                 'CEX_Main',
                                 'CEX_Basic',
                                 'SEC_Monomer',
                                 'SEC_Dimer'],
    'product_component_concentration_exps': [
        'product_concentration * not_a_variable * CEX_Acidic / 10000',
        'product_concentration * SEC_Monomer * CEX_Main / 10000',
        'product_concentration * SEC_Monomer * CEX_Basic / 10000',
        'product_concentration * SEC_Dimer / 100'
    ],
    'impurity_names': ['Host_Cell_Proteins', 'DNA'],
    'impurity_assays': ['HCP_Elisa', 'DNA_Pico_Green'],
    'impurity_concentration_exps': [
        'product_concentration * HCP_Elisa',
        'product_concentration * DNA_Pico_Green'
    ],
    'pI': UnitScalar(8.52, units='1'),
    'amino_acids': ['Histidine', 'Cysteine'],
    'amino_acid_numbers': [10, 2]
}

SOLUTIONWITHPRODUCT_LOAD = {
    'name': 'Load_2',
    'solution_type': 'Load',
    'source': 'Pilot Plant',
    'lot_id': 'A124',
    'product': Prod001,
    'product_concentration': UnitScalar(0.94, units=gram_per_liter),
    'product_component_assay_values': UnitArray([8.4, 88.2, 3.3997],
                                                units=percent),
    'impurity_assay_values': UnitArray([3.3997, 3.3997], units=assay_unit),
    'chemical_components': [Component(**COMPONENT_DATA),
                            Component(**COMPONENT3_DATA),
                            Component(**COMPONENT2_DATA)],
    'chemical_component_concentrations': UnitArray([30.0, 17.0, 20.0],
                                                   units=milli_molar),
    'density': UnitScalar(1.0, units=kg_per_liter),
    'conductivity': UnitScalar(3.0, units='mS/cm'),
    'pH': UnitScalar(4.95, units='1'),
    'temperature': UnitScalar(20.0, units='celsius')
}


SOLUTIONWITHPRODUCT_LOAD_WITH_STRIP = {
    'name': 'Load_2',
    'solution_type': 'Load',
    'source': 'Pilot Plant',
    'lot_id': 'A124',
    'product': Prod001_with_strip,
    'product_concentration': UnitScalar(0.94, units=gram_per_liter),
    'product_component_assay_values': UnitArray([8.4, 88.2, 3.3997, 0],
                                                units=percent),
    'impurity_assay_values': UnitArray([3.3997, 3.3997], units=assay_unit),
    'chemical_components': [Component(**COMPONENT_DATA),
                            Component(**COMPONENT3_DATA),
                            Component(**COMPONENT2_DATA)],
    'chemical_component_concentrations': UnitArray([30.0, 17.0, 20.0],
                                                   units=milli_molar),
    'density': UnitScalar(1.0, units=kg_per_liter),
    'conductivity': UnitScalar(3.0, units='mS/cm'),
    'pH': UnitScalar(4.95, units='1'),
    'temperature': UnitScalar(20.0, units='celsius')
}


SOLUTIONWITHPRODUCT_POOL = {
    'name': 'Run_2_pool',
    'solution_type': 'Pool',
    'source': 'Run_2',
    'lot_id': 'A124',
    'product': Prod001,
    'product_concentration': UnitScalar(0.4, units=gram_per_liter),
    'product_component_assay_values': UnitArray([1.0, 99.0, 0.0],
                                                units=percent),
    'impurity_assay_values': UnitArray([15.0, 150.0], units=assay_unit),
    'chemical_components': [Component(**COMPONENT_DATA),
                            Component(**COMPONENT3_DATA),
                            Component(**COMPONENT2_DATA)],
    'chemical_component_concentrations': UnitArray([30.0, 17.0, 20.0],
                                                   units=milli_molar),
    'conductivity': UnitScalar(8.0, units='mS/cm'),
    'pH': UnitScalar(5.45, units='1'),
}

BUFFER_PREP_EQUIL_WASH = {
    'name': 'Equil_Wash_1',
    'source': 'Lab',
    'lot_id': '100001',
    'chemicals': [Chemical(**CHEMICAL2_DATA),
                  Chemical(**CHEMICAL3_DATA)],
    'chemical_amounts': [UnitScalar(1.39, units='g'),
                         UnitScalar(3.0, units=milliliter)],
    'chemical_stock_concentrations': UnitArray([0.0, 1.0], units=molar),
    'chemical_densities': UnitArray([0.0, 1.01],
                                    units=gram_per_milliliter),
    'volume': UnitScalar(1000, units=milliliter),
    'density': UnitScalar(1.00, units=gram_per_liter),
    'conductivity': UnitScalar(2.01, units=mS_per_cm),
    'pH': UnitScalar(5.01, units='dimensionless'),
    'temperature': UnitScalar(20.0, units='celsius')
}

BUFFER_EQUIL_WASH1 = {
    'name': 'Equil_Wash_1',
    'source': 'Lab',
    'lot_id': '100001',
    'chemical_components': [
        Component(**COMPONENT_DATA),
        Component(**COMPONENT3_DATA)
    ],
    'chemical_component_concentrations': UnitArray(
        [16.94708608, 19.94708608],
        units=milli_molar
    ),
    'density': UnitScalar(1.00, units=gram_per_liter),
    'conductivity': UnitScalar(2.01, units=mS_per_cm),
    'pH': UnitScalar(5.01, units='dimensionless'),
    'temperature': UnitScalar(20.0, units='celsius')
}

BUFFER_ELUTION = {
    'name': 'Elution_1',
    'source': 'Lab',
    'lot_id': '100002',
    'chemical_components': [
        Component(**COMPONENT_DATA),
        Component(**COMPONENT3_DATA),
        Component(**COMPONENT2_DATA)
    ],
    'chemical_component_concentrations': UnitArray(
        [184.0020726652036, 20.00207266520361, 167.0],
        units=milli_molar
    ),
    'density': UnitScalar(1.01, units=gram_per_liter),
    'conductivity': UnitScalar(15.01, units=mS_per_cm),
    'pH': UnitScalar(4.99, units='dimensionless'),
    'temperature': UnitScalar(20.0, units='celsius')
}

BUFFER_PREP_ELUTION = {
    'name': 'Elution_1',
    'source': 'Lab',
    'lot_id': '100002',
    'chemicals': [Chemical(**CHEMICAL2_DATA),
                  Chemical(**CHEMICAL_DATA),
                  Chemical(**CHEMICAL3_DATA)],
    'chemical_amounts': [UnitScalar(1.39, units='g'),
                         UnitScalar(9.76, units='g'),
                         UnitScalar(3.0, units=milliliter)],
    'chemical_stock_concentrations': UnitArray([0.0, 0.0, 1.0], units=molar),
    'volume': UnitScalar(1000, units=milliliter),
    'density': UnitScalar(1.01, units=gram_per_liter),
    'conductivity': UnitScalar(15.01, units=mS_per_cm),
    'pH': UnitScalar(4.99, units='dimensionless'),
    'temperature': UnitScalar(20.0, units='celsius')
}

ELUTION_INTERNAL = {
    'components': [
        Component(**COMPONENT_DATA),
        Component(**COMPONENT3_DATA),
        Component(**COMPONENT2_DATA)
    ],
    'chemical_concentrations': UnitArray(
        [17.00207266520361, 167.0, 3.0],
        units=milli_molar
    ),
    'chemical_component_concentrations': UnitArray(
        [184.0020726652036, 20.00207266520361, 167.0],
        units=milli_molar
    )
}

STUDY_DATA = {
    "name": "New study",
    "study_type": "Parameter Estimation",
    "study_purpose": "This is a test study for unit testing purposes.",
}

EXPERIMENTAL_STUDY_DATA = {
    "name": "New experimental study",
    "study_purpose": "This is a test study for unit testing purposes.",
    "study_site": "Boulder",
    "experimentalist": "John Doe",
    "study_type": "Model Calibration",
}

buffer_equil_wash1 = Buffer(**BUFFER_EQUIL_WASH1)

PRE_EQUIL_STEP = {
    'step_type': 'Pre-Equilibration',
    'name': 'Pre-Equilibration',
    'solutions': [buffer_equil_wash1],
    'flow_rate': UnitScalar(200.0, units=cm_per_hr),
    'volume': UnitScalar(1.5, units=column_volumes)
}

EQUIL_STEP = {
    'step_type': 'Equilibration',
    'name': 'Equilibration',
    'solutions': [buffer_equil_wash1],
    'flow_rate': UnitScalar(200.0, units=cm_per_hr),
    'volume': UnitScalar(1.5, units=column_volumes)
}

LOAD_STEP = {
    'step_type': 'Load',
    'name': 'whatever name',
    'solutions': [SolutionWithProduct(**SOLUTIONWITHPRODUCT_LOAD)],
    'flow_rate': UnitScalar(200.0, units=cm_per_hr),
    'volume': UnitScalar(1.5, units=column_volumes)
}

GRADIENT_ELUTION_STEP = {
    'step_type': 'Gradient Elution',
    'name': 'Gradient Elution',
    'solutions': [buffer_equil_wash1, Buffer(**BUFFER_ELUTION)],
    'flow_rate': UnitScalar(100.0, units=cm_per_hr),
    'volume': UnitScalar(8.4, units=column_volumes)
}

COLLECTION_CRITERIA_DATA = {
    'name': 'criteria-1',
    'start_collection_type': 'Fixed Absorbance',
    'start_collection_target': 0.1,
    'stop_collection_type': 'Percent Peak Maximum',
    'stop_collection_target': 20.0,
}

METHOD_DATA = {
    'name': 'method-1',
    'run_type': 'Gradient Elution',
    'method_steps': [MethodStep(**PRE_EQUIL_STEP), MethodStep(**EQUIL_STEP),
                     MethodStep(**LOAD_STEP),
                     MethodStep(**GRADIENT_ELUTION_STEP)],
    'collection_step_number': 3,
    'collection_criteria': CollectionCriteria(**COLLECTION_CRITERIA_DATA),
}

SYSTEM_TYPE_DATA = {
    'name': 'AKTA_explorer',
    'manufacturer': 'GE',
    'manufacturer_name': 'AKTA Explorer 100',
    'flow_range': UnitArray([10, 100], units=ml_per_min),
    'num_inlets': 4,
    'num_channels': 2,
}

SYSTEM_DATA = {
    'name': 'Chrom Skid 1',
    'system_number': 'CS1234',
    'holdup_volume': UnitScalar(100, units=milliliter),
    'abs_path_length': UnitScalar(0.2, units='cm'),
}
