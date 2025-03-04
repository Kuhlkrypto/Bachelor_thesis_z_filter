import csv
import os

import constants as con
from concurrent.futures import ProcessPoolExecutor

import file_utilities as utils
import pm4py
from csv2simple_auto import convert_csv2auto as csv2auto
from unicity_activities import risk_re_ident_quant
from tqdm import tqdm


class Measurement:

    def __init__(self, result_name):
        """
        Initializes the Measurement instance.

        Args:
            result_name (str): The name used to store the results.
        """
        self.unfiltered_log = None  # Log used for comparison
        self.results = self.init_dict()  # Dictionary to store results
        self.basename_orig = ''  # Original file basename
        self.result_path = con.PATH_RESULTS  # Directory to save results
        self.result_name = result_name  # Name for the results file

    @staticmethod
    def init_dict():
        """
        Initializes the result dictionary with predefined keys.

        Returns:
            dict: A dictionary containing measurement categories.
        """
        results_dict = {
            "Z": [], "dT": [], "Fitness": [], "Fitness_ref": [],
            "Precision": [], "Precision_ref": [], "Generality": [], "Generality_ref": [], "Simplicity": []
        }
        risk_at = "RISK_AT_"
        risk_a = "RISK_A_"

        # Add risk categories based on constants
        for risk in con.RISK_POINTS_ABSOLUTE | con.RISK_POINTS_RELATIVE:
            results_dict[risk_at + str(risk)] = []
            results_dict[risk_a + str(risk)] = []
        return results_dict

    def set_unfiltered_log(self, directory, basename):
        """
        Loads the original (unfiltered) event log.

        Args:
            directory (str): Directory containing the log file.
            basename (str): Name of the log file.
        """
        path = os.path.join(directory, basename)
        self.unfiltered_log = utils.import_csv(path)
        self.basename_orig = basename

    @staticmethod
    def fitness(event_log, net, im, fm):
        """
        Computes the fitness metric of a process model.

        Args:
            event_log: The event log.
            net: The Petri net.
            im: Initial marking.
            fm: Final marking.

        Returns:
            float: The fitness score.
        """
        if con.FITNESS_ALIGNMENT:
            return pm4py.fitness_alignments(event_log, net, im, fm, multi_processing=con.PM4PY_MULTIPROCESSING)[
                'log_fitness']
        return pm4py.fitness_token_based_replay(event_log, net, im, fm)['log_fitness']

    @staticmethod
    def simplicity(net, im, fm):
        """
        Computes the simplicity metric of a process model.

        Args:
            net: The Petri net.
            im: Initial marking.
            fm: Final marking.

        Returns:
            float: The simplicity score.
        """
        return pm4py.simplicity_petri_net(net, im, fm)

    @staticmethod
    def precision(event_log, net, im, fm):
        """
        Computes the precision metric of a process model.

        Args:
            event_log: The event log.
            net: The Petri net.
            im: Initial marking.
            fm: Final marking.

        Returns:
            float: The precision score.
        """
        if con.PRECISION_ALIGNEMNT:
            return pm4py.precision_alignments(event_log, net, im, fm, multi_processing=con.PM4PY_MULTIPROCESSING)
        return pm4py.precision_token_based_replay(event_log, net, im, fm)

    @staticmethod
    def generality(log, net, im, fm):
        """
        Computes the generality metric of a process model.

        Args:
            log: The event log.
            net: The Petri net.
            im: Initial marking.
            fm: Final marking.

        Returns:
            float: The generality score.
        """
        return pm4py.generalization_tbr(log, net, im, fm)

    def __metrics_utility_log(self, net, im, fm, log, ):
        if con.MODEL_QUALITY_MULTIPROCESSING:
            with (ProcessPoolExecutor() as executor):
                # Measure simplicity as it does not depend on the quality
                sim = executor.submit(self.simplicity, net, im, fm)
                if con.MODEL_QUALITY_EVALUATION:
                    # Submit jobs for executor
                    fit = executor.submit(self.fitness, log, net, im, fm)
                    prec = executor.submit(self.precision, log, net, im, fm)
                    gen = executor.submit(self.generality, log, net, im, fm)

                    # add to result dict
                    self.results["Fitness"].append(fit.result())
                    self.results["Precision"].append(prec.result())
                    self.results["Generality"].append(gen.result())

                # case of Model Quality
                if con.REF_MODEL_QUALITY_EVALUATION and self.unfiltered_log is None and con.MODEL_QUALITY_EVALUATION:
                    # add the last entry as it refers to the unfiltered log,
                    # only possible if model quality shall be measured
                    self.results["Fitness_ref"].append(self.results["Fitness"][-1])
                    self.results["Precision_ref"].append(self.results["Precision"][-1])
                    self.results["Generality_ref"].append(self.results["Generality"][-1])

                # reference model quality with unfiltered log
                elif con.REF_MODEL_QUALITY_EVALUATION and self.unfiltered_log is not None:
                    # use unfiltererd log for Calculation
                    fit = executor.submit(self.fitness, self.unfiltered_log, net, im, fm)
                    prec = executor.submit(self.precision, self.unfiltered_log, net, im, fm)
                    gen = executor.submit(self.generality, self.unfiltered_log, net, im, fm)

                    self.results["Precision_ref"].append(prec.result())
                    self.results["Generality_ref"].append(gen.result())
                    self.results["Fitness_ref"].append(fit.result())

                # this case happens usually at the original models where model quality is disabled but no unfiltered
                # log is set
                elif con.REF_MODEL_QUALITY_EVALUATION:
                    fit = executor.submit(self.fitness, log, net, im, fm)
                    prec = executor.submit(self.precision, log, net, im, fm)
                    gen = executor.submit(self.generality, log, net, im, fm)

                    fit = fit.result()
                    prec = prec.result()
                    gen = gen.result()

                    # add to result dict
                    self.results["Fitness_ref"].append(fit)
                    self.results["Precision_ref"].append(prec)
                    self.results["Generality_ref"].append(gen)

                # add to result dict
                self.results["Simplicity"].append(sim.result())
        else:
            # calc simplicity and add to results
            self.results["Simplicity"].append(self.simplicity(net, im, fm))

            # case of Model Quality
            if con.MODEL_QUALITY_EVALUATION:
                self.results["Fitness"].append(self.fitness(log, net, im, fm))
                self.results["Precision"].append(self.fitness(log, net, im, fm))
                self.results["Generality"].append(self.fitness(log, net, im, fm))

            # Case of reference Model Quality with no unfiltered event log,
            # already measured model quality allows for shortcut
            if con.REF_MODEL_QUALITY_EVALUATION and self.unfiltered_log is None and con.MODEL_QUALITY_EVALUATION:
                # add the last entry as it refers to the unfiltered log
                self.results["Fitness_ref"].append(self.results["Fitness"][-1])
                self.results["Precision_ref"].append(self.results["Precision"][-1])
                self.results["Generality_ref"].append(self.results["Generality"][-1])

            # reference model quality with unfiltered log
            elif con.REF_MODEL_QUALITY_EVALUATION and self.unfiltered_log is not None:
                # use unfiltererd log for Calculation
                self.results["Precision_ref"].append(self.precision(self.unfiltered_log, net, im, fm))
                self.results["Generality_ref"].append(self.generality(self.unfiltered_log, net, im, fm))
                self.results["Fitness_ref"].append(self.fitness(self.unfiltered_log, net, im, fm))

            elif con.REF_MODEL_QUALITY_EVALUATION:
                # this case happens usually at the original models where model quality is disabled but no unfiltered log
                # is set
                self.results["Fitness_ref"].append(self.fitness(log, net, im, fm))
                self.results["Precision_ref"].append(self.fitness(log, net, im, fm))
                self.results["Generality_ref"].append(self.fitness(log, net, im, fm))

    def __metrics_privacy_file(self, path: str, file: str):
        path, file = csv2auto(path + "/", file, con.PATH_TMP)
        with ProcessPoolExecutor() as executor:
            risk_at = executor.submit(risk_re_ident_quant, path + "/", file, projection='A')
            risk_a = executor.submit(risk_re_ident_quant, path + "/", file, projection='E')
            risk_at = risk_at.result()
            risk_a = risk_a.result()

        for i, rel in enumerate(con.RISK_POINTS_RELATIVE):
            self.results['RISK_AT_' + str(rel)].append(risk_at[0][i][1])
            self.results['RISK_A_' + str(rel)].append(risk_a[0][i][1])
        for i, r in enumerate(con.RISK_POINTS_ABSOLUTE):
            self.results['RISK_AT_' + str(r)].append(risk_at[1][i][1])
            self.results['RISK_A_' + str(r)].append(risk_a[1][i][1])

    def comp_qualities_of_file(self, path, file, z_val, dt_val):
        """
        Evaluates the quality of a discovered Petri net model based on a filtered event log,
        incorporating validation.

        Args:
            path (str): Path to the folder of the event log CSV file.
            file (str): Name of the event log CSV file.
            z_val (int): z-anonymity value.
            dt_val (str): Delta threshold for anonymization.
        """
        print(f"\nMeasuring file: {file}")

        if con.RISK_EVALUATION or con.MODEL_QUALITY_EVALUATION or con.REF_MODEL_QUALITY_EVALUATION:
            self.results["Z"].append(z_val)
            self.results["dT"].append(dt_val)

        # utilize metrics for privacy on log
        if con.RISK_EVALUATION:
            self.__metrics_privacy_file(path, file)

        # import event log into pandas df
        file_path = os.path.join(path, file)
        log_df = utils.import_csv(file_path)

        # discover petri net
        net, im, fm = pm4py.discover_petri_net_inductive(log_df, multi_processing=True)

        # safe to .pnml if wanted
        if con.SAVE_PETRI_NETS:
            # path for corresponding petri net
            p = file_path.removesuffix(".csv") + ".pnml"
            # write pnml file
            pm4py.write_pnml(net, im, fm, p)

        # utilize metrics for utility (quality dimensions)
        if con.MODEL_QUALITY_EVALUATION or con.REF_MODEL_QUALITY_EVALUATION:
            self.__metrics_utility_log(net, im, fm, log_df)

        # print to CSV if there is at least one row at least containing Z
        if self.results["Z"]:
            self.write_to_csv()

    def __set_dict(self, new_dict):
        self.results = new_dict

    def write_to_csv(self):
        """
        Writes the measurement results to a CSV file.
        """
        try:
            filtered_hashmap = self.sort_dict_according_to_z()
            with open(f"{self.result_path}/{self.result_name}.csv", mode='w', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=filtered_hashmap.keys())
                writer.writeheader()
                rows = [dict(zip(filtered_hashmap.keys(), row)) for row in zip(*filtered_hashmap.values())]
                writer.writerows(rows)
        except Exception as e:
            print(f"Error while writing hashmap to csv file: {e}")

    def clear(self):
        """
        Clear the result hashmap and init with new default dict
        :return:
        """
        helper = self.results.copy()
        self.results.clear()
        self.results = self.init_dict()
        return helper

    def sort_dict_according_to_z(self):
        filtered_hashmap = {k: v for k, v in self.results.items() if len(v) > 0}
        sorted_indices = sorted(range(len(filtered_hashmap["Z"])), key=lambda i: int(filtered_hashmap["Z"][i]))
        filtered_hashmap = {key: [value[i] for i in sorted_indices] for key, value in filtered_hashmap.items()}
        return filtered_hashmap

    def read_from_csv(self, csv_file_path):
        """
           Reads a hashmap from a csv file written by the `write_to_csv` method.

           csv_file_path: Path to the csv file.

           Returns:
               A hashmap (dictionary) where keys are the column headers and values are lists of column data.
               """
        try:
            with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                hashmap = {field: [] for field in reader.fieldnames}  # Initialize hashmap with empty lists

                for row in reader:
                    for key, value in row.items():
                        hashmap[key].append(value)

            self.__set_dict(hashmap)

        except Exception as e:
            raise Exception(f"Error while reading hashmap from csv file: {e}")


