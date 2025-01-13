import csv
from priv_metrik import calculate_sparsity

import pm4py
from pm4py.algo.evaluation.simplicity.algorithm import EXTENDED_CARDOSO, EXTENDED_CYCLOMATIC
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness_algorithm
from pm4py.algo.evaluation.precision import algorithm as precision_algorithm
from pm4py.algo.evaluation.generalization import algorithm as generalization_algorithm
from pm4py.algo.evaluation.simplicity import algorithm as simplicity_algorithm
from pm4py.objects.conversion.process_tree import converter as pt_converter
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.process_tree import visualizer as pt_visualizer

from pm4py.algo.evaluation.precision import variants
from pm4py.visualization.bpmn import visualizer as bpmn_visualizer

from compute import import_csv


class Measurement:

    def __init__(self, result_path):
        self.unfiltered_log = None
        self.quality_dict = self.init_dict()
        self.result_path = result_path

    def init_dict(self):
        return {
            "Fitness": [],
            "Precision": [],
            "Generality": [],
            "Simplicity": [],
            "Simplicity_EXTENDED_CARDOSO": [],
            "Simplicity_EXTENDED_CYCLOMATIC": [],
            "AECS": []
        }

    def set_unfiltered_log(self, path):
        #TODO: just parse the xes log using the rust parser into a csv file and then compute the qualities, don't user the simulator
        log = pm4py.read_xes(path)
        self.unfiltered_log = log

    def fitness(self, event_log, net, initial_m, final_m, z_val, dt_val):
        fitness = replay_fitness_algorithm.apply(event_log,
                                                 net,
                                                 initial_m,
                                                 final_m,
                                                 variant=replay_fitness_algorithm.Variants.TOKEN_BASED)
        print(f"fitness: {fitness}")
        self.quality_dict["Fitness"].append((z_val, dt_val, fitness['log_fitness']))

    def simplicity(self, net, z_val, dt_val):
        simplicity = simplicity_algorithm.apply(net)
        print(f"simplicity: {simplicity}")
        self.quality_dict["Simplicity"].append((z_val, dt_val, simplicity))

    def precision(self, event_log, net, im, fm, z_val, dt_val):
        precision = precision_algorithm.apply(event_log, net, im, fm, variant=variants.etconformance_token)
        print(f"Precision: {precision}")
        self.quality_dict["Precision"].append((z_val, dt_val, precision))

    def generality(self, event_log, net, im, fm, z_val, dt_val):
        generality = generalization_algorithm.apply(event_log, net, im, fm)
        print(f"Generality: {generality}")
        self.quality_dict["Generality"].append((z_val, dt_val, generality))

    def calculate_aecs(self, event_log, quasi_identifiers, z_val, dt_val):
        # group based on quasi-identifiers
        equivalence_classes = event_log.groupby(quasi_identifiers)

        # Calculate size of every equivalence class
        class_sizes = equivalence_classes.size()
        aecs = class_sizes.mean()
        print(f"AECS: {aecs}")
        # AECS is the average of all classes
        self.quality_dict["AECS"].append((z_val, dt_val, aecs))

    def __compute_qualities(self, log, z_val, dt_val, quasi_identifiers):
        # Calculate AECS for the complete log
        self.calculate_aecs(log, quasi_identifiers, z_val, dt_val)

        # Discover the Petri Net model from the log
        net, im, fm = pm4py.discover_petri_net_inductive(log)

        # Evaluate simplicity of model
        self.simplicity(net, z_val, dt_val)

        # Evaluate Model on Discovery Log
        self.fitness(log, net, im, fm, z_val, dt_val)
        self.precision(log, net, im, fm, z_val, dt_val)
        if self.unfiltered_log is None:
            return
        self.generality(self.unfiltered_log, net, im, fm, z_val, dt_val)

    def comp_qualities_of_file(self, file_path, z_val, dt_val, quasi_identifiers=["case_id", "activity"]):
        """
        Evaluates the quality of a discovered Petri net model based on a filtered event log,
        incorporating validation.

        Args:
            file_path (str): Path to the event log CSV file.
            z_val (int): z-anonymity value.
            dt_val (str): Delta threshold for anonymization.
            quasi_identifiers (list): List of quasi-identifiers used for filtering (default is ["activity"]).
        """
        # Import event log
        log = import_csv(file_path)  # import event log
        calculate_sparsity(log)
        # Calculate AECS for the complete log
        self.__compute_qualities(log, z_val, dt_val, quasi_identifiers)

    def __set_dict(self, dict):
        self.quality_dict = dict

    def write_to_csv(self, basename):
        """
            Writes member hashmap into a csv-file at the path provided at construction.

            basename: name of the csv file
            """
        try:
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


if __name__ == "__main__":
    ms = Measurement("/home/fabian/Github/Bachelor_thesis_z_filter/evaluation/results")
    path = "/home/fabian/TU_DRESDEN/PrivateMine/SOURCED/data/Sepsis_Cases-Event_Log.xes"
    ms.set_unfiltered_log(path)
    ms.comp_qualities_of_file("/home/fabian/Github/Bachelor_thesis_z_filter/evaluation/results_filtering/Sepsis_Cases-Event_Log/Sepsis_Cases-Event_LogZ1PT3600S.csv", 0, "0s")
    ms.comp_qualities_of_file(
        "/home/fabian/Github/Bachelor_thesis_z_filter/evaluation/results_filtering/Sepsis_Cases-Event_Log/Sepsis_Cases-Event_LogZ10PT3600S.csv",
        10, "3600s")



# def measure_other_simplicities(quality_dict, net, z, t):
#     '''
#     Not necessary!!
#     Args:
#         quality_dict: dictionary containing quality measure
#         net:
#         z:
#         t:
#
#     Returns:
#
#     '''
#     quality_dict["Simplicity_EXTENDED_CARDOSO"].append(
#         (z, t, simplicity_algorithm.apply(net, variant=EXTENDED_CARDOSO)))
#     quality_dict["Simplicity_EXTENDED_CYCLOMATIC"].append(
#         (z, t, simplicity_algorithm.apply(net, variant=EXTENDED_CYCLOMATIC)))
