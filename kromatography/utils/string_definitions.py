
#: Name of method_step entry
INITIAL_CONDITION = "INITIAL CONDITIONS"

#: Name of default SMA binding model
DEFAULT_BINDING_MODEL_NAME = 'Default SMA model'

#: Name of default SMA binding model
DEFAULT_PH_BINDING_MODEL_NAME = 'Default pH-dependent SMA model'

#: Name of default Transport GR model
DEFAULT_TRANSPORT_MODEL_NAME = 'Default GR model'

#: All possible run statuses for a simulation
SIM_NOT_RUN = "Not run"
SIM_SUBMITTED = "Submitted"
SIM_RUNNING = "Running..."
SIM_FINISHED_SUCCESS = "Run successfully"
SIM_FINISHED_FAIL = "Run failed"

#: Status of an optimizer or optimizer step before it is run"
MULTI_SIM_RUNNER_CREATED = "Created"

#: Status of an optimizer or optimizer step while it runs"
MULTI_SIM_RUNNER_RUNNING = "Running..."

#: Status of an optimizer or optimizer step once finished running"
MULTI_SIM_RUNNER_FINISHED = "Finished running"

#: Experimental data loader: name of the sum
FRACTION_TOTAL_DATA_KEY = 'Sum comp. fractions'

#: Automatically generated strip component when creating new product
STRIP_COMP_NAME = "Strip"

#: Name of UV entry in AKTA file and continuous_data of experimental result
UV_DATA_KEY = 'uv'

#: All possible method step types
PRE_EQ_STEP_TYPE = "Pre-Equilibration"
EQ_STEP_TYPE = "Equilibration"
LOAD_STEP_TYPE = "Load"
INJECTION_STEP_TYPE = "Injection"
WASH_STEP_TYPE = "Wash"
STEP_ELUT_STEP_TYPE = "Step Elution"
GRADIENT_ELUT_STEP_TYPE = "Gradient Elution"
CLEAN_STEP_TYPE = "Clean"
REGENERATION_STEP_TYPE = "Regeneration"
STORE_STEP_TYPE = "Store"
STRIP_STEP_TYPE = "Strip"

#: CHROMATOGRAM PLOT LOG FAMILY NAMES
LOG_FAMILY_UV = 'Protein Concentrations'
LOG_FAMILY_CATION = 'Chemical Concentrations'
LOG_FAMILY_PH = 'pH'
