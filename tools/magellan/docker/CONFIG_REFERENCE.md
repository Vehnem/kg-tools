# Configuration Reference — Magellan (py_entitymatching) Pipeline

Full overview of all stages, all available `method` values, and their
parameters, as used in `config-example.yaml` / `run_magellan.py`.

Verified against `py_entitymatching==0.4.2` (PyPI package name
`py-entitymatching`) by installing the wheel and inspecting the actual
class constructors, method signatures, and source code — not from
memory. Every stage below has also been exercised end-to-end against a
small synthetic dataset.

Unlike pyJedAI, Magellan does not have a strict "one stage produces one
DataFrame that feeds the next" pipeline. `run_magellan.py` wires the
stages together as:

```
read ltable/rtable
   -> N blockers, combined via union or chain  -> candidate set
   -> (optional) debug_blocker                  -> false-negative report
   -> attach gold labels (if configured)         -> labeled candidate set
   -> feature generation                          -> feature table
   -> (optional) matcher_selection (CV)           -> matcher_selection.csv
   -> per matcher: [train/test split ->] fit -> predict -> evaluate
```

Every section below documents every key the runner reads: its type,
which values it accepts, its default if omitted, and what it drives
in `py_entitymatching`.

---

## 1. `io`

No `method` field. Table paths are resolved relative to `--input`
unless absolute.

```yaml
io:
  ltable: dblp_demo.csv
  rtable: acm_demo.csv
  l_key: id
  r_key: id
  labeled_data: labeled_data_demo.csv   # optional, only needed for ML matchers / evaluation
```

| Key              | Type             | Allowed values                                                       | Default      | Notes                                                                                           |
|------------------|------------------|----------------------------------------------------------------------|--------------|-------------------------------------------------------------------------------------------------|
| `ltable`         | string           | any path, relative to `--input` unless absolute                      | *required*   | Read via `em.read_csv_metadata(path, key=l_key)`.                                               |
| `rtable`         | string           | any path, relative to `--input` unless absolute                      | *required*   | Read via `em.read_csv_metadata(path, key=r_key)`.                                               |
| `l_key`          | string           | must name an existing, unique-valued column in `ltable`              | *required*   | Registered as `ltable`'s Magellan catalog key.                                                  |
| `r_key`          | string           | must name an existing, unique-valued column in `rtable`              | *required*   | Registered as `rtable`'s Magellan catalog key.                                                  |
| `labeled_data`   | string or `null` | any path, relative to `--input` unless absolute; omit/`null` to skip | `null`       | Read with plain `pandas.read_csv` (**not** `em.read_csv_metadata`) — see id-column rules below. |

`labeled_data`, if given, must contain:
- an id column for the left side — any of **`ltable_ID`**, `ltable_id`,
  or `ltable_<l_key>` (the runner accepts all three spellings, checked
  in that order; see section 5),
- the same for the right side (`rtable_ID` / `rtable_id` /
  `rtable_<r_key>`),
- a label column, name configurable via `labeling.label_column`
  (default `label`).

It is required if any `matching.matchers` entry uses an ML method
(section 7a), and optional for rule-based matchers (only needed there
if you also want an evaluation summary).

---

## 2. `blocking`

Module: `pyjedai`-style list under `blocking.blockers`, each blocked
via a class from `py_entitymatching.blocker`. Multiple blockers are
combined with `em.combine_blocker_outputs_via_union` (`union`) or
chained via `block_candset` (`chain`).

| Key          | Type              | Allowed values                | Default                 | Notes                                                   |
|--------------|-------------------|-------------------------------|-------------------------|---------------------------------------------------------|
| `combine`    | string            | `union` \| `chain`            | `union`                 | See strategy description below.                         |
| `blockers`   | list of objects   | see per-`method` tables below | *required*, min 1 entry | Order matters for `chain` (stage 1 = first entry).      |

Every entry under `blockers` shares these common keys, on top of the
`method`-specific ones in the table further down:

