# CONFIG_REFERENCE.md — `config.yaml`

This file explains every setting in `config.yaml` and all valid values.
It refers to **OntoAligner v1.9.3** (`pip install ontoaligner`), against whose
source code all class names and parameters in this document were verified.
(The latest release published on PyPI at the time of writing is 1.9.2 —
double-check your installed version with `pip show ontoaligner` if in doubt.)

Usage:

```bash
pip install ontoaligner pyyaml
python run_ontoaligner.py --config config.yaml
```

CLI overrides (override the config without changing the file):

```bash
python run_ontoaligner.py --config config.yaml \
    --source data/source.owl --target data/target.owl \
    --reference data/reference.rdf \
    --output-dir results --output-format json \
    --method retrieval
```

---

## 0. Which OntoAligner paradigms does this runner cover?

OntoAligner ships more than a dozen alignment paradigms in total. This
runner wraps the subset that is unified behind `ontoaligner.OntoAlignerPipeline`
and its `method=` argument:

| Paradigm | Covered by `run_ontoaligner.py`? |
|---|---|
| Lightweight (fuzzy string matching) | ✅ `method: lightweight` |
| Retrieval-based | ✅ `method: retrieval` |
| LLM-based | ✅ `method: llm` |
| Retrieval-Augmented (RAG / FewShot-RAG / ICV-RAG) | ✅ `method: rag` / `fewshot-rag` / `icv-rag` |
| Knowledge Graph Embedding (KGE) | ❌ not covered (separate module, see §9) |
| Ensemble Learning | ❌ not covered (separate module, see §9) |

The last two work on different inputs (KG triples instead of OWL classes,
or a voting combination of several already-finished pipelines) and are not
exposed via `OntoAlignerPipeline`'s `method=` dispatch — see §9 for details
and pointers to the OntoAligner examples that do cover them.

## 1. `input`

| Field | Type | Description |
|---|---|---|
| `source_ontology_path` | string | Path to the source ontology. Must be parseable by `rdflib` as RDF/XML OWL (`Graph().parse(path, format="xml")`). |
| `target_ontology_path` | string | Path to the target ontology. Same format as above. |
| `reference_matching_path` | string | Optional. Path to an OAEI reference alignment file (RDF format `http://knowledgeweb.semanticweb.org/heterogeneity/alignment`). Empty string `""` = no reference available. Only needed for `evaluate: true`; if the file is missing/empty, OntoAligner simply falls back to an empty reference list internally (no error). |
| `task_class` | `generic` \| `generic_olala` | Determines which OntoAligner dataset class is used to read your own files (see below). |

**`task_class` options:**

- **`generic`** → `ontoaligner.ontology.GenericOMDataset`. For every `owl:Class`, extracts: IRI, label, child/parent classes, synonyms (`skos:altLabel`), and comments (`rdfs:comment`). This is the right choice for arbitrary custom OWL ontologies.
- **`generic_olala`** → `ontoaligner.ontology.OLaLaOMDataset`. Same as `generic`, but additionally extracts a broader set of text fields (MELT `TextExtractorSet` style: `skos:prefLabel/altLabel/hiddenLabel`, schema.org name fields, URI fragments, host detection, etc.). Useful when your ontologies have sparse/inconsistent `rdfs:label` values, or if you want to use the `OLaLaAligner` separately.

> Note: OntoAligner also ships fixed dataset classes for the official OAEI benchmarks (Anatomy, Bio-ML, Common-KG, Food, Material Science, Phenotype, Biodiversity — each with hard-wired ontology pairs). These are meant for reproducing published benchmarks, not for your own files, and are therefore not offered by `run_ontoaligner.py`.

## 2. `output`

| Field | Type | Description |
|---|---|---|
| `output_dir` | string | Base directory for results. OntoAligner automatically creates a subfolder named after the `method`, e.g. `results/lightweight/matchings.xml`. |
| `output_format` | `xml` \| `json` | `xml` produces an OAEI-compliant alignment XML; `json` produces a plain list of `{"source": ..., "target": ..., "relation": ..., "score": ...}` objects. |
| `output_file_name` | string | File name without extension. |
| `save_matchings` | bool | Whether the result file is actually written to disk. |
| `return_matching` | bool | Whether `run_ontoaligner.py` also returns/prints the matchings in addition to the evaluation. |
| `evaluate` | bool | If `true`, evaluates against `reference_matching_path` (precision, recall, F1) and prints it as JSON on stdout. Without a reference file set, this yields trivial/empty values. |

