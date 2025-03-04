import os

# delimiter for files in CSV format
DELIMITER = ';'

# Date time format
# DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# d Day
ABSTRACTION_LEVEL = 'd'
# Column names for pm4py
COL_NAME_TIMESTAMP = 'timestamp'
COL_NAME_CASE_IDENT = 'case_id'
COL_NAME_ACTIVITY = 'activity'
ABSTRACTED_NAME_SUFFIX = 'abstracted'

# Multiprocessing flags
PM4PY_MULTIPROCESSING: bool = True
RISK_MULTIPROCESSING: bool = True
MODEL_QUALITY_MULTIPROCESSING: bool = True


# Temporary path used for storing files used by the re-identification risk evaluation
PATH_TMP = os.path.join(os.getcwd(), "tmp/")
PATH_RESULTS = os.path.join(os.getcwd(), "results/")
PATH_DATA = os.path.join(os.getcwd(), "data_work/")
PATH_FILTER_BINARY = os.path.join(os.getcwd(), "executables/z-anon-impl")

# If set true the metrics are assessed using the alignment method, otherwise token based replay technique is used
FITNESS_ALIGNMENT: bool = True
PRECISION_ALIGNEMNT: bool = True

# If true event logs are assessed with generalized timestamps
ABSTRACT_TIMESTAMPS_EVALUATION: bool = True

# If true event logs are assessed with unchanged timestamps
USUAL_TIMESTAMP_EVALUATION: bool = False

# If true the discovered petri-nets are written to disk in a .pnml file
SAVE_PETRI_NETS: bool = False

# Evaluate model quality using event log used to discover petri-net
MODEL_QUALITY_EVALUATION: bool = False

# Evaluate model quality using unfiltered event log used
REF_MODEL_QUALITY_EVALUATION: bool = False

# Evaluate re-identification Risk of process Models
RISK_EVALUATION: bool = True

# absolute amount of points used for assessing re-identification risk
RISK_POINTS_ABSOLUTE: set = {1, 5, 8}
# relative amount of points used for assessing re-identification risk
RISK_POINTS_RELATIVE: set = {0.3, 0.6, 0.9}

# Absolute Z-values used for filtering event logs
FILTERING_ABSOLUTE_ZS: set = {10,20,30,40}
# Z-values relative to the maximal amount of points of the corresponding trace used for filtering event logs
FILTERING_RELATIVE_ZS: set = {0.1, 0.2, 0.3}

# Time Deltas used for Filtering
FILTERING_TIME_DELTAS = {
    # '1h',
    # '24h',
    '72h',
    # "7d",
     #'28d'
    #'inf'
}

# Filtering Modes
FILTERING_MODES = [
    '0',  # basic
    '1'  # balanced
]

