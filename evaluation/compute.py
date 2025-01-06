from pathlib import Path
import re
import pandas as pd
import pm4py
import measurement as ms
import os


def import_csv(filepath):
    """Import CSV as a pandas DataFrame."""
    event_log = pd.read_csv(filepath, sep=',')
    event_log = pm4py.format_dataframe(event_log, case_id='case_id', activity_key='activity', timestamp_key='timestamp')

    num_events = len(event_log)
    num_cases = len(event_log['case_id'].unique())

    print(f"Events {num_events}, unique cases: {num_cases}")
    return event_log


def walk_dir(folder_path, cmp, quality_dict):
    """Walk through all files in a directory."""
    for file_path in sorted([file for file in Path(folder_path).iterdir()]):
        if file_path.is_file():
            process_file(file_path, cmp, quality_dict)


def process_file(file_path, cmp, quality_dict):
    """Process a single file and update quality metrics."""
    print(f"Processing file: {file_path}")
    log = import_csv(file_path)
    aecs = ms.calculate_aecs(log, ["activity", "source"])
    print(f"AECS SOURCE ACTIVITY: {aecs}")
    aecs = ms.calculate_aecs(log, "activity")
    print(f"AECS Activity: {aecs}")
    # train_log = log[:int(0.8 * len(log))]
    # test_log = log[int(0.8 * len(log)):]

    net, im, fm = pm4py.discover_petri_net_inductive(log)

    petri_stats(net)

    z, prefix, dur = extract_number_and_prefix(os.path.basename(file_path))

    # get quality measurings
    fitness = ms.measure_fitness(cmp, net, im, fm)
    precision = ms.measure_precision(log, net, im, fm)
    generality = ms.measure_generality(log, net, im, fm)
    simplicity = ms.measure_simplicity(net)
    aecs = ms.calculate_aecs(log, ["activity"])

    # add quality measuring results to quality_dict
    quality_dict["Fitness"].append((z, dur, fitness['log_fitness']))
    quality_dict["Precision"].append((z, dur, precision))
    quality_dict["Generalization"].append((z, dur, generality))
    quality_dict["Simplicity"].append((z, dur, simplicity))
    quality_dict["AECS"].append((z, dur, aecs))

    # ms.measure_other_simplicities(quality_dict, net, z, dur)  # optional


def petri_stats(petri_net):
    """Print statistics of the Petri net."""
    print(f"Number of transitions: {len(petri_net.transitions)}")
    print(f"Number of places: {len(petri_net.places)}")
    print(f"Number of arcs: {len(petri_net.arcs)}")


def extract_number_and_prefix(filename):
    """Parses a filename according to following format:
    <original_filename>Z<value>PT<time in seconds>S

    Returns:
    number: z-value
    prefix: original filename
    duration: duration in seconds
    """
    match = re.match("^(.*?[^Z]*)Z(\\d+)PT(\\d+)S*", filename)
    if match:
        prefix = match.group(1)  # Characters before 'Z'
        number = int(match.group(2))
        duration = int(match.group(3))
        return number, prefix, duration
    else:
        return -1, "", ""
