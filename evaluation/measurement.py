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


def discover_models(log):
    tree = pm4py.discover_process_tree_inductive(log)
    net, im, fm = pt_converter.apply(tree)
    return tree, (net, im, fm)


def visualize_petri(net, im, fm):
    gviz_petri = pn_visualizer.apply(net, im, fm)
    pn_visualizer.view(gviz_petri)


def visualize_process_tree(tree):
    gviz_tree = pt_visualizer.apply(tree)
    pt_visualizer.view(gviz_tree)


def init_dict():
    return {
        "Fitness": [],
        "Precision": [],
        "Generalization": [],
        "Simplicity": [],
        "Simplicity_EXTENDED_CARDOSO": [],
        "Simplicity_EXTENDED_CYCLOMATIC": [],
        "AECS": []
    }


def measure_fitness(o_log, net, im, fm):
    # Fitness Evaluation
    fitness = replay_fitness_algorithm.apply(o_log,
                                             net,
                                             im,
                                             fm,
                                             variant=replay_fitness_algorithm.Variants.TOKEN_BASED)
    # print(f"Fitness: {fitness['log_fitness']}")
    print(f"{fitness}")
    # print(replay_fitness_algorithm.evaluate(fitness)) # nicht nötig, bekommt man schon durch den call oben
    return fitness


def measure_other_simplicities(quality_dict, net, z, t):
    quality_dict["Simplicity_EXTENDED_CARDOSO"].append((z, t, simplicity_algorithm.apply(net, variant=EXTENDED_CARDOSO)))
    quality_dict["Simplicity_EXTENDED_CYCLOMATIC"].append((z, t, simplicity_algorithm.apply(net, variant=EXTENDED_CYCLOMATIC)))


def measure_simplicity(net):
    # Simplicity Evaluation

    simplicity = simplicity_algorithm.apply(net)
    print(f"Simplicity: {simplicity}")
    return simplicity


def measure_generality(o_log, net, im, fm):
    # Generalization Evaluation
    generality = generalization_algorithm.apply(o_log, net, im, fm)
    print(f"Generalization: {generality}")
    return generality


def measure_precision(log, net, im, fm):
    # Precision Evaluation
    precision = precision_algorithm.apply(log, net, im, fm, variant=variants.etconformance_token)
    print(f"Precision: {precision}")
    return precision


import pandas as pd


def calculate_aecs(event_log, quasi_identifiers):
    """
    Berechnet die Average Equivalence Class Size (AECS).

    Parameters:
    - event_log: Pandas DataFrame mit Event-Log-Daten
    - quasi_identifiers: Liste der Spalten, die als quasi-identifiers dienen (z.B. ['activity', 'source'])

    Returns:
    - aecs: Durchschnittliche Größe der Äquivalenzklassen
    """
    # Gruppen basierend auf quasi-identifiers
    equivalence_classes = event_log.groupby(quasi_identifiers)

    # Berechnung der Größe jeder Äquivalenzklasse
    class_sizes = equivalence_classes.size()
    # AECS ist der Durchschnitt der Klassengrößen
    aecs = class_sizes.mean()

    return aecs

#
# # Beispiel-Daten
# data = {
#     'case_id': [1, 1, 2, 2, 3, 3, 4, 4],
#     'activity': ['A', 'B', 'A', 'B', 'A', 'C', 'A', 'B'],
#     'source': ['doctor1', 'doctor1', 'doctor1', 'doctor1', 'doctor2', 'doctor2', 'doctor2', 'doctor2']
# }
# event_log = pd.DataFrame(data)
#
# # Berechnung der AECS für die quasi-identifiers 'activity' und 'source'
# aecs = calculate_aecs(event_log, ['activity', 'source'])
# print(f"Average Equivalence Class Size (AECS): {aecs}")
