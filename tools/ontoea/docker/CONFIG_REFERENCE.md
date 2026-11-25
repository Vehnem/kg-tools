# Configuration Reference — OntoEA Wrapper

Full overview of all keys supported in `config-example.yaml` / `run_ontoea.py`.

Verified against the OntoEA source at commit
`afa1c79281fdfca5b123fc8e6dfc8ceb41dd4ded` of `ZihengZZH/OntoEA`, by reading
`code/run/main_from_args.py`, `args_hander.py`, `modules/load/kgs.py`,
`modules/utils/check.py`, `models/basic_model.py`, `approaches/ontoea.py` and the
shipped `code/run/args/ontoea_args_15K.json` — not from memory. All defaults below
are the values of `ontoea_args_15K.json` (a script compared every schema default
against that file). Neither the Docker build nor a real OntoEA training run was
exercised in the authoring environment (no TensorFlow 1.14 available); the runner
itself was tested end-to-end against a stub `main_from_args.py` and the real
`MED_BBK_9K` directory layout.

```
config.yaml ──> run_ontoea.py ──> <tmp>/args.json        (flat OntoEA args file)
benchmark dir ─> <tmp>/benchmark/ (symlinks)
                    │
                    └──> python main_from_args.py <tmp>/args.json benchmark <CUDA_VISIBLE_DEVICES>
                              └──> results folder ──> alignment.tsv, evaluation.csv, raw files
```

---

## 1. Input: benchmark directory

`--input` is one directory in the OntoEA benchmark format (the layout of the zips in the
upstream `benchmarks/` folder, e.g. `MED_BBK_9K.zip`, `EN_FR_15K_V1.zip`; unzip them first).
The loader reads exactly these files:

| Path (relative to `--input`)                | Content                                          |
|---------------------------------------------|--------------------------------------------------|
| `rel_triples_1`, `rel_triples_2`            | Relation triples of KG 1 / KG 2                  |
| `attr_triples_1`, `attr_triples_2`          | Attribute triples of KG 1 / KG 2                 |
| `onto_subClassOf_triples`                   | Ontology subclass triples                        |
| `onto_disjointWith_triples`                 | Ontology disjointness triples                    |
| `onto_attr_triples`                         | Ontology attribute triples                       |
| `crossview_link_1`, `crossview_link_2`      | Membership links (entity → class) of KG 1 / KG 2 |
| `class_path.json`                           | Class paths per class                            |
| `<dataset_division>train_links`             | Training alignment                               |
| `<dataset_division>valid_links`             | Validation alignment                             |
| `<dataset_division>test_links`              | Test alignment                                   |

`ent_links` (present in the shipped benchmarks) is not read by the loader and not required.
The runner checks that all required files exist before starting and fails otherwise.

Everything else under `--input` is ignored. `--input` itself is never written to: the runner
works on a temp directory of symlinks (see section 6).

---

## 2. Invocation

```
python run_ontoea.py --input <benchmark_dir> --output <output_dir> --config <config.yaml>
bash ontoea.sh <benchmark_dir> <output_dir> <config.yaml>
```

Environment: `ONTOEA_HOME` (default `/app/OntoEA`) must contain `code/run/main_from_args.py` and
`code/src/openea`. The runner sets `PYTHONPATH` for the subprocess itself.

Upstream's own usage text describes the third argument of `main_from_args.py` as the splits
folder. In the code it is `CUDA_VISIBLE_DEVICES`
(`os.environ["CUDA_VISIBLE_DEVICES"] = sys.argv[3]`), and the split is chosen by
`dataset_division` in the args JSON. The runner follows the code.

---

## 3. Config file format

- YAML with the sections below. Unknown sections or keys abort the run: upstream's
  `ARGs` class accepts any JSON key, so a typo would otherwise be silently ignored.
- Values are type-checked before TensorFlow is started. YAML `true`/`false` for booleans,
  `0`/`1` for the integer flags.
- Omitted keys use the default listed here; only `runtime.cuda_visible_devices` is required.
- Sections are flattened into the flat args JSON upstream expects; the generated
  file is copied to `<output_dir>/ontoea_args.json`.

### 3a. `io`

| Key                | Type   | Default         | Notes                                                                                                                                         |
|--------------------|--------|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| `dataset_division` | string | `721_5fold/1/`  | Split folder relative to `--input`, containing `train_links`, `valid_links`, `test_links`. A trailing `/` is added if missing (upstream concatenates strings). |
| `ordered`          | bool   | `true`          | Passed as `ordered` to `KGs` / `read_kgs_from_folder`, which forwards it to the id-generation functions.                                      |