## 3. `method`

Selects the alignment approach. Allowed values:

| Value | Short description |
|---|---|
| `lightweight` | Pure string/fuzzy matching on labels (fast, no model download, CPU-only). |
| `retrieval` | Bi-encoder / TF-IDF / BM25-based similarity search between concept texts. |
| `llm` | A language model directly answers "match: yes/no" for every candidate pair. |
| `rag` | Retrieval-Augmented Generation: a retriever proposes candidates first, then an LLM decides. |
| `fewshot-rag` | Like `rag`, but additionally feeds the LLM few-shot examples drawn from the reference alignments (**requires `reference_matching_path`**). |
| `icv-rag` | Like `rag`, but uses In-Context Vectors (activation-based conditioning) instead of prompt few-shots (**also requires `reference_matching_path`**). |

Only the config block matching the chosen `method` (`lightweight:`, `retrieval:`, `llm:`, or `rag:`) is actually used; the other blocks are ignored and don't need to be removed.

## 4. `encoder`

The encoder determines **which information per concept** flows into the matching. Valid values for `encoder.name` depend on the chosen `method`:

| `method` | valid `encoder.name` values |
|---|---|
| `lightweight` | `concept`, `concept_children`, `concept_parent`, `doc_concept`, `mila` |
| `retrieval` | `concept`, `concept_children`, `concept_parent`, `doc_concept`, `mila` *(OntoAligner internally uses the same encoder family for `retrieval` as for `lightweight`)* |
| `llm` | `concept`, `concept_children`, `concept_parent` |
| `rag`, `icv-rag` | `concept`, `concept_children`, `concept_parent` |
| `fewshot-rag` | `concept`, `concept_children`, `concept_parent` |

What the options mean:

- **`concept`** — only IRI + label of the concept.
- **`concept_children`** — label + labels of the direct child classes.
- **`concept_parent`** — label + labels of the direct parent classes (`rdfs:subClassOf`).
- **`doc_concept`** *(only `lightweight`/`retrieval`)* — label + synonyms + comments joined into one "document", lowercased, underscores replaced with spaces.
- **`mila`** *(only `lightweight`/`retrieval`)* — like `concept`, but prepared internally as a term↔class dictionary (a specialized format for the MILA approach; for most use cases `concept` is the better choice).

## 5. `lightweight` (only for `method: lightweight`)

| Field | Type | Description |
|---|---|---|
| `matcher` | `simple_fuzzy` \| `weighted_fuzzy` \| `token_set_fuzzy` | Which RapidFuzz similarity function is used. |
| `fuzzy_sm_threshold` | float, 0.0–1.0 | Minimum similarity above which a candidate pair counts as a match. |

`matcher` options in detail:

- **`simple_fuzzy`** (`SimpleFuzzySMLightweight`) → `rapidfuzz.fuzz.ratio` (classic Levenshtein-based ratio).
- **`weighted_fuzzy`** (`WeightedFuzzySMLightweight`) → `rapidfuzz.fuzz.WRatio` (combines several heuristics, more robust with differing string lengths).
- **`token_set_fuzzy`** (`TokenSetFuzzySMLightweight`) → `rapidfuzz.fuzz.token_set_ratio` (ignores word order/duplicates, good for multi-word labels).

This method needs no ML model and runs purely on CPU.

## 6. `retrieval` (only for `method: retrieval`)

| Field | Type | Description |
|---|---|---|
| `matcher` | see below | Retrieval approach. |
| `retriever_path` | string | Model path/name. Meaning depends on `matcher` (see below). Ignored for `tfidf`/`bm25`. |
| `device` | string | `cpu`, `cuda`, `cuda:0`, `mps`, … (only relevant for `sbert`/`svm_bert`). |
| `top_k` | int | Number of top candidates per source concept. |
| `ir_threshold` | float | Score threshold below which candidates are discarded in postprocessing. |
| `openai_key` | string | Only for `matcher: ada` (OpenAI embeddings). |

`matcher` options:

- **`sbert`** (`SBERTRetrieval`) — sentence-transformers bi-encoder. `retriever_path` = any HuggingFace sentence-transformers model, e.g. `sentence-transformers/all-MiniLM-L6-v2`.
- **`tfidf`** (`TFIDFRetrieval`) — classic TF-IDF + cosine similarity (scikit-learn). No model download needed.
- **`bm25`** (`BM25Retrieval`) — Okapi BM25 (`rank_bm25`). No model download needed.
- **`svm_bert`** (`SVMBERTRetrieval`) — BERT embeddings + SVM reranking approach.
- **`ada`** (`AdaRetrieval`) — OpenAI embedding models (`retriever_path` = e.g. `text-embedding-3-small`), requires `openai_key`.

