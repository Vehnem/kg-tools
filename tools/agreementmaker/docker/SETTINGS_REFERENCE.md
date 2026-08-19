# AgreementMakerLight Settings Reference

This document lists every setting used by the `agreementmaker.sh` wrapper and
`store/config.ini`, the values each setting accepts, and what each value
means. For background on how these settings relate to AML's internal
architecture, see `README.md`.

---

## `mode`

Wrapper-level setting. Selects which AML CLI flag is used for the run.

| Value      | Meaning                                                                                                                                                             |
|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `auto`     | Runs AML with `-a`. AML profiles the ontologies and picks matching/filtering strategies automatically.                                                              |
| `manual`   | Runs AML with `-m`. AML uses the matcher configuration from `store/config.ini` as given, without automatic profiling.                                               |
| `repair`   | Runs AML with `-i <input_alignment> -r`. Repairs an existing alignment instead of computing a new one; requires the fifth wrapper argument (`input_alignment.rdf`). |

---

## `use_translator`

Controls whether AML translates labels between different ontology languages.

| Value     | Meaning                                                                          |
|-----------|----------------------------------------------------------------------------------|
| `true`    | Translation is always performed.                                                 |
| `false`   | Translation is disabled.                                                         |
| `auto`    | AML decides based on the detected languages of the source and target ontologies. |

---

## `bk_sources`

Selects which Background Knowledge sources AML may use. Files must be
located in `store/knowledge/`.

| Value                            | Meaning                                                         |
|----------------------------------|-----------------------------------------------------------------|
| `all`                            | All available background knowledge sources may be used.         |
| `none`                           | Background knowledge is disabled.                               |
| `<file1>,<file2>,...`            | Only the listed files are used as background knowledge sources. |

---

## `word_matcher`

Configures the word-matching stage of the pipeline.

| Value        | Meaning                                                                                                                                                                                                                                     |
|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `auto`       | AML decides based on the ontology profile.                                                                                                                                                                                                  |
| `none`       | The word-matching stage is disabled.                                                                                                                                                                                                        |
| `by_class`   | Word matching is performed at the class level.                                                                                                                                                                                              |
| `by_name`    | Word matching is performed based on entity names.                                                                                                                                                                                           |
| `average`    | Word similarity is averaged across contributing values.                                                                                                                                                                                     |
| `maximum`    | The maximum contributing similarity value is used.                                                                                                                                                                                          |
| `mininum`    | The minimum contributing similarity value is used. **Note:** this is the exact spelling used by the config file (missing the second "m"); do not change it to `minimum` without confirming your AML version accepts the corrected spelling. |

---

## `string_matcher`

Configures the string-matching stage of the pipeline.

| Value      | Meaning                                                                |
|------------|------------------------------------------------------------------------|
| `auto`     | AML decides based on the ontology profile.                             |
| `none`     | String matching is disabled.                                           |
| `global`   | String matching is performed globally (all pairs compared).            |
| `local`    | String matching is restricted to locally relevant candidate pairs.     |

---

## `string_measure`

Selects the string-similarity function used by the string matcher.

| Value            | Meaning                                                                                                                                                                                                          |
|------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ISub`           | Uses the ISub similarity measure.                                                                                                                                                                                |
| `Levenstein`     | Uses Levenshtein (edit-distance) similarity. **Note:** this is the exact spelling used by the config file; do not change it to `Levenshtein` without confirming your AML version accepts the corrected spelling. |
| `Jaro-Winkler`   | Uses the Jaro-Winkler similarity measure.                                                                                                                                                                        |
| `Q-gram`         | Uses Q-gram-based similarity.                                                                                                                                                                                    |

---

## `struct_matcher`

Configures the structural-matching stage of the pipeline (based on
relationships between ontology entities).

| Value           | Meaning                                                          |
|-----------------|------------------------------------------------------------------|
| `auto`          | AML decides based on the ontology profile.                       |
| `none`          | Structural matching is disabled.                                 |
| `ancestors`     | Structural similarity is computed from ancestor relationships.   |
| `descendants`   | Structural similarity is computed from descendant relationships. |
| `average`       | Structural similarity is averaged across contributing values.    |
| `maximum`       | The maximum contributing similarity value is used.               |
| `minimum`       | The minimum contributing similarity value is used.               |

---

## `match_properties`

Controls whether AML matches ontology properties in addition to classes.

| Value     | Meaning                                                                |
|-----------|------------------------------------------------------------------------|
| `true`    | Property matching is enabled.                                          |
| `false`   | Property matching is disabled.                                         |
| `auto`    | AML decides based on the ontology profile.                             |

---

## `selection_type`

Configures the correspondence-selection (filtering) step applied after
matching.

| Value          | Meaning                                                                                   |
|----------------|-------------------------------------------------------------------------------------------|
| `auto`         | AML decides based on the ontology profile.                                                |
| `none`         | No selection step is applied.                                                             |
| `strict`       | A strict selection strategy is used, keeping fewer, higher-confidence correspondences.    |
| `permissive`   | A permissive selection strategy is used, allowing more candidate correspondences through. |
| `hybrid`       | A combination of strict and permissive selection strategies is used.                      |

---

## `repair_alignment`

Controls whether the coherence-repair step is run after selection.

| Value     | Meaning                                                                                    |
|-----------|--------------------------------------------------------------------------------------------|
| `true`    | The repair step is applied, removing correspondences that would cause logical incoherence. |
| `false`   | The repair step is skipped.                                                                |