# Valentine Wrapper – Configuration Reference

All values in this document were checked against the source code of **Valentine 1.1.0** (`pip install valentine==1.1.0`). Older releases have different matcher signatures (for example `Coma(java_xmx=..., strategy=...)`), so the config does not apply to them.

## Usage

```bash
bash valentine.sh <source.csv> <target.csv> <output_dir> <config.yaml> [mapping.json]
```

| Argument | Description |
|---|---|
| `source.csv` | Source table. Its columns are matched against the target columns. |
| `target.csv` | Target table. |
| `output_dir` | Output directory (created if missing). |
| `config.yaml` | Configuration, see below. |
| `mapping.json` | Optional ground truth for evaluation. |

Ground-truth format (table names are ignored, only column names are compared):

```json
{"matches": [{"source_column": "id", "target_column": "ident"}]}
```

### Output files

| File | Content |
|---|---|
| `<Matcher>_matches.json` | One file per enabled matcher: `{"matches": [{"id_1", "id_2", "score", "id_type"}], "blocks": [], "clusters": []}`. `id_1` is the source column, `id_2` the target column. |
| `evaluation.csv` | One row per matcher: `dataset`, `matcher`, `runtime_seconds`, `n_matches`; with a mapping additionally `TP`, `FP`, `FN`, `Precision`, `Recall`, `F1`. |

`runtime_seconds` covers `valentine_match` and the result selection (`selection`), not CSV reading or writing. `TP/FP/FN/Precision/Recall/F1` are computed on the **selected** matches (after `selection`).

## General rules

- Unknown keys anywhere in the config raise an error.
- In `matchers.*.params`, a value of `null` means "not set": the parameter is not passed and Valentine's own default applies. Only keys that exist in the constructor of the matcher are accepted.
- Enum values (`distance_fun`, `coeff_policy`, `formula`, `string_matcher`) are given by member name, case-sensitive.
- Floats that must lie in `[0, 1]` are validated by Valentine itself and raise `ValueError` otherwise.

## `io`

| Key | Type | Default | Description |
|---|---|---|---|
| `nrows` | int or null | `null` | Read only the first n rows of each CSV (`pandas.read_csv(nrows=...)`). `null` reads everything. Replaces the former `cutoff` argument. |
| `encoding` | string | `utf-8` | CSV encoding. |
| `separator` | string | `,` | CSV separator. |
| `source_name` | string or null | `null` | Table name passed to Valentine for the source table. |
| `target_name` | string or null | `null` | Table name for the target table. Must be set together with `source_name`. |
| `instance_sample_size` | int or null | `1000` | Maximum number of non-empty rows used for instance sampling (`valentine_match(instance_sample_size=...)`). `null` disables sampling. Must be `>= 0`. |

**Why `source_name` / `target_name` default to `null`:** if no names are given, Valentine uses `aaa` and `bbb`. These share no trigrams, no prefix/suffix and have maximal Levenshtein distance, so table names cannot influence schema-based matchers (Coma, Cupid, Similarity Flooding). Custom names can change scores.

## `matchers`

Each matcher has `enabled` (default `true`) and `params`. At least one matcher must be enabled. Matchers run one after another on the same pair of tables.

| Matcher | Uses |
|---|---|
| `Coma` | schema, optionally instances |
| `Cupid` | schema only |
| `SimilarityFlooding` | schema only |
| `DistributionBased` | instances only |
| `JaccardDistanceMatcher` | instances only |

### `matchers.Coma.params`

Pure-Python COMA 3.0 implementation. Schema matchers: name, path, leaves, parents. Instance matcher: TF-IDF cosine similarity. After scoring, a bidirectional best-match selection is applied via `max_n`, `delta` and `threshold`. Per-pair sub-scores are available through `output.include_details`.

| Key | Type | Default | Range | Description |
|---|---|---|---|---|
| `max_n` | int | `0` | `>= 0` | Maximum matches kept per column. `0` means unlimited. |
| `use_instances` | bool | `false` | | Enable TF-IDF instance matching. |
| `use_schema` | bool | `true` | | Enable schema matchers. At least one of `use_schema` / `use_instances` must be `true`. |
| `delta` | float | `0.15` | `[0, 1]` | Keep matches scoring within this fraction of the best score of a column. |
| `threshold` | float | `0.0` | `[0, 1]` | Absolute minimum score. |
| `instance_weight` | float | `1.0` | `>= 0` | Weight of the instance matcher relative to the schema matchers (weight 1.0). |

### `matchers.Cupid.params`

Cupid (Madhavan et al., VLDB 2001): linguistic similarity of names combined with structural similarity of the schema tree.