## 7. `llm` (only for `method: llm`)

| Field | Type | Description |
|---|---|---|
| `matcher` | `auto_decoder` \| `flan_t5` \| `gpt_openai` | LLM architecture. |
| `llm_path` | string | Model ID/path; see below. |
| `dataset` | `concept` \| `concept_parent` \| `concept_children` \| `property` \| `property_full_text` | Which prompt template/dataset is used for the LLM input. |
| `device` | string | Compute device for local models. |
| `batch_size` | int | Batch size during generation. |
| `max_length` | int | Maximum input sequence length (tokenizer truncation). |
| `max_new_tokens` | int | Maximum generated tokens per answer. |
| `llm_threshold` | float | Confidence threshold in postprocessing. |
| `llm_mapper_interested_class` | string | Which class from the LLM output counts as a "match" (default: `"yes"`). |
| `answer_set` | dict with `yes`/`no` lists | Which words the model is allowed to use to express "yes"/"no". |
| `huggingface_access_token` | string | Needed for gated/private HF models. |
| `openai_key` | string | Only for `matcher: gpt_openai`. |

`matcher` options:

- **`auto_decoder`** (`AutoModelDecoderLLM`) — loads **any** causal HuggingFace language model via `transformers.AutoModelForCausalLM`/`AutoTokenizer`. `llm_path` = any HF model ID, e.g. `Qwen/Qwen2.5-0.5B-Instruct`, `meta-llama/Llama-3.1-8B-Instruct` (access token may be required).
- **`flan_t5`** (`FlanT5LEncoderDecoderLM`) — encoder-decoder model via `T5ForConditionalGeneration`. `llm_path` = e.g. `google/flan-t5-base`.
- **`gpt_openai`** (`GPTOpenAILLM`) — calls the OpenAI chat API. `llm_path` = model name (e.g. `gpt-4o-mini`), requires `openai_key`.

`dataset` options (determine the prompt format):

- **`concept`** (`ConceptLLMDataset`) — standard prompt with source/target label.
- **`concept_parent`** (`ConceptParentLLMDataset`) — prompt including parent-class context.
- **`concept_children`** (`ConceptChildrenLLMDataset`) — prompt including child-class context.
- **`property`** / **`property_full_text`** (`PropertyLLMDataset` / `PropertyFullTextLLMDataset`) — for the (separate) property-matching use case; only useful together with the corresponding property encoders (not part of this generic runner, see §9).

## 8. `rag` (for `method: rag`, `fewshot-rag`, or `icv-rag`)

The same YAML block is used for all three RAG variants.

| Field | Type | Description |
|---|---|---|
| `matcher` | see table below | Combination of LLM backbone and retriever. |
| `retriever_path` | string | HF sentence-transformers model (for `*_bert`), or OpenAI embedding model name (for `*_ada`). |
| `llm_path` | string | HF model ID (for `llama_*`, `mistral_*`, `falcon_*`, `vicuna_*`, `mpt_*`, `mamba_*`) or OpenAI model name (for `gpt_openai_*`). |
| `device` | string | Compute device for local models. |
| `batch_size`, `max_length`, `max_new_tokens` | as in `llm` | |
| `top_k` | int | Number of candidates the retriever proposes per source concept. |
| `ir_rag_threshold` | float | Score threshold for the retriever part. |
| `llm_threshold` | float | Confidence threshold for the LLM part. |
| `device_map` | string | Passed through to `transformers` (e.g. `"auto"` for automatic multi-GPU placement). |
| `huggingface_access_token` | string | For gated HF models. |
| `openai_key` | string | For `*_ada` retrievers and `gpt_openai_*` LLMs. |
| `answer_set` | dict | Same as for `llm`. |
| `n_shots` | int | **`fewshot-rag` only**: number of few-shot examples drawn from `reference_matching_path`. |
| `positive_ratio` | float, 0.0–1.0 | **`fewshot-rag` only**: share of positive (true-match) examples among the few-shots. |

**`matcher` values by `method`:**

