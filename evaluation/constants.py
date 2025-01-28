
import pm4py.util.constants as pm4pyc
DELIMITER = ';'
DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC'
COL_NAME_TIMESTAMP = 'timestamp'
COL_NAME_CASE_IDENT = 'case_id'
COL_NAME_ACTIVITY = 'activity'
ABSTRACTED_NAME_SUFFIX = 'abstracted'
PATH_TMP = "/home/fabian/Github/Bachelor_thesis_z_filter/tmp/"
# FILTERING_ABSOLUTE_ZS = {2, 3, 4, 5, 15, 30, 45, 60}
FILTERING_ABSOLUTE_ZS =  set(range(30))
FILTERING_RELATIVE_ZS = [0.001, 0.005, 0.01, 0.05, 0.1, 0.15, 0.2]
FILTERING_TIME_DELTAS = ['30m', '1h', '24h', '72h', 'inf']
FILTERING_MODES = ['0','1']

METRIC_PARAMETERS = {
    "multiprocessing": True,
    "show_progress_bar": False

}