| Key                 | Type                      | Allowed values                                                                                                                  | Default                    | Applies to                                                                                                                                             |
|---------------------|---------------------------|---------------------------------------------------------------------------------------------------------------------------------|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`              | string                    | any (used only for logging)                                                                                                     | `method` value             | all                                                                                                                                                    |
| `method`            | string                    | `attr_equivalence_blocker` \| `overlap_blocker` \| `sorted_neighborhood_blocker` \| `rule_based_blocker` \| `black_box_blocker` | *required*                 | all                                                                                                                                                    |
| `block_attr_l`      | string                    | an existing column in `ltable`                                                                                                  | *required*                 | all except `rule_based_blocker`, `black_box_blocker`                                                                                                   |
| `block_attr_r`      | string                    | an existing column in `rtable`                                                                                                  | *required*                 | all except `rule_based_blocker`, `black_box_blocker`                                                                                                   |
| `l_output_attrs`    | list of strings or `null` | any existing `ltable` columns; `null` = key only                                                                                | `null`                     | all — columns carried into the candidate set as `ltable_<attr>`                                                                                        |
| `r_output_attrs`    | list of strings or `null` | any existing `rtable` columns; `null` = key only                                                                                | `null`                     | all — columns carried into the candidate set as `rtable_<attr>`                                                                                        |
| `show_progress`     | bool                      | `true` \| `false`                                                                                                               | `false`                    | all *except* `attr_equivalence_blocker` (no such kwarg, verified via signature)                                                                        |
| `n_jobs`            | integer                   | `-1` (all cores) or `>= 1`                                                                                                      | `1`                        | all — `0` is invalid and will surface as the numpy error described in the [Troubleshooting](#troubleshooting) section if the input happens to be empty |
| `method_params`     | object                    | method-specific, see below                                                                                                      | `{}`                       | `overlap_blocker`, `sorted_neighborhood_blocker`                                                                                                       |
| `rules`             | list of conjunct lists    | see section 7b for the rule syntax                                                                                              | `[]`                       | `rule_based_blocker`                                                                                                                                   |
| `function`          | string                    | `"module.path.func_name"` of `f(ltuple, rtuple) -> bool`                                                                        | *required for this method* | `black_box_blocker`                                                                                                                                    |

### `method` reference

| `method`                         | Class                          | `method_params`                                                                                                                                               |
|----------------------------------|--------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `attr_equivalence_blocker`       | `AttrEquivalenceBlocker`       | none (only the common keys above)                                                                                                                             |
| `overlap_blocker`                | `OverlapBlocker`               | `overlap_size` (int ≥ 1, default `1`), `rem_stop_words` (bool, default `false`), `q_val` (int or `null`, default `null`), `word_level` (bool, default `true`) |
| `sorted_neighborhood_blocker`    | `SortedNeighborhoodBlocker`    | `window_size` (odd int ≥ 3, default `3`) — **see caveats below**                                                                                              |
| `rule_based_blocker`             | `RuleBasedBlocker`             | n/a — uses `rules` instead; needs a blocking feature table (auto-built via `em.get_features_for_blocking`)                                                    |
| `black_box_blocker`              | `BlackBoxBlocker`              | n/a — uses `function` instead                                                                                                                                 |

`q_val` and `word_level` are mutually exclusive tokenization modes for
`OverlapBlocker`: set `word_level: true, q_val: null` for whitespace
tokenization, or `word_level: false, q_val: <int>` for q-gram
tokenization — passing both/neither non-null follows whatever
`py_entitymatching` itself does with conflicting kwargs (not
independently re-validated by the runner).

`blocking.combine` supports two strategies:

- **`union`** (default): every blocker in `blocking.blockers` runs
  independently via `block_tables` on the full `ltable`/`rtable`, and
  the results are merged with `em.combine_blocker_outputs_via_union`
  (a pair survives if *any* blocker produced it).
- **`chain`**: cascading/progressive blocking. The *first* blocker runs
  `block_tables` on the full tables; every *subsequent* blocker runs
  `block_candset` on the previous stage's output (a pair survives only
  if *every* blocker in the chain keeps it). This maps to Magellan's
  own recommended pattern of combining a cheap coarse blocker with a
  more expensive precise one, and is generally more efficient than
  `union` because later stages only re-check an already-shrunk
  candidate set.

```yaml
blocking:
  combine: union   # union | chain
  blockers:
    - name: overlap_name
      method: overlap_blocker
      block_attr_l: name
      block_attr_r: name
      l_output_attrs: [title, authors, paper year]
      r_output_attrs: [title, authors, paper year]
      show_progress: false
      n_jobs: 1
      method_params:
        overlap_size: 1
        rem_stop_words: true
        q_val: null
        word_level: true
