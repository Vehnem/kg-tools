# CONFIG_REFERENCE.md

Full reference for every key that `run_splink.py` reads from `config.yaml`.
Applies to **Splink >= 4.0** (`SettingsCreator`, `splink.comparison_library`,
`linker.training.*`).

Invocation:

```bash
python run_splink.py --input left.csv --input2 right.csv --output out.csv --config config.yaml
```

`--input2` is only needed for `link_only` / `link_and_dedupe`.
`--threshold` overrides `output.threshold_match_probability` from the
command line.

---

## 1. Backend

| Key | Values | Meaning |
|---|---|---|
| `backend` | `duckdb` \| `sqlite` \| `spark` \| `postgres` | SQL engine Splink runs on. `duckdb` is the default choice for local CSV/Parquet files. |
| `postgres_connection_string` | e.g. `postgresql://user:pw@host:5432/db` | Required only with `backend: postgres`. Used to build a SQLAlchemy engine. |
| `postgres_schema` | schema name, default `splink` | Only with `backend: postgres`. Schema Splink creates its intermediate tables in. |
| `postgres_other_schemas_to_search` | list of schema names | Only with `backend: postgres`. Additional schemas to search for already-existing tables. |

`spark` needs a running `SparkSession` and the `pyspark` installation;
`postgres` needs `sqlalchemy` and a reachable server. For the two CSV files
in this project, `duckdb` is entirely sufficient.

---

## 2. Core settings (`SettingsCreator`)

| Key | Default | Meaning |
|---|---|---|
| `link_type` | `dedupe_only` | `dedupe_only` = one file, find duplicates within it. `link_only` = two (or more) files, only find matches **between** them. `link_and_dedupe` = matches within **and** between the files. For two paper CSV files, `link_only` is the right choice as long as each file is already duplicate-free on its own; otherwise use `link_and_dedupe`. |
| `unique_id_column_name` | `unique_id` | Column that uniquely identifies each record. Here: `id`. Must be unique within each input file, not necessarily across both files. |
| `source_dataset_column_name` | `source_dataset` | Only relevant for `link_only`/`link_and_dedupe`. Name of the column Splink generates to track which input file a record came from. |
| `probability_two_random_records_match` | `0.0001` | Prior probability that two randomly drawn records are a match. Leave as `null` if this value should be estimated via training (`estimate_probability_two_random_records_match`). |
| `em_convergence` | `0.0001` | Convergence threshold for the Expectation Maximisation algorithm (maximum parameter change between two iterations). |
| `max_iterations` | `25` | Maximum number of EM iterations, even if `em_convergence` hasn't been reached yet. |
| `retain_matching_columns` | `true` | Keeps the raw columns used by the comparisons in the result (for manually checking matches). `false` saves memory/time. |
| `retain_intermediate_calculation_columns` | `false` | Keeps intermediate columns such as the per-comparison Bayes factors. `true` only for debugging. |
| `additional_columns_to_retain` | `[]` | Extra columns not used in `comparisons` that should still appear in the output (e.g. labels). |
| `bayes_factor_column_prefix` | `bf_` | Prefix of the generated Bayes-factor columns. |
| `term_frequency_adjustment_column_prefix` | `tf_` | Prefix of the generated term-frequency columns. |
| `comparison_vector_value_column_prefix` | `gamma_` | Prefix of the generated comparison-level columns (gamma values). |

There is **no** separate `sql_dialect` key on `SettingsCreator`: the SQL
dialect in which `sql_condition` strings (blocking rules, `raw` comparisons)
are evaluated is derived automatically from the `db_api` object, i.e. from
`backend` (Section 1).

---

## 3. `blocking_rules_to_generate_predictions`

List of SQL conditions (alias `l.` = left side, `r.` = right side). Only
pairs that satisfy **at least one** rule are compared at all — this is what
makes Splink scale to large datasets. Without blocking rules (empty list),
the full cross product of all record pairs is formed, which becomes
impractical beyond a few thousand rows per file.

Since the year column here is called `"paper year"` (with a space), it must
be quoted with double quotes in SQL: `l."paper year"`.

Rule order doesn't matter for prediction; it only matters for
`training.estimate_parameters_using_expectation_maximisation` (see below),
where each rule drives its own EM training step.

---

## 4. `comparisons`

Each entry describes how one (or several) columns are compared.

