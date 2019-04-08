from traitsui.api import EnumEditor, ObjectColumn, RangeEditor, TableEditor

from app_common.std_lib.str_utils import format_array

from kromatography.model.random_parameter_scan_description import \
    FAMILIAR_DISTROS

MAX_NUM_VALUES = 10000


class ModifiedObjectColumn(ObjectColumn):
    def get_value(self, object):
        """ Gets the formatted value of the column for a specified object
        passing the object rather than the value.
        """
        return self.format_func(object)


def build_regular_parameter_table_editor(center_sim=None,
                                         num_values_fixed=False,
                                         support_parallel_params=False):
    """ TableEditor factory for the parameter scans that are possible to
    explore around the simulation provided.

    Note: the table editor doesn't support adding elements: it should be
    accompanied with a button which manually contributes to the list of
    ParameterScanDescriptions since that provides a higher level of controls
    anyway.
    """
    if num_values_fixed:
        num_value_style = "readonly"
    else:
        num_value_style = "simple"

    columns = [
        ObjectColumn(name='name', label="Parameter name"),
        ObjectColumn(name='low'),
        ObjectColumn(name='high'),
        ObjectColumn(name='num_values',
                     editor=RangeEditor(low=1, high=MAX_NUM_VALUES,
                                        mode='spinner'),
                     style=num_value_style),
        ObjectColumn(name='spacing'),
        ObjectColumn(name='scanned_values', format_func=format_array,
                     label="Final parameter values"),
    ]

    def format_adtl_params(param):
        if hasattr(param, "parallel_parameters") and param.parallel_parameters:
            return "%s param(s)" % len(param.parallel_parameters)
        return "None"

    if support_parallel_params:
        add_parallel_param_column = ModifiedObjectColumn(
            name='add_parallel_params', label="Add Parallel Param.",
            format_func=format_adtl_params
        )
        columns.append(add_parallel_param_column)

    if center_sim:
        center_val_col = ObjectColumn(name='center_value', style="readonly")
        columns.insert(1, center_val_col)

    editor = TableEditor(
        columns=columns,
        editable=True,
        sortable=False,
        deletable=True,
    )
    return editor


def build_mc_parameter_table_editor(center_sim=None):
    """ TableEditor factory for the parameter scans that are possible to
    explore around the simulation provided.

    Note: the table editor doesn't support adding elements: it should be
    accompanied with a button which manually contributes to the list of
    ParameterScanDescriptions since that provides a higher level of controls
    anyway.
    """
    distro_tooltip = "Type of distribution to draw random numbers from."
    param1_tooltip = "First parameter to describe the distribution. " \
                     "Corresponds to the 'mean' for 'Gaussian' distribution " \
                     "and to the lower limit for values (inclusive) for " \
                     "'Uniform' distribution."
    param2_tooltip = "Second parameter to describe the distribution. " \
                     "Corresponds to the 'std dev' for 'Gaussian' " \
                     "distribution and to the higher limit for values " \
                     "(exclusive) for 'Uniform' distribution."
    columns = [
        ObjectColumn(name='name', label="Parameter name"),
        ObjectColumn(name='distribution', tooltip=distro_tooltip,
                     # Let's restrict the number of options to just
                     editor=EnumEditor(values=FAMILIAR_DISTROS)),
        ObjectColumn(name='dist_param1', tooltip=param1_tooltip,
                     label="Low/Mean/1st param"),
        ObjectColumn(name='dist_param2', tooltip=param2_tooltip,
                     label="High/Std Dev/2nd param"),
    ]
    if center_sim:
        center_val_col = ObjectColumn(name='center_value', style="readonly")
        columns.insert(1, center_val_col)

    editor = TableEditor(
        columns=columns,
        editable=True,
        sortable=False,
        deletable=True,
    )
    return editor
