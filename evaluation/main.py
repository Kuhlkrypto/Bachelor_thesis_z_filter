import os.path

from tqdm import tqdm

import result_printer as printer
import pm4py
import compute as comp
import measurement as ms
import filtering


def store_pandas_dataframe_as_xes(pandas_dataframe):
    """Store pandas DataFrame as a XES file."""
    pm4py.write_xes(pandas_dataframe, "test_files/exp1")


def filter_z_range(path, t, values):
    total_steps = len(values)
    with tqdm(total=total_steps, desc="Filtering files", unit="file") as pbar:
        for e, z in enumerate(values):
            print(f"Z: {z}, e: {e}")
            filtering.filter_log(path, z, t)
            pbar.update(e)


def cleanup_logs(path, depth=0):
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
       # elif os.path.isdir(item_path):
       #      cleanup_logs(path, depth+1)


def main(orig_path):
    # Dictionary to store quality metrics
    result_path = '/home/fabian/Github/Bachelor_thesis_z_filter/evaluation/results_filtering'
    # path to original event log
    base_name = os.path.basename(orig_path)
    base_name = base_name.removesuffix('.xes')

    meas = ms.Measurement(result_path)
    meas.set_unfiltered_log(orig_path)

    # Directory with filtered event logs
    path = f"{result_path}/{base_name}/"

    # Plot the quality metrics
    # printer.plot_quality_metrics(quality_dict, result_path, base_name)


if __name__ == "__main__":
    path = "/home/fabian/TU_DRESDEN/PrivateMine/SOURCED/data/Sepsis_Cases-Event_Log.xes"
    # cleanup_logs("/home/fabian/TU_DRESDEN/Bachelorarbeit/pm4py_test/pythonProject/results_filtering")
    filter_z_range(path, "3600s", [1])
    # main(path)
