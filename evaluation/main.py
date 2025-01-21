import os

import filtering as fi
import measurement as ms
import compute as cp
import visualize as vi


def main():
    """
    The core loop of the evaluation process, it will traverse all csv files in the base_directory,
    filter them according to the dt and z values described in the functions. Next, build a petri net of every one.
    Lastly, apply metrics used to measure the utility and privacy of the corresponding models and files.
    Results can be found in /results_csv
    :return:
    """
    base_folder = "/home/fabian/Github/Bachelor_thesis_z_filter/data/data_csv/"
    # Presume there are filtered logs already in the base folder
    # Filter log for various z and ts
    fi.traverse_and_filter(base_folder, 0)
    # abstract every existing csv file
    cp.abstract_timestamps(base_folder)

    # build a petri net for every csv file
    # ms.traverse_and_build_petri_nets(base_folder)

    # lastly traverse everything and measure what u can
    ms.traverse()

    # base = "/home/fabian/Github/Bachelor_thesis_z_filter/results_csv/"
    # visualization(base)

main()


def visualization(base):
    measure = ms.Measurement("")

    for file in os.listdir(base):
        try:
            measure.read_from_csv(os.path.join(base, file))
            vi.visualize_dict(measure.quality_dict, file)
        except Exception as e:
            print(f"Sth went wrong: {e}")
#
# if __name__ == "__main__":
#     visualization("/home/fabian/Github/Bachelor_thesis_z_filter/results_csv/")
#
