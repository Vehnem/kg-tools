import spacy
from spacy.matcher import DependencyMatcher

nlp = spacy.load("en_core_web_sm")


def extract_entities(text):
    """Perform Named Entity Recognition (NER)"""
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities, doc



# The second part, "He is the CEO of Tesla," doesn’t match a simple SVO pattern:



def extract_relations(doc):
    """Extract subject-verb-object and other relations"""
    relations = []

    for token in doc:
        # Look for subject -> verb -> object type relations
        if "subj" in token.dep_:
            subject = token.text
            verb = token.head.lemma_  # Verb is the head of the subject
            # Find objects or prepositional objects
            for child in token.head.children:
                if "obj" in child.dep_ or child.dep_ == "prep":
                    obj = child.text
                    relations.append((subject, verb, obj))

    return relations


# def extract_relations(doc):
#     """Extract simple subject-verb-object relations (Pattern-based)"""
#     matcher = DependencyMatcher(nlp.vocab)
#     pattern = [
#         {"RIGHT_ID": "subject", "RIGHT_ATTRS": {"dep": "nsubj"}},
#         {"LEFT_ID": "subject", "REL_OP": ">", "RIGHT_ID": "verb", "RIGHT_ATTRS": {"pos": "VERB"}},
#         {"LEFT_ID": "verb", "REL_OP": ">", "RIGHT_ID": "object", "RIGHT_ATTRS": {"dep": "dobj"}},
#     ]
#     matcher.add("SVO", [pattern])

#     matches = matcher(doc)
#     relations = []
#     for match_id, token_ids in matches:
#         subject = doc[token_ids[0]]
#         verb = doc[token_ids[1]]
#         obj = doc[token_ids[2]]
#         relations.append((subject.text, verb.lemma_, obj.text))
#     return relations


def link_entities(entities):
    """Mock entity linking: simulate linking to Wikidata or a KB"""
    entity_map = {}
    for ent_text, ent_label in entities:
        # Mocking a Knowledge Base lookup (replace with a real linker later)
        entity_map[ent_text] = f"http://example.com/entity/{ent_text.replace(' ', '_')}"
    return entity_map


def build_knowledge_triples(relations, entity_map):
    """Convert relations and entity links into RDF-like triples"""
    triples = []
    for subj, verb, obj in relations:
        subj_uri = entity_map.get(subj, subj)
        obj_uri = entity_map.get(obj, obj)
        triples.append((subj_uri, verb, obj_uri))
    return triples


def main():
    text = "Elon Musk founded SpaceX in 2002. He is the CEO of Tesla."
    print(f"Text: {text}\n")

    # 1. Named Entity Recognition
    entities, doc = extract_entities(text)
    print(f"Entities: {entities}")

    # 2. Relation Extraction
    relations = extract_relations(doc)
    print(f"Relations (SVO): {relations}")

    # 3. Entity Linking (Mock)
    entity_map = link_entities(entities)
    print(f"Entity Links (Mock URIs): {entity_map}")

    # 4. Knowledge Triples
    triples = build_knowledge_triples(relations, entity_map)
    print("\nKnowledge Triples (Subject, Predicate, Object):")
    for triple in triples:
        print(triple)


if __name__ == "__main__":
    main()