```

For `combine: chain`, a second stage looks the same but is applied via
`block_candset` instead of `block_tables` — no config syntax
difference, only the runtime behavior changes based on `combine`.

### ⚠️ Verified `sorted_neighborhood_blocker` caveats (py_entitymatching 0.4.2)

`SortedNeighborhoodBlocker` prints
`WARNING: THIS IS AN EXPERIMENTAL COMMAND. THIS COMMAND IS NOT TESTED.`
at call time, and this is accurate — inspecting `sn_blocker.py` and
running it directly turned up three real bugs/limitations that break
things if not accounted for:

1. It registers a **copy** of `ltable`/`rtable` in the metadata catalog
   instead of the original objects. `combine_blocker_outputs_via_union`
   compares tables by Python object identity (`id(...)`), so combining
   its output with any other blocker's output raises
   `AssertionError: Candidate set list contains different left tables`.
2. It unconditionally adds two extra columns literally named
   `<l_output_prefix>ID` / `<r_output_prefix>ID` (hardcoded `"ID"` in
   `sn_blocker.py`, regardless of your actual key column name), on top
   of the real, correctly-named foreign-key columns. The union step
   misreads these as an output attribute called `ID`, and blows up with
   `KeyError: "None of [Index(['ID'], ...)] are in the [columns]"`
   unless your key column happens to be spelled `ID`.
3. `SortedNeighborhoodBlocker.block_candset()` is a stub that
   unconditionally raises `AssertionError('unimplemented')` — verified
   directly in `sn_blocker.py` (`# It isn't clear what SN on a
   candidate set would mean, throw an AssertionError`). This means it
   can **only** be used as the *first* blocker in a `chain`; using it
   as a later stage raises immediately, with a clear error from
   `run_magellan.py` pointing this out rather than surfacing Magellan's
   raw `AssertionError`.

`run_magellan.py` works around (1) and (2) automatically (`em.set_ltable`,
`em.set_rtable`, and dropping the junk columns) for both `union` and
`chain` — you do not need to do anything in the config, just be aware
this blocker is the fragile one if you extend the runner, and that (3)
is a hard library limitation with no workaround.

---

## 3. `candidate_set`

Deduplicates the (possibly unioned) candidate set on the foreign-key
pair. No `method` field.

```yaml
candidate_set:
  drop_duplicates: true
```

| Key                 | Type | Allowed values    | Default   | Notes                                                                                                                                                                                   |
|---------------------|------|-------------------|-----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `drop_duplicates`   | bool | `true` \| `false` | `true`    | Drops on `(ltable_<l_key>, rtable_<r_key>)`; harmless to leave on for `chain`, since chaining already can't introduce duplicates across a single pass, but a no-op there costs nothing. |

---

## 4. `debug_blocker`

Wraps `em.debug_blocker`, which estimates which blocked-out pairs were
likely true matches (false negatives of blocking), for manual review.
Writes a CSV, does not affect the pipeline.

```yaml
debug_blocker:
  enabled: false
  output_size: 200
  n_jobs: 1
  output_path: debug_blocker_output.csv
```

| Key             | Type      | Allowed values                         | Default                    | Notes                                                                |
|-----------------|-----------|----------------------------------------|----------------------------|----------------------------------------------------------------------|
| `enabled`       | bool      | `true` \| `false`                      | `false`                    | Whole stage is skipped if `false`.                                   |
| `output_size`   | integer   | `>= 1`                                 | `200`                      | Number of candidate false-negative pairs `em.debug_blocker` returns. |
| `n_jobs`        | integer   | `-1` or `>= 1`                         | `1`                        | See the `n_jobs` note under section 2.                               |
| `output_path`   | string    | any filename, written under `--output` | `debug_blocker_output.csv` |                                                                      |

---

## 5. `labeling`

Merges `io.labeled_data` into the candidate set on
`(ltable_<l_key>, rtable_<r_key>)`.

```yaml
labeling:
  strategy: from_file   # from_file | none
  label_column: label
