""" Content to populate the **release version** of the default DataSources.
"""
from scimath.units.api import UnitArray, UnitScalar

import kromatography.utils.chromatography_units as chr_units

g_per_mol = chr_units.gram_per_mol
milli_mol = chr_units.milli_molar
ext_coef_unit = chr_units.extinction_coefficient_unit

# Product component defaults ------------------------------------------

product_components = [
    {
        'target_product': 'Prod000',
        'name': 'Acidic_1',
        'molecular_weight': UnitScalar(18.8, units="kDa"),
        'extinction_coefficient': UnitScalar(.75, units=ext_coef_unit),
    },
    {
        'target_product': 'Prod000',
        'name': 'Acidic_2',
        'molecular_weight': UnitScalar(18.8, units="kDa"),
        'extinction_coefficient': UnitScalar(.75, units=ext_coef_unit),
    },
    {
        'target_product': 'Prod000',
        'name': 'Native',
        'molecular_weight': UnitScalar(18.8, units="kDa"),
        'extinction_coefficient': UnitScalar(.75, units=ext_coef_unit),
    },
    {
        'target_product': 'Prod001',
        'name': 'Pre_Peak_A',
        'molecular_weight': UnitScalar(79.0, units="kDa"),
        'extinction_coefficient': UnitScalar(.86, units=ext_coef_unit),
    },
    {
        'target_product': 'Prod001',
        'name': 'Pre_Peak_B',
        'molecular_weight': UnitScalar(59.0, units="kDa"),
        'extinction_coefficient': UnitScalar(.86, units=ext_coef_unit),
    },
    {
        'target_product': 'Prod001',
        'name': 'Pre_Peak_C',
        'molecular_weight': UnitScalar(39.0, units="kDa"),
        'extinction_coefficient': UnitScalar(.86, units=ext_coef_unit),
    },
    {
        'target_product': 'Prod001',
        'name': 'Main_Peak_D',
        'molecular_weight': UnitScalar(39.0, units="kDa"),
        'extinction_coefficient': UnitScalar(.86, units=ext_coef_unit),
    },
    {
        'target_product': 'Prod001',
        'name': 'Post_Peak_E',
        'molecular_weight': UnitScalar(19.0, units="kDa"),
        'extinction_coefficient': UnitScalar(.86, units=ext_coef_unit),
    },
    {
        'target_product': 'Prod001_Pulse',
        'name': 'Protein',
        'molecular_weight': UnitScalar(39.0, units="kDa"),
        'extinction_coefficient': UnitScalar(.86, units=ext_coef_unit),
    },
]

products = [
    {
        'name': 'Prod000',
        'product_type': 'Product',
        'product_components': ['Acidic_2', 'Acidic_1', 'Native'],
        'product_component_assays': [
            'CEX_Acidic_2', 'CEX_Acidic_1', 'CEX_Native'
        ],
        'product_component_concentration_exps': [
            'product_concentration * CEX_Acidic_2 / 100',
            'product_concentration * CEX_Acidic_1 / 100',
            'product_concentration * CEX_Native / 100'
        ],
        'impurity_names': [],
        'impurity_assays': [],
        'impurity_concentration_exps': [],
        'pI': UnitScalar(7.52, units='1'),
        'amino_acids': ['Histidine', 'Cysteine'],
        'amino_acid_numbers': [10, 2]
    },
    {
        'name': 'Prod001_Pulse',
        'product_type': 'Globular Protein',
        'description': '1-component description of Prod001',
        'product_components': ['Protein'],
        'product_component_assays': [],
        'product_component_concentration_exps': ['product_concentration'],
        'impurity_names': [],
        'impurity_assays': [],
        'impurity_concentration_exps': [],
        'pI': UnitScalar(5.7, units='1'),
        'amino_acids': [],
        'amino_acid_numbers': []
    },
    {
        'name': 'Prod001',
        'product_type': 'Protein',
        'description': 'Example Protein, PROD001',
        'product_components': ['Pre_Peak_A', 'Pre_Peak_B', 'Pre_Peak_C',
                               'Main_Peak_D', 'Post_Peak_E'],
        'product_component_assays': ['Pre_Peak_A', 'Pre_Peak_B', 'Pre_Peak_C',
                                     'Main_Peak_D', 'Post_Peak_E'],
        'product_component_concentration_exps': [
            'product_concentration * Pre_Peak_A / 100',
            'product_concentration * Pre_Peak_B / 100',
            'product_concentration * Pre_Peak_C / 100',
            'product_concentration * Main_Peak_D / 100',
            'product_concentration * Post_Peak_E / 100'
        ],
        'impurity_names': [],
        'impurity_assays': [],
        'impurity_concentration_exps': [],
        'pI': UnitScalar(5.7, units='1'),
        'amino_acids': [],
        'amino_acid_numbers': []
    },
]

