from pathlib import Path
import re
import pandas as pd
import pm4py
import os


def import_csv(filepath):
    """Import CSV as a pandas DataFrame."""
    event_log = pd.read_csv(filepath, sep=',')
    required_columns = ['case_id', 'activity', 'timestamp']
    event_log = event_log[required_columns]
    # event_log.rename(columns={"case_id=case":"concept:name", "activity":"concept:name", "timestamp":"time:timestamp"})
    event_log = pm4py.format_dataframe(event_log, case_id='case_id', activity_key='activity', timestamp_key='timestamp')
    num_events = len(event_log)
    num_cases = len(event_log['case_id'].unique())

    print(f"Events {num_events}, unique cases: {num_cases}")
    return event_log


# def walk_dir(folder_path, cmp, measurement):
#     """Walk through all files in a directory."""
#     for file_path in sorted([file for file in Path(folder_path).iterdir()]):
#         if file_path.is_file():
#             measurement.comp_qualities_of_file()
#             process_file(file_path, cmp, quality_dict)




def petri_stats(petri_net):
    """Print statistics of the Petri net."""
    print(f"Number of transitions: {len(petri_net.transitions)}")
    print(f"Number of places: {len(petri_net.places)}")
    print(f"Number of arcs: {len(petri_net.arcs)}")


def extract_number_and_prefix(filename):
    """Parses a filename according to following format:
    <original_filename>Z<value>PT<time in seconds>S

    Returns:
    number: z-value
    prefix: original filename
    duration: duration in seconds
    """
    match = re.match("^(.*?[^Z]*)Z(\\d+)PT(\\d+)S*", filename)
    if match:
        prefix = match.group(1)  # Characters before 'Z'
        number = int(match.group(2))
        duration = int(match.group(3))
        return number, prefix, duration
    else:
        return -1, "", ""