| Key | Type | Default | Range | Description |
|---|---|---|---|---|
| `leaf_w_struct` | float | `0.2` | `[0, 1]` | Weight of structural similarity at leaf level. |
| `w_struct` | float | `0.2` | `[0, 1]` | Weight of structural similarity at inner-node level. |
| `th_accept` | float | `0.7` | `[0, 1]` | Acceptance threshold for the final mapping. |
| `th_high` | float | `0.6` | `[0, 1]` | High-confidence threshold during structural propagation. |
| `th_low` | float | `0.35` | `[0, 1]` | Low-confidence threshold during structural propagation. |
| `c_inc` | float | `1.2` | `> 0` | Reinforcement coefficient for matching children. |
| `c_dec` | float | `0.9` | `> 0` | Reinforcement coefficient for non-matching children. |
| `th_ns` | float | `0.7` | `[0, 1]` | Name-similarity threshold. |
| `process_num` | int | `1` | `>= 1` | Number of worker processes. |

### `matchers.DistributionBased.params`

Distribution-based matching (Zhang et al., SIGMOD 2011): quantile histograms of the column values, ranked by Earth Mover's Distance.

| Key | Type | Default | Range | Description |
|---|---|---|---|---|
| `threshold1` | float | `0.15` | `[0, 1]` | Distance threshold of phase 1 (distribution clustering). |
| `threshold2` | float | `0.15` | `[0, 1]` | Distance threshold of phase 2 (attribute clustering). |
| `quantiles` | int | `256` | `>= 1` | Number of quantiles for the histogram summaries. |
| `process_num` | int | `1` | `>= 1` | Number of worker processes. |
| `use_bloom_filters` | bool | `false` | | Use Bloom filters for approximate set intersection in phase 2. Cheaper on large columns, with a small false-positive rate. |

### `matchers.JaccardDistanceMatcher.params`

Baseline instance matcher: Jaccard (Tversky) similarity of the value sets, where two values count as equal if their string similarity reaches `threshold_dist`.

| Key | Type | Default | Range | Description |
|---|---|---|---|---|
| `threshold_dist` | float | `0.8` | `[0, 1]` | Minimum string similarity for two values to count as equal. Ignored for `Exact`. For `Embedding` it is applied to cosine similarity (about `0.7` is typical). |
| `distance_fun` | enum | `Levenshtein` | see below | String similarity function. |
| `process_num` | int | `1` | `>= 1` | Number of worker threads passed to `rapidfuzz.process.cdist`. |
| `embedding_model` | string | `all-MiniLM-L6-v2` | | Sentence-transformers model. Only used with `distance_fun: Embedding`. |
| `embedding_device` | string or null | `null` | | `cpu`, `cuda`, `cuda:1`, `mps`. `null` lets the library choose. Only used with `Embedding`. |
| `embedding_batch_size` | int or null | `null` | `>= 1` | Batch size of `model.encode`. `null` uses the sentence-transformers default (32). Only used with `Embedding`. |
| `tversky_alpha` | float | `1.0` | | Penalty for unmatched values on the reference side. |
| `tversky_beta` | float | `1.0` | | Penalty for unmatched values on the other side. |

`distance_fun` values:

| Value | Meaning |
|---|---|
| `Levenshtein` | Normalized Levenshtein ratio. |
| `DamerauLevenshtein` | Normalized Damerau-Levenshtein ratio. |
| `Jaro` | Jaro similarity. |
| `JaroWinkler` | Jaro-Winkler similarity. |
| `Hamming` | Normalized Hamming distance (strings of equal length). |
| `Exact` | Exact string equality; forces the threshold to 1.0. |
| `Embedding` | Cosine similarity of sentence-transformer embeddings. Requires `pip install "valentine[embeddings]"`. |

The pair similarity is `T(A,B) = |A∩B| / (|A∩B| + alpha·|A−B| + beta·|B−A|)`. Valentine computes both `T(A,B)` and `T(B,A)` and takes the maximum. With `alpha = beta = 1.0` this is plain Jaccard. With `alpha = 1.0, beta = 0.0` (or the reverse) it becomes set containment, which suits columns where one is expected to be a subset of the other.

### `matchers.SimilarityFlooding.params`

Similarity Flooding (Melnik et al., ICDE 2002): schemas are treated as labelled graphs, and an initial similarity is propagated until a fixpoint (max. 100 iterations, residual `1e-4`, fixed in Valentine).

| Key | Type | Default | Allowed values | Description |
|---|---|---|---|---|
| `coeff_policy` | enum | `INVERSE_AVERAGE` | `INVERSE_AVERAGE`, `INVERSE_PRODUCT` | Coefficient policy of the propagation graph: inverse of the average or of the product of in-degrees. |
| `formula` | enum | `FORMULA_C` | `BASIC`, `FORMULA_A`, `FORMULA_B`, `FORMULA_C` | Fixpoint iteration formula. |
| `string_matcher` | enum | `PREFIX_SUFFIX` | `PREFIX_SUFFIX`, `PREFIX_SUFFIX_TFIDF`, `LEVENSHTEIN` | Similarity function for the initial element mapping. |
| `tfidf_corpus` | list of CSV paths | `[]` | | Additional tables for the IDF weights. Only used with `PREFIX_SUFFIX_TFIDF`. Paths are resolved from the working directory of the runner (inside the container when run via Docker, so they must be mounted there). Read with the `io` settings. |

