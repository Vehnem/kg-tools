import time

from pyjedai.matching import EntityMatching, VectorBasedMatching

MATCHING_CLASS_REGISTRY = {
    "entity_matching": EntityMatching,
    "vector": VectorBasedMatching,
}

def match(matcher_cfg, blocks, data, df1, df2):
    matcher_cfg = dict(matcher_cfg)
    method = matcher_cfg.pop("method", "entity_matching")
    if method not in MATCHING_CLASS_REGISTRY:
        raise ValueError(
            f"Unknown matching-Method '{method}'. "
            f"Available: {list(MATCHING_CLASS_REGISTRY)}"
        )
    matcher_cls = MATCHING_CLASS_REGISTRY[method]
    start = time.perf_counter()

    if method == "vector":
        from sentence_transformers import SentenceTransformer

        model_name = matcher_cfg.pop("embedding_model", "all-MiniLM-L6-v2")
        text_col_1 = matcher_cfg.pop("text_column_1", df1.columns[1])
        text_col_2 = matcher_cfg.pop("text_column_2", df2.columns[1])

        model = SentenceTransformer(model_name)
        vectors_d1 = model.encode(df1[text_col_1].tolist(), convert_to_numpy=True)
        vectors_d2 = model.encode(df2[text_col_2].tolist(), convert_to_numpy=True)

        em = matcher_cls(**matcher_cfg)
        graph = em.predict(blocks, data, vectors_d1, vectors_d2, tqdm_disable=True)
    else:
        em = matcher_cls(**matcher_cfg)
        graph = em.predict(blocks, data, tqdm_disable=True)

    runtime = time.perf_counter() - start
    return graph, runtime