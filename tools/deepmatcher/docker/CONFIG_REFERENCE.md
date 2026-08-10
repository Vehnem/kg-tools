# Configuration Reference — DeepMatcher Pipeline

Full overview of all sections and parameters in
`deepmatcher_config.example.yaml`, as used by `run_deepmatcher.py`.

---

## 1. `process`

Passed to `dm.data.process(path=..., train=..., validation=..., test=..., **process)`.
Applies identically to train/validation/test.

| Parameter                 | Type      | Default           | Meaning                                                                                                                   |
|---------------------------|-----------|-------------------|---------------------------------------------------------------------------------------------------------------------------|
| `cache`                   | str       | `cacheddata.pth`  | Filename for the processing cache.                                                                                        |
| `check_cached_data`       | bool      | `true`            | Checks whether the cache still matches the current CSV files.                                                             |
| `auto_rebuild_cache`      | bool      | `true`            | Automatically rebuilds the cache if it's stale.                                                                           |
| `tokenize`                | str       | `nltk`            | Tokenizer, e.g. `"nltk"` or a spaCy tokenizer name.                                                                       |
| `lowercase`               | bool      | `true`            | Lowercase text before processing.                                                                                         |
| `embeddings`              | str       | `glove.6B.50d`    | Word embeddings, e.g. also `"fasttext.en.bin"`.                                                                           |
| `embeddings_cache_path`   | str       | `~/.vector_cache` | Storage location for downloaded embeddings.                                                                               |
| `ignore_columns`          | list[str] | `[]`              | Columns to ignore while reading.                                                                                          |
| `include_lengths`         | bool      | `true`            | Also read sequence lengths (needed by some modules).                                                                      |
| `id_attr`                 | str       | `id`              | Name of the ID column.                                                                                                    |
| `label_attr`              | str       | `label`           | Name of the label column (0/1 match).                                                                                     |
| `left_prefix`             | str       | `left_`           | Prefix of entity-1 columns.                                                                                               |
| `right_prefix`            | str       | `right_`          | Prefix of entity-2 columns.                                                                                               |
| `use_magellan_convention` | bool      | `false`           | `true` if the CSVs follow the Magellan/py_entitymatching column scheme (`ltable_`/`rtable_` instead of `left_`/`right_`). |
| `pca`                     | bool      | `true`            | Apply PCA to the embeddings (dimensionality reduction).                                                                   |

```yaml
process:
  cache: cacheddata.pth
  check_cached_data: true
  auto_rebuild_cache: true
  tokenize: nltk
  lowercase: true
  embeddings: fasttext.en.bin
  embeddings_cache_path: ~/.vector_cache
  ignore_columns: []
  include_lengths: true
  id_attr: id
  label_attr: label
  left_prefix: left_
  right_prefix: right_
  use_magellan_convention: false
  pca: true
```

---

## 2. `process_unlabeled`

Passed to `dm.data.process_unlabeled(path=..., trained_model=..., **process_unlabeled)`.

| Parameter        | Type              | Default   | Meaning                                                                                                                                                                                |
|------------------|-------------------|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ignore_columns` | list[str] \| null | `null`    | `null` = automatically reuses the same ignored columns as during training (`trained_model.meta.ignore_columns`). Only set explicitly if the unlabeled CSV has different extra columns. |

```yaml
process_unlabeled:
  ignore_columns: null