| Key | Required | Meaning |
|---|---|---|
| `output_column_name` | yes (or via `raw`) | Name under which the comparison appears in the result. Also used as a fallback for `input_columns` if that's missing. |
| `input_columns` | no | List of the actual column names in the input data, passed to this comparison class as positional arguments. Usually a single column; a few classes (`ForenameSurnameComparison`, `DistanceInKMAtThresholds`, `PostcodeComparison` with lat/long) take several. |
| `comparison_type` | yes (or `raw`) | Alias or exact class name from `splink.comparison_library` (table below). |
| `params` | no | Forwarded 1:1 as keyword arguments to the comparison class's constructor (exception: `term_frequency_adjustments`, `m_probabilities`, `u_probabilities`, see below). The exact parameter names per class are in the table below. |
| `raw` | alternative | A fully hand-written Splink comparison dict (the same structure returned by `comparison.get_comparison(dialect).as_dict()`). Reaches every setting, including a `CustomComparison` with freely defined `comparison_levels`. Passed through unchanged; all other keys of the entry are then ignored. |

### Configurable only via `.configure()`

These three keys may additionally appear in `params`, but `run_splink.py`
automatically filters them out and sets them via `.configure(...)` after
building the comparison (in Splink >= 4 they are no longer constructor
arguments):

| Key | Meaning |
|---|---|
| `term_frequency_adjustments` | `true`/`false`. Weights rare values more heavily than common ones (e.g. a match on a rare venue name counts for more than one on "arXiv"). Requires that the column is also listed under `term_frequency_adjustments.columns` (Section 5). |
| `m_probabilities` | List to set the m-probabilities per comparison level manually instead of via training. |
| `u_probabilities` | List to set the u-probabilities per comparison level manually instead of via training. |

### Table: `comparison_type` aliases and their `params`

`comparison_type` can either be one of the aliases below, or directly the
exact class name from `splink.comparison_library` (e.g.
`CosineSimilarityAtThresholds`), if no alias exists.

| Alias | Splink class | Important `params` keys |
|---|---|---|
| `exact_match` | `ExactMatch` | no required parameters |
| `levenshtein` | `LevenshteinAtThresholds` | `distance_threshold_or_thresholds` (list of edit distances, e.g. `[1, 2]`) |
| `damerau_levenshtein` | `DamerauLevenshteinAtThresholds` | `distance_threshold_or_thresholds` |
| `jaro` | `JaroAtThresholds` | `score_threshold_or_thresholds` (list of similarity scores 0–1, descending) |
| `jaro_winkler` | `JaroWinklerAtThresholds` | `score_threshold_or_thresholds` |
| `jaccard` | `JaccardAtThresholds` | `score_threshold_or_thresholds` |
| `cosine_similarity` | `CosineSimilarityAtThresholds` | `score_threshold_or_thresholds` |
| `distance_function` | `DistanceFunctionAtThresholds` | `distance_function_name` (SQL function name of the backend dialect), `distance_threshold_or_thresholds`, optional `higher_is_more_similar` |
| `pairwise_string_distance` | `PairwiseStringDistanceFunctionAtThresholds` | like `distance_function`, but for array columns with pairwise comparison of all elements |
| `distance_in_km` | `DistanceInKMAtThresholds` | `input_columns` = `[lat_column, long_column]`, `params.km_threshold_or_thresholds` |
| `array_intersect` | `ArrayIntersectAtSizes` | `size_threshold_or_thresholds` (minimum intersection size, list) — only for genuine array columns |
| `name_comparison` | `NameComparison` | `jaro_winkler_thresholds` (default `[0.92, 0.88, 0.7]`), optional `dmeta_col_name` for a phonetic level |
| `forename_surname` | `ForenameSurnameComparison` | `input_columns` = `[forename_column, surname_column]`, `params.jaro_winkler_thresholds`, optional `forename_surname_concat_col_name` |
| `date_of_birth` | `DateOfBirthComparison` | `input_is_string` (bool), `datetime_format` (e.g. `"%Y-%m-%d"`), `datetime_thresholds` (list of numeric values), `datetime_metrics` (list of `day`/`month`/`year`) |
| `absolute_time_difference` | `AbsoluteTimeDifferenceAtThresholds` | like `date_of_birth`, without the name-specific extra levels |
| `absolute_date_difference` | `AbsoluteDateDifferenceAtThresholds` | alias of `absolute_time_difference` |
| `postcode` | `PostcodeComparison` | without extra parameters: postcode-only comparison. With `input_columns: [postcode, long, lat]` and `params.lat_col`, `params.long_col`, `params.km_thresholds`: adds geo-distance levels |
| `email` | `EmailComparison` | no required parameters |

