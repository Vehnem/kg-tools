# Splink Paper-Matching – README

This project deduplicates/links two CSV files of paper metadata
(`id, title, authors, venue, "paper year"`) using
[Splink](https://moj-analytical-services.github.io/splink/) (>= 4.0).

Files in this project:

| File | Purpose |
|---|---|
| `run_splink.py` | The actual config-driven runner. |
| `config.yaml` | All content settings (columns, comparison logic, training, output). |
| `CONFIG_REFERENCE.md` | Full explanation of every key in `config.yaml`. |
| `splink.sh` | Convenient shell wrapper around `run_splink.py`. |

---

## 1. Installation

Python 3.9 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install splink pandas pyyaml
```

Only needed if you want to use a backend other than the default `duckdb`
(controlled via `backend:` in `config.yaml`, see `CONFIG_REFERENCE.md`):

```bash
pip install "splink[spark]"      # backend: spark
pip install "splink[postgres]"   # backend: postgres, also requires: sqlalchemy
```

`sqlite` and `duckdb` are already bundled with `splink` and need no extra
installation.

---

## 2. Preparing the data

Both input files need the columns `id`, `title`, `authors`, `venue`,
`paper year`, with `id` unique within each file. Example `left.csv`:

```csv
id,title,authors,venue,paper year
1,Deep Learning for Entity Resolution,"J. Smith, A. Lee",VLDB,2019
2,A Survey on Record Linkage,"M. Müller",SIGMOD,2020
```

`right.csv` in the same format.

---

## 3. Running it

### Directly with Python

```bash
python run_splink.py \
  --input left.csv \
  --input2 right.csv \
  --output matches.csv \
  --config config.yaml
```

The optional `--threshold 0.95` parameter overrides the value set under
`output.threshold_match_probability` in `config.yaml`.

### With the shell wrapper

```bash
chmod +x splink.sh

bash splink.sh left.csv right.csv matches.csv config.yaml
```

With an optional threshold as the fifth argument:

```bash
bash splink.sh left.csv right.csv matches.csv config.yaml 0.95
```

The result (`matches.csv`) contains every record pair whose
`match_probability` is above the configured threshold, including the
`match_probability` column and — depending on `retain_matching_columns` in
`config.yaml` — the compared source columns.

---

## 4. Deduplicating a single file instead of linking two

`splink.sh` is tailored to this project's two-file case
(`link_type: link_only`). For a single file (`link_type: dedupe_only` in
`config.yaml`), call `run_splink.py` directly without `--input2`:

```bash
python run_splink.py --input papers.csv --output duplicates.csv --config config.yaml
```

---

## 5. Adjusting the configuration

All content-related settings (which columns are compared and how, blocking
rules, training steps, thresholds, clustering, backend) live exclusively in
`config.yaml`. Every single key is explained in `CONFIG_REFERENCE.md` —
including why `paper_year` is defined as a `raw` comparison with an
explicit `CAST(... AS VARCHAR)`.

After the first test run, it's worth tuning the following in particular to
match your actual data quality:

- `comparisons[*].params.score_threshold_or_thresholds` or
  `distance_threshold_or_thresholds` – how strict/lenient the comparison is.
- `blocking_rules_to_generate_predictions` – how many candidate pairs are
  compared at all (performance vs. recall).
- `output.threshold_match_probability` – the probability above which a
  pair is output as a match.