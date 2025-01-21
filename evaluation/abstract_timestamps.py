import pandas as pd
import sys
import argparse
import constants



def run_abstraction(eventLog, abstractionLevel):
    eventLog[constants.COL_NAME_TIMESTAMP] = pd.to_datetime(eventLog[constants.COL_NAME_TIMESTAMP], format=constants.DATE_TIME_FORMAT, errors='raise')
    eventLog[constants.COL_NAME_TIMESTAMP] = eventLog[constants.COL_NAME_TIMESTAMP].apply(lambda x: x.ceil(freq=abstractionLevel))
    return eventLog


def abstract_timestamp(input_file, output_file, abstraction_level):
    eventLog = pd.read_csv(input_file, delimiter=constants.DELIMITER)
    try:
        run_abstraction(eventLog,abstraction_level)
    except ValueError as e:
        print(f"input file {input_file};: {e}")
    eventLog.to_csv(output_file, sep=constants.DELIMITER)
