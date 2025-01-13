from scipy.spatial.distance import cosine
import pandas as pd
import numpy as np
from tqdm import tqdm


def similarity_jaccard(record1, record2):
    record1 = set(record1)
    record2 = set(record2)
    return len(record1 & record2) / len(record1 | record2)
    # print(f"calculating jaccard")
    # set1, set2 = set(record1), set(record2)
    # return len(set1.intersection(set2)) / len(set1.union(set2))
def similarity(record1, record2):
    return similarity_jaccard(record1, record2)

def calculate_sparsity(event_log, threshold=0.5):
    # acf(event_log)
    event_log = event_log[["case_id", "activity", "timestamp"]].copy()
    # next_try(event_log)
    again_next(event_log)
    # sparsity_scores = []
    # l = len(event_log) * len(event_log) -1
    # with tqdm(total=l, desc="Filtering files", unit="record") as pbar:
    #     similarities = []
    #     for i, record in event_log.iterrows():
    #             for j, other_record in event_log.iterrows():
    #                 if i != j:
    #                     similarities.append(similarity(record, other_record))
    #                     pbar.update()
    #     # Prüfen, ob ähnliche Nachbarn existieren
    #     sparsity_scores.append(np.sum(np.array(similarities) > threshold))
    #     print(f"Sparsity: {sparsity_scores}")
    #     return sparsity_scores



def next_try(event_log):
    # Gruppieren von Aktivitäten je Trace
    traces = event_log.groupby('case_id')['activity'].apply(list).reset_index()
    traces.columns = ['case_id', 'Activity Sequence']

    traces['Activity Sequence'] = traces['Activity Sequence'].apply(tuple)

    # Frequenz der Traces berechnen
    traces['Frequency'] = traces['Activity Sequence'].map(traces['Activity Sequence'].value_counts())

    # Einzigartigkeit berechnen: Inverse der Frequenz
    traces['Uniqueness'] = 1 / traces['Frequency']

    # Kombination aus Aktivität und Zeitstempel
    event_log['Attribute Combo'] = event_log[['activity']].apply(tuple, axis=1)

    # Häufigkeit der Attributkombinationen berechnen
    combo_frequency = event_log['Attribute Combo'].value_counts()

    # Einzigartigkeit basierend auf Attribut-Kombinationen
    event_log['Combo Uniqueness'] = event_log['Attribute Combo'].map(lambda x: 1 / combo_frequency[x])

    # Beispiel: Ähnlichkeiten berechnen (Paarweise für alle Traces)
    similarities = []
    for i, trace1 in enumerate(traces['Activity Sequence']):
        for j, trace2 in enumerate(traces['Activity Sequence']):
            if i < j:  # Keine Duplikate
                similarity = calculate_similarity_traces_levenshtein(trace1, trace2)
                similarities.append({'Trace 1': i, 'Trace 2': j, 'Similarity': similarity})

    similarities_df = pd.DataFrame(similarities)

    # Risiko berechnen: Anzahl der ähnlichen Traces pro Trace
    traces['Risk'] = traces['Activity Sequence'].apply(
        lambda x: sum(calculate_similarity_traces_levenshtein(x, y) > 0.4 for y in traces['Activity Sequence'])
    )

    import matplotlib.pyplot as plt

    # Verteilung der Einzigartigkeit
    plt.hist(traces['Uniqueness'], bins=10, color='blue', alpha=0.7)
    plt.title('Verteilung der Trace-Einzigartigkeit')
    plt.xlabel('Uniqueness')
    plt.ylabel('Frequency')
    plt.savefig("/home/fabian/Github/Bachelor_thesis_z_filter/evaluation/testerstest2")
    plt.show()

    # Verteilung des Re-Identifikationsrisikos
    plt.hist(traces['Risk'], bins=10, color='red', alpha=0.7)
    plt.title('Verteilung des Re-Identifikationsrisikos')
    plt.xlabel('Risk')
    plt.ylabel('Frequency')
    plt.savefig("/home/fabian/Github/Bachelor_thesis_z_filter/evaluation/testerstest")
    plt.show()