resin_types = [
    {
        'name': 'Fractogel-SO3 (M)',
        'resin_type': 'CEX',
        'ligand': 'SO3',
        'average_bead_diameter': UnitScalar(65.0, units='um'),
        'ligand_density': UnitScalar(75.0, units=milli_mol),
        'settled_porosity': UnitScalar(0.42, units=chr_units.fraction),
    },
    {
        'name': 'MabSelect',
        'resin_type': 'Protein A',
        'ligand': 'Protein A',
        'average_bead_diameter': UnitScalar(85.0, units='um'),
        'ligand_density': UnitScalar(100.0, units=milli_mol),
        'settled_porosity': UnitScalar(0.38, units=chr_units.fraction),
    },
    {
        'name': 'SP_Sepharose_FF',
        'lot_id': 'Lot0',
        'resin_type': 'CEX',
        'ligand': 'SP',
        'average_bead_diameter': UnitScalar(90.0, units='um'),
        'ligand_density': UnitScalar(100.0, units=milli_mol),
        'settled_porosity': UnitScalar(0.35, units=chr_units.fraction),
    },
    {
        'name': 'Capto_SP_ImpRes',
        'resin_type': 'CEX',
        'ligand': 'SP',
        'average_bead_diameter': UnitScalar(40.0, units='um'),
        'ligand_density': UnitScalar(145, units=milli_mol),
        'settled_porosity': UnitScalar(0.35, units=chr_units.fraction),
    },
]

column_types = [
    {
        "name": "Axichrom100",
        "manufacturer_name": "Axichrom 100",
        "manufacturer": "GE",
        "diameter": UnitScalar(100, units="cm"),
        "bed_height_range": UnitArray([10., 30.], units="cm"),
        "bed_height_adjust_method": "Hydraulic",
        # "material_of_construction": "316_Stainless"
    },
    {
        "name": "BPG5",
        "manufacturer_name": "BPG5",
        "manufacturer": "GE",
        "diameter": UnitScalar(5, units="cm"),
        "bed_height_range": UnitArray([10., 40.], units="cm"),
        "bed_height_adjust_method": "Manual",
        # "material_of_construction": "Acrylic"
    },
    {
        "name": "GEHiScale50",
        "manufacturer_name": "GE HiScale 50",
        "manufacturer": "GE",
        "diameter": UnitScalar(5, units="cm"),
        "bed_height_range": UnitArray([10., 40.], units="cm"),
        "bed_height_adjust_method": "Manual",
        # "material_of_construction": "Acrylic"
    },
    # FIXME - Bed Height Adjustment Range Not Required for fixed bed
    # height
    {
        "name": "HiTrap 5 mL",
        "manufacturer_name": "HiTrap 5 mL",
        "manufacturer": "GE",
        "diameter": UnitScalar(1.6, units="cm"),
        "bed_height_range": UnitArray([2.5, 2.5], units="cm"),
        "bed_height_adjust_method": "None",
        # "material_of_construction": "Acrylic"
    },
    {
        "name": "HiTrap 1 mL",
        "manufacturer_name": "HiTrap 1 mL",
        "manufacturer": "GE",
        "diameter": UnitScalar(0.7, units="cm"),
        "bed_height_range": UnitArray([2.5, 2.5], units="cm"),
        "bed_height_adjust_method": "None",
        # "material_of_construction": "Acrylic"
    },
    {
        "name": "HiScreen",
        "manufacturer_name": "HiScreen",
        "manufacturer": "GE",
        "diameter": UnitScalar(0.77, units="cm"),
        "bed_height_range": UnitArray([10.0, 10.0], units="cm"),
        "bed_height_adjust_method": "None",
        # "material_of_construction": "Acrylic"
    },
    {
        "name": "XK 16",
        "manufacturer_name": "XK 16",
        "manufacturer": "GE",
        "diameter": UnitScalar(1.6, units="cm"),
        "bed_height_range": UnitArray([0.0, 40.0], units="cm"),
        "bed_height_adjust_method": "None",
        # "material_of_construction": "Acrylic"
    }
]

