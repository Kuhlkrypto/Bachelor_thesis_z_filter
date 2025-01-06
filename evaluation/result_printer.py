import os.path
import csv

from matplotlib import pyplot as plt


def preprocess_quality_dict(entries):
    # Extract z-values, t-values, and result-values
    z_values = []
    result_values = []
    t_values = set()  # To track unique t-values

    for entry in entries:
        print(entry)
        z, t, result = entry
        z_values.append(z)
        result_values.append(result)
        t_values.add(t)

    return z_values, t_values, result_values


def convert_t_readable(duration_seconds):
    if duration_seconds >= 3600:  # Convert to hours
        duration = f"{duration_seconds // 3600}h {(duration_seconds % 3600) // 60}m {duration_seconds % 60}s"
    elif duration_seconds >= 60:  # Convert to minutes
        duration = f"{duration_seconds // 60}m {duration_seconds % 60}s"
    else:  # Keep in seconds
        duration = f"{duration_seconds}s"
    return duration


def plot_quality_metrics(quality_dict, result_path,base_name):
    """Plot each quality dimension."""
    for dimension, values in quality_dict.items():

        z_val, t_val, r_val = preprocess_quality_dict(values)

        # Plot the results
        plt.figure(figsize=(8, 5))
        plt.plot(z_val, r_val, marker='o', linestyle='-', label=f"{dimension} results")
        plt.title(f"{dimension} over {base_name}")
        plt.xlabel("Z-Value")
        plt.ylabel(f"{dimension} Result")
        plt.grid(True)
        plt.legend()

        # Add t-value label if consistent
        if len(t_val) == 1:  # All t-values are the same
            t_val = t_val.pop()  # Get the single t-value
            plt.text(0.95, 0.95, f"t: {convert_t_readable(t_val)}", transform=plt.gca().transAxes,
                     fontsize=10, verticalalignment='top', horizontalalignment='right',
                     bbox=dict(facecolor='white', alpha=0.5))

        # Save each plot as a PNG file
        plt.savefig(f"{result_path}/{base_name}_{dimension}_plot.png")
        plt.close()  # Close the figure to avoid overlapping plots


def hashmap_to_csv(hashmap, file_path, basename):
    """
    Writes a hashmap into a csv-file.

    :param hashmap: dict, Hashmap with keys as header values, and hashmap values als entries.
    :param file_path: str, path to
    """
    try:
        #only consider keys with value-list-size greater 0
        filtered_hashmap = {k: v for k, v in hashmap.items() if len(v) > 0}
        # Sicherstellen, dass alle Listen in der Hashmap die gleiche Länge haben
        lengths = [len(v) for v in filtered_hashmap.values()]
        if len(set(lengths)) > 1:
            raise ValueError("Entries arent equal long!")

        # Schreiben der Hashmap in die CSV-Datei
        with open(f"{file_path}/{basename}.csv", mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=filtered_hashmap.keys())
            writer.writeheader()
            rows = [dict(zip(filtered_hashmap.keys(), row)) for row in zip(*filtered_hashmap.values())]
            writer.writerows(rows)

    except Exception as e:
        print(f"Error while writing hashmap to csv file: {e}")