```

| Key              | Type    | Allowed values                                                         | Default   | Notes                                                                                                           |
|------------------|---------|------------------------------------------------------------------------|-----------|-----------------------------------------------------------------------------------------------------------------|
| `strategy`       | string  | `from_file` \| `none`                                                  | `none`    | `none` (or omitting `io.labeled_data`) skips this stage entirely — only `rule_based` matchers can be used then. |
| `label_column`   | string  | any name — must match the column actually present in `io.labeled_data` | `label`   | Also the target column name Magellan matchers `fit`/`predict` against.                                          |

**Id-column matching (`ltable`/`rtable` side of the merge).** The
labeled CSV's id columns are not guaranteed to spell/case-match the
table's own key column name — e.g. the tables use `l_key: id` but the
labeled CSV follows the common benchmark convention of literal
`ltable_ID`/`rtable_ID` columns instead of `ltable_id`/`rtable_id`.
The runner checks, per side, in this order and uses the first match:

1. `ltable_ID` / `rtable_ID` (fixed literal — the common benchmark convention)
2. `ltable_id` / `rtable_id` (fixed literal, lowercase)
3. `ltable_<l_key>` / `rtable_<r_key>` (derived from `io.l_key`/`io.r_key`)

If none of the three is present on a side, or `label_column` isn't a
column in `io.labeled_data` at all, the runner raises a clear
`ValueError` naming the columns it looked for and the columns it
actually found — instead of silently producing 0 labeled rows.

**Dtype safety.** The join itself is performed on string-cast copies
of the id columns (not the raw dtypes) so that e.g. `int64` ids in the
candidate set (produced by `em.read_csv_metadata`) still match
string/object ids from the plain `pandas.read_csv` read of
`io.labeled_data`, even though the two readers can infer different
dtypes for what is otherwise the same id value.

**Fail-fast on 0 matched rows.** If the merge still produces 0 rows
after all of the above (e.g. the id *values* genuinely don't overlap,
or blocking discarded every true match), the runner raises a
`ValueError` immediately at this stage — see
[Troubleshooting](#troubleshooting) for why this matters.

---

## 6. `feature_generation`

Wraps `em.get_features_for_matching(ltable, rtable)`, which
auto-generates a feature table from attribute types (verified sim
functions: `abs_norm, affine, cosine, dice, exact_match, hamming_dist,
hamming_sim, jaccard, jaro, jaro_winkler, lev_dist, lev_sim,
monge_elkan, needleman_wunsch, overlap_coeff, rel_diff,
smith_waterman`; verified tokenizers: `alphabetic, alphanumeric,
dlm_dc0, qgm_2, qgm_3, wspace`).

```yaml
feature_generation:
  validate_inferred_attr_types: false
  select_features: null      # e.g. [name_name_lev_sim, zipcode_zipcode_exm]
  attrs_before: null
  attrs_after: null
  blackbox_features: []      # e.g. [{feature_name: custom_sim, function: myfeatures.custom_sim}]
  show_progress: false
  n_jobs: 1