chemicals = [
    {
        'name': 'Sodium_Chloride',
        'component_names': ['Sodium', 'Chloride'],
        'component_atom_counts': [1, 1],
        'state': 'Solid',
        'molecular_weight': UnitScalar(58.44, units=g_per_mol)
    },
    {
        'name': 'Sodium_Acetate',
        'component_names': ['Sodium', 'Acetate'],
        'component_atom_counts': [1, 1],
        'state': 'Solid',
        'molecular_weight': UnitScalar(82.02, units=g_per_mol)
    },
    {
        'name': 'Acetic_Acid',
        'component_names': ['Acetate'],
        'component_atom_counts': [1],
        'state': 'Liquid',
        'molecular_weight': UnitScalar(60.05, units=g_per_mol)
    },
    {
        'name': 'Sodium_Hydroxide',
        'component_names': ['Sodium'],
        'component_atom_counts': [1],
        'state': 'Liquid',
        'molecular_weight': UnitScalar(40.0, units=g_per_mol)
    },
    {
        'name': 'EDTA_Disodium_Dihydrate',
        'component_names': ['EDTA', 'Sodium'],
        'component_atom_counts': [1, 2],
        'state': 'Solid',
        'molecular_weight': UnitScalar(372.24, units=g_per_mol)
    },
    {
        'name': 'Hydrochloric_Acid',
        'component_names': ['Chloride'],
        'component_atom_counts': [1],
        'state': 'Liquid',
        'molecular_weight': UnitScalar(36.46, units=g_per_mol)
    },
    {
        'name': 'Glacial_Acetic_Acid',
        'component_names': ['Acetate'],
        'component_atom_counts': [1],
        'state': 'Liquid',
        'molecular_weight': UnitScalar(60.05, units=g_per_mol)
    },
]

components = [
    {
        'name': 'Sodium',
        'charge': UnitScalar(1, units='1'),
        'pKa': UnitScalar(0.0, units='1')
    },
    {
        'name': 'Chloride',
        'charge': UnitScalar(-1, units='1'),
        'pKa': UnitScalar(0.0, units='1')
    },
    {
        'name': 'Acetate',
        'charge': UnitScalar(-1, units='1'),
        'pKa': UnitScalar(4.73, units='1')
    },
    {
        'name': 'EDTA',
        'charge': UnitScalar(-2, units='1'),
        'pKa': UnitScalar(6.2, units='1')
    },
    {
        'name': 'EDTACOO-',
        'charge': UnitScalar(-1, units='1'),
        # FIXME: EDTA is a polyprotic compound => has multiple pKas.
        # This is an average of all values (0.0, 1.5, 2.0, and 2.7).
        'pKa': UnitScalar(2.3, units='1')
    },
    {
        'name': 'EDTANH+',
        'charge': UnitScalar(+1, units='1'),
        # FIXME: EDTA is a polyprotic compound => has multiple pKas.
        # This is an average of all values (6.2 and 10.3).
        'pKa': UnitScalar(8.2, units='1')
    },
]

system_types = [
    {
        'name': 'AKTA_Explorer',
        'manufacturer': 'GE',
        'manufacturer_name': 'AKTA_Explorer',
        'flow_range': UnitArray([10, 100], units=chr_units.ml_per_min),
        'num_inlets': 4,
        'num_channels': 2,
        # 'construction_material': 'Plastic'
    },
    {
        'name': 'AKTA_Purifier',
        'manufacturer': 'GE',
        'manufacturer_name': 'AKTA_Purifier',
        'flow_range': UnitArray([10, 100], units=chr_units.ml_per_min),
        'num_inlets': 4,
        'num_channels': 2,
        # 'construction_material': 'Plastic'
    },
    {
        'name': 'AKTA_Pilot',
        'manufacturer': 'GE',
        'manufacturer_name': 'AKTA_pilot',
        'flow_range': UnitArray([10, 100], units=chr_units.ml_per_min),
        'num_inlets': 6,
        'num_channels': 2,
        # 'construction_material': 'Plastic'
    },
    {
        'name': 'AKTA_Avant',
        'manufacturer': 'GE',
        'manufacturer_name': 'AKTA_Avant',
        'flow_range': UnitArray([0.01, 150],
                                units=chr_units.ml_per_min),
        'num_inlets': 6,
        'num_channels': 2,
        # 'construction_material': 'Plastic'
    },
]

DATA_CATALOG = {
    'products': products,
    'product_components': product_components,
    'resin_types': resin_types,
    'column_models': column_types,
    'components': components,
    'chemicals': chemicals,
    'system_types': system_types,
}
