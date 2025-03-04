import constants
import re
import pandas as pd
import pm4py


def import_csv(filepath):
    """
    Import a CSV file as a pandas DataFrame and format it for process mining.

    :param filepath: Path to the CSV file.
    :return: Formatted pandas DataFrame.
    """
    event_log = pd.read_csv(filepath, sep=constants.DELIMITER)

    # Ensure required columns are present
    required_columns = [constants.COL_NAME_CASE_IDENT, constants.COL_NAME_ACTIVITY, constants.COL_NAME_TIMESTAMP]
    event_log = event_log[required_columns]

    # Format DataFrame for PM4Py
    event_log = pm4py.format_dataframe(
        event_log,
        case_id=constants.COL_NAME_CASE_IDENT,
        activity_key=constants.COL_NAME_ACTIVITY,
        timestamp_key=constants.COL_NAME_TIMESTAMP
    )

    return event_log


def extract_number_and_prefix(filename):
    """
    Extracts number, prefix, and duration from a filename.

    Filename format: <original_filename>Z<value>PT<time_in_seconds_or_0inf0>S

    :param filename: Filename to parse.
    :return: Tuple (number, prefix, duration)
    """
    match = re.match(r"^(.*?[^Z]*)Z(\d+)PT((\d+)|0inf0)S*", filename)
    if match:
        prefix = match.group(1)  # Characters before 'Z'
        number = int(match.group(2))

        # Handle duration as either a number or infinity
        duration = float('inf') if match.group(3) == "0inf0" else int(match.group(3))

        return number, prefix, duration

    return -1, "", ""


def shorten_log(path, output_path, nrows, sep):
    """
    Shortens a log file by keeping only a subset of rows and required columns.

    :param path: Path to the input CSV file.
    :param output_path: Path to save the shortened CSV file.
    :param nrows: Number of rows to retain.
    :param sep: CSV delimiter.
    """
    log = pd.read_csv(path, nrows=nrows, sep=sep)
    required_columns = ["case_id", "activity", "timestamp", "source"]
    log = log[required_columns]
    log.to_csv(output_path, sep=constants.DELIMITER, index=False)


def extract_dt_from_data_dict(file_path: str, dt: str, name: str = None):
    """
    Extracts rows from a data dictionary for a given time parameter.

    :param file_path: Path to the CSV file.
    :param dt: Time parameter to filter.
    :param name: If provided, stores the filtered dictionary in a CSV format.
    :return: Filtered data dictionary.
    """

    from measurement import Measurement
    ms = Measurement(name)
    ms.read_from_csv(file_path)

    # Identify indices where time parameter matches
    indices = [i for i, t in enumerate(ms.results["dT"]) if t == str(dt) or t == "base"]

    # Extract data for matching indices
    new_data = {key: [value[i] for i in indices] for key, value in ms.results.items() if key != ""}

    if name is not None:
        ms.results = new_data
        ms.write_to_csv()

    return new_data
