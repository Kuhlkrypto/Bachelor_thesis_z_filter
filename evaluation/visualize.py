import os
import matplotlib.pyplot as plt
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
    metrics_privacy_A = ["RISK_A_0.3", "RISK_A_0.6", "RISK_A_0.9"]
    metrics_privacy_AT = ["RISK_AT_0.3", "RISK_AT_0.6", "RISK_AT_0.9"]
    metrics_utility = ["Fitness", "Precision", "Generality", "Simplicity"]
    metrics_utility_cmp = ["Fitness_cmp", "Precision_cmp", "Generality_cmp"]

    metrics = set(metrics_privacy_AT) | {"Precision_cmp", "Precision", "Simplicity", "Generality", "Generality_cmp"}

    # Einzigartige dT-Werte identifizieren (inkl. Baseline mit dT = inf)
    unique_dT_values = sorted(set(dT_values), key=lambda x: float('inf') if x == "inf" else 0 if x == 'base' else int(x))
    unique_dT_values.remove('base')
    for t in unique_dT_values:
        if t == "inf":
            continue
        plt.figure(figsize=(10, 6))
        indices = [i for i, dt in enumerate(dT_values) if t == dt or dt == 'base']
        Z_filtered = [Z_values[i] for i in indices]
        plt.ylim(0, 1)  # Einheitliche Skala für die y-Achse
        for column in metrics:
            data[column] = list(map(float, data[column]))  # Alle numerischen Spalten in float umwandeln
        for metric in metrics:
            values = [data[metric][i] for i in indices]
            plt.plot(Z_filtered, values, marker='o', label=metric)

        # Plot-Details
        plt.title(f"vis {b_name} dt= {convert_t_readable(t)}")
        plt.xlabel("Z")
        plt.ylabel("Metric Value")
        plt.legend(title="Metrics", loc="best")
        plt.grid(True)

        # Speichern des Plots
        plot_path = os.path.join(output_folder, f"vis {b_name} dt={convert_t_readable(t)}.png")
        plt.savefig(plot_path)
        plt.close()


def convert_t_readable(duration_seconds):
    if duration_seconds == 'base':
        return duration_seconds
    elif duration_seconds == '0':
        return 'inf'
    duration_seconds = int(duration_seconds)
    if duration_seconds >= 3600:  # Convert to hours
        duration = f"{duration_seconds // 3600}h {(duration_seconds % 3600) // 60}m {duration_seconds % 60}s"
    elif duration_seconds >= 60:  # Convert to minutes
        duration = f"{duration_seconds // 60}m {duration_seconds % 60}s"
    else:  # Keep in seconds
        duration = f"{duration_seconds}s"
    return duration



if __name__ == "__main__":
    path = "/results_csv/SepsisCasses-EventLog/Sepsis Cases - Event Logabstractedresults_filtering_improved.csv"
    meas = ms.Measurement("")
    meas.read_from_csv(path)
    visualize_dict(meas.results, os.path.basename(path).removesuffix('.csv'))
