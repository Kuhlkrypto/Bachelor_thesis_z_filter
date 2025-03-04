import os
import sys

import pm4py

import filtering as fi
import abstract_timestamps as cp
import measurement as ms
import constants as cons


def main():
    """
    The core loop of the evaluation process, it will traverse all csv files in the base_directory,
    filter them according to the dt and z values described in the functions. Next, build a petri net of every one.
    Lastly, apply metrics used to measure the utility and privacy of the corresponding models and files.
    Results can be found in /results_csv
    :return:
    """
    # set recursion limit for hard computation tasks (expected)
    sys.setrecursionlimit(5000)
    # Presume there are filtered logs already in the base folder
    # Filter log for various z and ts
    fi.traverse_and_filter(cons.PATH_DATA)
    # abstract every existing csv file
    if cons.ABSTRACT_TIMESTAMPS_EVALUATION:
        cp.abstract_timestamps(cons.PATH_DATA)

    # lastly traverse everything and measure what u can
    ms.traverse(cons.PATH_DATA)


if __name__ == "__main__":
    main()