| `matcher` | `rag` | `fewshot-rag` | `icv-rag` | LLM backbone | Retriever |
|---|:---:|:---:|:---:|---|---|
| `llama_ada` | ✓ | ✓ | ✓ | LLaMA family | OpenAI embeddings |
| `llama_bert` | ✓ | ✓ | ✓ | LLaMA family | Bi-encoder (SBERT) |
| `mistral_ada` | ✓ | ✓ | – | Mistral | OpenAI embeddings |
| `mistral_bert` | ✓ | ✓ | – | Mistral | Bi-encoder (SBERT) |
| `gpt_openai_ada` | ✓ | ✓ | – | OpenAI GPT | OpenAI embeddings |
| `gpt_openai_bert` | ✓ | ✓ | – | OpenAI GPT | Bi-encoder (SBERT) |
| `falcon_ada` | ✓ | ✓ | ✓ | Falcon | OpenAI embeddings |
| `falcon_bert` | ✓ | ✓ | ✓ | Falcon | Bi-encoder (SBERT) |
| `vicuna_ada` | ✓ | ✓ | ✓ | Vicuna | OpenAI embeddings |
| `vicuna_bert` | ✓ | ✓ | ✓ | Vicuna | Bi-encoder (SBERT) |
| `mpt_ada` | ✓ | ✓ | ✓ | MPT | OpenAI embeddings |
| `mpt_bert` | ✓ | ✓ | ✓ | MPT | Bi-encoder (SBERT) |
| `mamba_ada` | ✓ | ✓ | – | Mamba (SSM) | OpenAI embeddings |
| `mamba_bert` | ✓ | ✓ | – | Mamba (SSM) | Bi-encoder (SBERT) |

`llm_path` specifies the **concrete** HuggingFace model for every backbone (e.g. `mistralai/Mistral-7B-Instruct-v0.2` for `mistral_*`, `tiiuae/falcon-7b-instruct` for `falcon_*`, etc.) — the backbone name in the `matcher` value only selects the matching prompt/architecture class; the actual model weights always come from `llm_path`. For `gpt_openai_*`, `llm_path` is the OpenAI model name instead.

**`fewshot-rag` and `icv-rag` strictly require `input.reference_matching_path`**, since the few-shot examples / in-context vectors are generated from the reference alignments.

## 9. OntoAligner modules not covered here

`run_ontoaligner.py` covers the four method families unified behind
`OntoAlignerPipeline` (`lightweight`, `retrieval`, `llm`, `*-rag`).
OntoAligner also ships additional, more specialized aligners that do
**not** run through this unified dispatch and therefore need their own
scripts/configuration (see the `examples/` scripts in the OntoAligner
repository):

- **Graph embedding aligners** (`ontoaligner.aligner.graph`): TransE, TransR, TransH, TransF, TransD, DistMult, ComplEx, HolE, RotatE, SimplE, CrossE, BoxE, CompGCN, MuRE, QuatE, ConvE, SE — for knowledge-graph alignment via embedding distances. This is the **Embedding-based (KGE)** family.
- **`PropMatchAligner`** (`ontoaligner.aligner.propmatch`) — property/attribute matching instead of class matching.
- **`FLORAAligner`** (`ontoaligner.aligner.flora`) — fuzzy-logic-based KG alignment.
- **`OLaLaAligner`** (`ontoaligner.aligner.olala`) — combined high-precision + LLM approach specifically for very heterogeneous, loosely structured ontologies.
- **`EnsembleLearningAligner`** (`ontoaligner.aligner.ensemble`) — combines several finished `AlignerPipeline` runs via a voting strategy (`WeightedVoting`, `BordaVoting`, `CondorcetVoting`, `ReciprocalRankFusionVoting`, …). This is the **Ensemble** family.
- **Reranking** (`CrossEncoderReranking`, `CohereReranking`) — post-processing of `retrieval` candidates; technically only usable via the lower-level `AlignerPipeline` API, not via `OntoAlignerPipeline`.

These modules are deliberately left out because they use different input
formats (knowledge-graph triples instead of OWL classes, pretrained
embedding files, etc.) and their own constructor signatures, which don't
map cleanly onto a single generic YAML schema without losing precision.

## 10. Resource notes

- `lightweight` and `retrieval` with `tfidf`/`bm25` run without a GPU and
  without any model download.
- `retrieval` with `sbert`/`svm_bert`, as well as all `llm`/`rag` methods,
  download models via HuggingFace `transformers`/`sentence-transformers`
  (several hundred MB to several GB) and benefit strongly from a GPU
  (`device: cuda`).
- API costs apply for `gpt_openai*` and `*_ada` matchers.