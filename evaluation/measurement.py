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
from csv2auto import convert_csv2auto as csv2auto
from re_ident import risk_re_ident_quant
from tqdm import tqdm


class Measurement:

    def __init__(self, result_path, result_name):
        # log used for comparison
        self.unfiltered_log = None
        # init result dicts
        self.results = self.init_dict()
        # original basename
        self.basename_orig = ''
        # path where to print results
        self.result_path = result_path
        self.result_name = result_name

    def init_dict(self):
        return {
            "Z": [],
            "dT": [],
            "Fitness": [],
            "Fitness_cmp": [],
            "Precision": [],
            "Precision_cmp": [],
            "Generality": [],
            "Generality_cmp": [],
            "Simplicity": [],
            "RISK_AT_0.3": [],
            "RISK_AT_0.6": [],
            "RISK_AT_0.9": [],
            "RISK_A_0.3": [],
            "RISK_A_0.6": [],
            "RISK_A_0.9": [],
        }

    def set_unfiltered_log(self, directory, basename):
        path = os.path.join(directory, basename)
        log = compute.import_csv(path)
        self.unfiltered_log = log
        self.basename_orig = basename

    def fitness(self, event_log, net, im, fm):
        fitness = pm4py.fitness_alignments(event_log, net, im, fm, multi_processing=True)
        # print(f"fitness: {fitness}")
        return fitness['log_fitness']

    def simplicity(self, net, im, fm):
        simplicity = pm4py.simplicity_petri_net(net, im, fm)
        # print(f"simplicity: {simplicity}")
        return simplicity

    def precision(self, event_log, net, im, fm):
        precision = pm4py.precision_alignments(event_log, net, im, fm, multi_processing=True)
        # print(f"Precision: {precision}")
        return precision

    def generality(self, log, net, im, fm):
        generality = pm4py.generalization_tbr(log, net, im, fm)
        # print(f"Generality: {generality}")
        return generality

    def __metrics_utility_log(self, net, im, fm, log, z_val, dt_val):
        self.results["Z"].append(z_val)
        self.results["dT"].append(dt_val)
        with ProcessPoolExecutor() as executor:
            sim = executor.submit(self.simplicity, net, im, fm)
            gen = executor.submit(self.generality, log, net, im, fm)
            fit = executor.submit(self.fitness, log, net, im, fm)
            prec = executor.submit(self.precision, log, net, im, fm)
            #

            if self.unfiltered_log is not None:
                fit_cmp = executor.submit(self.fitness, self.unfiltered_log, net, im, fm)
                gen_cmp = executor.submit(self.generality, self.unfiltered_log, net, im, fm)
                prec_cmp = executor.submit(self.precision, self.unfiltered_log, net, im, fm)

                fit = fit.result()
                gen = gen.result()
                prec = prec.result()

                self.results['Fitness_cmp'].append(fit_cmp.result())
                self.results["Generality_cmp"].append(gen_cmp.result())
                self.results['Precision_cmp'].append(prec_cmp.result())
            else:
                fit = fit.result()
                gen = gen.result()
                prec = prec.result()
                self.results['Fitness_cmp'].append(fit)
                self.results["Generality_cmp"].append(gen)
                self.results['Precision_cmp'].append(prec)

            self.results['Simplicity'].append(sim.result())
            self.results['Fitness'].append(fit)
            self.results['Precision'].append(prec)
            self.results['Generality'].append(gen)

    def __metrics_privacy_file(self, path: str, file: str):
        path, file = csv2auto(path + "/", file, constants.PATH_TMP)
        with ProcessPoolExecutor() as executor:
            risk_at = executor.submit(risk_re_ident_quant, path + "/", file, projection='A')
            risk_a = executor.submit(risk_re_ident_quant, path + "/", file, projection='E')
            risk_at = risk_at.result()
            risk_a = risk_a.result()
        self.results['RISK_AT_0.3'].append(risk_at[0][1])
        self.results['RISK_AT_0.6'].append(risk_at[1][1])
        self.results['RISK_AT_0.9'].append(risk_at[2][1])

        self.results['RISK_A_0.3'].append(risk_a[0][1])
        self.results['RISK_A_0.6'].append(risk_a[1][1])
        self.results['RISK_A_0.9'].append(risk_a[2][1])

    def comp_qualities_of_file(self, path, file, z_val, dt_val):
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
        # utilize metrics for privacy on log
        self.__metrics_privacy_file(path, file)

        # utilize metrics for privacy
        file_path = os.path.join(path, file)

        # import event log into pandas df
        log_df = compute.import_csv(file_path)
        # path for corresponding petri net
        p = file_path.removesuffix(".csv") + ".pnml"
        # discover petri net
        net, im, fm = pm4py.read_pnml(p)

        # utilize metrics for utility (quality dimensions)
        self.__metrics_utility_log(net, im, fm, log_df, z_val, dt_val)
        self.write_to_csv()

    def __set_dict(self, dict):
        self.results = dict

    def write_to_csv(self):
        """
            Writes member hashmap into a csv-file at the path provided at construction.

            basename: name of the csv file
            """
        try:
            filtered_hashmap = self.sort_dict_according_to_z()
            # only consider keys with value-list-size greater 0
            # Sicherstellen, dass alle Listen in der Hashmap die gleiche Länge haben
            lengths = [len(v) for v in filtered_hashmap.values()]
            if len(set(lengths)) > 1:
                raise ValueError("Entries arent equal long!")
            print(filtered_hashmap)
            # Schreiben der Hashmap in die CSV-Datei
            with open(f"{self.result_path}/{self.result_name}.csv", mode='w', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=filtered_hashmap.keys())
                writer.writeheader()
                rows = [dict(zip(filtered_hashmap.keys(), row)) for row in zip(*filtered_hashmap.values())]
                writer.writerows(rows)

        except Exception as e:
            print(f"Error while writing hashmap to csv file: {e}")

    def clear(self):
        self.results.clear()
        self.results = self.init_dict()

    def sort_dict_according_to_z(self):
        filtered_hashmap = {k: v for k, v in self.results.items() if len(v) > 0}
        sorted_indices = sorted(range(len(filtered_hashmap["Z"])), key=lambda i: filtered_hashmap["Z"][i])
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
                try:
                    log = compute.import_csv(str(path))
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
    :param directory: directory to be traversed, dont't
    :param abstracted: True if only time_abstracted files should be considered, else False
    :return:
    """

    for entry in os.listdir(directory):
        # entry in a directory, should include results_filtering_classic /improved and the original file as well as
        # an abstracted one (if necessary) and a petri net for every file
        full_path = os.path.join(directory, entry)
        # if os.path.isfile(full_path):
        if os.path.isdir(full_path):
            with tqdm(total=(count_csv_files(directory) - 1) / 4,
                      desc=os.path.basename(directory) if not abstracted else os.path.basename(directory)+'_abstracted',
                      unit='file') as pbar:
                # prepare Measurement object
                # prepare file path to csv file
                # distinguish between abstracted (generalized timestamps) files and `normal' ones
                if abstracted:
                    b_name = os.path.basename(directory).removesuffix('.csv') + constants.ABSTRACTED_NAME_SUFFIX
                else:
                    b_name = str(os.path.basename(directory)).removesuffix(".csv")
                basename = b_name + ".csv"
                ms = Measurement(os.path.join(os.getcwd(), "tmp/"), b_name + str(entry))

                # Compute qualitites of unfiltered / base event log

                ms.comp_qualities_of_file(directory, basename, 0, "base")
                pbar.update(1)
                ms.set_unfiltered_log(directory, basename)
                # measure filtered logs and nets
                measure_other_nets(full_path, ms, abstracted, pbar)

                # write results dict to csv file
                ms.write_to_csv()


def traverse(path):

    # ProcessPoolExecutor für parallele Ausführung
    with ProcessPoolExecutor() as executor:

        futures = []
        for entry in os.listdir(path):
            curr = os.path.join(path, entry)
            if os.path.isdir(curr):
                # Task zur Verarbeitung des Verzeichnisses parallel hinzufügen
                futures.append(executor.submit(traverse_and_measure, curr, True))
                futures.append(executor.submit(traverse_and_measure, curr, False))

        # Wait for every task
        for future in futures:
            future.result()


def measure_other_nets(full_path, ms, abstracted: bool, pbar):
    for entry in os.listdir(str(full_path)):
        p = os.path.join(full_path, entry)
        if os.path.isfile(p) and os.path.basename(p).endswith(".csv"):
            if abstracted and not entry.__contains__(constants.ABSTRACTED_NAME_SUFFIX):
                continue
            elif not abstracted and entry.__contains__(constants.ABSTRACTED_NAME_SUFFIX):
                continue
            curr_path = os.path.join(full_path, entry)
            basename = os.path.basename(curr_path).removesuffix(".csv")

            number, prefix, duration = compute.extract_number_and_prefix(basename)
            ms.comp_qualities_of_file(full_path, entry, number, str(duration))
            pbar.update(1)


def count_csv_files(path: str):
    count = 0
    for _, _, files in os.walk(path):
        for file in files:
            if file.endswith('.csv'):
                count += 1
    return count


if __name__ == "__main__":

    directory = './results/Hospital_log/Hospital_log.csv'
    # log = compute.import_csv(directory)
    #
    # net, im, fm = pm4py.discover_petri_net_inductive(log, multi_processing=True)
    # pm4py.view_petri_net(net, im, fm)


    # traverse_and_build_petri_nets(directory)
    # traverse()
    # with ProcessPoolExecutor() as executor:
    #     futures = [
    #         executor.submit(traverse_and_measure, directory, False),
    #                executor.submit(traverse_and_measure, directory, True)
    #                ]

    #     for f in futures:
    #         f.result()