```

| Key                               | Type                      | Allowed values                                                               | Default           | Notes                                                                                                                                                                                          |
|-----------------------------------|---------------------------|------------------------------------------------------------------------------|-------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `validate_inferred_attr_types`    | bool                      | `true` \| `false`                                                            | `false`           | `true` pauses for interactive y/n confirmation of inferred attribute types — do **not** set `true` in Docker/CI, there is no stdin to answer it.                                               |
| `select_features`                 | list of strings or `null` | must be `feature_name` values that exist in the auto-generated feature table | `null` (keep all) | Row filter on the feature table.                                                                                                                                                               |
| `attrs_before`                    | list of strings or `null` | existing candidate-set columns                                               | `null`            | Extra non-feature columns to prepend in the feature-vector output, via `em.extract_feature_vecs`.                                                                                              |
| `attrs_after`                     | list of strings or `null` | existing candidate-set columns                                               | `null`            | Same, but appended. **The runner always appends the label column here itself** (see below) — you don't need to list it.                                                                        |
| `blackbox_features`               | list of objects           | `{feature_name: <string>, function: "module.path.func_name"}`                | `[]`              | Adds custom features via `em.add_blackbox_feature`; `function` is `f(ltuple, rtuple) -> value`.                                                                                                |
| `show_progress`                   | bool                      | `true` \| `false`                                                            | `false`           | Passed to `em.extract_feature_vecs`.                                                                                                                                                           |
| `n_jobs`                          | integer                   | `-1` or `>= 1`                                                               | `1`               | See the `n_jobs` note under section 2 — this is the parameter most likely to surface the [Troubleshooting](#troubleshooting) error if upstream stages produced an empty labeled candidate set. |

The label column (from section 5) is always kept through feature
extraction — the runner appends it to `attrs_after` for you, so ML
matchers can train against it without you listing it in the config.

Feature vectors themselves are produced via
`em.extract_feature_vecs(candset, feature_table=..., attrs_before=...,
attrs_after=...)`, run once per pipeline execution and shared across
all ML matchers. The runner checks the result is non-empty immediately
after this call (see [Troubleshooting](#troubleshooting)).

---

## 7. `matching`

Module: `pyjedai`-style dict under `matching.matchers`, each with a
`method`. Two fundamentally different families, matching the DeepMatcher
config style you've used before.

Common keys under each `matching.matchers.<name>` entry:

| Key                | Type                   | Allowed values                                                                                                                                                          | Default                                       | Applies to        |
|--------------------|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|-------------------|
| `method`           | string                 | `decision_tree` \| `random_forest` \| `svm` \| `naive_bayes` \| `logistic_regression` \| `linear_regression` \| `xgboost` (only if `xgboost` installed) \| `rule_based` | *required*                                    | all               |
| `method_params`    | object                 | forwarded verbatim as `**kwargs` to the underlying estimator constructor (see 7a)                                                                                       | `{}`                                          | ML matchers only  |
| `train_test_split` | object                 | `{train_proportion: float, random_state: int or null}`                                                                                                                  | `{train_proportion: 0.5, random_state: null}` | ML matchers only  |
| `rules`            | list of conjunct lists | see section 7b                                                                                                                                                          | `[]`                                          | `rule_based` only |

### 7a. ML matchers (train/test split → `fit` → `predict`)

| `method`                 | Class              | Notes                                                                                            |
|--------------------------|--------------------|--------------------------------------------------------------------------------------------------|
| `decision_tree`          | `DTMatcher`        | wraps `sklearn.tree.DecisionTreeClassifier`                                                      |
| `random_forest`          | `RFMatcher`        | wraps `sklearn.ensemble.RandomForestClassifier`                                                  |
| `svm`                    | `SVMMatcher`       | wraps `sklearn.svm.SVC`                                                                          |
| `naive_bayes`            | `NBMatcher`        | wraps `sklearn.naive_bayes.GaussianNB`                                                           |
| `logistic_regression`    | `LogRegMatcher`    | wraps `sklearn.linear_model.LogisticRegression`                                                  |
| `linear_regression`      | `LinRegMatcher`    | wraps `sklearn.linear_model.LinearRegression`                                                    |
| `xgboost`                | `XGBoostMatcher`   | wraps `xgboost.sklearn.XGBClassifier` — **only registered if `xgboost` is installed**, see below |

`method_params` are forwarded verbatim as `**kwargs` to the underlying
scikit-learn (or XGBoost) estimator constructor — verified via
`inspect.getsource`, e.g. `DTMatcher.__init__` does
`self.clf = DecisionTreeClassifier(*args, **kwargs)`. Allowed keys and
values are therefore whatever the wrapped constructor accepts (e.g.
for `random_forest`: `n_estimators` int ≥ 1, `max_depth` int or
`null`, `random_state` int or `null`, ... — see the scikit-learn docs
for the full list per estimator).

```yaml
random_forest_default:
  method: random_forest
  method_params:
    n_estimators: 100
    random_state: 42
  train_test_split:
    train_proportion: 0.5
    random_state: 42
