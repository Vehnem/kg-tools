import argparse
import json
import os

from REL.mention_detection import MentionDetection
from REL.utils import process_results
from REL.entity_disambiguation import EntityDisambiguation
from REL.ner import Cmns, load_flair_ner


def main(input_file, output_file):
    wiki_version = "wiki_2019"
    base_url = os.path.join(os.getenv("PWD", os.getcwd()), "bin")

    with open(input_file, "r", encoding="utf-8") as f:
        input_text = {"my_doc": (f.read().strip(), [])}

    mention_detection = MentionDetection(base_url, wiki_version)
    tagger_ner = load_flair_ner("ner-fast")
    tagger_ngram = Cmns(base_url, wiki_version, n=5)
    mentions, n_mentions = mention_detection.find_mentions(input_text, tagger_ngram)

    config = {
        "mode": "eval",
        "model_path": "ed-wiki-2019",
    }
    model = EntityDisambiguation(base_url, wiki_version, config)

    predictions, timing = model.predict(mentions)
    result = process_results(mentions, predictions, input_text)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(f"Saved results in {output_file}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entity Linking Script")
    parser.add_argument("--input", required=True, help="Path to input file")
    parser.add_argument("--output", required=True, help="Path to output file")
    args = parser.parse_args()

    main(args.input, args.output)