### 3b. `runtime`

| Key                    | Type   | Default | Notes                                                                                                                                                                  |
|------------------------|--------|---------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `cuda_visible_devices` | string | —       | **Required.** Third CLI argument of `main_from_args.py`, mandatory upstream (no default). Use `''` for CPU. The Docker image has no CUDA, so only `''` is meaningful there. The value is a string, quote numbers (`'0'`). |
| `batch_threads_num`    | int    | `4`     | Number of batch-generation processes.                                                                                                                                  |
| `test_threads_num`     | int    | `8`     | Threads used when ranking test entities.                                                                                                                               |

### 3c. `word_embeddings`

| Key                        | Type   | Default                                    | Notes                                                                                                                                        |
|----------------------------|--------|--------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| `word_embed`               | string | `../../benchmarks/wiki-news-300d-1M.vec`   | Path to a word-vector file. OntoEA reads the key unconditionally, so it must exist in the args file; it is only opened when one of the flags below enables initialisation. The default is upstream's value; that file is **not** shipped in the repository. The runner requires an existing file if a flag is `1`. |
| `use_word_embed_init`      | 0 / 1  | `0`                                        | Initialise entity and relation embeddings from word vectors (`ontoea.py`, `_define_variables`).                                              |
| `use_word_embed_init_onto` | 0 / 1  | `0`                                        | Same for the ontology embeddings.                                                                                                            |
| `word_embed_init_zh`       | 0 / 1  | `0`                                        | Only effective with `use_word_embed_init=1`: tokenise names per character instead of per `_`-separated token.                                |
| `use_alter_label`          | 0 / 1  | `0`                                        | Only effective with `use_word_embed_init=1`: use the loader's `name_dict` (from `attr_triples_*`) as entity names instead of URI tokens.      |

### 3d. `model`

| Key                    | Type   | Allowed                       | Default      | Notes                                                                                                                                            |
|------------------------|--------|-------------------------------|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| `embedding_module`     | string | `OntoEA`                      | `OntoEA`     | `main_from_args.py` can also instantiate `BasicModel` etc. (`ModelFamily`); those do not train the ontology components and are not supported.    |
| `alignment_module`     | string | `mapping`                     | `mapping`    | `OntoEA.init()` asserts `alignment_module == 'mapping'`.                                                                                         |
| `ent_emb_loss`         | string | `limit_loss`, `pos_loss`      | `limit_loss` | `ontoea.py` only handles these two values.                                                                     |
| `onto_training_method` | string | `hier`, `transe`, `linear`    | `hier`       | Loss used for ontology triples.                                                                                                                  |
| `fusion_way`           | string | `add`, `null`                 | `add`        | How entity and class embeddings are fused for evaluation. In the code `add` and `null` take the same branch.                                     |
| `dim`                  | int    |                               | `300`        | Entity/relation embedding dimension.                                                                                                             |
| `onto_dim`             | int    |                               | `300`        | Ontology embedding dimension.                                                                                                                    |
| `init`                 | string | `unit`                        | `unit`       | `OntoEA.init()` asserts `init == 'unit'`.                                                                                                        |
| `ent_l2_norm`          | bool   | `true`                        | `true`       | `OntoEA.init()` asserts it is `true`.                                                                                                            |
| `rel_l2_norm`          | bool   |                               | `true`       |                                                                                                                                                  |
| `loss_norm`            | string | `L1`, `L2`                    | `L2`         | In the loss functions `'L1'` selects the L1 distance, any other value the L2 distance; the runner only accepts the two names.                    |
| `alpha`                | float  | `> 1`                         | `5`          | Weight of the embedding-alignment (mapping) loss. Asserted `> 1`.                                                                                |
| `beta`                 | float  |                               | `0`          | Weight of the pseudo-ontology calibration loss.                                                                                                  |
| `gamma`                | float  |                               | `1`          | Weight of the ontology calibration loss **and** the class-similarity weight (`type_weight` / `onto_weight`) when fusing for evaluation.          |
| `sigma`                | float  |                               | `1`          | Weight of the ontology likelihood loss.                                                                                                          |

### 3e. `ontology`

