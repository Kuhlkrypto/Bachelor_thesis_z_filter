import constants
import re
import pandas as pd
import pm4py


def import_csv(filepath):
    """Import CSV as a pandas DataFrame."""
    event_log = pd.read_csv(filepath, sep=constants.DELIMITER)
    # required_columns = [constants.COL_NAME_CASE_IDENT, constants.COL_NAME_ACTIVITY, constants.COL_NAME_TIMESTAMP]
    required_columns = ["case_id", "activity", "timestamp"]
    event_log = event_log[required_columns]
    # event_log.rename(columns={"case_id=case":"concept:name", "activity":"concept:name", "timestamp":"time:timestamp"})
    event_log = pm4py.format_dataframe(event_log, case_id=constants.COL_NAME_CASE_IDENT,
                                       activity_key=constants.COL_NAME_ACTIVITY,
                                       timestamp_key=constants.COL_NAME_TIMESTAMP)
    # print(f"Events {len(event_log)}, unique cases: {len(event_log[constants.COL_NAME_CASE_IDENT].unique())}")
    return event_log


def extract_number_and_prefix(filename):
    """Parses a filename according to the following format:
    <original_filename>Z<value>PT<time in seconds or 0inf0>S

    Returns:
    number: z-value
    prefix: original filename
    duration: duration in seconds or float('inf') for 0inf0
    """
    # Updated regex to handle both numeric durations and '0inf0'
    match = re.match(r"^(.*?[^Z]*)Z(\d+)PT((\d+)|0inf0)S*", filename)
    if match:
        prefix = match.group(1)  # Characters before 'Z'
        number = int(match.group(2))

        # Handle duration as either a number or infinity
        if match.group(3) == "0inf0":
            duration = float('inf')
        else:
            duration = int(match.group(3))

        return number, prefix, duration
    else:
        #TODO: Raise Exception here
        return -1, "", ""
#
# if __name__ == "__main__":
#     log = import_csv("/home/fabian/Github/Bachelor_thesis_z_filter/data/data_csv_hard_petri/Hospital_log/Hospital_log.csv")
#     net, im , fm = pm4py.discover_petri_net_heuristics(log)
#     pm4py.view_petri_net(net, im, fm)
