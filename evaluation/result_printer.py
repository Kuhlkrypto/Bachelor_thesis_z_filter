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