```

| `train_test_split` key   | Type          | Allowed values                           | Default   | Notes                                                                                                                                                                                                                                                                                                       |
|--------------------------|---------------|------------------------------------------|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `train_proportion`       | float         | `0.0 < x < 1.0`                          | `0.5`     | Drives `em.split_train_test`. The runner requires the shared feature-vector table to have **at least 2 rows** before calling this, since a too-small table (or an extreme proportion) can floor one side of the split to 0 rows and trip the same failure described in [Troubleshooting](#troubleshooting). |
| `random_state`           | int or `null` | any int, or `null` for non-deterministic | `null`    |                                                                                                                                                                                                                                                                                                             |

#### `em.XGBoostMatcher` — yes, it exists, but it's optional

`py_entitymatching`'s `__init__.py` imports it defensively:

```python
try:
    from py_entitymatching.matcher.xgboostmatcher import XGBoostMatcher
except ImportError:
    pass
```

So `em.XGBoostMatcher` is only available if the separate `xgboost`
package is installed (`pip install xgboost`); it is **not** a hard
dependency of `py-entitymatching` itself (confirmed: `xgboost` is
absent from `pip show py-entitymatching`'s `Requires:` list). If it's
missing, `run_magellan.py` simply omits `"xgboost"` from the matcher
registry rather than crashing at import time — using `method: xgboost`
in the config without the package installed raises a clear
`ImportError` from inside `XGBoostMatcher.__init__` at matcher-build
time, with the message it ships:
*"Check if xgboost library is installed..."*.

`XGBoostMatcher(*args, **kwargs)` forwards everything to
`xgboost.sklearn.XGBClassifier(*args, **kwargs)`; recent `xgboost`
versions warn (not error) if you still pass the removed
`use_label_encoder` kwarg — safe to drop it from `method_params`.

### 7b. Rule-based matcher (no training)

| `method`        | Class                | Notes                                                                                                                                                                                            |
|-----------------|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `rule_based`    | `BooleanRuleMatcher` | operates directly on the candidate set (or feature vectors); no `fit` against labels required, though `BooleanRuleMatcher.fit()` exists for internal bookkeeping and is not called by the runner |

Rules are conjunct lists exactly like `RuleBasedBlocker`'s rules
(section 2), referencing feature names from the same feature table,
e.g. `"title_title_lev_sim(ltuple, rtuple) > 0.7"`.

| Key       | Type                        | Allowed values                                                                                                                                                                                | Default   | Notes                                                                        |
|-----------|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------|------------------------------------------------------------------------------|
| `rules`   | list of lists of strings    | each inner list is a set of AND-ed conjuncts; each conjunct is a Python boolean expression string referencing `feature_name(ltuple, rtuple)` values from `feature_generation`'s feature table | `[]`      | Multiple entries under `rules` are OR-ed together (disjunctive normal form). |

```yaml
name_rule_check:
  method: rule_based
  rules:
    - ["title_title_lev_sim(ltuple, rtuple) > 0.7"]
```

Each entry in `rules` is itself a list of conjuncts (AND-ed together);
multiple entries under `rules` are OR-ed by `BooleanRuleMatcher`
(standard Magellan disjunctive-normal-form rule semantics).

---

## 8. `matcher_selection` (optional)

Wraps `em.select_matcher`, which runs k-fold cross-validation over a
list of already-configured ML matchers and picks the best one by a
chosen metric. Verified return structure:
`OrderedDict({'selected_matcher': <fitted-ish matcher object>,
'cv_stats': <DataFrame per candidate matcher>, 'drill_down_cv_stats':
<per-fold detail>})`.

```yaml
matcher_selection:
  enabled: false
  candidates: [random_forest_default, xgb_default]   # must all be ML matchers from matching.matchers
  metric_to_select_matcher: f1        # precision | recall | f1
  metrics_to_display: [precision, recall, f1]
  k: 5
  random_state: 42
  output_csv: matcher_selection.csv
