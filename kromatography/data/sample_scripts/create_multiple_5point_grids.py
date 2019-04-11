""" Create 5-point grids around a simulation to study parameter impacts.
"""
# Script inputs ---------------------------------------------------------------

SIM_NAME = 'Sim: 8.4CV'

PARAM_LIST = ["column.bed_height_actual",
              "method.method_steps[2].flow_rate",
              "method.method_steps[0].volume",
              "method.collection_criteria.start_collection_target",
              "method.collection_criteria.stop_collection_target"]

# Script ----------------------------------------------------------------------

from kromatography.model.factories.simulation_group import build_simulation_grid

cp = study.search_simulation_by_name(SIM_NAME)
for param in PARAM_LIST:
        grid = build_simulation_grid(cp, [param], num_values=5, val_ranges=0.2)
        grid.name = "Scan {}".format(param)
        study.analysis_tools.simulation_grids.append(grid)
        task.edit_object_in_central_pane(grid)

# End of script ---------------------------------------------------------------
