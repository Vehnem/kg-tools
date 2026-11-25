# Configuration Reference — LogMap Wrapper

Full overview of all keys supported in `config-example.conf` / `run_logmap.sh`.

Verified against the LogMap source at commit
`a031fa9889e139fd5ab9e8c7415c8113f9c285ee` of
`ernestojimenezruiz/logmap-matcher` (pom version `4.0`), by reading
`LogMap2_CommandLine.java`, `LogMap2_Matcher.java`, `Parameters.java`,
`OutPutFilesManagerStatic.java`, `OntologyProcessing.java` and the
shipped `parameters.txt` — not from memory. The Maven build and a real
LogMap run were not exercised in the authoring environment (no Maven
Central access); the runner itself was tested end-to-end against a
stubbed `java`.

LogMap has no swappable components (no blockers/matchers to choose from),
so there is no Python layer: `run_logmap.sh` translates a flat
`key=value` config into LogMap's native `parameters.txt` and calls the
CLI.

```
config.conf ──> run_logmap.sh ──> parameters.txt (temp dir, = cwd of the JVM)
                    │
                    └──> java -jar logmap-matcher.jar MATCHER|EVALUATION ... <output_dir>/
```

---

## 1. Invocation

```
bash run_logmap.sh <ontology1> <ontology2> <output_dir> <config.conf> [reference.rdf]
```

| Argument        | Notes                                                                                                                              |
|-----------------|------------------------------------------------------------------------------------------------------------------------------------|
| `ontology1`     | Local file, any format the OWL API reads (RDF/XML, OWL/XML, OWL Functional, OBO, KRSS, Turtle). Converted to an absolute `file:` IRI. |
| `ontology2`     | Same as `ontology1`.                                                                                                               |
| `output_dir`    | Created if missing. The runner appends the trailing `/` that LogMap requires (see section 5).                                     |
| `config.conf`   | See section 2.                                                                                                                     |
| `reference.rdf` | Optional. OAEI RDF alignment format. Switches LogMap from `MATCHER` to `EVALUATION` mode and produces `evaluation.csv`. If the path is empty or not an existing file, it is ignored (MATCHER mode) — the KGpipe task always passes this argument. |

Environment: `LOGMAP_HOME` must contain `logmap-matcher.jar`,
`java-dependencies/` and `parameters.txt` (set to `/opt/logmap` in the
Docker image, to `.build/logmap` by `make build`).

Not covered on purpose: `MATCHER-BIO` (needs BioPortal network access),
`LITE`, `DEBUGGER`, `RDF2OWL` — all exist in `LogMap2_CommandLine` but
are out of scope for this wrapper.

---

## 2. Config file format

- One `key=value` per line. Blank lines and lines starting with `#` are ignored.
- Keys are case-sensitive and must be known (unknown keys abort the run).
- Values are validated by type before LogMap is started. This matters
  because LogMap itself parses booleans with `Boolean.valueOf`, which
  turns any typo (`True `, `yes`, `ture`) silently into `false`, and its
  parameter reader swallows all exceptions.