```

| Key                          | Type                      | Allowed values                                                    | Default                                            | Notes                                                                                                                                                                                                                                                                                                               |
|------------------------------|---------------------------|-------------------------------------------------------------------|----------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `enabled`                    | bool                      | `true` \| `false`                                                 | `false`                                            | Whole stage skipped if `false`.                                                                                                                                                                                                                                                                                     |
| `candidates`                 | list of strings or `null` | names that exist under `matching.matchers` and use an ML `method` | `null` (= every ML matcher in `matching.matchers`) | Rule-based matchers listed here are rejected with a clear error.                                                                                                                                                                                                                                                    |
| `metric_to_select_matcher`   | string                    | `precision` \| `recall` \| `f1`                                   | `precision`                                        |                                                                                                                                                                                                                                                                                                                     |
| `metrics_to_display`         | list of strings           | any subset of `precision`, `recall`, `f1`                         | `[precision, recall, f1]`                          | Only affects which columns land in `cv_stats`/`matcher_selection.csv`.                                                                                                                                                                                                                                              |
| `k`                          | integer                   | `>= 2`                                                            | `5`                                                | Number of CV folds. With a very small labeled feature-vector table, `k` larger than the number of examples in the smallest class will make `em.select_matcher`'s internal fold-splitting fail with the same class of error as [Troubleshooting](#troubleshooting) — lower `k` (or label more data) if you hit this. |
| `random_state`               | int or `null`             | any int, or `null` for non-deterministic                          | `null`                                             |                                                                                                                                                                                                                                                                                                                     |
| `output_csv`                 | string                    | any filename, written under `--output`                            | `matcher_selection.csv`                            |                                                                                                                                                                                                                                                                                                                     |

- Runs **in addition to**, not instead of, the normal per-matcher
  train/predict loop in section 7 — it's a reporting/decision-support
  step. All configured matchers still get their own
  `<matcher_name>.csv` and a row in `evaluation.csv`; this stage
  additionally writes `matcher_selection.csv` (one row per candidate,
  with average precision/recall/F1 across the `k` folds) and logs which
  matcher `select_matcher` picked.
- Uses fresh matcher instances (built the same way as in section 7),
  separate from the ones used for the final train/test-split
  train+predict — `select_matcher` fits each candidate internally
  during cross-validation, so reusing an already-fit object would be
  incorrect.
- Runs on the **full** labeled feature-vector table (not the
  train/test split used elsewhere), since cross-validation does its
  own internal splitting.

---

## 9. `evaluation`

No `method` field. `run_magellan.py` calls `em.eval_matches(predictions,
label_column, "predicted_label")` for every matcher that had labels
available, and writes one row per matcher.

```yaml
evaluation:
  output_csv: evaluation.csv
```

| Key            | Type    | Allowed values                         | Default          | Notes                                                                 |
|----------------|---------|----------------------------------------|------------------|-----------------------------------------------------------------------|
| `output_csv`   | string  | any filename, written under `--output` | `evaluation.csv` | Only written at all if at least one matcher produced an eval summary. |

Output columns: `matcher, method, precision, recall, f1`.

---

## Outputs

For every entry under `matching.matchers`, `run_magellan.py` writes
`<output_dir>/<matcher_name>.csv` with predictions (and, for ML
matchers, only the held-out test split; for `rule_based`, the full
input table). `evaluation.csv` aggregates precision/recall/F1 across
all matchers that had ground truth to compare against. If
`matcher_selection.enabled: true`, `matcher_selection.csv` additionally
reports cross-validated precision/recall/F1 per candidate matcher.

---

## Interactive labeling (`label_candidates.py`)

Separate script, not part of `run_magellan.py`. `em.label_table()` —
verified via source (`py_entitymatching/labeler/labeler.py`) — launches
a **PyQt5-based GUI** (`py_entitymatching.gui.table_gui.edit_table`)
and blocks until the window is closed; it is not a terminal y/n loop.
That's fundamentally incompatible with a headless `--input/--output/
--config` batch script (and with the Dockerfile's container, which has
no display).

```bash
python label_candidates.py --input <input_dir> --output <output_dir> --config <config.yaml> \
    [--sample-size N] [--seed 42]
