import argparse
import json
import os

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

    os.makedirs(args.output+".tmp", exist_ok=True)

    for left_file in os.listdir(args.file1):
        for right_file  in os.listdir(args.file2):
            try:
                match_csv(
                    os.path.join(args.file1, left_file),
                    os.path.join(args.file2, right_file), 
                    args.attr1, 
                    args.attr2, 
                    os.path.join(args.output+".tmp", f"{left_file}_{right_file}.json"))
            except Exception as e:
                print(f"Error matching {left_file} and {right_file}: {e}")
                with open(os.path.join(args.output+".tmp", f"{left_file}_{right_file}.json"), "w") as f:
                    json.dump({"matches": [], "blocks": [], "clusters": []}, f, ensure_ascii=False, indent=4)

    selected_matches = {}

    for file in os.listdir(args.output+".tmp"):
        with open(os.path.join(args.output+".tmp", file), "r") as f:
            data = json.load(f)
            matches = data["matches"]
            for match in matches:
                if match["id_1"] not in selected_matches:
                    selected_matches[match["id_1"]] = match
                else:
                    if selected_matches[match["id_1"]]["score"] < match["score"]:
                        selected_matches[match["id_1"]] = match

    doc = {"matches": list(selected_matches.values()), "blocks": [], "clusters": []}

    with open(args.output, "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=4)

def match_csv(file1, file2, attr1, attr2, output_file):
    data = data_reading.read(file1, file2)

    df1 = data.dataset_1
    df2 = data.dataset_2
    offset = len(df1)
    id_col1 = data.id_column_name_1
    id_col2 = data.id_column_name_2

    data_cleaning.clean(data)

    if not (attr1 and attr2):
        attributes1 = []
        attributes2 = []
    else:
        attributes1 = [attr.strip() for attr in attr1.split(',')]
        attributes2 = [attr.strip() for attr in attr2.split(',')]

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

    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(json_output, json_file, ensure_ascii=False, indent=4)

    print(f"Saved EM_JSON to: {output_file}")

if __name__ == '__main__':
    main()
