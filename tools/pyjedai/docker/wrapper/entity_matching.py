import pyjedai.matching
from pyjedai.matching import EntityMatching

MATCHERS = {
    "char_bigram_tfidf": dict(
        metric="cosine",
        tokenizer="char_tokenizer",
        vectorizer="tfidf",
        qgram=2,
        similarity_threshold=0.0
    ),

    "char_trigram_tfidf": dict(
        metric="cosine",
        tokenizer="char_tokenizer",
        vectorizer="tfidf",
        qgram=3,
        similarity_threshold=0.0
    ),

    "char_bigram_bow": dict(
        metric="cosine",
        tokenizer="char_tokenizer",
        vectorizer="bow",
        qgram=2,
        similarity_threshold=0.0
    ),

    "char_trigram_bow": dict(
        metric="cosine",
        tokenizer="char_tokenizer",
        vectorizer="bow",
        qgram=3,
        similarity_threshold=0.0
    ),

    "word_tfidf": dict(
        metric="cosine",
        tokenizer="word_tokenizer",
        vectorizer="tfidf",
        similarity_threshold=0.0
    )
}

def match(candidate_pairs_blocks, data):
    em = EntityMatching(
        metric='cosine',
        tokenizer='char_tokenizer',
        vectorizer='tfidf',
        qgram=3,
        similarity_threshold=0.0
    )

    pairs_graph = em.predict(candidate_pairs_blocks, data, tqdm_disable=True)

    return pairs_graph