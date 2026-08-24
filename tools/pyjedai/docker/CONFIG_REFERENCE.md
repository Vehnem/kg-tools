# Configuration Reference — pyJedAI Pipeline

Full overview of all stages, all available `method` values, and their
`method_params`, as used in `pipeline_config.example.yaml` /
`run_pipeline.py`.

---

## 1. `data_cleaning`

Calls `Data.clean_dataset(...)`. No `method` field, just an enable flag
plus the four flags directly as `params`.

```yaml
data_cleaning:
  enabled: false
  params:
    remove_stopwords: true
    remove_punctuation: true
    remove_numbers: true
    remove_unicodes: true
```

---

## 2. `blocking` (Block Building)

Module: `pyjedai.block_building`. Always called via
`bb.build_blocks(data, attributes_1=..., attributes_2=..., tqdm_disable=True)`.

| `method`                          | Class                          | `method_params`                                                                                            | Note                                                                                         |
|-----------------------------------|--------------------------------|------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| `standard_blocking`               | `StandardBlocking`             | `{}` — parameter-free                                                                                      | One block per token that appears in ≥2 entities.                                             |
| `qgrams_blocking`                 | `QGramsBlocking`               | `{"qgrams": 3}` (number of characters per q-gram)                                                          | One block per q-gram that is extracted from any token in the attribute values of any entity. | 
| `extended_qgrams_blocking`        | `ExtendedQGramsBlocking`       | `{"qgrams": 3, "threshold": 0.95}` same as above, plus a `threshold` for combining multiple q-gram lengths | Extension of QGramsBlocking that combines several q-gram sizes.                              |
| `suffix_arrays_blocking`          | `SuffixArraysBlocking`         | `{"suffix_length": 6, "max_block_size": 53}`                                                               | One block per suffix that appears in ≥2 entities.                                            |
| `extended_suffix_arrays_blocking` | `ExtendedSuffixArraysBlocking` | `{"suffix_length": 6, "max_block_size": 53}`                                                               | One Block per substring (not just suffix)                                                    |

```yaml
blocking:
  method: standard_blocking
  attributes_1: null        # e.g. ["name", "city"]
  attributes_2: null
  method_params: {}
```

Not included, because it's structurally different (uses embeddings
instead of `attributes_1/2`): `EmbeddingsNNBlockBuilding` from
`pyjedai.vector_based_blocking`. Let me know if you want it — it would
need its own code path.

---

## 3. `block_purging`

Module: `pyjedai.block_cleaning.BlockPurging`.

| `method`        | Class          | `method_params`                                                                                  |
|-----------------|----------------|--------------------------------------------------------------------------------------------------|
| `block_purging` | `BlockPurging` | `{"smoothing_factor": 1.025}` (blocks larger than `smoothing_factor × average size` are removed) |

```yaml
block_purging:
  enabled: true
  method: block_purging
  method_params:
    smoothing_factor: 1.025
```

---

## 4. `block_cleaning`

Module: `pyjedai.block_cleaning.BlockFiltering`.

| `method`          | Class            | `method_params`                                                                  |
|-------------------|------------------|----------------------------------------------------------------------------------|
| `block_filtering` | `BlockFiltering` | `{"ratio": 0.8}` (fraction of the (size-sorted) smallest blocks kept per entity) |

```yaml
block_cleaning:
  enabled: true
  method: block_filtering
  method_params:
    ratio: 0.8
```

---

## 5. `comparison_cleaning` (Meta-Blocking)

Module: `pyjedai.comparison_cleaning`. Called via
`mb.process(blocks, data, tqdm_disable=True)`.

| `method`                              | Class                              | `method_params`                                                      |
|---------------------------------------|------------------------------------|----------------------------------------------------------------------|
| `weighted_edge_pruning`               | `WeightedEdgePruning`              | `{"weighting_scheme": "CBS"}`                                        |
| `weighted_node_pruning`               | `WeightedNodePruning`              | `{"weighting_scheme": "CBS"}`                                        |
| `cardinality_edge_pruning`            | `CardinalityEdgePruning`           | `{"weighting_scheme": "JS"}`                                         |
| `cardinality_node_pruning`            | `CardinalityNodePruning`           | `{"weighting_scheme": "JS"}`                                         |
| `blast`                               | `BLAST`                            | `{"weighting_scheme": "X2"}`                                         |
| `reciprocal_cardinality_node_pruning` | `ReciprocalCardinalityNodePruning` | `{"weighting_scheme": "CN-CBS"}`                                     |
| `reciprocal_weighted_node_pruning`    | `ReciprocalWeightedNodePruning`    | `{"weighting_scheme": "CN-CBS"}`                                     |
| `comparison_propagation`              | `ComparisonPropagation`            | `{}` — parameter-free (pure graph propagation, no pruning parameter) |

