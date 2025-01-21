import csv
import os
import constants
from concurrent.futures import ProcessPoolExecutor

import pandas.errors

import compute

import pm4py
from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness_algorithm
from pm4py.algo.evaluation.precision import algorithm as precision_algorithm
from pm4py.algo.evaluation.generalization import algorithm as generalization_algorithm
from pm4py.algo.evaluation.simplicity import algorithm as simplicity_algorithm
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.process_tree import visualizer as pt_visualizer
from pm4py.algo.evaluation.precision import variants
from compute import import_csv
from csv2auto import convert_csv2auto as csv2auto
from re_ident import risk_re_ident_quant


class Measurement:

    def __init__(self, result_path):
        self.unfiltered_log = None
        self.quality_dict = self.init_dict()
        self.result_path = result_path

    def init_dict(self):
        return {
            "Z": [],
            "dT": [],
            "Fitness": [],
            "Precision": [],
            "Generality": [],
            "Simplicity": [],
            "RISK_A": [],
            "RISK_E": [],
        }

    def set_unfiltered_log(self, path):
        # TODO: just parse the xes log using the rust parser into a csv file and then compute the qualities, don't user the simulator
        log = pm4py.read_xes(path)
        self.unfiltered_log = log

    def fitness(self, event_log, net, initial_m, final_m):
        fitness = replay_fitness_algorithm.apply(event_log,
                                                 net,
                                                 initial_m,
                                                 final_m,
                                                 variant=replay_fitness_algorithm.Variants.TOKEN_BASED)
        print(f"fitness: {fitness}")
        self.quality_dict["Fitness"].append(fitness['log_fitness'])

    def simplicity(self, net):
        simplicity = simplicity_algorithm.apply(net)
        print(f"simplicity: {simplicity}")
        self.quality_dict["Simplicity"].append(simplicity)

    def precision(self, event_log, net, im, fm):
        precision = precision_algorithm.apply(event_log, net, im, fm, variant=variants.etconformance_token)
        print(f"Precision: {precision}")
        self.quality_dict["Precision"].append(precision)

    def generality(self, event_log, net, im, fm):
        generality = generalization_algorithm.apply(event_log, net, im, fm)
        print(f"Generality: {generality}")
        self.quality_dict["Generality"].append(generality)

    def calculate_aecs(self, event_log, quasi_identifiers, ):
        # group based on quasi-identifiers
        equivalence_classes = event_log.groupby(quasi_identifiers)

        # Calculate size of every equivalence class
        class_sizes = equivalence_classes.size()
        aecs = class_sizes.mean()
        print(f"AECS: {aecs}")
        # AECS is the average of all classes

    def compute_qualities(self, net, im, fm, log, z_val, dt_val, quasi_identifiers):
        # Discover the Petri Net model from the log
        # net, im, fm = pm4py.discover_petri_net_inductive(log)

        # pm4py.write_pnml(net, im, fm, )

        # Evaluate simplicity of model

        self.quality_dict["Z"].append(z_val)
        self.quality_dict["dT"].append(dt_val)
        self.simplicity(net)

        # Evaluate Model on Discovery Log
        self.fitness(log, net, im, fm)
        self.precision(log, net, im, fm)

        self.generality(log, net, im, fm)

    def comp_qualities_of_file(self, path, file, z_val, dt_val, quasi_identifiers=["case_id", "activity"]):
        """
        Evaluates the quality of a discovered Petri net model based on a filtered event log,
        incorporating validation.

        Args:
            path (str): Path to the folder of the event log CSV file.
            file (str): Name of the event log CSV file.
            z_val (int): z-anonymity value.
            dt_val (str): Delta threshold for anonymization.
            quasi_identifiers (list): List of quasi-identifiers used for filtering (default is ["activity"]).
        """
        # Import event log
        file_path = os.path.join(path, file)
        log = import_csv(file_path)  # import event log

        p = file_path.removesuffix(".csv") + ".pnml"
        net, im, fm = pm4py.read_pnml(p)
        path, file = csv2auto(path + "/", file, "/home/fabian/Github/Bachelor_thesis_z_filter/tmp/")
        self.quality_dict['RISK_A'].append(risk_re_ident_quant(path + "/", file))
        self.quality_dict['RISK_E'].append(risk_re_ident_quant(path + "/", file, projection='E'))
        # self.calculate_aecs(log, z_val, dt_val, quasi_identifiers)
        self.compute_qualities(net, im, fm, log, z_val, dt_val, quasi_identifiers)

    def __set_dict(self, dict):
        self.quality_dict = dict

    def write_to_csv(self, basename):
        """
            Writes member hashmap into a csv-file at the path provided at construction.

            basename: name of the csv file
            """
        try:
            self.sort_dict_according_to_z()
            # only consider keys with value-list-size greater 0
            filtered_hashmap = {k: v for k, v in self.quality_dict.items() if len(v) > 0}
            # Sicherstellen, dass alle Listen in der Hashmap die gleiche Länge haben
            lengths = [len(v) for v in filtered_hashmap.values()]
            if len(set(lengths)) > 1:
                raise ValueError("Entries arent equal long!")

            # Schreiben der Hashmap in die CSV-Datei
            with open(f"{self.result_path}/{basename}.csv", mode='w', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=filtered_hashmap.keys())
                writer.writeheader()
                rows = [dict(zip(filtered_hashmap.keys(), row)) for row in zip(*filtered_hashmap.values())]
                writer.writerows(rows)

        except Exception as e:
            print(f"Error while writing hashmap to csv file: {e}")

    def clear(self):
        self.quality_dict.clear()
        self.quality_dict = self.init_dict()

    def sort_dict_according_to_z(self):
        sorted_indices = sorted(range(len(self.quality_dict["Z"])), key=lambda i: self.quality_dict["Z"][i])
        self.quality_dict = {key: [value[i] for i in sorted_indices] for key, value in self.quality_dict.items()}

        print(self.quality_dict)

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