from Levenshtein import distance as levenshtein_distance
def calculate_similarity_traces_levenshtein(trace1, trace2):
    return 1 -levenshtein_distance(trace1, trace2) / max(len(trace1), len(trace2))

def acf(event_log):
    log = event_log[["case_id", "activity", "timestamp"]].copy()


    # log['Combo Hash'] = log.apply(lambda row: hash(tuple(row)), axis=1)
    frequency_table = log.value_counts(subset=['activity', 'timestamp']).reset_index()
    frequency_table.columns = ['activity', 'timestamp', 'Frequency']
    frequency_table['Uniqueness'] = 1 / frequency_table['Frequency']

    # Join der Einzigartigkeit zurück zum Event Log
    log = log.merge(
        frequency_table[['activity', 'timestamp', 'Uniqueness']],
        on=['activity', 'timestamp'],
        how='left'
    )

    # Risiko pro Fall aggregieren
    case_risk = log.groupby("case_id")['Uniqueness'].mean().reset_index()
    case_risk.columns = ['Case ID', 'Re-identification Risk']

    import matplotlib.pyplot as plt

    # Verteilung des Re-Identifikationsrisikos
    plt.hist(case_risk['Re-identification Risk'], bins=20, color='blue', alpha=0.7)
    plt.title("Re-identification Risk Distribution")
    plt.xlabel("Risk")
    plt.ylabel("Frequency")
    # plt.show()
    plt.savefig("/home/fabian/Github/Bachelor_thesis_z_filter/evaluation/testerstest")


def again_next(event_log):
    # Beispiel: Teilmenge von Attributen
    event_log['Auxiliary Info'] = event_log[['activity', 'case_id']].apply(tuple, axis=1)
# Frequenz der Hilfsinformationen
    aux_frequency = event_log['Auxiliary Info'].value_counts()

# Risiko basierend auf Kandidatenanzahl
    event_log['Risk'] = event_log['Auxiliary Info'].map(lambda x: 1 / aux_frequency[x])

    # Anteil eindeutig identifizierbarer Datensätze
    total_records = len(event_log)
    unique_records = sum(aux_frequency == 1)
    de_anonymization_risk = unique_records / total_records
    print(f"De-Anonymization Risk: {de_anonymization_risk:}")

def sparsity_list(similiarity_matrix):
    similiarity_prob = []
    for i, row in enumerate(similiarity_matrix):
        v_row = row[row != -1]
        similiarity_prob.append(np.sum(v_row) / (len(row)))
    return similiarity_prob

def calculate_sim_matrix(event_log, sim_method):
    event_log = event_log[["case_id", "activity", "timestamp"]].copy()
    traces = event_log.groupby('case_id')['activity'].apply(list).reset_index()
    traces.columns = ['case_id', 'Activity Sequence']

    # Initialisierung der quadratischen Matrix
    num_traces = len(traces)
    similarity_matrix = np.zeros((num_traces, num_traces))

    # Berechnung der Ähnlichkeiten und Eintragen in die Matrix
    for i, trace1 in enumerate(traces['Activity Sequence']):
        for j, trace2 in enumerate(traces['Activity Sequence']):
            if i == j:
                similarity_matrix[i, j] = -1.0  # Diagonale mit 1.0 füllen
            elif i < j:  # Nur obere Hälfte berechnen (wegen Symmetrie)
                sim = sim_method(trace1, trace2)
                # similarity = calculate_similarity_traces_levenshtein(trace1, trace2)
                similarity_matrix[i, j] = sim
                similarity_matrix[j, i] = sim  # Symmetrisch eintragen

    return similarity_matrix

def log_sparsity_mean(sparsity_list):
    print(sum(sparsity_list)/len(sparsity_list))

def sparsity_pair(sparsity_list, epsilon):
    prop = []
    for e in sparsity_list:
        if e > epsilon:
            prop.append(e)
    print(sum(prop)/ (len(prop)**2) if len(prop) > 0 else 1)