def traverse_and_measure(directory: str, abstracted: bool):
    """
    Traverses a directory and evaluates the quality of process models discovered from event logs.

    Args:
        directory (str): The directory to traverse.
        abstracted (bool): Whether to consider only time-abstracted logs.
    """
    for entry in os.listdir(directory):
        full_path = os.path.join(directory, entry)
        if os.path.isdir(full_path):
            with tqdm(total=(count_csv_files(directory) - 2) / 4, desc=os.path.basename(directory),
                      unit='file') as pbar:
                basename = os.path.basename(directory).removesuffix('.csv') + (
                    con.ABSTRACTED_NAME_SUFFIX if abstracted else '')
                ms = Measurement(basename + str(entry))

                # compute qualities of original log
                ms.comp_qualities_of_file(directory, basename + ".csv", 0, "base")

                # update pbar
                pbar.update(1)

                # set unfiltered log in order to measure Reference Model Quality
                ms.set_unfiltered_log(directory, basename + ".csv")

                # measure all other proces models
                measure_other_nets(full_path, ms, abstracted, pbar)
                if ms.results["Z"]:
                    ms.write_to_csv()


def traverse(path):
    """
    Traverse the path directory and kick off evaluation algorithm.
    :param path: directory to traverse
    """
    for entry in os.listdir(path):
        curr = os.path.join(path, entry)
        if os.path.isdir(curr):
            if con.ABSTRACT_TIMESTAMPS_EVALUATION:
                traverse_and_measure(curr, True)
            if con.USUAL_TIMESTAMP_EVALUATION:
                traverse_and_measure(curr, False)