**`weighting_scheme` values**:

| Value                     | Meaning                                                                                                                                      |
|---------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| `CBS`, `CN-CBS`, `SN-CBS` | Common Blocks Scheme — raw count of shared blocks. **All three values are aliases**                                                          |
| `ECBS`                    | Enhanced CBS — CBS multiplied by a log-IDF-style weighting based on block count per entity.                                                  |
| `JS`                      | Jaccard Scheme.                                                                                                                              |
| `EJS`                     | Enhanced Jaccard Scheme — JS multiplied by a log-weighting based on comparisons per entity.                                                  |
| `X2`                      | Pearson chi-squared test on a 2×2 contingency table.                                                                                         |
| `COSINE`                  | Cosine similarity, normalized by each entity's block-index size.                                                                             |
| `DICE`                    | Dice coefficient, normalized by each entity's block-index size.                                                                              |
| `CNC`, `SNC`              | Cosine, normalized by `comparisons_per_entity` instead of block-index size (Cardinality-/Size-Node variant — identical formula in the code). |
| `CND`, `SND`              | Dice, normalized by `comparisons_per_entity` (identical formula).                                                                            |
| `CNJ`, `SNJ`              | Jaccard, normalized by `comparisons_per_entity` (identical formula).                                                                         |


```yaml
comparison_cleaning:
  enabled: true
  method: weighted_edge_pruning
  method_params:
    weighting_scheme: EJS
```

---

## 6. `matching`

Module: `pyjedai.matching`. Two fundamentally different matcher types,
selected via `method` within each matcher entry.

### 6a. `method: entity_matching` → `EntityMatching`

| Parameter              | Example values                                                          |
|------------------------|-------------------------------------------------------------------------|
| `metric`               | `cosine`, `dice`, `sorensen_dice`, `jaccard` (string similarity metric) |
| `tokenizer`            | `char_tokenizer`, `word_tokenizer`                                      |
| `vectorizer`           | `tfidf`, `tf`, `boolean`                                                |
| `qgram`                | `1`, `2`, `3`, ...                                                      |
| `similarity_threshold` | `0.0`–`1.0`                                                             |
| `attributes`           | e.g. `["name", "description"]` — restricts matching to specific columns |

### 6b. `method: vector` → `pyjedai.matching.VectorBasedMatching`

In addition to the fields above, the following config keys are handled
by the **runner itself** (not passed directly to the class) before the
rest is forwarded to the constructor:

| Parameter                         | Meaning                                                                       |
|-----------------------------------|-------------------------------------------------------------------------------|
| `embedding_model`                 | SentenceTransformers model name, default `all-MiniLM-L6-v2`                   |
| `text_column_1` / `text_column_2` | Which column gets encoded, default: second column of the respective DataFrame |
| `metric`, `similarity_threshold`  | as above                                                                      |

```yaml
matching:
  matchers:
    vector_cosine:
      method: vector
      metric: cosine
      similarity_threshold: 0.8
      embedding_model: all-MiniLM-L6-v2

    char_bigram_tfidf:
      method: entity_matching
      metric: cosine
      tokenizer: char_tokenizer
      vectorizer: tfidf
      qgram: 2
      similarity_threshold: 0.8
```

You can list any number of matchers under `matching.matchers` — each one
runs separately and produces its own `<name>.json` plus its own row in
`evaluation.csv`.

---

## 7. `clustering`

Module: `pyjedai.clustering`. Called via `cc.process(pairs_graph, data, ...)`.

| `method`                            | Class                            | `method_params` |
|-------------------------------------|----------------------------------|-----------------|
| `best_match_clustering`             | `BestMatchClustering`            | `{}`            |
| `center_clustering`                 | `CenterClustering`               | `{}`            |
| `connected_components_clustering`   | `ConnectedComponentsClustering`  | `{}`            |
| `correlation_clustering`            | `CorrelationClustering`          | `{}`            |
| `cut_clustering`                    | `CutClustering`                  | `{}`            |
| `exact_clustering`                  | `ExactClustering`                | `{}`            |
| `kiraly_msm_approximate_clustering` | `KiralyMSMApproximateClustering` | `{}`            |
| `markov_clustering`                 | `MarkovClustering`               | `{}`            |
| `merge_center_clustering`           | `MergeCenterClustering`          | `{}`            |
| `ricochet_sr_clustering`            | `RicochetSRClustering`           | `{}`            |
| `row_column_clustering`             | `RowColumnClustering`            | `{}`            |
| `unique_mapping_clustering`         | `UniqueMappingClustering`        | `{}`            |

```yaml
clustering:
  enabled: true
  method: unique_mapping_clustering
  method_params:
```

---

## Full example with all stages enabled

See `config-example.yaml` — it has all stages populated with
sensible default parameters and is ready to run.
