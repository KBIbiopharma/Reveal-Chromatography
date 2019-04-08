""" Create 5-point grids around a simulation to study parameter impacts.

This version is more complex than create_multiple_5point_grids in that it
"""
# Script inputs ---------------------------------------------------------------

SIM_NAME = 'Sim: 8.4CV'

PARAM_LIST = {
    # unit=cm
    "column.bed_height_actual": (23, 27, 19, 31),
    # unit=cm/hr
    "method.method_steps[2].flow_rate": (85, 103, 74, 114),
    # unit=CV
    "method.method_steps[0].volume": (3., 5., 2., 6.),
    # unit=%
    "method.collection_criteria.start_collection_target": (40, 60, 30, 70),
    # unit=%
    "method.collection_criteria.stop_collection_target": (30, 50, 20, 60),
    # unit=% Grouped scan modifying both start and stop collect together:
    ("method.method_steps[0].solutions[0].product_component_assay_values[3]",
     "method.method_steps[0].solutions[0].product_component_assay_values[2]"):
        ((83.1, 86.5, 80.1, 89.5),
         (6.8, 3.4, 9.8, 0.4)),
    # "method.method_steps[0].flow_rate": (85, 103, 74, 114),
    # "method.initial_buffer.pH": (5.4, 0.2, 0.6, ""),
    # "method.initial_buffer.chemical_component_concentrations[1]":
    #     (20, 0.2, 0.6, "mmol/L"),
    # "method.method_steps[0].solutions[0].pH": (5.2, 0.2, 0.6, ""),
    # "method.method_steps[1].solutions[0].pH": (5.4, 0.2, 0.6, ""),
    # "method.method_steps[1].solutions[0].chemical_component_concentrations[1]":  # noqa
    #     (20, 0.2, 0.6, "mmol/L"),
    # "method.method_steps[1].flow_rate": (94, 9.4, 28.2, "cm/hr"),
    # "method.method_steps[1].volume": (3, 0.1, 0.3, "CV"),
    # "method.method_steps[2].solutions[1].pH": (5.4, 0.2, 0.6, ""),
    # "method.method_steps[2].solutions[1].chemical_component_concentrations[1]":  # noqa
    #     (187, 1.87, 5.61, "mmol/L"),
    # "method.method_steps[2].volume": (8.4, 0.1, 1, "CV"),
}

# Script ----------------------------------------------------------------------

from kromatography.model.factories.simulation_group import \
    build_5_point_groups_from_param_desc

cp = study.search_simulation_by_name(SIM_NAME)
grids = build_5_point_groups_from_param_desc(cp, PARAM_LIST)
for param, grid in grids.items():
    study.analysis_tools.simulation_grids.append(grid)
    task.edit_object_in_central_pane(grid)

# End of script ---------------------------------------------------------------
