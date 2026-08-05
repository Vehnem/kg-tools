import argparse
import json
import os
import time

import pandas as pd
import pyjedai.matching

import data_cleaning
import data_reading
from blocking import token_blocking
from pyjedai.matching import EntityMatching
import block_purging
import block_cleaning
from comparison_cleaning import weighted_edge_pruning
import entity_matching
MATCHERS = {
    "vector_cosine": dict(
        metric="cosine",
        similarity_threshold=0.8
    ),
    "char_bigram_tfidf": dict(
        metric="cosine",
        tokenizer="char_tokenizer",
        vectorizer="tfidf",
        qgram=2,
        similarity_threshold=0.8
    ),
    "char_trigram_tfidf": dict(
        metric="cosine",
        tokenizer="char_tokenizer",
        vectorizer="tfidf",
        qgram=3,
        similarity_threshold=0.8
    ),

    "char_bigram_tf": dict(
        metric="cosine",
        tokenizer="char_tokenizer",
        vectorizer="tf",
        qgram=2,
        similarity_threshold=0.8
    ),

    "char_trigram_tf": dict(
        metric="cosine",
        tokenizer="char_tokenizer",
        vectorizer="tf",
        qgram=3,
        similarity_threshold=0.8
    ),

    "char_bigram_boolean": dict(
        metric="cosine",
        tokenizer="char_tokenizer",
        vectorizer="boolean",
        qgram=2,
        similarity_threshold=0.8
    ),

    "char_trigram_boolean": dict(
        metric="cosine",
        tokenizer="char_tokenizer",
        vectorizer="boolean",
        qgram=3,
        similarity_threshold=0.8
    ),

    "word_tfidf": dict(
        metric="cosine",
        tokenizer="word_tokenizer",
        vectorizer="tfidf",
        qgram=1,
        similarity_threshold=0.8
    ),

    "word_bigram_tfidf": dict(
        metric="cosine",
        tokenizer="word_tokenizer",
        vectorizer="tfidf",
        qgram=2,
        similarity_threshold=0.8
    ),


    "word_tf": dict(
        metric="cosine",
        tokenizer="word_tokenizer",
        vectorizer="tf",
        qgram=1,
        similarity_threshold=0.8
    ),
    "word_bigram_tf": dict(
        metric="cosine",
        tokenizer="word_tokenizer",
        vectorizer="tf",
        qgram=2,
        similarity_threshold=0.8
    ),

    "word_boolean": dict(
        metric="cosine",
        tokenizer="word_tokenizer",
        vectorizer="boolean",
        qgram=1,
        similarity_threshold=0.8
    ),

    "word_bigram_boolean": dict(
        metric="cosine",
        tokenizer="word_tokenizer",
        vectorizer="boolean",
        qgram=2,
        similarity_threshold=0.8
    ),
}

def evaluate(predicted, gt):

    predicted = set(predicted)

    tp = len(predicted & gt)
    fp = len(predicted - gt)
    fn = len(gt - predicted)

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0
    )

    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
    }

