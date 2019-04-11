""" Plot Pareto plot comparing parameter impacts from run 5-point grids.
"""
# Script inputs ---------------------------------------------------------------

# Specify the name of the performance to extract and its display name:
PERFORMANCE_NAME_TITLE = ("step_yield (%)", "Yield")

# Script ----------------------------------------------------------------------

import matplotlib.pyplot as plt
from kromatography.plotting.mpl_param_impact_plot import \
    plot_performance_as_tornado_plot, extract_perf_data

data = {grid.name.split()[1]:grid.group_data for grid in
        study.analysis_tools.simulation_grids if grid.name.startswith("Scan ")}

index = ["low2", "low1", "set point", "high1", "high2"]
formatted_data, cp_val = extract_perf_data(data, PERFORMANCE_NAME_TITLE[0],
                                           index_desc=index)
plot_performance_as_tornado_plot(formatted_data, PERFORMANCE_NAME_TITLE[1],
                                 cp_perf=cp_val, include_grid=True)
plt.show()

# End of script ---------------------------------------------------------------