def visualize_petri(net, im, fm):
    gviz_petri = pn_visualizer.apply(net, im, fm)
    pn_visualizer.view(gviz_petri)


def visualize_process_tree(tree):
    gviz_tree = pt_visualizer.apply(tree)
    pt_visualizer.view(gviz_tree)


def traverse_and_build_petri_nets(path):
    for (parent, dirs, files) in os.walk(path):
        for file in files:
            path = os.path.join(parent, file)
            if path.endswith(".csv"):
                if os.path.exists(path.removesuffix(".csv") + '.pnml'):
                    continue
                print(path)
                try:
                    log = import_csv(str(path))
                    # pandas.to_datetime(log['timestamp'], utc=True)
                    net, im, fm = pm4py.discover_petri_net_inductive(log, multi_processing=True)
                    pm4py.write_pnml(net, im, fm, str(path.removesuffix(".csv")))
                except pandas.errors.ParserError as e:
                    print(e)
                except Exception as e:
                    print(e)


def traverse_and_measure(directory: str, abstracted: bool):
    """
    Args:
    :param directory: directory to be traversed
    :param abstracted: True if only time_abstracted files should be considered, else False
    :return:
    """

    for entry in os.listdir(directory):
        full_path = os.path.join(directory, entry)
        # if os.path.isfile(full_path):
        if os.path.isdir(full_path):
            print(f"Traversing this directory: {full_path}")
            # prepare Measurement object
            ms = Measurement("/home/fabian/Github/Bachelor_thesis_z_filter/results_csv")
            # prepare file path to csv file
            b_name = ""
            if abstracted:
                b_name = os.path.basename(directory).removesuffix('.csv') + constants.ABSTRACTED_NAME_SUFFIX
            else:
                b_name = str(os.path.basename(directory)).removesuffix(".csv")
            basename = b_name + ".csv"
            # compute qualities of original csv-file
            ms.comp_qualities_of_file(directory, basename, 1, "base")

            #TODO: weiter durchreichen
            measure_nets(full_path, ms, abstracted)

            ms.write_to_csv(b_name + str(entry))


def traverse():
    path = "/home/fabian/Github/Bachelor_thesis_z_filter/data/data_csv"

    # ProcessPoolExecutor für parallele Ausführung
    with ProcessPoolExecutor() as executor:
        futures = []
        for entry in os.listdir(path):
            curr = os.path.join(path, entry)
            if os.path.isdir(curr):
                print(curr)
                # Task zur Verarbeitung des Verzeichnisses parallel hinzufügen
                futures.append(executor.submit(traverse_and_measure, curr, True))
                futures.append(executor.submit(traverse_and_measure, curr, False))

        # Wait for every task
        for future in futures:
            future.result()


def measure_nets(full_path, ms, abstracted: bool):
    for entry in os.listdir(str(full_path)):
        p = os.path.join(full_path, entry)
        print(p)
        if os.path.isfile(p) and os.path.basename(p).endswith(".csv"):
            if abstracted and not entry.__contains__(constants.ABSTRACTED_NAME_SUFFIX):
                continue
            elif not abstracted and entry.__contains__(constants.ABSTRACTED_NAME_SUFFIX):
                continue
            curr_path = os.path.join(full_path, entry)
            basename = os.path.basename(curr_path).removesuffix(".csv")

            print(curr_path)
            number, prefix, duration = compute.extract_number_and_prefix(basename)
            ms.comp_qualities_of_file(full_path, entry, number, str(duration))


if __name__ == "__main__":
    # traverse_and_build_petri_nets("/home/fabian/Github/Bachelor_thesis_z_filter/data/data_csv/Sepsis Cases - Event Log")
    # ms = Measurement("")
    # traverse()
    traverse_and_measure("/home/fabian/Github/Bachelor_thesis_z_filter/data/data_csv/Sepsis Cases - Event Log", True)