```

| CLI flag          | Type    | Allowed values   | Default                                     | Notes                                    |
|-------------------|---------|------------------|---------------------------------------------|------------------------------------------|
| `--sample-size`   | integer | `>= 1`, or omit  | omit (label the full blocked candidate set) | Downsamples via `em.sample_table` first. |
| `--seed`          | integer | any int          | `None`                                      | Passed as the sampling `random_state`.   |

It reuses the exact same `io` + `blocking` sections from the given
config (via `run_magellan.load_tables` / `run_magellan.run_blocking`),
so the candidate set you label matches what the pipeline will actually
see. Writes `<output_dir>/labeled_pairs.csv` in exactly the format
`io.labeled_data` expects (`ltable_ID`, `rtable_ID`, `<label_column>`
from `labeling.label_column`), so its output can be pointed to
directly — and note this is the fixed `ltable_ID`/`rtable_ID` spelling
that section 5's id-column matching checks first.

Requires `PyQt5` (`pip install PyQt5`), deliberately **not** pinned in
`requirements.txt` since it's only needed for this one interactive
workflow — installing it pulls in Qt system libraries that the batch
pipeline and Docker image have no use for. Run this locally, on a
machine with a display.

The blocking/config-reuse and CSV-export parts of this script were
tested end-to-end (with `em.label_table` stubbed out, since this
sandbox has neither `PyQt5` nor a display); the GUI call itself could
not be exercised here and should be smoke-tested on your machine before
relying on it.

---

## Troubleshooting

### `ValueError: number sections must be larger than 0.`

This is a **numpy** error (`np.array_split(x, 0)`), not a
`py_entitymatching` one — but it surfaces from inside
`em.extract_feature_vecs`, `matcher.fit`/`.predict`, and
`em.select_matcher`, which all parallelize by computing their chunk
count as `min(n_jobs, len(table))` and then splitting the table into
that many chunks. **If the table they're handed has 0 rows, the chunk
count becomes 0** and `np.array_split` raises exactly this message —
several stages downstream of whatever actually caused the table to be
empty, which is what makes it confusing to debug from the traceback
alone.

The runner now checks table sizes at each stage boundary and raises a
specific, actionable `ValueError` at the point something actually went
to 0 rows, instead of letting execution continue into this generic
failure later:

1. **After `labeling`** (section 5): 0 rows usually means either the
   candidate set and `io.labeled_data` don't share any
   `(ltable_ID, rtable_ID)`-style id pairs (check the id *values* on
   both sides, not just the column names), or `blocking` (section 2)
   is too aggressive and is discarding every pair that has a label.
2. **After `extract_features`** (section 6): 0 feature vectors out of
   a non-empty labeled candidate set points at `feature_generation`
   config (e.g. `select_features` filtering everything out).
3. **Before `em.split_train_test`** (section 7a): fewer than 2 labeled
   feature vectors total — either label more data, or (for a quick
   test run) lower `train_test_split.train_proportion` won't help
   here, you need more rows, not a different split.
4. **`matcher_selection.k`** (section 8): a `k` larger than the number
   of examples in the smaller class will hit the same failure inside
   `em.select_matcher`'s own fold-splitting — lower `k`.

If you hit this error somewhere *not* covered above, it's still almost
always "some table upstream had 0 rows" — add a quick
`log.info("... %d rows", len(df))` at the suspected stage to confirm,
rather than trying to interpret the numpy traceback directly.

---

## Not (yet) implemented

The following genuine `py_entitymatching` capabilities exist in the
library but are **not** wired into `run_magellan.py` / this config
schema, to keep the reference honest about what has actually been
built and tested:

- `MatchTrigger` (post-matching business-rule triggers that can
  override `predicted_label` after the fact). Verified to exist
  (`add_cond_rule`, `add_action`, `execute`), but overlaps heavily in
  practice with configuring an additional `rule_based` matcher, and
  wiring it in as a genuine post-processing step over an ML matcher's
  output would need its own config section — happy to add if you have
  a concrete use case that a `rule_based` matcher can't already cover.
- `block_tuples` (single-tuple-pair blocking check) — a debugging
  utility for one pair at a time, not a batch operation; the runner
  only calls `block_tables` / `block_candset`.

---

## Environment note (verified)

`py_entitymatching==0.4.2` (and its dependency `py-stringsimjoin`,
used internally by `OverlapBlocker`/`SortedNeighborhoodBlocker`) is
**not compatible with pandas ≥ 2.2's default backend on pandas 3.x**:
importing/running it under pandas 3.0 raises
`TypeError: Cannot interpret '<StringDtype(...)>' as a data type`
inside `py_stringsimjoin`. Pin `pandas<2.2,>=2.0` (see
`requirements.txt` / `Makefile`) — this was reproduced and fixed
directly during development of this pipeline, not a hypothetical.