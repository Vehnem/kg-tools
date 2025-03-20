import spacy
from fuzzywuzzy import process
import sys

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


def text2genRDF():
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

def text2WikidataRDF():
    pass

def linkEntites():
    nlp = spacy.load("en_core_web_sm")

    # add pipeline (declared through entry_points in setup.py)
    nlp.add_pipe("entityLinker", last=True)

    doc = nlp("I watched the Pirates of the Caribbean last silvester")

    # returns all entities in the whole document
    all_linked_entities = doc._.linkedEntities
    # iterates over sentences and prints linked entities
    for sent in doc.sents:
        sent._.linkedEntities.pretty_print()


def text2genTriple():
    nlp = spacy.load("en_core_web_sm")


    def extract_entities(text):
        """Perform Named Entity Recognition (NER)"""
        doc = nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        return entities, doc

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
    usage = "Usage: python ie.py [text2GenRDF]"
    if len(sys.argv) < 2:
        print(usage)
    else:
        match sys.argv[1]:
            case "text2GenRDF":
                text2genRDF()
            case "text2WikidataRDF":
                text2WikidataRDF()
            case "linkEntities":
                linkEntites()
            case "text2genTriple":
                text2genTriple()
            case _:    
                print(usage)


### OLD CODE BELOW ###

# import spacy
# from spacy.pipeline import EntityRuler, EntityLinker
# from spacy.kb import InMemoryLookupKB
# import pandas as pd


# def load_knowledge_base(nlp, csv_path, kb_path="kb"):
#     """Create a spaCy InMemoryLookupKB from a CSV file and save it."""
#     df = pd.read_csv(csv_path)
#
#     kb = InMemoryLookupKB(vocab=nlp.vocab, entity_vector_length=1)
#
#     for _, row in df.iterrows():
#         entity_id = row['entity_id']
#         entity_name = row['entity_name']
#         aliases = [alias.strip() for alias in row['aliases'].split(",")]
#         description = row.get('description', "")
#
#         # Adding entity with a fake embedding vector (size must match entity_vector_length)
#         kb.add_entity(entity_id, 1.0, [1.0])
#
#         # Adding aliases
#         for alias in aliases:
#             kb.add_alias(alias, [entity_id], [1.0])
#
#     kb.to_disk(kb_path)
#     print(f"KnowledgeBase saved to {kb_path}")
#
#
# def create_nlp_pipeline_with_linker(kb_path="kb"):
#     nlp = spacy.blank("en")
#
#     # Entity linker
#
#     # EntityRuler to recognize patterns like "Apple", "Orange"
#     ruler = nlp.add_pipe("entityRuler", name="entityRuler", before="entityLinker")
#     patterns = [
#         {"label": "PRODUCT", "pattern": "Apple"},
#         {"label": "PRODUCT", "pattern": "Orange"},
#     ]
#     ruler.add_patterns(patterns)
#
#     # OPTIONAL: You may still add a blank 'ner' if you want
#     # nlp.add_pipe("ner")
#
#     nlp.add_pipe("entityLinker", config={"kb_path": kb_path, "resolve_ambiguous": False})
#
#     return nlp
#
# def link_entities(nlp, text):
#     doc = nlp(text)
#     for ent in doc.ents:
#         print(f"Entity: {ent.text} | Label: {ent.label_}")
#         if ent._.kb_entity:
#             print(f"  ↳ Linked to: {ent._.kb_entity.get('entity')} (Score: {ent._.kb_entity.get('score'):.3f})")
#         else:
#             print("  ↳ No link found")
#     return doc
#
#
# if __name__ == "__main__":
#     nlp = spacy.blank("en")
#
#     # 1. Load Knowledge Base from CSV
#     load_knowledge_base(nlp, "kg.csv")
#
#     # 2. Create NLP Pipeline with EntityRuler + EntityLinker
#     nlp_with_linker = create_nlp_pipeline_with_linker()
#
#     # 3. Test linking
#     text = "I love Apple and Orange."
#     link_entities(nlp_with_linker, text)


# import spacy
# from fuzzywuzzy import process
#
# nlp = spacy.load("en_core_web_sm")
#
# def extract_entities(text):
#     doc = nlp(text)
#     entities = [(ent.text, ent.label_) for ent in doc.ents]
#     return entities, doc
#
#
# def extract_relations(doc):
#     relations = []
#
#     for token in doc:
#         if "subj" in token.dep_:
#             subject = token.text
#             verb = token.head.lemma_
#
#             for child in token.head.children:
#                 if "obj" in child.dep_:
#                     obj = child.text
#                     relations.append((subject, verb, obj))
#
#             if token.head.pos_ == "AUX" and token.head.lemma_ == "be":
#                 copula_complement = None
#                 preposition_object = None
#
#                 for child in token.head.children:
#                     if child.dep_ in {"attr", "acomp"}:
#                         copula_complement = child.text
#                     elif child.dep_ == "prep":
#                         preposition_object = " ".join(
#                             [child.text] + [c.text for c in child.children]
#                         )
#
#                 if copula_complement and preposition_object:
#                     relations.append(
#                         (subject, f"is_{copula_complement}", preposition_object)
#                     )
#
#     return relations
#
#
# def link_entities(entities):
#     entity_map = {}
#     for ent_text, ent_label in entities:
#         entity_map[ent_text] = f"http://example.com/entity/{ent_text.replace(' ', '_')}"
#     return entity_map
#
#
# def match_entity(text, entity_map):
#     """Find the best matching entity from the entity map (fuzzy matching)"""
#     best_match, score = process.extractOne(text, entity_map.keys())
#     if score > 80:  # Adjust threshold if needed
#         return entity_map[best_match]
#     return text
#
# def build_knowledge_triples(relations, entity_map):
#     triples = []
#     for subj, verb, obj in relations:
#         subj_uri = match_entity(subj, entity_map)
#         obj_uri = match_entity(obj, entity_map)
#         triples.append((subj_uri, verb, obj_uri))
#     return triples
#
# def main():
#     text = "Elon Musk founded SpaceX in 2002. He is the CEO of Tesla."
#     print(f"Text: {text}\n")
#
#     # 1. Extract Entities
#     entities, doc = extract_entities(text)
#     print(f"Entities: {entities}")
#
#     # 2. Extract Relations
#     relations = extract_relations(doc)
#     print(f"Relations (SVO + Copula): {relations}")
#
#     # 3. Link Entities (Mock)
#     entity_map = link_entities(entities)
#     print(f"Entity Links (Mock URIs): {entity_map}")
#
#     # 4. Build Knowledge Triples
#     triples = build_knowledge_triples(relations, entity_map)
#     print("\nKnowledge Triples (Subject, Predicate, Object):")
#     for triple in triples:
#         print(triple)
