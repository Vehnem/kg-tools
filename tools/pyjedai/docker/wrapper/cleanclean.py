import argparse
import json

import data_cleaning
import data_reading
from blocking import token_blocking
import block_purging
import block_cleaning
from comparison_cleaning import weighted_edge_pruning
import entity_matching


def main():
    parser = argparse.ArgumentParser(description='Entity Resolution with optional blocking attributes')
    parser.add_argument('--file1', required=True, help='path to file1')
    parser.add_argument('--file2', required=True, help='path to file2')
    parser.add_argument('--attr1', required=False, help='comma seperated list of attributes to block for Dataset 1')
    parser.add_argument('--attr2', required=False, help='comma seperated list of attributes to block for Dataset 1')
    parser.add_argument('--output', required=True, help='output path for EM_JSON')

    args = parser.parse_args()

    data = data_reading.read(args.file1, args.file2)

    df1 = data.dataset_1
    df2 = data.dataset_2
    offset = len(df1)
    id_col1 = data.id_column_name_1
    id_col2 = data.id_column_name_2

    data_cleaning.clean(data)

    if not (args.attr1 and args.attr2):
        attributes1 = []
        attributes2 = []
    else:
        attributes1 = [attr.strip() for attr in args.attr1.split(',')]
        attributes2 = [attr.strip() for attr in args.attr2.split(',')]

    blocks = token_blocking.block(data, attributes1, attributes2)

    #cleaned_blocks = block_purging.purge(blocks, data)
    cleaned_blocks = blocks

    filtered_blocks = block_cleaning.clean(cleaned_blocks, data)

    candidate_pairs_blocks = weighted_edge_pruning.clean(filtered_blocks, data)

    # Matching
    pairs_graph = entity_matching.match(candidate_pairs_blocks, data)

    print(pairs_graph)
    # Clustering
    #clusters = unique_mapping_clustering.cluster(pairs_graph, data)

    results = []

    for node1, node2, data_dict in pairs_graph.edges(data=True):
        if node1 < offset:
            val1 = df1.iloc[node1][id_col1]
        else:
            val1 = df2.iloc[node1 - offset][id_col2]

        if node2 < offset:
            val2 = df1.iloc[node2][id_col1]
        else:
            val2 = df2.iloc[node2 - offset][id_col2]

        entry = {
            "id_1": val1,
            "id_2": val2,
            "score": float(data_dict.get('weight', 1.0)),
            "id_type": "entity"
        }
        results.append(entry)

    json_output = {"matches": results, "blocks": [], "clusters": []}

    with open(args.output, 'w', encoding='utf-8') as json_file:
        json.dump(json_output, json_file, ensure_ascii=False, indent=4)

    print(f"Saved EM_JSON to: {args.output}")

if __name__ == '__main__':
    main()