- Values must not contain `|` (the separator of LogMap's `parameters.txt`).
- Omitted keys keep the value from LogMap's shipped `parameters.txt`.
  `config-example.conf` reproduces the shipped values exactly.
- Run-level keys (section 3) are consumed by the runner; all other keys
  (section 4) are written into `parameters.txt`.

---

## 3. Run-level keys

| Key                      | Type            | Default | Notes                                                                                                                                                                  |
|--------------------------|-----------------|---------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `classify`               | bool            | `true`  | 5th CLI argument: classify the input ontologies together with the mappings (runs the reasoner to check the logical impact of the mappings).                           |
| `java_xms`               | JVM size        | unset   | `-Xms`. Upstream README suggests `500M`.                                                                                                                               |
| `java_xmx`               | JVM size        | —       | **Required.** `-Xmx`. No upstream default; upstream README uses `25G` as an example for large ontologies. `config-example.conf` uses `8G` as a starting point.        |
| `entity_expansion_limit` | integer         | unset   | `-DentityExpansionLimit`. Upstream README suggests `10000000`.                                                                                                         |

JVM sizes: integer followed by `k`, `m` or `g` (any case).

The runner always adds `--add-opens=java.base/java.lang=ALL-UNNAMED`
(required on newer Java versions, see upstream issue #39 referenced in
the LogMap README) and `-Duser.language=en -Duser.country=US`.
The latter is needed because the EVALUATION output is printed with
`System.out.format("%.3f")`, which would otherwise emit decimal commas
on a German locale.

---

## 4. LogMap parameters (`parameters.txt` keys)

Types are enforced by the runner. Defaults are the values of the shipped
`parameters.txt`; they differ in several places from the Java field
initialisers in `Parameters.java`, which only apply when the file is
missing or a key is absent (marked "Java default" below).

### 4a. Reasoning and repair

| Key                             | Type   | Allowed                           | Default  | Java default | Notes                                                                                           |
|---------------------------------|--------|-----------------------------------|----------|--------------|-------------------------------------------------------------------------------------------------|
| `reasoner`                      | string | `HermiT` \| `ELK` \| `Structural` | `HermiT` | `HermiT`     | In `OntologyProcessing`, `HermiT` and `ELK` select those reasoners; **any other value silently selects the structural reasoner**. The runner therefore only accepts the three names. |
| `timeout`                       | int    | seconds                           | `25`     | `25`         | Reasoner classification timeout (`future.get(timeoutSecs, TimeUnit.SECONDS)`).                  |
| `reason_datatypes`              | bool   |                                   | `false`  | `true`       |                                                                                                 |
| `perform_repair`                | bool   |                                   | `true`   | `true`       | Read into `Parameters.cleanD_G`.                                                                |
| `glogal_info`                   | bool   |                                   | `true`   | `true`       | Spelled `glogal_info` in LogMap itself (typo upstream); the runner uses the same spelling.      |
| `second_chance_conflicts`       | bool   |                                   | `true`   | `true`       |                                                                                                 |
| `ratio_second_chance_discarded` | int    |                                   | `10`     | `5`          |                                                                                                 |

### 4b. Output selection

| Key                             | Type | Default | Java default | Notes                                           |
|---------------------------------|------|---------|--------------|-------------------------------------------------|
| `output_equivalences_only`      | bool | `false` | `false`      |                                                 |
| `output_class_mappings`         | bool | `true`  | `true`       |                                                 |
| `output_prop_mappings`          | bool | `true`  | `true`       |                                                 |
| `output_instance_mappings`      | bool | `true`  | `true`       |                                                 |
| `output_instance_mapping_files` | bool | `false` | `false`      | Shipped file marks this "only for statistics".  |
| `print_output`                  | bool | `false` | `false`      | Controls LogMap's console logging. With `false` the log contains almost nothing (e.g. only `Num unsat classes after integration: 0`); set `true` to see progress, entity counts and `Number of computed mappings`. |

### 4c. Matching scope

| Key                                    | Type | Default | Java default | Notes                                                                                                                  |
|----------------------------------------|------|---------|--------------|------------------------------------------------------------------------------------------------------------------------|
| `property_matching`                    | bool | `true`  | `true`       |                                                                                                                        |
| `instance_matching`                    | bool | `true`  | `true`       |                                                                                                                        |
| `restrict_individual_types`            | bool | `false` | `false`      | If `true`, only individuals of the types in `allowed_individual_type` (section 4f) are matched.                        |
| `index_undeclared_abox_predicates`     | bool | `true`  | `false`      | Index predicates used in ABox assertions without a declaration for property matching. The shipped file sets it to `true`, the code comment says "off by default". |
| `index_undeclared_abox_use_both_props` | bool | `true`  | `true`       | Only effective if `index_undeclared_abox_predicates=true`.                                                             |
| `use_overlapping`                      | bool | `false` | `false`      | Divide the task into overlapping modules for large ontologies.                                                         |
| `min_size_overlapping`                 | int  | `15000` | `15000`      | Size threshold for `use_overlapping`.                                                                                  |

### 4d. Lexical and scoring thresholds

| Key                             | Type   | Default | Java default | Notes                                                                        |
|---------------------------------|--------|---------|--------------|------------------------------------------------------------------------------|
| `good_isub_anchors`             | double | `0.98`  | `0.98`       |                                                                              |
| `good_isub_candidates`          | double | `0.95`  | `0.95`       |                                                                              |
| `good_confidence`               | double | `0.50`  | `0.50`       |                                                                              |
| `good_sim_coocurrence`          | double | `0.08`  | `0.08`       | Spelled `coocurrence` upstream.                                              |
| `bad_score_scope`               | double | `0.0`   | `0.0`        |                                                                              |
| `min_conf_pro_map`              | double | `0.80`  | `0.75`       | Java source comment: "in parameters.txt is 0.80".                            |
| `confidence_composed_mappings1` | double | `0.8`   | `0.8`        |                                                                              |
| `confidence_composed_mappings2` | double | `0.7`   | `0.7`        |                                                                              |
| `avoid_redundant_labels`        | bool   | `true`  | `true`       |                                                                              |
| `max_redundancy_labels`         | int    | `3`     | `3`          |                                                                              |
| `max_ambiguity`                 | int    | `4`     | `4`          |                                                                              |
| `good_ambiguity`                | int    | `2`     | `2`          |                                                                              |
| `use_stemming`                  | bool   | `false` | `false`      |                                                                              |
| `reverse_labels`                | bool   | `false` | `false`      | See caveat below.                                                            |
| `use_umls_lexicon`              | bool   | `true`  | `true`       |                                                                              |

`reverse_labels` caveat: the shipped `parameters.txt` contains the line
`reverse_labels=false` with `=` instead of `|`. LogMap's reader skips
every line without `|`, so that line is ignored and the Java default
applies. The runner always writes `reverse_labels|<value>` when you set
the key, so the setting actually takes effect.

### 4e. Multilingual, BioPortal and interactivity

| Key                           | Type   | Default                         | Java default | Notes                                                                                                                                  |
|-------------------------------|--------|---------------------------------|--------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `allow_multilingual`          | bool   | `false`                         | `true`       |                                                                                                                                        |
| `is_test_mode_multilingual`   | bool   | `false`                         | `false`      |                                                                                                                                        |
| `use_local_dict`              | bool   | `false`                         | `true`       |                                                                                                                                        |
| `call_online_translator`      | bool   | `false`                         | `false`      |                                                                                                                                        |
| `target_lang`                 | string | `en`                            | `en`         |                                                                                                                                        |
| `translator_id`               | int    | `9`                             | all (`ALL_TRANSLATORS`) | Shipped comment: `0=Google, 1=Microsoft, >=2 -> all`.                                                                       |
| `path_chinese_segmenter_dict` | string | `multilingual/dict_ictclas4j`   | author's local path | Not in `config-example.conf`.                                                                                                   |
| `path_multilingual_tmp`       | string | `multilingual`                  | author's local path | Not in `config-example.conf`.                                                                                                   |
| `path_multilingual_local`     | string | `multilingual/local`            | author's local path | Not in `config-example.conf`.                                                                                                   |
| `path_mappings_categories`    | string | `mappings/categories`           | `/mappings/categories` | Not in `config-example.conf`.                                                                                                |
| `allow_bioportal`             | bool   | `false`                         | `false`      | Only relevant for the `MATCHER-BIO` facility, which this wrapper does not call.                                                        |
| `max_mediating_ontologies`    | int    | `10`                            | `12`         | Same.                                                                                                                                  |
| `allow_interactivity`         | bool   | `false`                         | `false`      |                                                                                                                                        |

Relative `path_*` values resolve against the JVM's working directory,
which is the runner's temporary directory and contains no dictionaries.
Use absolute paths if you enable multilingual matching.

### 4f. List keys

These keys may occur multiple times in `parameters.txt`. In the config
file give them once with a **comma-separated** list. If a key is set,
**all** shipped lines of that key are replaced by your list; if it is
omitted, the shipped lines stay.

| Key                               | Shipped content                                                                                      | Meaning (from `Parameters.java` / `parameters.txt`)                                  |
|-----------------------------------|------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| `annotation_URI`                  | `rdfs:label`, many synonym/preferred-label properties (SKOS, OBO, NCI, FMA, EFO, ...), `foaf:name`   | Annotation properties whose values are used as class labels.                         |
| `category_URI`                    | one DOREMUS property (commented-out alternatives)                                                    | Category properties for individuals.                                                 |
| `data_assertion_URI_Indiv`        | `foaf:name`, `dbpedia` name/title properties, benchmark-specific properties                          | Data properties whose values are used as individual labels.                          |
| `data_assertion_URI_Indiv_deep2`  | `IIMB2012/ADDONS#has_value`                                                                          | Second-level data assertions.                                                        |
| `object_assertion_URI_Indiv`      | IIMB/BBC/TomTom benchmark-specific properties                                                        | Object properties followed for individuals.                                          |
| `allowed_individual_type`         | benchmark-specific types (OAEI 2015, SPIMBENCH, process-model matching, DOREMUS)                     | Types of individuals to match when `restrict_individual_types=true`.                 |
| `filter_entity`                   | `foaf`, `rdf-syntax-ns`, `dc/elements`, `mouse.owl#UNDEFINED_part_of`, `human.owl#UNDEFINED_part_of` | URI prefixes excluded from matching.                                                 |

Example:

```
annotation_URI=http://www.w3.org/2000/01/rdf-schema#label,http://www.w3.org/2004/02/skos/core#altLabel
```

---

## 5. Output

LogMap builds output paths by plain string concatenation
(`output_path + name`), so a missing trailing slash would write
`out` + `logmap_mappings.rdf` as `outlogmap_mappings.rdf`. The runner
always passes `<output_dir>/`.

Written by `LogMap2_Matcher.saveMappings`:

| File                                                | Content                                                                    |
|-----------------------------------------------------|----------------------------------------------------------------------------|
| `logmap_mappings.{owl,rdf,txt,tsv,ttl}`             | Final mappings in five formats (`rdf` = OAEI alignment format).            |
| `logmap_anchors.{owl,rdf,txt,tsv,ttl}`              | Anchor mappings in the same five formats.                                  |
| `logmap_discarded_mappings.txt`                     | Discarded mappings.                                                        |
| `logmap_hard_discarded_mappings.txt`                | Hard-discarded mappings.                                                   |
| `logmap_logically_conflicting_mappings.txt`         | Logically conflicting mappings.                                            |
| `logmap_mappings_to_ask_oracle_user_llm.txt`        | Mappings that would be sent to an oracle (user/LLM).                       |
| `logmap_overestimation.txt`                         | Over-estimation of the mappings, with scores per set.                      |

Written by the runner:

| File               | Content                                                                                                              |
|--------------------|----------------------------------------------------------------------------------------------------------------------|
| `logmap_stdout.log`| Combined stdout/stderr of the JVM.                                                                                   |
| `evaluation.csv`   | `precision,recall,f1` — only in EVALUATION mode. Parsed from the `Precision\tRecall\tF-score` line LogMap prints.    |

---

## 6. Failure detection

`LogMap2_CommandLine` catches every exception and prints its usage text,
and `LogMap2_Matcher` only prints stack traces; the JVM exits with `0`
in both cases. The runner therefore fails (exit code `1`) if:

- the usage text appears in the output,
- `logmap_mappings.rdf` is missing or empty, or `logmap_mappings.txt` is missing (an empty `.txt` is valid: LogMap creates it even when it finds no mappings, and the runner only logs a warning),
- in EVALUATION mode the scores cannot be parsed.

Config and argument errors are reported before the JVM is started.

---

## Troubleshooting

| Symptom                                                              | Cause / fix                                                                                                      |
|----------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| `LogMap printed its usage text instead of running`                   | An exception inside LogMap (unreadable ontology, wrong format, OOM). Inspect `logmap_stdout.log`.                |
| `InaccessibleObjectException` / reflection errors on newer Java      | `--add-opens` is set by the runner; if you call the jar manually, add it yourself.                               |
| `OutOfMemoryError`                                                   | Increase `java_xmx`.                                                                                             |
| Output files named `outlogmap_...`                                   | Only when calling the jar directly without a trailing `/` on the output path.                                    |
| `Using default parameters` on stderr                                 | `parameters.txt` was not found in the JVM's working directory. Cannot happen via `run_logmap.sh`.                |