This configuration uses, for the paper data:

- **`title`**: `jaro_winkler` with `score_threshold_or_thresholds: [0.95, 0.9, 0.8]` – titles often only differ by typos or small variations (Unicode, hyphens), Jaro-Winkler is a robust default for this.
- **`authors`**: `jaccard` with `score_threshold_or_thresholds: [0.9, 0.7]` – for comma-separated author names, a token-based similarity is tolerant of order and missing/extra authors.
- **`venue`**: `jaro_winkler` with `score_threshold_or_thresholds: [0.95, 0.85]` – tolerates minor spelling variants of conference/journal names.
- **`paper_year`** (input column `"paper year"`): defined via `raw`, see the box below.

### Why `paper_year` uses `raw` instead of `comparison_type: levenshtein`

Pandas reads a purely numeric CSV column such as `paper year` as an integer
(`int64`) by default, and DuckDB then stores it as `BIGINT`. Splink's string
function `levenshtein()` expects `VARCHAR`, though, and raises a
`Binder Error` if you use `comparison_type: levenshtein` directly on such a
column (`levenshtein(BIGINT, BIGINT)` doesn't exist). The
`comparison_library` classes don't offer a built-in cast parameter for
this, so the comparison is hand-written here via the `raw` escape hatch
with an explicit `CAST(... AS VARCHAR)`:

```yaml
- raw:
    output_column_name: paper_year
    comparison_levels:
      - sql_condition: "\"paper year_l\" IS NULL OR \"paper year_r\" IS NULL"
        label_for_charts: "Null"
        is_null_level: true
      - sql_condition: "\"paper year_l\" = \"paper year_r\""
        label_for_charts: "Exact match"
      - sql_condition: "levenshtein(CAST(\"paper year_l\" AS VARCHAR), CAST(\"paper year_r\" AS VARCHAR)) <= 1"
        label_for_charts: "Levenshtein <= 1"
      - sql_condition: "ELSE"
        label_for_charts: "All other comparisons"
```

Important: in `raw` comparisons you reference columns the way Splink names
them internally — the original column name plus the `_l`/`_r` suffix, here
quoted because of the space: `"paper year_l"` and `"paper year_r"` (not
`l."paper year"`/`r."paper year"` as in the blocking rules — the `l.`/`r.`
alias prefix is only used in `blocking_rules_to_generate_predictions` and
the `training` rules, not inside a comparison).

Alternatives, if you'd rather fix this in the data instead of in the
config:
- Explicitly parse the column as a string before reading it in
  `run_splink.py` (`read_table`) (`dtype={"paper year": str}` in
  `pd.read_csv`), then `comparison_type: levenshtein` also works without
  `raw`.
- Quote the column as text in the CSV file itself (`"2020"` instead of
  `2020`), then pandas will also read it as `object`/string.

Adjust these thresholds after the first test runs based on actual data
quality.

---

## 5. `term_frequency_adjustments`

```yaml
term_frequency_adjustments:
  columns:
    - title
    - authors
    - venue
```

List of **input column names** (not `output_column_name`) for which a
frequency table is computed before training
(`linker.table_management.compute_tf_table(col)`). Only useful for columns
whose associated comparison also has `term_frequency_adjustments: true`
set.

---

## 6. `training`

Each sub-key corresponds to a method on `linker.training`. All keys within
a step are forwarded 1:1 as keyword arguments to that method (except for
the positional arguments explicitly named below).

### `estimate_probability_two_random_records_match`

Calls `linker.training.estimate_probability_two_random_records_match(deterministic_matching_rules, **rest)`.

| Key | Meaning |
|---|---|
| `deterministic_matching_rules` | List of SQL blocking rules that yield (almost) exclusively true matches, e.g. exact match on title + year. Passed as the first positional argument. |
| `recall` | Estimated recall of these deterministic rules (0–1). The lower this is, the more conservative the resulting estimate of `probability_two_random_records_match`. |
| `max_rows_limit` | Optional. Upper bound on the pairs formed internally, to avoid performance issues on very large data. |

### `estimate_u_using_random_sampling`

Calls `linker.training.estimate_u_using_random_sampling(**kwargs)`.

| Key | Meaning |
|---|---|
| `max_pairs` | Number of randomly drawn record pairs used to estimate the u-probabilities (typically `1e6`–`1e7`). More = more accurate but slower. |
| `seed` | Optional random seed for reproducibility. |

### `estimate_parameters_using_expectation_maximisation`

List of training runs. For each entry, the script calls
`linker.training.estimate_parameters_using_expectation_maximisation(blocking_rule, **rest)`.

| Key | Meaning |
|---|---|
| `blocking_rule` | SQL rule restricting the training pairs for this EM run. Choose rules that do **not** block on a column whose comparison is being trained in this specific run, and that overlap with each other as little as possible. Passed as the first positional argument. |
| `estimate_without_term_frequencies` | `true`/`false`. If `true`, m/u are estimated without taking the term-frequency adjustment into account. |
| `fix_probability_two_random_records_match` | `true`/`false`. Holds `probability_two_random_records_match` constant during this EM run. |
| `fix_m_probabilities` | `true`/`false`. Holds already-estimated m-probabilities of other comparisons constant. |
| `fix_u_probabilities` | `true`/`false`. Holds already-estimated u-probabilities of other comparisons constant. |
| `populate_probability_two_random_records_match_from_trained_values` | `true`/`false`. Carries the estimated value over into the global settings after this run. |

### `estimate_m_from_label_column`

Optional single key (not a sub-dict), e.g.:

```yaml
training:
  estimate_m_from_label_column: cluster_id
```

Calls `linker.training.estimate_m_from_label_column(column_name)`, if a
column with known, already-grouped true matches is available. Not set in
this configuration, since no labeled data is available.

---

## 7. `output`

| Key | Meaning |
|---|---|
| `threshold_match_probability` | Only rows with `match_probability >= value` are output. `null` = keep all compared pairs (this is also already passed to `linker.inference.predict(...)` as a threshold, so unnecessary rows aren't even materialised). Can be overridden from the command line via `--threshold`. |
| `threshold_match_weight` | Alternative to `threshold_match_probability`, expressed as a log2 Bayes factor ("match weight"). Only set one of the two; leave the other as `null`. |
| `clustering.enabled` | `true`/`false`. If `true`, instead of individual pairwise predictions a clustering step (`linker.clustering.cluster_pairwise_predictions_at_threshold`) is run, and the result is connected clusters (e.g. one `cluster_id` per presumably identical paper across both files). |
| `clustering.threshold_match_probability` | Match probability above which two records end up in the same cluster. |

---

## 8. Note on the `"paper year"` column

Since the column name contains a space, it must be quoted with double
quotes in every SQL expression (blocking rules, `raw` comparisons), e.g.
`l."paper year" = r."paper year"`. In `input_columns`, on the other hand,
it's given as a plain YAML string without SQL quoting
(`input_columns: ["paper year"]`) — Splink handles the quoting itself when
it builds the comparison SQL internally. `output_column_name` is
deliberately set to `paper_year` (with an underscore) so that the columns
generated in the result (`gamma_paper_year`, `bf_paper_year`, ...) are
themselves free of spaces and thus unproblematic to work with further.

---

## 9. Escape hatch: `raw`

For any setting the table above doesn't cover (e.g. a `CustomComparison`
with freely defined `comparison_levels`, or very specific
`tf_adjustment_weight`/`tf_minimum_u_value` values at the level level), a
comparison entry can contain a `raw` key with the full Splink dict instead
of `comparison_type`/`params`:

```yaml
comparisons:
  - raw:
      output_column_name: title
      comparison_levels:
        - sql_condition: "title_l IS NULL OR title_r IS NULL"
          label_for_charts: "Null"
          is_null_level: true
        - sql_condition: "title_l = title_r"
          label_for_charts: "Exact match"
          tf_adjustment_column: "title"
          tf_adjustment_weight: 1.0
        - sql_condition: "jaro_winkler_similarity(title_l, title_r) >= 0.9"
          label_for_charts: "Jaro-Winkler >= 0.9"
        - sql_condition: "ELSE"
          label_for_charts: "All other comparisons"
```

This dict corresponds exactly to what
`comparison.get_comparison(dialect).as_dict()` returns in Python, and is
passed through unchanged to `SettingsCreator(comparisons=[...])`.