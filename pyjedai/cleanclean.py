import argparse
import json
from itertools import product

import data_cleaning
import data_reading
from blocking import token_blocking
import block_purging
import block_cleaning
from comparison_cleaning import weighted_edge_pruning
import entity_matching
from entity_clustering import unique_mapping_clustering

def main():
    parser = argparse.ArgumentParser(description='Entity Resolution with optional blocking attributes')
    parser.add_argument('--file1', required=True, help='path to file1')
    parser.add_argument('--file2', required=True, help='path to file2')
    parser.add_argument('--attr1', required=False, help='comma seperated list of attributes to block for Dataset 1')
    parser.add_argument('--attr2', required=False, help='comma seperated list of attributes to block for Dataset 1')
    parser.add_argument('--output', required=True, help='output path for EM_JSON')

    args = parser.parse_args()

    data = data_reading.read(args.file1, args.file2)

    data_cleaning.clean(data)

    if not (args.attr1 and args.attr2):
        attributes1 = []
        attributes2 = []
    else:
        attributes1 = [attr.strip() for attr in args.attr1.split(',')]
        attributes2 = [attr.strip() for attr in args.attr2.split(',')]

    blocks = token_blocking.block(data, attributes1, attributes2)
    cleaned_blocks = block_purging.purge(blocks, data)
    filtered_blocks = block_cleaning.clean(cleaned_blocks, data)
    candidate_pairs_blocks = weighted_edge_pruning.clean(filtered_blocks, data)


    # Matching
    pairs_graph = entity_matching.match(candidate_pairs_blocks, data)

    # Clustering
    #clusters = unique_mapping_clustering.cluster(pairs_graph, data)

    results = []

    for node1, node2, data_dict in pairs_graph.edges(data=True):
        entry = {
            "id_1": node1,
            "id_2": node2,
            "score": float(data_dict.get('weight', 1.0)),
            "id_type": type(node1).__name__
        }
        results.append(entry)

    json_output = {"matches": results, "blocks": [], "clusters": []}

    with open(args.output, 'w', encoding='utf-8') as json_file:
        json.dump(json_output, json_file, ensure_ascii=False, indent=4)

    print(f"Saved EM_JSON to: {args.output}")

if __name__ == '__main__':
    main()

