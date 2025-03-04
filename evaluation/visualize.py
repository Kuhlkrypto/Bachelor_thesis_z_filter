import os
import re
import sys

import matplotlib.pyplot as plt
import pandas as pd
import pm4py
from scipy.stats import hmean
import csv

import measurement as ms






def visualize_dict(data, basename: str):
    """
    Visualisiert die Daten aus einem Dictionary und speichert die Plots in einem Ordner.

    Parameters:
        data (dict): Ein Dictionary mit den Spaltennamen als Keys und Listen von Werten als Values.

    """
    # Erstellen des Ausgabeordners
    b_name = basename.removesuffix(".csv")
    output_folder = "results/visualize/" + b_name
    os.makedirs(output_folder, exist_ok=True)

    # Daten extrahieren
    Z_values = data["Z"]
    dT_values = data["dT"]
    metrics_utility ={"Fitness_cmp", "Generality_cmp", "Precision_cmp", "Simplicity", "RISK_AT_5"} #{"Fitness_cmp", "RISK_AT_0.9", "RISK_AT_1", "RISK_AT_8", "RISK_AT_5"}


    metrics = metrics_utility
    # Einzigartige dT-Werte identifizieren (inkl. Baseline mit dT = inf)
    unique_dT_values = sorted(set(dT_values),
                              key=lambda x: float('inf') if x == "inf" else 0 if x == 'base' else int(x))
    unique_dT_values.remove('base')
    for t in unique_dT_values:
        if t == "inf":
            continue

        plt.figure(figsize=(10, 6))
        plt.ylim(0, 1)

        indices = [i for i, dt in enumerate(dT_values) if t == dt or dt == 'base']
        Z_filtered = [Z_values[i] for i in indices]
        for column in metrics:
            data[column] = list(map(float, data[column]))  # Alle numerischen Spalten in float umwandeln
        for metric in metrics:
            values = [data[metric][i] for i in indices]
            plt.plot(Z_filtered, values, 'o--' , label=metric)

        # Plot-Details
        plt.title(f"{transform_filename(b_name)} ΔT={convert_t_readable(t)}")
        plt.xlabel("Z")
        plt.ylabel("Metric Value")
        plt.legend(title="Metrics", loc="best")
        plt.grid(True)

        # Speichern des Plots
        plot_path = os.path.join(output_folder, f"vis {b_name} dt={convert_t_readable(t)}.png")
        plt.savefig(plot_path)
        plt.close()


def transform_filename(input_str: str) -> str:
    match = re.match(r"(.+?)_(classic|improved)(?:_(generalized))?", input_str)

    if not match:
        print(input_str)
        raise ValueError("Invalid input format. Expected '<name>_(classic|improved)[_generalized].csv'")

    name, variant, generalized = match.groups()
    suffix = "_Variant1" if variant == "classic" else "_Variant2"


    if "_generalized" in input_str:
        suffix += "_generalized"

    return name + suffix

def harmonic_mean(data, privacy_treshold, metrics):
    print(metrics)
    metrics = set(metrics) | {"Fitness_cmp"}
    unique_dT_values = sorted(set(data["dT"]), key=lambda x: float('inf') if x == "inf" else 0 if x == 'base' else int(x))
    for t in unique_dT_values:
        if t == "base":
            continue

        indices = [i for i, dt in enumerate(data["dT"]) if t == dt or dt == 'base']

        # Z values corresponding to dt value in this iteration

        valid_indices = range(len(data["Z"])) # [i for i , risk in enumerate(data["RISK_AT_0.9"]) if float(risk) <= privacy_treshold and i in indices]
        Z_filtered = [data["Z"][i] for i in valid_indices]

        max_hmean = None
        max_z = None

        for i,z in zip(valid_indices, Z_filtered):
            # if float(data["Fitness_cmp"][i]) < 0.8 :#or float(data["Simplicity"][i]) > 0.8:
            #     continue
            values = [float(data[metric][i] ) for metric in metrics]

            if all(v >= 0 for v in values):  # Harmonic Mean needs positive values
                h_mean = hmean(values)
                print(f"{h_mean} z:{z}")
                if max_hmean is None or h_mean > max_hmean:
                    max_hmean = h_mean
                    max_z = z



        print(f"{max_hmean}, time: {t}, z: {max_z}")