```

---

## 3. `model`

Passed to `dm.MatchingModel(**model)`.

| Parameter              | Type        | Default           | Meaning                                                                                                                                                                                                            |
|------------------------|-------------|-------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `attr_summarizer`      | str         | `hybrid`          | How a single attribute (e.g. "title") is summarized into a vector. Options: `sif`, `rnn`, `attention`, `hybrid`.                                                                                                   |
| `attr_condense_factor` | str \| int  | `auto`            | Factor by which the attribute representation is condensed before comparison.                                                                                                                                       |
| `attr_comparator`      | str \| null | `null`            | How the summarized attribute vectors of both sides are compared. Options: `abs-diff`, `diff`, `concat`, `concat-diff`, `concat-abs-diff`, `mul`. `null` = automatic choice based on `attr_summarizer` (see below). |
| `attr_merge`           | str         | `concat`          | How the compared attribute representations of all columns are merged into a single vector. Same option list as `attr_comparator`.                                                                                  |
| `classifier`           | str         | `2-layer-highway` | Transform-network syntax for the final classifier, see below.                                                                                                                                                      |
| `hidden_size`          | int         | `300`             | Size of the hidden representations used throughout the model.                                                                                                                                                      |

**Automatic `attr_comparator` selection when `null`** (from `models/core.py`):

| `attr_summarizer`   | automatically chosen `attr_comparator` |
|---------------------|----------------------------------------|
| `sif`               | `abs-diff`                             |
| `rnn`               | `abs-diff`                             |
| `attention`         | `concat`                               |
| `hybrid`            | `concat-abs-diff`                      |

**`attr_merge` / `attr_comparator` — shared option list** (from `Merge._style_map`):

| Value             | Operation                               |
|-------------------|-----------------------------------------|
| `concat`          | Concatenates both vectors.              |
| `diff`            | `x - y`                                 |
| `abs-diff`        | `\|x - y\|`                             |
| `concat-diff`     | Concatenates `x`, `y`, and `x - y`.     |
| `concat-abs-diff` | Concatenates `x`, `y`, and `\|x - y\|`. |
| `mul`             | Elementwise multiplication `x * y`.     |

**`classifier` syntax** (mini-DSL of the `Transform` class in
`models/modules.py`, parts separated by `-`, order doesn't matter, each
part optional):

- `<N>-layer` — number of linear transform layers (e.g. `2-layer`).
- Non-linearity — one of: `leaky_relu` (default), `relu`, `elu`, `selu`, `glu`, `tanh`, `sigmoid`.
- Bypass — `residual` or `highway`, if desired.

Examples from the docs: `"2-layer-highway"`, `"3-layer-relu-highway"`,
`"tanh-residual-2-layer"`, `"tanh"`, `"highway"`, `"4-layer"`.

```yaml
model:
  attr_summarizer: hybrid
  attr_condense_factor: auto
  attr_comparator: null
  attr_merge: concat
  classifier: 2-layer-highway
  hidden_size: 300
```

---

## 4. `train`

Passed to `model.run_train(train, validation, best_save_path=..., **train)`.

| Parameter           | Type                                  | Default | Meaning                                                                                                                                       |
|---------------------|---------------------------------------|---------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| `epochs`            | int                                   | `30`    | Number of training epochs.                                                                                                                    |
| `criterion`         | `torch.nn.Module` \| null             | `null`  | Loss function. `null` = `SoftNLLLoss` with `label_smoothing` (default behavior).                                                              |
| `optimizer`         | `deepmatcher.optim.Optimizer` \| null | `null`  | `null` = an Adam optimizer is constructed automatically.                                                                                      |
| `pos_neg_ratio`     | int \| null                           | `null`  | Weight of the positive (match) class relative to the negative class — set this if there's significant class imbalance.                        |
| `pos_weight`        | float \| null                         | `null`  | Alternative/additional weighting of the positive class.                                                                                       |
| `label_smoothing`   | float                                 | `0.05`  | Only relevant when `criterion` is `null` (feeds into `SoftNLLLoss`).                                                                          |
| `save_every_prefix` | str \| null                           | `null`  | Path prefix for periodically saving models (e.g. `"checkpoints/model"` → `model_ep1.pth`, `model_ep2.pth`, ...). `null` = no periodic saving. |
| `save_every_freq`   | int                                   | `1`     | How often (in epochs) periodic saving happens (only effective if `save_every_prefix` is set).                                                 |
| `batch_size`        | int                                   | `32`    | Mini-batch size.                                                                                                                              |
| `device`            | str \| null                           | `null`  | `"cpu"` or `"cuda"`. `null` = automatically the first available GPU, otherwise CPU.                                                           |
| `progress_style`    | str                                   | `bar`   | `bar` = progress bar, `log` = text output every `log_freq` batches.                                                                           |
| `log_freq`          | int                                   | `5`     | Number of batches between progress updates.                                                                                                   |
| `sort_in_buckets`   | bool \| null                          | `null`  | Whether examples of similar length are grouped to minimize padding. `null` matches the internal default (`True`).                             |

```yaml
train:
  epochs: 30
  criterion: null
  optimizer: null
  pos_neg_ratio: null
  pos_weight: null
  label_smoothing: 0.05
  save_every_prefix: null
  save_every_freq: 1
  batch_size: 32
  device: null
  progress_style: bar
  log_freq: 5
  sort_in_buckets: null
