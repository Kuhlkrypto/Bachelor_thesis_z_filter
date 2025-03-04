import os
import pandas as pd

from pandas.tseries.offsets import MonthEnd
import constants


def run_abstraction(eventLog, abstractionLevel):
    """
    Applies timestamp abstraction to the given event log.

    Parameters:
    eventLog (DataFrame): The event log containing timestamps.
    abstractionLevel (str): The frequency level for rounding timestamps (e.g., 'H' for hour, 'T' for minute).

    Returns:
    DataFrame: The event log with abstracted timestamps.
    """
    # Convert timestamp column to datetime format, removing ' UTC' if present
    eventLog[constants.COL_NAME_TIMESTAMP] = pd.to_datetime(
        eventLog[constants.COL_NAME_TIMESTAMP].str.replace(" UTC", "", regex=True),
        format='ISO8601',
        errors='raise'
    )

    # Round timestamps to month end
    eventLog[constants.COL_NAME_TIMESTAMP] = eventLog[constants.COL_NAME_TIMESTAMP].apply(lambda x: x.ceil(freq=abstractionLevel))


    # Round timestamps to the specified abstraction level
    # eventLog[constants.COL_NAME_TIMESTAMP] = eventLog[constants.COL_NAME_TIMESTAMP].apply(
    #     lambda x:
    #         MonthEnd().rollforward(x)
    # )



    return eventLog


def abstract_timestamp_of_file(input_file, output_file, abstraction_level):
    """
    Reads an input CSV file, applies timestamp abstraction, and writes the result to an output file.

    Parameters:
    input_file (str): Path to the input CSV file.
    output_file (str): Path to the output CSV file where results will be saved.
    abstraction_level (str): The frequency level for timestamp abstraction.
    """
    # Read input CSV file into a DataFrame
    eventLog = pd.read_csv(input_file, delimiter=constants.DELIMITER)

    try:
        # Apply timestamp abstraction
        run_abstraction(eventLog, abstraction_level)
    except ValueError as e:
        # Handle potential value errors and print an error message
        print(f"Error processing input file {input_file}: {e}")

    # Save the modified DataFrame to a new CSV file
    eventLog.to_csv(output_file, sep=constants.DELIMITER)


def abstract_timestamps(search_path):
    """
    Recursively processes all CSV files in the given directory, applying timestamp abstraction.

    Parameters:
    search_path (str): The root directory to search for CSV files.
    """
    # Walk through all directories and files in the given path
    for parent, dirs, files in os.walk(search_path):
        for file in files:
            print(file)  # Print the filename for tracking progress

            # Process only CSV files
            if file.endswith(".csv"):
                input_file = os.path.join(parent, file)
                # Construct output filename with 'abstracted' suffix
                output_file = input_file.removesuffix(".csv").removesuffix('abstracted') + 'abstracted.csv'

                # Process only if the output file does not already exist
                if not os.path.exists(output_file):
                    abstract_timestamp_of_file(input_file, output_file, constants.ABSTRACTION_LEVEL)