def method1(event_log):
    similarity_matrix = calculate_sim_matrix(event_log, similarity_jaccard)
    print(similarity_matrix)
    l = sparsity_list(similarity_matrix)
    print(f"Minima: {min(l)}")
    print(f"Maxima: {max(l)}")
    log_sparsity_mean(l)
    sparsity_pair(l, 0.5)

    similarity_matrix = calculate_sim_matrix(event_log, calculate_similarity_traces_levenshtein)
    print(similarity_matrix)
    l = sparsity_list(similarity_matrix)
    print(f"Minima: {min(l)}")
    print(f"Maxima: {max(l)}")
    log_sparsity_mean(l)
    sparsity_pair(l, 0.5)


from collections import defaultdict


def calculate_trace_uniqueness(event_log, points_per_trace):
    """
    Calculate the re-identification risk based on trace uniqueness.

    Parameters:
        event_log (pd.DataFrame): Event log with columns ['case_id', 'activity', 'timestamp'].
        points_per_trace (int): Number of points (activity-timestamp pairs) known to the adversary.

    Returns:
        float: Uniqueness score (proportion of unique traces).
    """
    # Step 1: Prepare the trace representation
    trace_dict = defaultdict(list)
    for _, row in event_log.iterrows():
        trace_dict[row['case_id']].append((row['activity'], row['timestamp']))

    # Step 2: Generate all subsets of points_per_trace for each trace
    from itertools import combinations
    trace_subsets = defaultdict(list)
    for case_id, trace in trace_dict.items():
        subsets = list(combinations(trace, points_per_trace))
        trace_subsets[case_id] = subsets

    # Step 3: Count the occurrences of each subset in the entire dataset
    subset_counts = defaultdict(int)
    for subsets in trace_subsets.values():
        for subset in subsets:
            subset_counts[tuple(sorted(subset))] += 1

    # Step 4: Identify unique traces
    unique_count = 0
    total_traces = len(trace_dict)
    for subsets in trace_subsets.values():
        for subset in subsets:
            if subset_counts[tuple(sorted(subset))] == 1:
                unique_count += 1
                break  # If one subset is unique, the trace is unique
    return unique_count / total_traces


# Example event log
# data = {
#     "case_id": [1, 1, 1, 2, 2, 3, 3, 3],
#     "activity": ["A", "B", "C", "A", "C", "A", "B", "D"],
#     "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03",
#                   "2023-01-01", "2023-01-03", "2023-01-01",
#                   "2023-01-02", "2023-01-04"]
# }
# event_log = pd.DataFrame(data)



def start2(event_log):
    event_log = event_log[["case_id", "activity", "timestamp"]].copy()
    # event_log['Auxiliary Info'] = event_log[['activity',"timestamp"]].apply(tuple, axis=1)
    # candidates = event_log['Auxiliary Info'].value_counts()
    # print(candidates)
    # event_log['Risk'] = event_log['Auxiliary Info'].map(lambda x: 1 / candidates[x])
    # # Gesamtrisiko des Logs
    # log_risk = event_log['Risk'].mean()
    # print(f"Gesamtrisiko des Event Logs: {log_risk:.4f}")
    # Compute the uniqueness score for 2 known points per trace
    uniqueness_score = calculate_trace_uniqueness(event_log, points_per_trace=2)
    print(f"Uniqueness Score: {uniqueness_score:.2f}")


if __name__ == "__main__":
    from compute import import_csv
    path1 = "/home/fabian/Github/Bachelor_thesis_z_filter/evaluation/results_filtering/Sepsis_Cases-Event_Log/Sepsis_Cases-Event_LogZ1PT3600S.csv"
    frame = import_csv(path1)
    print(path1)
    start2(frame)
    # method1(frame)
    # path1 = "/home/fabian/Github/Bachelor_thesis_z_filter/evaluation/results_filtering/Sepsis_Cases-Event_Log/Sepsis_Cases-Event_LogZ10PT3600S.csv"
    # frame = import_csv(path1)
    # print(path1)
    #
    # method1(frame)
    #
    # path1 = "/home/fabian/Github/Bachelor_thesis_z_filter/evaluation/results_filtering/Sepsis_Cases-Event_Log/Sepsis_Cases-Event_LogZ20PT3600S.csv"
    # frame = import_csv(path1)
    # print(path1)
    #
    # method1(frame)