## `selection`

Post-processing of the raw matcher result. Raw results contain a score for every column pair, so some selection is normally needed. The steps run in this order: (1) 1:1 method, (2) `min_score`, (3) `top_percent`, (4) `top_n`, (5) `top_n_per_source`. Unset (`null`) steps are skipped.

| Key | Type | Default | Description |
|---|---|---|---|
| `method` | enum | `one_to_one_greedy` | `none`: keep all pairs. `one_to_one_greedy`: greedy 1:1 starting at the best pair. `one_to_one_hungarian`: globally optimal 1:1 (maximizes the total score; Valentine's recommended default selector). `one_to_one_mutual_top`: keep pairs where each side ranks the other within its top `mutual_top_n`. |
| `threshold` | float or null | `null` | Minimum score for `one_to_one_greedy` and `one_to_one_hungarian`. `null` uses the **median** of the distinct scores. Ignored by the other methods. |
| `mutual_top_n` | int or null | `null` | Top-n cut per side for `one_to_one_mutual_top`, `>= 1`. `null` uses Valentine's default (`1`, mutual nearest neighbour). |
| `min_score` | float or null | `null` | Drop pairs with a score below this value. |
| `top_percent` | int or null | `null` | Keep the top p percent of the remaining pairs (0-100). |
| `top_n` | int or null | `null` | Keep the n best remaining pairs. |
| `top_n_per_source` | int or null | `null` | Keep the n best remaining pairs per source column. |

The default (`one_to_one_greedy`, no threshold) reproduces the behaviour of the previous script.

## `output`

| Key | Type | Default | Description |
|---|---|---|---|
| `include_details` | bool | `false` | Add a `details` object with sub-matcher scores to each match in the JSON files. Only `Coma` provides details (for example `NameCM`, `InstancesCM`); other matchers write no `details`. |
| `evaluation_csv` | string | `evaluation.csv` | File name of the evaluation table inside `output_dir`. |

## `evaluation`

Evaluation needs a mapping file as fifth argument. Without one, a warning is printed and only `dataset`, `matcher`, `runtime_seconds` and `n_matches` are written.

| Key | Type | Default | Description |
|---|---|---|---|
| `enabled` | bool | `true` | Compute `TP`, `FP`, `FN`, `Precision`, `Recall`, `F1` on the selected matches. |
| `valentine_metrics.enabled` | bool | `false` | Additionally compute Valentine's own metrics on the **raw** matcher result (before `selection`). The columns are prefixed with `valentine_`. |
| `valentine_metrics.metrics` | list | all six | Subset of `Precision`, `Recall`, `F1Score`, `PrecisionTopNPercent`, `RecallAtSizeofGroundTruth`, `MeanReciprocalRank`. |
| `valentine_metrics.one_to_one` | bool | `true` | 1:1 filtering for `Precision`, `Recall`, `F1Score` and `PrecisionTopNPercent`. The other two metrics keep their Valentine default (`false`). |
| `valentine_metrics.one_to_one_method` | enum | `hungarian` | `greedy`, `hungarian` or `mutual_top`. Used where a metric applies 1:1 filtering. |
| `valentine_metrics.top_n_percent` | int | `10` | The `n` of `PrecisionTopNPercent`. |

`evaluation.csv` therefore contains two kinds of precision and recall: the plain columns (`Precision`, `Recall`, `F1`) describe the final selection, the `valentine_*` columns are Valentine's metrics on the raw result.

## KGpipe parameters

`valentine_tasks.py` exposes every key above as a task parameter and writes them into a temporary `config.yaml`. Naming scheme:

| Config key | Parameter name |
|---|---|
| `io.<key>` | `<key>` (for example `nrows`) |
| `matchers.Coma.*` | `coma_<key>` |
| `matchers.Cupid.*` | `cupid_<key>` |
| `matchers.DistributionBased.*` | `distribution_based_<key>` |
| `matchers.JaccardDistanceMatcher.*` | `jaccard_<key>` |
| `matchers.SimilarityFlooding.*` | `similarity_flooding_<key>` |
| `selection.<key>` | `selection_<key>` |
| `output.include_details`, `output.evaluation_csv` | `include_details`, `evaluation_csv` |
| `evaluation.enabled` | `evaluation_enabled` |
| `evaluation.valentine_metrics.*` | `valentine_metrics_<key>`; the metric list is `valentine_metrics` |

Floats are transported as strings and converted when the YAML is written. `instance_sample_size` is a string as well: use `none` to disable sampling. Lists (`valentine_metrics`, `similarity_flooding_tfidf_corpus`) are comma-separated strings.