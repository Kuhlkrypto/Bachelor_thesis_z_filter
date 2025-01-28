import os

import pandas as pd
import sys
import argparse
import constants



def run_abstraction(eventLog, abstractionLevel):
    eventLog[constants.COL_NAME_TIMESTAMP] = pd.to_datetime(eventLog[constants.COL_NAME_TIMESTAMP], format=constants.DATE_TIME_FORMAT, errors='raise')
    eventLog[constants.COL_NAME_TIMESTAMP] = eventLog[constants.COL_NAME_TIMESTAMP].apply(lambda x: x.ceil(freq=abstractionLevel))
    # eventLog[constants.COL_NAME_TIMESTAMP] = eventLog[constants.COL_NAME_TIMESTAMP].apply(lambda x: x.replace(month=1, day=1))
    return eventLog


def abstract_timestamp_of_file(input_file, output_file, abstraction_level):
    eventLog = pd.read_csv(input_file, delimiter=constants.DELIMITER)
    try:
        run_abstraction(eventLog,abstraction_level)
    except ValueError as e:
        print(f"input file {input_file};: {e}")
    eventLog.to_csv(output_file, sep=constants.DELIMITER)


def abstract_timestamps(search_path):
    for parent, dirs, files in os.walk(search_path):
        for file in files:
            if file.endswith(".csv"):
                input_file = os.path.join(parent, file)
                output_file = input_file.removesuffix(".csv").removesuffix('abstracted') + 'abstracted.csv'
                if not os.path.exists(output_file):
                    abstract_timestamp_of_file(input_file, output_file, 'D')


if __name__ == "__main__":
    abstract_timestamps("/work_data/Sepsis Cases - Event Log/")