```

---

## 5. `eval`

Passed to `model.run_eval(test, **eval)`. Same meaning as the identically
named parameters in `train` (minus the training-specific ones like
`epochs`, `criterion`, etc.).

| Parameter         | Type         | Default |
|-------------------|--------------|---------|
| `batch_size`      | int          | `32`    |
| `device`          | str \| null  | `null`  |
| `progress_style`  | str          | `bar`   |
| `log_freq`        | int          | `5`     |
| `sort_in_buckets` | bool \| null | `null`  |

```yaml
eval:
  batch_size: 32
  device: null
  progress_style: bar
  log_freq: 5
  sort_in_buckets: null
```

---

## 6. `prediction`

Passed to `model.run_prediction(unlabeled, **prediction)`.

| Parameter           | Type         | Default | Meaning                                                                |
|---------------------|--------------|---------|------------------------------------------------------------------------|
| `output_attributes` | bool         | `false` | `true` = include all original CSV columns in the result table as well. |
| `batch_size`        | int          | `32`    | as above                                                               |
| `device`            | str \| null  | `null`  | as above                                                               |
| `progress_style`    | str          | `bar`   | as above                                                               |
| `log_freq`          | int          | `5`     | as above                                                               |
| `sort_in_buckets`   | bool \| null | `null`  | as above                                                               |

```yaml
prediction:
  output_attributes: false
  batch_size: 32
  device: null
  progress_style: bar
  log_freq: 5
  sort_in_buckets: null
```

---


## 7. `threshold`

**Not a deepmatcher parameter** — custom post-processing in
`run_deepmatcher.py` that's applied to the `match_score` column of the
DataFrame returned by `model.run_prediction(...)`, before it's saved as a CSV.

| Parameter        | Type   | Default   | Meaning                                                                                                                        |
|------------------|--------|-----------|--------------------------------------------------------------------------------------------------------------------------------|
| `enabled`        | bool   | `false`   | Enable/disable the threshold logic.                                                                                            |
| `mode`           | str    | `fixed`   | How the threshold value is computed, see table below.                                                                          |
| `value`          | float  | `0.8`     | Only for `mode: fixed` — the threshold itself.                                                                                 |
| `fraction`       | float  | `0.1`     | Only for `relative_to_mean` / `relative_to_max`.                                                                               |
| `std_multiplier` | float  | `1.0`     | Only for `mean_minus_std`.                                                                                                     |
| `percentile`     | float  | `90`      | Only for `percentile` (range 0–100).                                                                                           |
| `output_mode`    | str    | `filter`  | `filter` = rows below the threshold are removed. `flag` = all rows are kept, an additional boolean column `is_match` is added. |

**`mode` options in detail:**

| `mode`             | Formula                                                             | When it's useful                                                                                                                                                                                                |
|--------------------|---------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `fixed`            | `threshold = value`                                                 | You already know a good threshold (e.g. from evaluating on the test set) and want to apply it consistently.                                                                                                     |
| `relative_to_mean` | `threshold = mean(match_score) × (1 − fraction)`                    | Automatically adapts to how "confident" the model is overall on this dataset.                                                                                                                                   |
| `relative_to_max`  | `threshold = max(match_score) × (1 − fraction)`                     | Similar, but relative to the best match found rather than the average — useful when most scores are low and only the top ones matter.                                                                           |
| `mean_minus_std`   | `threshold = mean(match_score) − std_multiplier × std(match_score)` | Classic statistical outlier approach: anything more than `std_multiplier` standard deviations below the mean counts as uncertain/non-match. More robust than `relative_to_mean` for skewed score distributions. |
| `percentile`       | `threshold = Percentile(match_score, percentile)`                   | If you want a fixed **count/share** of top matches instead of a score-based cutoff, e.g. `percentile: 90` → keep only the top 10% of rows, regardless of the absolute score values.                             |

```yaml
threshold:
  enabled: true
  mode: relative_to_mean
  fraction: 0.1
  output_mode: filter
```

---

## Full example

See [`config-example.yaml`](config-example.yaml) — all sections are already populated
with the default values and ready to use as-is.