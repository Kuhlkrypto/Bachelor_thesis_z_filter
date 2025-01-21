import math
import os.path
import subprocess
import constants
import pandas as pd


def filter_log(log_path, z, t, modi):
    binary_arg = os.path.join("/home/fabian/Github/Bachelor_thesis_z_filter/target/release/z-anon-impl")

    try:
        res = subprocess.run(
            [binary_arg,
             str(log_path),
             str(z),
             str(t),
             modi],
            check=True,
            text=True,
                # capture_output=True  # Um die Ausgabe zu erfassen
        )
        res.check_returncode()

    except subprocess.CalledProcessError as e:
        print(f"Raised error{e.stderr}")
        exit(1)


def generate_z_values(file_path, percentages=[0.001, 0.005, 0.01, 0.05, 0.1, 0.15, 0.2]):
    # CSV-Datei einlesen
    df = pd.read_csv(file_path, sep=constants.DELIMITER)

    # Anzahl der einzigartigen Identifier
    unique_values = df["case_id"].unique()
    unique_count = len(unique_values)
    print(unique_count)

    # Berechnung der z-Werte
    z_values = [max(1, int(math.ceil(unique_count * p))) for p in percentages]

    return z_values


DEPTH_MAX = 1


def traverse_and_filter(directory: str, depth, t_l=['1h', '24h', '72h', 'inf'], modi=['0', '1']):
    if depth >= DEPTH_MAX:
        return
    for (parent, dirs, files) in os.walk(directory):
        for file in files:
            path = str(os.path.join(parent, file))
            print(str(path))
            former_z = 0
            # z_l = generate_z_values(path)
            z_l = {15, 30, 45, 60} | set(generate_z_values(path))
            for z in z_l:
                if z == former_z:
                    continue
                former_z = z
                for t in t_l:
                    for m in modi:
                        print(f"Z: {z}, t: {t}, m:{m}")
                        filter_log(path, z, t, m)


if __name__ == "__main__":
    # # filter_log("/home/fabian/Github/Bachelor_thesis_z_filter/data_csv/Road_Traffic_Fine_Management_Process/Road_Traffic_Fine_Management_Process.csv", 1, "3600h")
    base_directory = "/home/fabian/Github/Bachelor_thesis_z_filter/data/data_csv/"
    # # filter_log("/home/fabian/Github/Bachelor_thesis_z_filter/data_csv/Road_Traffic_Fine_Management_Process/Road_Traffic_Fine_Management_Process.csv", 1, "3600h", "0")
    traverse_and_filter(base_directory, 0)