def process_and_plot(folder_path, folder_list: list = None, plot: bool = True, risk: str = "RISK_AT_0.9", name: str = "test"):
    data_dict = {}

    # Durch den Ordner iterieren und Dateien verarbeiten
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if not file_name.endswith(".csv"):
            continue  # Nur CSV-Dateien verarbeiten
    #
    # for file_path in folder_list:
    #     file_name = os.path.basename(file_path).removesuffix(".csv")
        with open(file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            temp_list = []

            for row in reader:
                try:
                    Z = float(row['Z'])
                    if row["dT"] == "base":
                        dT = -1
                    else:
                        dT = float(row['dT'])
                    if row["Fitness_cmp"] == "":
                        harmonic_mean = -1.0
                    else:
                        Fitness_cmp = float(row['Fitness_cmp'])
                        Precision_cmp = float(row['Precision_cmp'])
                        if Precision_cmp == 0.0:
                            Precision_cmp = sys.float_info.min
                        Generality_cmp = float(row['Generality_cmp'])
                        Simplicity = float(row['Simplicity'])
                        harmonic_mean = hmean([Fitness_cmp, Precision_cmp, Generality_cmp, Simplicity])

                    if row[risk] == "":
                        RISK = -1.0
                    else:
                        RISK = float(row[risk])


                    if row["RISK_A_0.9"] == "":
                        risk_a  = -1.0
                    else:
                        risk_a = float(row["RISK_A_0.9"])
                    # risk_a = -1.0
                    temp_list.append((Z, dT, harmonic_mean, RISK, risk_a))
                except ValueError:
                    continue  # Falls eine Zeile ungültige Werte enthält, wird sie übersprungen

            if not plot:
                print([x[2] for x in temp_list])
                print(len([x[2] for x in temp_list]))
                return [x[2] for x in temp_list]

            data_dict[file_name] = temp_list

    # Plot erstellen
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes = axes.flatten()

    # plt.figure(figsize=(10, 6))
    # plt.ylim(0.0, 1.0)

    axes[0].set_title(f"Harmonic Mean over Z for Δt={convert_t_readable(dT)}")
    axes[1].set_title(f"Re-identification Risk over Z for Δt={convert_t_readable(dT)}")
    axes[0].set_xlabel("Z")
    axes[1].set_xlabel("Z")
    axes[0].set_ylabel("Harmonic Mean")
    axes[1].set_ylabel(f"Re-identification Risk")

    for ax in axes:
        ax.set_ylim(0,1)

    index_map = {}  # Dictionary zur Speicherung von Indizes für die Legende

    for idx, (key, values) in enumerate(data_dict.items()):
        values.sort()  # Sortieren nach Z-Werten
        Z_vals = [entry[0] for entry in values if entry[2] != -1.0]
        Z_vals_risk = [entry[0] for entry in values if entry[3] != -1.0]
        harmonic_means = [entry[2] for entry in values if entry[2] != -1.0]
        risk_at_0_9_vals = [entry[3] for entry in values if entry[3] != -1.0]

        color = plt.cm.tab10(idx % 10)
        metric_name = key.removesuffix(".csv").removesuffix("_generalized")

        axes[0].plot(Z_vals, harmonic_means, 'o--', color= color, label=f'{metric_name}')
        axes[1].plot(Z_vals_risk, risk_at_0_9_vals, 'o--' ,color= color, label=f'{metric_name} {risk.removeprefix("RISK_")}')

        # extra for RISK_A_0.9
        color = plt.cm.tab10(idx + 2 % 10)
        axes[1].plot([entry[0] for entry in values if entry[4]!= -1.0], [entry[4] for entry in values if entry[4] != -1.0], 'o--', color= color, label=f'{metric_name} A_0.9')
        axes[0].set_ylim(0,1)
        axes[1].set_ylim(0, 1)
        index_map[idx] = key  # Speichern der Zuordnung von Index zu Dateiname

    axes[0].legend()
    axes[1].legend()
    axes[0].grid(True)
    axes[1].grid(True)
    # plt.xlabel("Z-Value")
    # plt.ylabel("Metric Value")
    # plt.title("Harmonic Mean and RISK_AT_0.9 over Z")
    # plt.grid(True)
    plt.tight_layout()
    plt.show()
    plt.savefig(f"{name}.png")

    # Indizes und zugehörige Dateinamen ausgeben
    for idx, filename in index_map.items():
        print(f"Log{idx} -> {filename}")

    return []

def convert_t_readable(duration_seconds):
    if duration_seconds == 'base':
        return duration_seconds
    elif duration_seconds == '0':
        return 'inf'
    duration_seconds = int(duration_seconds)
    if duration_seconds >= 3600:  # Convert to hours
        duration = f"{duration_seconds // 3600}h"
        if duration_seconds % 3600 != 0:
            duration = f"{duration} {(duration_seconds % 3600) // 60}m {duration_seconds % 60}s"
    elif duration_seconds >= 60:  # Convert to minutes
        duration = f"{duration_seconds // 60}m {duration_seconds % 60}s"
    else:  # Keep in seconds
        duration = f"{duration_seconds}s"
    return duration


if __name__ == "__main__":
    folder_path = "/home/fabian/Github/Bachelor_thesis_z_filter/results_csv/results_alignment/medium_z"
    paths_bpi_basic = [
        f"{folder_path}BPI_Challenge2012_basic_generalized.csv",
        f"{folder_path}BPI_Challenge2017_basic_generalized.csv",
        f"{folder_path}BPI_Challenge2018_basic_generalized.csv"
    ]
    #
    # folder_path = "/home/fabian/Github/Bachelor_thesis_z_filter/results_csv/results_alignment/balanced/"
    # paths_bpi_balanced = [
    #     f"{folder_path}BPI_Challenge2012_balanced_generalized.csv",
    #     f"{folder_path}BPI_Challenge_2017_balanced_generalized.csv",
    #     f"{folder_path}BPI_Challenge2018_balanced_generalized.csv"
    # ]

    process_and_plot("/home/fabian/Github/Bachelor_thesis_z_filter/results_csv/results_alignment/medium_z/", paths_bpi_basic, risk="RISK_AT_0.9", name="eval_hospital")
    # df1 = pd.read_csv("../results_csv/Sepsis1-30/usual/Sepsis Cases - EventLogabstractedresults_filtering_classic.csv")
    # df2 = pd.read_csv("../results_csv/Sepsis1-30/fitness/Sepsis Cases - EventLogabstractedresults_filtering_classic.csv")
    # df = df1.combine_first(df2)
    # df.update(df2)
    # df.to_csv("Sepsis_Cases_classic_generalized.csv")
    # print(df)
    # path = '/home/fabian/Github/Bachelor_thesis_z_filter/data/data_csv/Sepsis Cases - Event Log/Sepsis Cases - Event Log.pnml'
    # path1 = '/home/fabian/Github/Bachelor_thesis_z_filter/data/data_csv/Sepsis Cases - Event Log/results_filtering_improved/Sepsis Cases - Event LogZ17PT259200S.pnml'
    #
    #
    # paths = [
    #     "/home/fabian/Github/Bachelor_thesis_z_filter/data/data_csv/Sepsis Cases - Event Log/Sepsis Cases - Event Log.pnml",
    #     "/home/fabian/Github/Bachelor_thesis_z_filter/data/data_csv/Sepsis Cases - Event Log/results_filtering_improved/Sepsis Cases - Event LogZ15PT259200S.pnml",
    #     "/home/fabian/Github/Bachelor_thesis_z_filter/data/data_csv/Sepsis Cases - Event Log/results_filtering_improved/Sepsis Cases - Event LogZ29PT259200S.pnml"
    #
    # ]
    # for path in paths:
    #     net, im, fm = pm4py.read_pnml(path)
    #     pm4py.view_petri_net(net, im, fm)
    #
    # path = "/home/fabian/Github/Bachelor_thesis_z_filter/evaluation/results/Sepsis/"
    # # path = "Sepsis_Cases_classic_improved_generalized.csv"
    # for file in os.listdir(path):
    #     meas = ms.Measurement("", "")
    #
    #     meas.read_from_csv(os.path.join(path, file))
    #     visualize_dict(meas.results, file)

    # #------------------------------------ EVALUATOR
    path = "/home/fabian/Github/Bachelor_thesis_z_filter/results_csv/results_alignment/Road/Road_Management_balanced_generalized.csv"
    meas = ms.Measurement("")
    meas.read_from_csv(path)
    # visualize_dict(meas.results, os.path.basename(path))

    # harmonic_mean(meas.results, 0.3, ["Fitness_cmp", "Simplicity"])
    harmonic_mean(meas.results, 1, ["Fitness_cmp", "Generality_cmp", "Precision_cmp", "Simplicity"])
    # harmonic_mean(meas.results, 0.2, ["Fitness_cmp", "Precision_cmp", "Simplicity"])
    # harmonic_mean(meas.results, 0.1, ["Fitness_cmp", "Simplicity", "Generality_cmp"])


