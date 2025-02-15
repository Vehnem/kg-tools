import spacy
from fuzzywuzzy import process

nlp = spacy.load("en_core_web_sm")


def extract_entities(text):
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities, doc


def extract_relations(doc):
    relations = []

    for token in doc:
        if "subj" in token.dep_:
            subject = token.text
            verb = token.head.lemma_

            for child in token.head.children:
                if "obj" in child.dep_:
                    obj = child.text
                    relations.append((subject, verb, obj))

            if token.head.pos_ == "AUX" and token.head.lemma_ == "be":
                copula_complement = None
                preposition_object = None

                for child in token.head.children:
                    if child.dep_ in {"attr", "acomp"}:
                        copula_complement = child.text
                    elif child.dep_ == "prep":
                        preposition_object = " ".join(
                            [child.text] + [c.text for c in child.children]
                        )

                if copula_complement and preposition_object:
                    relations.append(
                        (subject, f"is_{copula_complement}", preposition_object)
                    )

    return relations


def link_entities(entities):
    entity_map = {}
    for ent_text, ent_label in entities:
        entity_map[ent_text] = f"http://example.com/entity/{ent_text.replace(' ', '_')}"
    return entity_map


def match_entity(text, entity_map):
    """Find the best matching entity from the entity map (fuzzy matching)"""
    best_match, score = process.extractOne(text, entity_map.keys())
    if score > 80:  # Adjust threshold if needed
        return entity_map[best_match]
    return text


def build_knowledge_triples(relations, entity_map):
    triples = []
    for subj, verb, obj in relations:
        subj_uri = match_entity(subj, entity_map)
        obj_uri = match_entity(obj, entity_map)
        triples.append((subj_uri, verb, obj_uri))
    return triples


def main():
    text = "Elon Musk founded SpaceX in 2002. He is the CEO of Tesla."
    print(f"Text: {text}\n")

    # 1. Extract Entities
    entities, doc = extract_entities(text)
    print(f"Entities: {entities}")

    # 2. Extract Relations
    relations = extract_relations(doc)
    print(f"Relations (SVO + Copula): {relations}")

    # 3. Link Entities (Mock)
    entity_map = link_entities(entities)
    print(f"Entity Links (Mock URIs): {entity_map}")

    # 4. Build Knowledge Triples
    triples = build_knowledge_triples(relations, entity_map)
    print("\nKnowledge Triples (Subject, Predicate, Object):")
    for triple in triples:
        print(triple)


if __name__ == "__main__":
    main()
