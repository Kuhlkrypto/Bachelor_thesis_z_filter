import math
import os.path
import subprocess
import constants
import pandas as pd


def filter_log(log_path, z, t, modi):
    """
    Filters a given event log for given z and t parameter in given filtering mode.
    :param log_path: event log to be filtered
    :param z: publishing threshold
    :param t: time parameter
    :param modi: filtering mode: '0' for basic filtering, otherwise balanced filtering
    :return: None
    """
    try:
        res = subprocess.run(
            [constants.PATH_FILTER_BINARY,
             str(log_path),
             str(z),
             str(t),
             modi],
            check=True,
            text=True,
            capture_output=True
        )
        res.check_returncode()
    except subprocess.CalledProcessError as e:
        print(f"Raised error while filtering: {e.stderr}")
        exit(1)


def generate_z_values(file_path, percentages=constants.FILTERING_RELATIVE_ZS):
    """
    Generates a set of z values which will be used to filter a given file path
    :param file_path: event log (CSV file path)
    :param percentages: percentages to generate z values relative to the max number of case identifiers
    :return: A set containing all valid z values
    """
    try:
        df = pd.read_csv(file_path, sep=constants.DELIMITER)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return set()
    except pd.errors.ParserError:
        print(f"Error: Unable to parse CSV file {file_path}.")
        return set()

    unique_values = df[constants.COL_NAME_CASE_IDENT].unique()
    unique_count = len(unique_values)

    z_values = ({max(1, int(math.ceil(unique_count * p))) for p in percentages} |
                {z for z in constants.FILTERING_ABSOLUTE_ZS if z > 0})

    return z_values


def convert_seconds(t: str):
    """
    Converts a time parameter in the format xh ym and zs into seconds.
    Can be used to generate the referring file name.
    :param t: time parameter following the format <hours>h <minutes>m <seconds>s
    :return: A string in the following format PT<seconds>S.csv
    """
    res = 'PT'
    if t == 'inf':
        middle = '0inf0'
    elif t.endswith('h'):
        t = t.removesuffix('h')
        middle = str(int(t) * 3600)
    elif t.endswith('m'):
        t = t.removesuffix('m')
        middle = str(int(t) * 60)
    elif t.endswith('s'):
        t = t.removesuffix('s')
        middle = str(int(t))
    else:
        raise ValueError(f"Invalid time format: {t}")
    return res + middle + 'S.csv'


def already_filtered(folder, file: str, z, t, mode) -> bool:
    """
    Checks whether a file has already been filtered.
    :param folder: Folder containing the file
    :param file: Filename
    :param z: z-value
    :param t: Time parameter
    :param mode: Filtering mode ('0' for basic, otherwise balanced)
    :return: True if already filtered, otherwise False
    """
    if mode == '0':
        p = os.path.join(folder, "results_filtering_basic")
    else:
        p = os.path.join(folder, "results_filtering_balanced")
    basename = file.removesuffix('.csv') + 'Z' + str(z) + convert_seconds(t)
    return os.path.exists(os.path.join(p, basename))


def filter_directory(parent, t_l=constants.FILTERING_TIME_DELTAS, modi=constants.FILTERING_MODES):
    """
    Filters every file in the directory, but not in the subdirectories for given time parameters and filtering modes.
    :param parent: Directory to be filtered
    :param t_l: Time parameters
    :param modi: Filtering modes
    :return: None
    """
    for entry in os.listdir(parent):
        path = os.path.join(parent, entry)
        if os.path.isdir(path) or constants.ABSTRACTED_NAME_SUFFIX in entry or not entry.endswith('.csv'):
            continue

        # Generate z values
        z_l = constants.FILTERING_ABSOLUTE_ZS | set(generate_z_values(path))
        if 0 in z_l:
            z_l.remove(0)

        for m in modi:
            for t in t_l:
                for z in z_l:
                    if already_filtered(parent, entry, z, t, m):
                        print(f"Z: {z}, t: {t}, m:{m} - SKIPPED")
                        continue
                    print(f"Z: {z}, t: {t}, m:{m}")
                    filter_log(path, z, t, m)


def traverse_and_filter(directory: str, t_l=constants.FILTERING_TIME_DELTAS, modi=constants.FILTERING_MODES):
    """
    Traverses a given directory and filters every file in every subdirectory of the given directory,
    but not further than one subdirectory level.
    :param directory: Directory to be filtered
    :param t_l: Time parameters
    :param modi: Mode parameters
    :return: None
    """
    for entry in os.listdir(directory):
        parent = os.path.join(directory, entry)
        if os.path.isdir(parent):
            filter_directory(parent, t_l, modi)