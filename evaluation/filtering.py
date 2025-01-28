import math
import os.path
import subprocess
import constants
import pandas as pd


def filter_log(log_path, z, t, modi):
    dir = os.getcwd()
    binary_arg = os.path.join(dir, "bin/z-anon-impl")

    try:
        res = subprocess.run(
            [binary_arg,
             str(log_path),
             str(z),
             str(t),
             modi],
            check=True,
            text=True,
            capture_output=True  # Um die Ausgabe zu erfassen
        )
        res.check_returncode()

    except subprocess.CalledProcessError as e:
        print(f"Raised error{e.stderr}")
        exit(1)


def generate_z_values(file_path, percentages=constants.FILTERING_RELATIVE_ZS):
    # CSV-Datei einlesen
    df = pd.read_csv(file_path, sep=constants.DELIMITER)

    # Anzahl der einzigartigen Identifier
    unique_values = df["case_id"].unique()
    unique_count = len(unique_values)

    # Berechnung der z-Werte
    z_values = [max(1, int(math.ceil(unique_count * p))) for p in percentages]

    return z_values


DEPTH_MAX = 1


def convert_seconds(t: str):
    res = 'PT'
    middle = ''
    if t == 'inf':
        middle = '0inf0'
    elif t.endswith('h'):
        t = t.removesuffix('h')
        middle = str(int(t) * 3600)
    elif t.endswith('m'):
        t = t.removesuffix('m')
        middle = str(int(t) * 60)
    else:
        return t
    return res + middle + 'S.csv'


def already_filtered(folder, file: str, z, t, mode) -> bool:
    p = None
    if mode == '0':
        p = os.path.join(folder, "results_filtering_classic")
    else:
        p = os.path.join(folder, "results_filtering_improved")
    basename = file.removesuffix('.csv') + 'Z' + str(z) + convert_seconds(t)
    return os.path.exists(os.path.join(p, basename))


def filter_directory(parent, t_l=constants.FILTERING_TIME_DELTAS, modi=constants.FILTERING_MODES):
    for entry in os.listdir(parent):
        path = str(os.path.join(parent, entry))
        if os.path.isdir(path) or entry.__contains__('abstracted') or not entry.__contains__('.csv'):
            continue
        z_l = constants.FILTERING_ABSOLUTE_ZS | set(generate_z_values(path))
        if z_l.__contains__(0):
            z_l.remove(0)
        for m in modi:
            for t in t_l:
                for z in z_l:
                    if already_filtered(parent, entry, z, t, m):
                        print(f"Z: {z}, t: {t}, m:{m} - SKIPPED")
                        continue
                    print(f"Z: {z}, t: {t}, m:{m}")
                    filter_log(path, z, t, m)


def traverse_and_filter(directory: str, depth, t_l=constants.FILTERING_TIME_DELTAS, modi=constants.FILTERING_MODES):
    if depth >= DEPTH_MAX:
        return

    for entry in os.listdir(directory):
        parent = os.path.join(directory, entry)
        if os.path.isdir(parent):
            filter_directory(parent, t_l, modi)


if __name__ == "__main__":
    # # filter_log("/home/fabian/Github/Bachelor_thesis_z_filter/data_csv/Road_Traffic_Fine_Management_Process/Road_Traffic_Fine_Management_Process.csv", 1, "3600h")
    base_directory = "/home/fabian/Github/Bachelor_thesis_z_filter/data/Sepsis Cases - Event Log/"
    # # filter_log("/home/fabian/Github/Bachelor_thesis_z_filter/data_csv/Road_Traffic_Fine_Management_Process/Road_Traffic_Fine_Management_Process.csv", 1, "3600h", "0")
    filter_directory(base_directory)