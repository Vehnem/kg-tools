import spacy
from spacy.pipeline import EntityRuler, EntityLinker
from spacy.kb import InMemoryLookupKB
import pandas as pd


def load_knowledge_base(nlp, csv_path, kb_path="kb"):
    """Create a spaCy InMemoryLookupKB from a CSV file and save it."""
    df = pd.read_csv(csv_path)

    kb = InMemoryLookupKB(vocab=nlp.vocab, entity_vector_length=1)

    for _, row in df.iterrows():
        entity_id = row['entity_id']
        entity_name = row['entity_name']
        aliases = [alias.strip() for alias in row['aliases'].split(",")]
        description = row.get('description', "")

        # Adding entity with a fake embedding vector (size must match entity_vector_length)
        kb.add_entity(entity_id, 1.0, [1.0])

        # Adding aliases
        for alias in aliases:
            kb.add_alias(alias, [entity_id], [1.0])

    kb.to_disk(kb_path)
    print(f"KnowledgeBase saved to {kb_path}")


def create_nlp_pipeline_with_linker(kb_path="kb"):
    nlp = spacy.blank("en")

    # Entity linker

    # EntityRuler to recognize patterns like "Apple", "Orange"
    ruler = nlp.add_pipe("entityRuler", name="entityRuler", before="entityLinker")
    patterns = [
        {"label": "PRODUCT", "pattern": "Apple"},
        {"label": "PRODUCT", "pattern": "Orange"},
    ]
    ruler.add_patterns(patterns)

    # OPTIONAL: You may still add a blank 'ner' if you want
    # nlp.add_pipe("ner")

    nlp.add_pipe("entityLinker", config={"kb_path": kb_path, "resolve_ambiguous": False})

    return nlp


def link_entities(nlp, text):
    doc = nlp(text)
    for ent in doc.ents:
        print(f"Entity: {ent.text} | Label: {ent.label_}")
        if ent._.kb_entity:
            print(f"  ↳ Linked to: {ent._.kb_entity.get('entity')} (Score: {ent._.kb_entity.get('score'):.3f})")
        else:
            print("  ↳ No link found")
    return doc


if __name__ == "__main__":
    nlp = spacy.blank("en")

    # 1. Load Knowledge Base from CSV
    load_knowledge_base(nlp, "kg.csv")

    # 2. Create NLP Pipeline with EntityRuler + EntityLinker
    nlp_with_linker = create_nlp_pipeline_with_linker()

    # 3. Test linking
    text = "I love Apple and Orange."
    link_entities(nlp_with_linker, text)
