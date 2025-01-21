import os
import constants
import re
import pandas as pd
import pm4py
import abstract_timestamps as abs_t
import re_ident as ri
import csv2auto as ca


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
    print(f"Events {len(event_log)}, unique cases: {len(event_log[constants.COL_NAME_CASE_IDENT].unique())}")
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


def make_dir_safe(path):
    if not os.path.exists(path):
        os.makedirs(path)


def traverse_and_compute_risk():
    search_path = '/home/fabian/Github/Bachelor_thesis_z_filter/data/tmp/'

    for dir in os.listdir(search_path):
        full_path = os.path.join(search_path, dir)
        if os.path.isdir(full_path):
            for parent, dirs, files in os.walk(full_path):
                for file in files:
                    print(file)
                    ri.risk_re_ident_quant(parent + "/", file)


def traverse_and_convert():
    search_path = '/data/data_csv/'
    result_path = '/home/fabian/Github/Bachelor_thesis_z_filter/data/tmp/'

    make_dir_safe(result_path)

    for a_dir in os.listdir(search_path):
        subdir = os.path.join(search_path, a_dir)
        path = result_path + a_dir
        make_dir_safe(path + "/")
        for entry in os.listdir(subdir):
            print(entry)
            sub_sub_entry = os.path.join(subdir, entry)
            if os.path.isdir(sub_sub_entry):
                res = path + "/" + entry
                make_dir_safe(res + "/")
                for file in os.listdir(sub_sub_entry):
                    if file.endswith('.csv'):
                        try:
                            ca.convert_csv2auto(sub_sub_entry + "/", file, res + "/")
                        except IndexError as e:
                            print(e)
            elif os.path.isfile(sub_sub_entry):
                print(entry)
                if entry.endswith(".csv"):
                    print(entry)
                    ca.convert_csv2auto(subdir + "/", entry, path + "/")


def abstract_timestamps(search_path):
    for parent, dirs, files in os.walk(search_path):
        for file in files:
            if file.endswith(".csv"):
                input_file = os.path.join(parent, file)
                print(input_file)
                output_file = input_file.removesuffix(".csv").removesuffix('abstracted') + 'abstracted.csv'
                if not os.path.exists(output_file):
                    abs_t.abstract_timestamp(input_file, output_file, 'd')


if __name__ == "__main__":
    abstract_timestamps("/home/fabian/Github/Bachelor_thesis_z_filter/data/data_csv/Sepsis Cases - Event Log/")
    # traverse_and_convert()
    # traverse_and_compute_risk()
    # traverse_and_convert()