def measure_other_nets(filter_dir, ms, abstracted: bool, pbar):
    """
    Evaluate all other filtered event logs in directory filter_dir.
    :param filter_dir: Directory to evaluate
    :param ms: Measurement object
    :param abstracted: boolean indicating whether to traverse abstracted files
    :param pbar: progress bar object
    """
    for entry in os.listdir(str(filter_dir)):
        p = os.path.join(filter_dir, entry)
        if os.path.isfile(p) and os.path.basename(p).endswith(".csv"):
            if abstracted and not entry.__contains__(con.ABSTRACTED_NAME_SUFFIX):
                continue
            elif not abstracted and entry.__contains__(con.ABSTRACTED_NAME_SUFFIX):
                continue
            curr_path = os.path.join(filter_dir, entry)
            basename = os.path.basename(curr_path).removesuffix(".csv")

            number, prefix, duration = utils.extract_number_and_prefix(basename)
            ms.comp_qualities_of_file(filter_dir, entry, number, str(duration))
            pbar.update(1)


def count_csv_files(path: str):
    """
    Counts the number of CSV files in a directory.

    Args:
        path (str): The directory path.

    Returns:
        int: The number of CSV files.
    """
    return sum(1 for _, _, files in os.walk(path) for file in files if file.endswith('.csv'))