| Key                      | Type   | Allowed             | Default     | Notes                                                                                                                                                                                                            |
|--------------------------|--------|---------------------|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `cvlink_module`          | string | `swapping`, `null`  | `null`      | Passed as `onto_mode`. `swapping` replaces the head entity of membership links to create more links (`kgs.py`).                                                                                                  |
| `check_version`          | int    | `0`–`5`             | `4`         | Selects the class-compatibility matrix that is computed at start-up (`check_type_coherence`): `0` v1, `1` v2, `2` v3 (considers common parents), `3` v4 (identity only), `4` v5 and `5` v6 (path-set overlap weights). The unexposed parameters `unsure_w` and `k` stay at upstream's `0`. |
| `onto_neg_sampling`      | string | `prob_based`, `null`| `null`      | `prob_based` samples ontology negatives from a softmax over the class-compatibility matrix; otherwise no probability matrix is used.                                                                                                   |
| `likelihood_vaild`       | bool   |                     | `true`      | Enables the ontology likelihood training step per iteration. Spelled `likelihood_vaild` upstream (typo); the wrapper uses the same spelling.                                                                      |
| `onto_likelihood_epochs` | int    |                     | `5`         | Epochs of the likelihood step per iteration.                                                                                                                                                                     |
| `likelihood_slice`       | int    |                     | `10`        | Number of classes per likelihood batch.                                                                                                                                                                          |

### 3f. `sampling`

| Key                      | Type   | Allowed                  | Default      | Notes                                                                                                                                        |
|--------------------------|--------|--------------------------|--------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| `neg_sampling`           | string |                          | `truncated`  | Only the value `truncated` is checked: it enables neighbour-based truncated negative sampling (neighbours are regenerated after every iteration). |
| `truncated_epsilon`      | float  | `(0, 1)`                 | `0.9`        | Asserted to be in `(0, 1)` when `neg_sampling` is `truncated`.                                                                               |
| `neg_triple_num`         | int    |                          | `10`         | Negatives per positive.                                                                                                                      |
| `alignment_neg_sampling` | string | `type_based`, `random`   | `type_based` | `random` samples alignment negatives from all entities; any other value samples from entities of the same class. The runner accepts the two names only. |
| `pos_margin`             | float  |                          | `0.01`       | Margin of the positive part of the limit-based losses.                                                                                       |
| `neg_margin`             | float  |                          | `2.0`        | Margin of the negative part.                                                                                                                 |
| `neg_margin_balance`     | float  |                          | `0.2`        | Balance between positive and negative loss parts.                                                                                            |

### 3g. `training`

| Key                 | Type   | Allowed    | Default   | Notes                                                                                                                                            |
|---------------------|--------|------------|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| `optimizer`         | string | `Adagrad`  | `Adagrad` | `OntoEA.init()` asserts `optimizer == 'Adagrad'`.                                                                                                |
| `learning_rate`     | float  |            | `0.01`    | Entity/relation/ontology learning rate.                                                                                                          |
| `cv_link_lr`        | float  |            | `0.001`   | Learning rate of the membership-link training.                                                                                                   |
| `likelihood_lr`     | float  |            | `0.001`   | Learning rate of the likelihood step.                                                                                                            |
| `max_epoch`         | int    |            | `2000`    | Total epochs. The loop runs `max_epoch // sub_epoch` iterations, so it must be `>= sub_epoch` (enforced by the runner).                         |
| `sub_epoch`         | int    |            | `10`      | Epochs per iteration of entity, ontology and membership-link training.                                                                           |
| `align_sub_epoch`   | int    |            | `5`       | Epochs of the alignment training per iteration.                                                                                                  |
| `batch_size`        | int    |            | `4500`    | Entity-triple batch size.                                                                                                                        |
| `onto_batch_size`   | int    |            | `64`      | Ontology-triple batch size.                                                                                                                      |
| `cvlink_batch_size` | int    |            | `2000`    | Membership-link batch size.                                                                                                                      |

### 3h. `evaluation`

| Key           | Type      | Allowed        | Default         | Notes                                                                                                                                                                  |
|---------------|-----------|----------------|-----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `start_valid` | int       |                | `50`            | Validation starts once `iteration * sub_epoch >= start_valid`.                                                                                                         |
| `eval_freq`   | int       | `>= 1`         | `10`            | Validate every `eval_freq` **iterations** (not epochs). Early stopping is evaluated at each validation.                                                                |
| `stop_metric` | string    | `hits1`, `mrr` | `hits1`         | `hits1` uses Hits@1, any other value MRR.                                                                                                                              |
| `eval_metric` | string    | `inner`        | `inner`         | `OntoEA.init()` asserts `eval_metric == 'inner'`.                                                                                                                      |
| `eval_norm`   | bool      |                | `true`          | L2-normalise embeddings before ranking.                                                                                                                                |
| `csls`        | int       |                | `10`            | `csls_k` of the CSLS evaluation; `0` makes the CSLS line identical to the plain fusion evaluation.                                                                     |
| `top_k`       | list[int] | contains `1`   | `[1, 5, 10, 50]`| Hits@k cut-offs; `1` is required (asserted by the ranking code).                                                                                                      |

