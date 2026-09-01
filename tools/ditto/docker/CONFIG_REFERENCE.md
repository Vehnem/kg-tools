# Ditto Config Reference (`ditto_config.yaml`)

Ditto ([megagonlabs/ditto](https://github.com/megagonlabs/ditto), `master`
branch) does not ship a single config file of its own. Every setting is
normally passed as a command line flag to one of its scripts:

| Script                                              | Purpose                                               |
|-----------------------------------------------------|-------------------------------------------------------|
| `matcher.py`                                        | Run a trained model on candidate pairs (inference)    |
| `train_ditto.py`                                    | Fine-tune a new matching model                        |
| `blocking/blocker.py` / `blocking/train_blocker.py` | Optional blocking step that generates candidate pairs |
| `configs.json`                                      | Registry of *tasks* (dataset name → file paths)       |

`ditto_config.yaml` collects all of these flags into one file, and
`run_ditto.py` translates it back into the exact CLI call Ditto expects.

**Verification note:** every field below, and every default value shown, was
checked directly against the `argparse` definitions in Ditto's own
`matcher.py`, `train_ditto.py`, and (for the `blocking` section)
`blocking/train_blocker.py` / `blocking/blocker.py`, plus the upstream
`README.md`, as of the current `master` branch. Two fields that appeared in
earlier drafts of this config - `matching.threshold`, `matching.batch_size`,
and `model.seed` - were **removed from the YAML entirely** because they are
not wired to anything Ditto actually reads; see the dedicated notes below
for what happens instead.

> **Terminology note:** Ditto does not have interchangeable "matcher
> algorithms" the way classic record-linkage toolkits do. It is a single
> matching approach — a pre-trained language model (LM) fine-tuned as a
> sequence-pair classifier. What *is* configurable is **which LM backbone**
> is used (`model.lm`) and which of Ditto's three optimizations
> (data augmentation, domain knowledge, summarization) are switched on. This
> config treats those as "the matcher and how it's configured".

---

## Top-level: `mode`

```yaml
mode: match   # or: train
```

Controls which underlying script `run_ditto.py` calls.

| Value     | Effect                                                                                                                                |
|-----------|---------------------------------------------------------------------------------------------------------------------------------------|
| `match`   | Calls `matcher.py`. Requires `--input`/`--output` (CLI) or `paths.input_path`/`paths.output_path` (config), and a trained checkpoint. |
| `train`   | Calls `train_ditto.py`. Reads `trainset`/`validset`/`testset` from `configs.json` via `task.name` — no `--input`/`--output` needed.   |

---

## `task`

```yaml
task:
  name: "Structured/Beer"   # --task
```

| Field  | Ditto flag | Type   | Description |
|--------|-----------|--------|--------------|
| `name` | `--task`  | string | Must match the `"name"` field of an entry in Ditto's `configs.json`. That entry defines where the task's `trainset`, `validset`, and `testset` files live. Both `matcher.py` and `train_ditto.py` load `configs.json` from the current working directory at runtime, which is why `run_ditto.py` `cd`s into `paths.ditto_repo` before invoking either script. |

Example `configs.json` entry:

```json
{
  "name": "Structured/Beer",
  "trainset": "data/er_magellan/Structured/Beer/train.txt",
  "validset": "data/er_magellan/Structured/Beer/valid.txt",
  "testset":  "data/er_magellan/Structured/Beer/test.txt"
}
```

The `validset` is also used by `matcher.py` at prediction time to
auto-tune the decision threshold (see the note under `mode: match` behaviour
below).

---

## `paths`

```yaml
paths:
  ditto_repo: "./ditto"
  checkpoint_path: "checkpoints/"
  input_path: "input/candidates.jsonl"
  output_path: "output/matched.jsonl"
```

| Field               | Ditto flag                                       | Description                                                                                                                                                                                                                                                                                                                                                     |
|---------------------|--------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ditto_repo`        | *(none — used by `run_ditto.py` only)*           | Local path to your clone of `megagonlabs/ditto`. The wrapper `cd`s into this directory before invoking `matcher.py` / `train_ditto.py`, since those scripts expect to run from the repo root (they look for `configs.json` there via a relative path).                                                                                                          |
| `checkpoint_path`   | `--checkpoint_path` (match) / `--logdir` (train) | Directory containing (match) or receiving (train) the checkpoint. Verified default in both scripts: `checkpoints/`. The checkpoint file itself is always at `<checkpoint_path>/<task.name>/model.pt` — this exact join (`os.path.join(path, task, 'model.pt')`) is hardcoded in `matcher.py`'s `load_model()`.                                                  |
| `input_path`        | `--input_path`                                   | Fallback for `--input` if not given on the command line. JSON-lines file, one `[entry_1, entry_2]` pair per line, where each entry is either a serialized string or a `{"attr": "value", ...}` object. `matcher.py` also accepts a `.txt` file in Ditto's tab-separated training format; if the path contains `.txt`, it is converted to a `.jsonl` file first. |
| `output_path`       | `--output_path`                                  | Fallback for `--output`. JSON-lines file; each line is `{"left": ..., "right": ..., "match": 0                                                                                                                                                                                                                                                                  |1, "match_confidence": float}`. |

---

## `model`

Settings describing the language-model backbone. **Must be identical
between training and matching** for a given checkpoint — a checkpoint
trained with `lm: bert` cannot be loaded with `lm: distilbert`.

```yaml
model:
  lm: distilbert
  max_len: 256
  use_gpu: true
  fp16: true
```

| Field       | Ditto flag    | Type      | Verified default            | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|-------------|---------------|-----------|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `lm`        | `--lm`        | string    | `distilbert` (both scripts) | Pre-trained language model backbone used to encode each serialized pair. The upstream `README.md` officially documents 3 values: `bert`, `distilbert`, `albert`. In practice, the project's own benchmarking script (`run_all_er_magellan.py`) also runs Ditto with `roberta` and `xlnet`, and both appear in public issue reports as working — but only `bert`/`distilbert`/`albert` are covered by the README as "supported". Use `roberta`/`xlnet` at your own risk if your checkpoint was trained with the exact same value. |
| `max_len`   | `--max_len`   | int       | `256` (both scripts)        | Max number of sub-word tokens per serialized input; longer sequences are truncated (or shortened by `summarization` if enabled). The README's own example commands use `64` for training on small benchmark datasets — `256` is only the code-level default, not necessarily what you want for your data.                                                                                                                                                                                                                        |
| `use_gpu`   | `--use_gpu`   | boolean   | `false` (store_true flag)   | **Match mode only.** If true, runs on CUDA when available, otherwise CPU. `train_ditto.py` has no `--use_gpu` flag: it calls `torch.cuda.manual_seed_all()` and otherwise relies on the model/tensors being moved to CUDA automatically whenever `torch.cuda.is_available()`, i.e. training always tries to use a visible GPU.                                                                                                                                                                                                   |
| `fp16`      | `--fp16`      | boolean   | `false` (store_true flag)   | Enables half-precision (mixed precision) training/inference via NVIDIA Apex (`from apex import amp`). Requires Apex installed and a CUDA GPU; ignored on CPU.                                                                                                                                                                                                                                                                                                                                                                    |

### Removed field: `seed`

Earlier drafts of this config had a `model.seed` field. It has been removed
because **neither script reads it**:

- `matcher.py` calls `set_seed(123)` at the very start of `__main__` and
  again inside `tune_threshold()` — the seed for matching is always
  hardcoded to `123`, unconditionally.
- `train_ditto.py` does not call any user-supplied seed either; it seeds
  `random`, `numpy`, and `torch` with `training.run_id` (see below), not a
  separate seed field.

If you need reproducible training runs, change `training.run_id` instead.

---

## `training` (train mode only)

```yaml
training:
  run_id: 0
  batch_size: 64
  lr: 3.0e-5
  n_epochs: 20
  finetuning: true
  save_model: true
  logdir: "checkpoints/"
  size: null
```

| Field           | Ditto flag         | Type          | Verified default          | Description                                                                                                                                                                                                                                                                                 |
|-----------------|--------------------|---------------|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `run_id`        | `--run_id`         | int           | `0`                       | Run identifier; also used directly as the random seed for `random.seed()`, `np.random.seed()`, `torch.manual_seed()`, and (if CUDA is available) `torch.cuda.manual_seed_all()`.                                                                                                            |
| `batch_size`    | `--batch_size`     | int           | `64`                      | Training batch size. Ditto's own README example uses `64`; the paper's experiments generally use 32 when data augmentation (`--da`) is enabled and the dataset is small.                                                                                                                    |
| `lr`            | `--lr`             | float         | `3e-5`                    | Learning rate for the optimizer.                                                                                                                                                                                                                                                            |
| `n_epochs`      | `--n_epochs`       | int           | `20`                      | Number of training epochs. The README's own example uses `40` for the small `Structured/Beer` benchmark — 20 is only the code-level argparse default.                                                                                                                                       |
| `finetuning`    | `--finetuning`     | boolean       | `false` (store_true flag) | If true, fine-tunes the LM's own weights (standard Ditto usage, and what every published Ditto command uses). If false (the code default), only the classification head is trained on top of a frozen LM — this is very unlikely to be what you want, so this config defaults it to `true`. |
| `save_model`    | `--save_model`     | boolean       | `false` (store_true flag) | If true, saves the checkpoint to `{logdir}/{task}/model.pt`. If false (the code default), the run only reports metrics without persisting a checkpoint — again, this config overrides the code default to `true` since you almost always want the checkpoint.                               |
| `logdir`        | `--logdir`         | string        | `checkpoints/`            | Output directory for checkpoints; equivalent to `--checkpoint_path` for `matcher.py`.                                                                                                                                                                                                       |
| `size`          | `--size`           | int or `null` | `None`                    | Optionally subsamples the training set to this many examples (useful for label-efficiency experiments, mirroring the WDC benchmark's `small`/`medium`/`large`/`xlarge` splits). `null`/omitted uses the full training set.                                                                  |

---

## `optimizations`

Ditto's three optional optimizations from the paper. All three can be
combined; `domain_knowledge` and `summarization` must be configured
**identically for training and matching** (a model trained with
`summarize: true` must also be matched with `summarize: true`).
`data_augmentation` only affects training and has no matching-time
counterpart.

### `data_augmentation` (training only)

```yaml
optimizations:
  data_augmentation:
    enabled: false
    operator: del
    alpha_aug: 0.8
```

Enables MixDA, a data-augmentation technique for text. Only affects
`train_ditto.py` — there is no `--da` flag on `matcher.py` at all.

| Field         | Ditto flag         | Verified default  | Description                                                                                                                                          |
|---------------|--------------------|-------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| `enabled`     | *(toggles `--da`)* | —                 | Whether to pass `--da` at all. `train_ditto.py`'s own default for `--da` is `None`, i.e. off.                                                        |
| `operator`    | `--da`             | —                 | Which augmentation operator to use. See table below (source: upstream `README.md`, "Data augmentation (DA)" section). Required if `enabled: true`.   |
| `alpha_aug`   | `--alpha_aug`      | `0.8`             | Interpolation strength for the `Beta(alpha, alpha)` distribution used by MixDA; `0.8` is both the code default and what the paper's experiments use. |

Augmentation operators (`operator`), as documented in the upstream README:

| Operator     | Details                                                       |
|--------------|---------------------------------------------------------------|
| `del`        | Delete a span of tokens                                       |
| `swap`       | Shuffle a span of tokens                                      |
| `drop_col`   | Delete a whole attribute                                      |
| `append_col` | Move an attribute (append it to the end of another attribute) |
| `all`        | Apply all of the above operators uniformly at random          |

### `domain_knowledge` (training **and** matching)

```yaml
optimizations:
  domain_knowledge:
    enabled: false
    mode: general
```

| Field      | Ditto flag         | Verified default                            | Description                                                                                                                                                                                                                                                                                          |
|------------|--------------------|---------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `enabled`  | *(toggles `--dk`)* | off (`--dk` default `None` in both scripts) | Whether to inject domain knowledge into serialized entries.                                                                                                                                                                                                                                          |
| `mode`     | `--dk`             | —                                           | `general` or `product`, per the upstream README. Ditto tags informative spans (e.g. IDs, person names, product attributes) with special tokens and normalizes spans such as numbers. `product` uses product-domain–specific rules; `general` uses generic NER-style rules. See `ditto/knowledge.py`. |

**Quirk verified in source:** `train_ditto.py` picks the injector with
`if hp.dk == 'product': ProductDKInjector else: GeneralDKInjector`
(exact string match), while `matcher.py` picks it with
`if 'product' in hp.dk: ProductDKInjector else: GeneralDKInjector`
(substring match). For the two documented values this makes no difference,
but it means the two scripts are not perfectly symmetric for arbitrary
strings — stick to exactly `general` or `product`.

### `summarization` (training **and** matching)

```yaml
optimizations:
  summarization:
    enabled: false
```

| Field     | Ditto flag                | Verified default      | Description                                                                                                                                                                                                                                                                                                                                 |
|-----------|---------------------------|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `enabled` | *(toggles `--summarize`)* | off (store_true flag) | If true, long serialized sequences are summarized by keeping only the highest TF-IDF-scoring tokens, so the result fits within `model.max_len` tokens instead of being naively truncated. See `ditto/summarize.py`. The README's WDC benchmark script (`run_all_wdc.py`) enables this for every attribute combination except plain `title`. |

---

## `runtime`

Settings for `run_ditto.py` itself, not passed through to Ditto's own
argument parsers.

```yaml
runtime:
  python_bin: "python"
  cuda_visible_devices: "0"
```

| Field                  | Description                                                                                                                                                                                                                                                    |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `python_bin`           | Interpreter used to invoke `matcher.py`/`train_ditto.py` (e.g. a path to a specific virtualenv's `python`).                                                                                                                                                    |
| `cuda_visible_devices` | Value written to the `CUDA_VISIBLE_DEVICES` environment variable for the subprocess (mirrors Ditto's own usage examples, e.g. `CUDA_VISIBLE_DEVICES=0 python matcher.py ...`). Set to `null` to leave it unset (uses whatever is already in your environment). |

---

## `blocking` (optional, informational — not run by `run_ditto.py`)

Ditto's full EM pipeline is *blocking → matching*. Blocking reduces the full
cross-product of two tables down to a manageable set of candidate pairs
before `matcher.py` runs. Ditto ships an optional learned blocker
(`blocking/train_blocker.py`, `blocking/blocker.py`) with its own CLI shape
that does not fit the `--input`/`--output`/`--config` interface `run_ditto.py`
exposes, so it is documented here but must be run manually. All flags below
are verified against `blocking/README.md`'s own example commands.

```yaml
blocking:
  train:
    train_fn: "../data/er_magellan/Structured/Beer/train.txt"
    valid_fn: "../data/er_magellan/Structured/Beer/valid.txt"
    model_fn: "model.pth"
    batch_size: 64
    n_epochs: 40
    lm: bert
    fp16: true
  apply:
    input_path: "input/"
    left_fn: "table_a.txt"
    right_fn: "table_b.txt"
    output_fn: "candidates.jsonl"
    model_fn: "model.pth"
    k: 10
```

| Field (train)   | Ditto flag     | Description                                                   |
|-----------------|----------------|---------------------------------------------------------------|
| `train_fn`      | `--train_fn`   | Serialized training pairs for the blocker.                    |
| `valid_fn`      | `--valid_fn`   | Serialized validation pairs for the blocker.                  |
| `model_fn`      | `--model_fn`   | Output path for the trained blocker model.                    |
| `batch_size`    | `--batch_size` | Training batch size for the blocker.                          |
| `n_epochs`      | `--n_epochs`   | Number of training epochs for the blocker.                    |
| `lm`            | `--lm`         | LM backbone used by the (Siamese/sentence-embedding) blocker. |
| `fp16`          | `--fp16`       | Half-precision training.                                      |

| Field (apply)  | Ditto flag      | Description                                                                                        |
|----------------|-----------------|----------------------------------------------------------------------------------------------------|
| `input_path`   | `--input_path`  | Directory containing `left_fn`/`right_fn`.                                                         |
| `left_fn`      | `--left_fn`     | Serialized entries of table A, one per line.                                                       |
| `right_fn`     | `--right_fn`    | Serialized entries of table B, one per line.                                                       |
| `output_fn`    | `--output_fn`   | Output path for the generated candidate pairs (this becomes `matching`'s `--input_path`).          |
| `model_fn`     | `--model_fn`    | Path to the trained blocker model.                                                                 |
| `k`            | `--k`           | Optional: keep only the top-*k* most similar candidates per row instead of a similarity threshold. |

Example manual invocation (from inside the Ditto repo, `blocking/` subfolder):

```bash
CUDA_VISIBLE_DEVICES=0 python train_blocker.py \
  --train_fn ../data/er_magellan/Structured/Beer/train.txt \
  --valid_fn ../data/er_magellan/Structured/Beer/valid.txt \
  --model_fn model.pth --batch_size 64 --n_epochs 40 --lm bert --fp16

CUDA_VISIBLE_DEVICES=0 python blocker.py \
  --input_path input/ --left_fn table_a.txt --right_fn table_b.txt \
  --output_fn candidates.jsonl --model_fn model.pth --k 10
```

The resulting `candidates.jsonl` is then what you point `paths.input_path`
/ `--input` at for `mode: match`.

---

## Fields deliberately *not* in the config (verified non-functional)

These were present in earlier versions of this config but have been removed
because upstream Ditto does not actually read them as configuration:

| Removed field         | What actually happens instead                                                                                                                                                                                                                                                                                                                                                                                                   |
|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `matching.threshold`  | `matcher.py`'s `__main__` always calls `tune_threshold()` before predicting. That function re-evaluates the model on `task.validset` (from `configs.json`) with `f1, th = evaluate(model, valid_iter, threshold=None)` and uses the resulting F1-optimal threshold for every single run. There is no `--threshold` flag in the stock `matcher.py` argparse block, so a fixed threshold cannot be requested from the CLI at all. |
| `matching.batch_size` | `predict()` in `matcher.py` has a `batch_size=1024` parameter, but the `__main__` block calls `predict(...)` without passing `batch_size`, so it is always `1024`. There is no `--batch_size` flag in `matcher.py`'s argparse block.                                                                                                                                                                                            |
| `model.seed`          | See the "Removed field: `seed`" note under `model` above — `matcher.py` hardcodes seed `123`; `train_ditto.py` seeds from `training.run_id`.                                                                                                                                                                                                                                                                                    |

If you patch your local copy of `matcher.py` to accept `--threshold` /
`--batch_size` flags, you can reintroduce a `matching:` section to this
config and extend `build_match_command()` in `run_ditto.py` accordingly —
but out of the box, upstream Ditto does not support it.

---

## End-to-end example

```bash
# 1. Train a model (writes checkpoints/Structured/Beer/model.pt)
python run_ditto.py --config config-example.yaml   # with mode: train in the file

# 2. Match candidate pairs with that checkpoint
python run_ditto.py \
  --input  input/candidates.jsonl \
  --output output/matched.jsonl \
  --config ditto_config.yaml       # with mode: match in the file
```

## References

- Ditto GitHub repository: <https://github.com/megagonlabs/ditto>
- `matcher.py`: <https://github.com/megagonlabs/ditto/blob/master/matcher.py>
- `train_ditto.py`: <https://github.com/megagonlabs/ditto/blob/master/train_ditto.py>
- `blocking/README.md`: <https://github.com/megagonlabs/ditto/tree/master/blocking>
- Paper: *Deep Entity Matching with Pre-trained Language Models* (VLDB 2020) — <https://arxiv.org/abs/2004.00584>