#n:n matches
def main():
    parser = argparse.ArgumentParser(description='Entity Resolution with optional blocking attributes')
    parser.add_argument('--file1', required=True, help='path to file1')
    parser.add_argument('--file2', required=True, help='path to file2')
    parser.add_argument(
    "--gt",
    required=False,
    help="Ground truth file")
    parser.add_argument('--attr1', required=False, help='comma seperated list of attributes to block for Dataset 1')
    parser.add_argument('--attr2', required=False, help='comma seperated list of attributes to block for Dataset 1')
    parser.add_argument('--output', required=True, help='output path for EM_JSON')

    args = parser.parse_args()

    data = data_reading.read(args.file1, args.file2, ground_truth_path=args.gt, sep="|")

    df1 = data.dataset_1
    df2 = data.dataset_2
    #gt = data.ground_truth

    gt = {
        (f"restaurant1-Restaurant{i}", f"restaurant1-Restaurant{i}")
        for i in range(113)
    }

    offset = len(df1)
    id_col1 = data.id_column_name_1
    id_col2 = data.id_column_name_2

    #data_cleaning.clean(data)

    if not (args.attr1 and args.attr2):
        attributes1 = None
        attributes2 = None
    else:
        attributes1 = [attr.strip() for attr in args.attr1.split('|')]
        attributes2 = [attr.strip() for attr in args.attr2.split('|')]

    print(data.dataset_1.columns)
    print(data.dataset_2.columns)

    blocks = token_blocking.block(data, attributes1, attributes2)

    #cleaned_blocks = block_purging.purge(blocks, data)
    cleaned_blocks = blocks

    #filtered_blocks = block_cleaning.clean(cleaned_blocks, data)

    #candidate_pairs_blocks = weighted_edge_pruning.clean(filtered_blocks, data)

    # Matching
    #pairs_graph = entity_matching.match(candidate_pairs_blocks, data)
    #pairs_graph = entity_matching.match(blocks, data)
    #print(pairs_graph)

    evaluation_rows = []

    from sentence_transformers import SentenceTransformer

    for matcher_name, config in MATCHERS.items():
        print(f"Running {matcher_name}")

        if matcher_name.startswith("vector"):
            model = SentenceTransformer("all-MiniLM-L6-v2")
            texts_d1 = df1[df1.columns[1]].tolist()
            texts_d2 = df2[df2.columns[1]].tolist()
            vectors_d1 = model.encode(texts_d1, convert_to_numpy=True)
            vectors_d2 = model.encode(texts_d2, convert_to_numpy=True)
            em = pyjedai.matching.VectorBasedMatching(**config)
        else:
            em = EntityMatching(**config)
        start = time.perf_counter()

        if matcher_name.startswith("vector"):
            pairs_graph = em.predict(
                blocks,
                data,
                vectors_d1,
                vectors_d2,
                tqdm_disable=True
            )
        else:
            pairs_graph = em.predict(
                blocks,
                data,
                tqdm_disable=True
            )

        runtime = time.perf_counter() - start

        results = []
        predicted = []

        for node1, node2, data_dict in pairs_graph.edges(data=True):

            score = float(data_dict.get("weight", 1.0))

            if score < 0.8:
                continue

            if node1 < offset:
                val1 = df1.iloc[node1][id_col1]
            else:
                val1 = df2.iloc[node1 - offset][id_col2]
            if node2 < offset:
                val2 = df1.iloc[node2][id_col1]
            else:
                val2 = df2.iloc[node2 - offset][id_col2]

            predicted.append((val1, val2))
            entry = { "id_1": val1, "id_2": val2, "score": float(data_dict.get('weight', 1.0)), "id_type": "entity" }
            results.append(entry)


        predicted = [
            (entry["id_1"], entry["id_2"])
            for entry in results
        ]
        os.makedirs(args.output, exist_ok=True)
        outfile = os.path.join(args.output, f"{matcher_name}.json")

        with open(outfile, "w", encoding="utf8") as f:
            json.dump(
                {
                    "matches": results,
                    "blocks": [],
                    "clusters": []
                },
                f,
                indent=4,
                ensure_ascii=False
            )
        if gt is not None:
            metrics = evaluate(predicted, gt)

            evaluation_rows.append({
                "matcher": matcher_name,
                "runtime": runtime,
                **metrics
            })
    if evaluation_rows:
        pd.DataFrame(evaluation_rows).to_csv(
            os.path.join(args.output, "evaluation.csv"),
            index=False
        )
    # Clustering
    #clusters = unique_mapping_clustering.cluster(pairs_graph, data)


    #json_output = {"matches": results, "blocks": [], "clusters": []}

    #with open(args.output, 'w', encoding='utf-8') as json_file:
    #    json.dump(json_output, json_file, ensure_ascii=False, indent=4)

    #print(f"Saved EM_JSON to: {args.output}")

if __name__ == '__main__':
    main()