### 3i. `output` (wrapper-only)

| Key               | Type | Default | Notes                                                                                           |
|-------------------|------|---------|-------------------------------------------------------------------------------------------------|
| `keep_embeddings` | bool | `true`  | If `false`, `*.npy` files (embedding matrices) are not copied to `--output`. Not an upstream key. |

---

## 4. Fixed and unexposed upstream keys

Written by the runner with fixed values, not configurable:

| Key             | Value     | Why                                                                                                       |
|-----------------|-----------|-----------------------------------------------------------------------------------------------------------|
| `onto_valid`    | `true`    | `main_from_args.py` only builds the ontology-aware KGs for `true`; OntoEA cannot run without them.        |
| `seed_ent_type` | `normal`  | Read by `main_from_args.py` but only used by the `raw` loader branch, which the runner never selects.     |
| `data_version`  | `popular` | Same.                                                                                                     |
| `lang`          | (derived) | Overwritten by `main_from_args.py` with the benchmark folder name.                                        |

Present in the shipped JSON but never read by OntoEA's code and therefore not exposed:
`cvlink_type_sample`, `search_module`, `is_save` (embeddings and results are always saved).
`truncated_freq` is only read by `BasicModel.run`; `OntoEA.run` regenerates neighbours every iteration.

---

## 5. Output

Everything OntoEA writes into its timestamped results folder is copied to `--output`
(a result folder is located by the presence of `alignment_results_12`), plus:

| File                  | Content                                                                                                                                                                       |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `alignment.tsv`       | `uri_kg1<TAB>uri_kg2`, one line per pair in `alignment_results_12`, mapped back from integer ids with `kg1_ent_ids` / `kg2_ent_ids`. Upstream saves the result of the fusion evaluation **without** CSLS only. |
| `evaluation.csv`      | `setting,hits_at_<k>...,mr,mrr` with the rows `entity_only`, `fusion`, `fusion_csls`, parsed from the last three `accurate results` lines of the log (the order of the three evaluations in `OntoEA.test()`). Values are percentages as printed upstream for Hits, raw for MR/MRR. |
| `ontoea_args.json`    | The generated args file.                                                                                                                                                      |
| `ontoea_stdout.log`   | Combined stdout/stderr of the training process.                                                                                                                               |
| `alignment_results_12`, `kg1_ent_ids`, `kg2_ent_ids`, `*.npy` | Raw upstream files (ids, embedding matrices, `mapping_mat` if produced).                                                                    |

Exit code is `1` on config/benchmark errors (before TensorFlow starts), on a non-zero exit of the
training process, if no `alignment_results_12` was produced, or if the three evaluation lines
cannot be found.

---

## 6. Why the runner builds a private benchmark view

- `main_from_args.py` computes `training_data + <benchmark name> + '/'` and chooses the loader by
  substring: a path containing `raw` uses the raw loader, `dbp15k` / `dwy100k` use dataset-specific
  loaders. A mount path such as `/data/raw/...` would silently take the wrong code path. The
  runner places a symlink view at `<tmp>/benchmark/` and re-creates the temp directory if its
  path contains one of these substrings.
- `check_type_coherence` writes `onto_check_mat.h5` into the benchmark folder on every start.
  That would fail on a read-only mount and clutter the input; here it lands in the temp directory.
- The temp directory is deleted when the run ends.

---

## Troubleshooting

| Symptom                                                           | Cause / fix                                                                                                         |
|-------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| `benchmark is missing required files`                             | The directory is not a (unzipped) OntoEA benchmark, or `dataset_division` points to a non-existent split folder.   |
| `ONTOEA_HOME=... does not contain ...`                            | Running outside the Docker image without `ONTOEA_HOME` set to a checkout of the repository.                         |
| `unknown config key: ...`                                         | Typo or a key listed as not exposed in section 4.                                                                   |
| Training is very slow                                             | The image is CPU-only (TensorFlow 1.14, Python 3.6). Reduce `training.max_epoch` or use a smaller benchmark.        |
| `expected 3 'accurate results' lines`                             | Training crashed late or the evaluation printed differently; inspect `ontoea_stdout.log`.                           |
