from transformers import pipeline
import argparse

def main():
    parser = argparse.ArgumentParser(description='Rebel Information Extraction')
    parser.add_argument('--file', required=True, help='path to text file')
    parser.add_argument('--output', required=True, help='output path for rebel_output')

    args = parser.parse_args()

    print("Loading model...")
    triplet_extractor = pipeline('text2text-generation', model='Babelscape/rebel-large', tokenizer='Babelscape/rebel-large')

    print("Generating text...")
    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read()
    # We need to use the tokenizer manually since we need special tokens.
    extracted_text = triplet_extractor.tokenizer.batch_decode([triplet_extractor(
        content,
        return_tensors=True,
    return_text=False)[0]["generated_token_ids"]])

    print(extracted_text[0])

    # Function to parse the generated text and extract the triplets
    def extract_triplets(text):
        triplets = []
        relation, subject, relation, object_ = '', '', '', ''
        text = text.strip()
        current = 'x'
        for token in text.replace("<s>", "").replace("<pad>", "").replace("</s>", "").split():
            if token == "<triplet>":
                current = 't'
                if relation != '':
                    triplets.append({'head': subject.strip(), 'type': relation.strip(),'tail': object_.strip()})
                    relation = ''
                subject = ''
            elif token == "<subj>":
                current = 's'
                if relation != '':
                    triplets.append({'head': subject.strip(), 'type': relation.strip(),'tail': object_.strip()})
                object_ = ''
            elif token == "<obj>":
                current = 'o'
                relation = ''
            else:
                if current == 't':
                    subject += ' ' + token
                elif current == 's':
                    object_ += ' ' + token
                elif current == 'o':
                    relation += ' ' + token
        if subject != '' and relation != '' and object_ != '':
            triplets.append({'head': subject.strip(), 'type': relation.strip(),'tail': object_.strip()})
        return triplets
    extracted_triplets = extract_triplets(extracted_text[0])
    print(extracted_triplets)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(str(extracted_triplets))

if __name__ == '__main__':
    main()