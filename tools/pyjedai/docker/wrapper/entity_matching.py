from pyjedai.matching import EntityMatching

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