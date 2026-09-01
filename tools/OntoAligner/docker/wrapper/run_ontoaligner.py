#!/usr/bin/env python3
"""
run_ontoaligner.py
===================

Config-driven runner for OntoAligner (https://github.com/sciknoworg/OntoAligner).

Takes a YAML configuration file (see config.yaml / CONFIG_REFERENCE.md) and
uses it to run ontoaligner.OntoAlignerPipeline. All combinations of method
(lightweight / retrieval / llm / rag / fewshot-rag / icv-rag), encoder, and
matcher/aligner available in the OntoAligner library (version 1.9.3, against
which this script was verified) are selectable via the config.

Covers the four method families unified behind OntoAlignerPipeline. It does
NOT cover Knowledge Graph Embedding (KGE) or Ensemble Learning aligners,
which use a different input format and API - see CONFIG_REFERENCE.md
section 9 for details.

Usage:
    python run_ontoaligner.py --config config.yaml
    python run_ontoaligner.py --config config.yaml \\
        --source data/source.owl --target data/target.owl --output-dir results/

Installation:
    pip install ontoaligner pyyaml
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, Type

import yaml

# ---------------------------------------------------------------------------
# Registries
#
# These registries map user-friendly YAML identifiers to the actual
# OntoAligner class names. The class names were checked against the source
# code of the ontoaligner wheel (v1.9.3). Details on every option are in
# CONFIG_REFERENCE.md.
# ---------------------------------------------------------------------------

TASK_CLASSES = {
    "generic": "GenericOMDataset",       # arbitrary custom OWL files (rdflib, format="xml")
    "generic_olala": "OLaLaOMDataset",   # like generic, but with OLaLa text extraction
}

# Encoder registry, keyed by "encoder family". Which family is used for
# which method is defined in ENCODER_FAMILY_BY_METHOD below.
ENCODERS = {
    "lightweight": {
        "concept": "ConceptLightweightEncoder",
        "concept_children": "ConceptChildrenLightweightEncoder",
        "concept_parent": "ConceptParentLightweightEncoder",
        "doc_concept": "DocConceptLightweightEncoder",
        "mila": "MILAEncoder",
    },
    "llm": {
        "concept": "ConceptLLMEncoder",
        "concept_children": "ConceptChildrenLLMEncoder",
        "concept_parent": "ConceptParentLLMEncoder",
    },
    "rag": {
        "concept": "ConceptRAGEncoder",
        "concept_children": "ConceptChildrenRAGEncoder",
        "concept_parent": "ConceptParentRAGEncoder",
    },
    "fewshot": {
        "concept": "ConceptFewShotEncoder",
        "concept_children": "ConceptChildrenFewShotEncoder",
        "concept_parent": "ConceptParentFewShotEncoder",
    },
}

# Which encoder family (key in ENCODERS) applies to which "method".
ENCODER_FAMILY_BY_METHOD = {
    "lightweight": "lightweight",
    "retrieval": "lightweight",   # OntoAlignerPipeline uses the same encoder as lightweight for retrieval
    "llm": "llm",
    "rag": "rag",
    "icv-rag": "rag",
    "fewshot-rag": "fewshot",
}

MATCHERS = {
    "lightweight": {
        "simple_fuzzy": "SimpleFuzzySMLightweight",
        "weighted_fuzzy": "WeightedFuzzySMLightweight",
        "token_set_fuzzy": "TokenSetFuzzySMLightweight",
    },
    "retrieval": {
        "sbert": "SBERTRetrieval",
        "tfidf": "TFIDFRetrieval",
        "bm25": "BM25Retrieval",
        "svm_bert": "SVMBERTRetrieval",
        "ada": "AdaRetrieval",
    },
    "llm": {
        "auto_decoder": "AutoModelDecoderLLM",   # any HF causal LM via llm_path
        "flan_t5": "FlanT5LEncoderDecoderLM",    # HF seq2seq model (e.g. Flan-T5) via llm_path
        "gpt_openai": "GPTOpenAILLM",            # OpenAI chat model via llm_path (model name) + openai_key
    },
    "rag": {
        "llama_ada": "LLaMALLMAdaRetrieverRAG",
        "llama_bert": "LLaMALLMBERTRetrieverRAG",
        "mistral_ada": "MistralLLMAdaRetrieverRAG",
        "mistral_bert": "MistralLLMBERTRetrieverRAG",
        "gpt_openai_ada": "GPTOpenAILLMAdaRetrieverRAG",
        "gpt_openai_bert": "GPTOpenAILLMBERTRetrieverRAG",
        "falcon_ada": "FalconLLMAdaRetrieverRAG",
        "falcon_bert": "FalconLLMBERTRetrieverRAG",
        "vicuna_ada": "VicunaLLMAdaRetrieverRAG",
        "vicuna_bert": "VicunaLLMBERTRetrieverRAG",
        "mpt_ada": "MPTLLMAdaRetrieverRAG",
        "mpt_bert": "MPTLLMBERTRetrieverRAG",
        "mamba_ada": "MambaLLMAdaRetrieverRAG",
        "mamba_bert": "MambaLLMBERTRetrieverRAG",
    },
    "fewshot-rag": {
        "llama_ada": "LLaMALLMAdaRetrieverFSRAG",
        "llama_bert": "LLaMALLMBERTRetrieverFSRAG",
        "mistral_ada": "MistralLLMAdaRetrieverFSRAG",
        "mistral_bert": "MistralLLMBERTRetrieverFSRAG",
        "gpt_openai_ada": "GPTOpenAILLMAdaRetrieverFSRAG",
        "gpt_openai_bert": "GPTOpenAILLMBERTRetrieverFSRAG",
        "falcon_ada": "FalconLLMAdaRetrieverFSRAG",
        "falcon_bert": "FalconLLMBERTRetrieverFSRAG",
        "vicuna_ada": "VicunaLLMAdaRetrieverFSRAG",
        "vicuna_bert": "VicunaLLMBERTRetrieverFSRAG",
        "mpt_ada": "MPTLLMAdaRetrieverFSRAG",
        "mpt_bert": "MPTLLMBERTRetrieverFSRAG",
        "mamba_ada": "MambaLLMAdaRetrieverFSRAG",
        "mamba_bert": "MambaLLMBERTRetrieverFSRAG",
    },
    "icv-rag": {
        "llama_ada": "LLaMALLMAdaRetrieverICVRAG",
        "llama_bert": "LLaMALLMBERTRetrieverICVRAG",
        "falcon_ada": "FalconLLMAdaRetrieverICVRAG",
        "falcon_bert": "FalconLLMBERTRetrieverICVRAG",
        "vicuna_ada": "VicunaLLMAdaRetrieverICVRAG",
        "vicuna_bert": "VicunaLLMBERTRetrieverICVRAG",
        "mpt_ada": "MPTLLMAdaRetrieverICVRAG",
        "mpt_bert": "MPTLLMBERTRetrieverICVRAG",
    },
}

LLM_DATASETS = {
    "concept": "ConceptLLMDataset",
    "concept_parent": "ConceptParentLLMDataset",
    "concept_children": "ConceptChildrenLLMDataset",
    "property": "PropertyLLMDataset",
    "property_full_text": "PropertyFullTextLLMDataset",
}

DEFAULTS: Dict[str, Any] = {
    "input": {
        "source_ontology_path": "",
        "target_ontology_path": "",
        "reference_matching_path": "",
        "task_class": "generic",
    },
    "output": {
        "output_dir": "results",
        "output_format": "xml",
        "output_file_name": "matchings",
        "save_matchings": True,
        "return_matching": True,
        "evaluate": False,
    },
    "method": "lightweight",
    "encoder": {"name": "concept"},
    "lightweight": {
        "matcher": "simple_fuzzy",
        "fuzzy_sm_threshold": 0.2,
    },
    "retrieval": {
        "matcher": "sbert",
        "retriever_path": "sentence-transformers/all-MiniLM-L6-v2",
        "device": "cpu",
        "top_k": 10,
        "ir_threshold": 0.5,
        "openai_key": "",
    },
    "llm": {
        "matcher": "auto_decoder",
        "llm_path": "",
        "dataset": "concept",
        "device": "cpu",
        "batch_size": 8,
        "max_length": 300,
        "max_new_tokens": 10,
        "llm_threshold": 0.5,
        "llm_mapper_interested_class": "yes",
        "answer_set": {"yes": ["yes", "true"], "no": ["no", "false"]},
        "huggingface_access_token": "",
        "openai_key": "",
    },
    "rag": {
        "matcher": "mistral_bert",
        "retriever_path": "sentence-transformers/all-MiniLM-L6-v2",
        "llm_path": "",
        "device": "cpu",
        "batch_size": 8,
        "max_length": 300,
        "max_new_tokens": 10,
        "top_k": 10,
        "ir_rag_threshold": 0.7,
        "llm_threshold": 0.5,
        "device_map": "auto",
        "huggingface_access_token": "",
        "openai_key": "",
        "answer_set": {"yes": ["yes", "true"], "no": ["no", "false"]},
        "n_shots": 5,
        "positive_ratio": 0.7,
    },
}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merges `override` into a copy of `base` (override wins)."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        user_config = yaml.safe_load(fh) or {}
    return deep_merge(DEFAULTS, user_config)


def resolve(module, class_name: str):
    """Fetches a class by name from an imported OntoAligner submodule."""
    if not hasattr(module, class_name):
        raise ValueError(
            f"'{class_name}' was not found in {module.__name__}. "
            f"Please check CONFIG_REFERENCE.md or verify the installed "
            f"OntoAligner version."
        )
    return getattr(module, class_name)


def build_pipeline_kwargs(cfg: Dict[str, Any], aligner_mod, encoder_mod) -> Dict[str, Any]:
    """Builds the kwargs dict for OntoAlignerPipeline.__call__ from the config."""
    method = cfg["method"]
    if method not in MATCHERS:
        raise ValueError(
            f"Unknown method '{method}'. Allowed: {sorted(MATCHERS.keys())}"
        )

    encoder_family = ENCODER_FAMILY_BY_METHOD[method]
    encoder_name = cfg["encoder"]["name"]
    if encoder_name not in ENCODERS[encoder_family]:
        raise ValueError(
            f"Encoder '{encoder_name}' is not valid for method '{method}'. "
            f"Allowed: {sorted(ENCODERS[encoder_family].keys())}"
        )
    encoder_class = resolve(encoder_mod, ENCODERS[encoder_family][encoder_name])

    kwargs: Dict[str, Any] = {"method": method, "encoder_model": encoder_class()}

    if method == "lightweight":
        m = cfg["lightweight"]
        kwargs["model_class"] = resolve(aligner_mod, MATCHERS["lightweight"][m["matcher"]])
        kwargs["fuzzy_sm_threshold"] = float(m["fuzzy_sm_threshold"])

    elif method == "retrieval":
        m = cfg["retrieval"]
        kwargs["model_class"] = resolve(aligner_mod, MATCHERS["retrieval"][m["matcher"]])
        kwargs["retriever_path"] = m["retriever_path"]
        kwargs["device"] = m["device"]
        kwargs["top_k"] = int(m["top_k"])
        kwargs["ir_threshold"] = float(m["ir_threshold"])
        kwargs["openai_key"] = m.get("openai_key", "")

    elif method == "llm":
        m = cfg["llm"]
        kwargs["model_class"] = resolve(aligner_mod, MATCHERS["llm"][m["matcher"]])
        kwargs["dataset_class"] = resolve(aligner_mod, LLM_DATASETS[m["dataset"]])
        kwargs["llm_path"] = m["llm_path"]
        kwargs["device"] = m["device"]
        kwargs["batch_size"] = int(m["batch_size"])
        kwargs["max_length"] = int(m["max_length"])
        kwargs["max_new_tokens"] = int(m["max_new_tokens"])
        kwargs["llm_threshold"] = float(m["llm_threshold"])
        kwargs["llm_mapper_interested_class"] = m["llm_mapper_interested_class"]
        kwargs["answer_set"] = m["answer_set"]
        kwargs["huggingface_access_token"] = m.get("huggingface_access_token", "")
        kwargs["openai_key"] = m.get("openai_key", "")

    else:  # rag, fewshot-rag, icv-rag
        m = cfg["rag"]
        kwargs["model_class"] = resolve(aligner_mod, MATCHERS[method][m["matcher"]])
        kwargs["retriever_path"] = m["retriever_path"]
        kwargs["llm_path"] = m["llm_path"]
        kwargs["device"] = m["device"]
        kwargs["batch_size"] = int(m["batch_size"])
        kwargs["max_length"] = int(m["max_length"])
        kwargs["max_new_tokens"] = int(m["max_new_tokens"])
        kwargs["top_k"] = int(m["top_k"])
        kwargs["ir_rag_threshold"] = float(m["ir_rag_threshold"])
        kwargs["llm_threshold"] = float(m["llm_threshold"])
        kwargs["device_map"] = m["device_map"]
        kwargs["huggingface_access_token"] = m.get("huggingface_access_token", "")
        kwargs["openai_key"] = m.get("openai_key", "")
        kwargs["answer_set"] = m["answer_set"]
        if method == "fewshot-rag":
            kwargs["n_shots"] = int(m["n_shots"])
            kwargs["positive_ratio"] = float(m["positive_ratio"])

    out = cfg["output"]
    kwargs["evaluate"] = bool(out["evaluate"])
    kwargs["return_matching"] = bool(out["return_matching"])
    kwargs["output_file_name"] = out["output_file_name"]
    kwargs["save_matchings"] = bool(out["save_matchings"])

    return kwargs


def apply_cli_overrides(cfg: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.source:
        cfg["input"]["source_ontology_path"] = args.source
    if args.target:
        cfg["input"]["target_ontology_path"] = args.target
    if args.reference is not None:
        cfg["input"]["reference_matching_path"] = args.reference
    if args.output_dir:
        cfg["output"]["output_dir"] = args.output_dir
    if args.output_format:
        cfg["output"]["output_format"] = args.output_format
    if args.method:
        cfg["method"] = args.method
    return cfg


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Runs OntoAligner in a config-driven way from a YAML file."
    )
    parser.add_argument("--config", required=True, help="Path to the YAML configuration file")
    parser.add_argument("--source", help="Overrides input.source_ontology_path")
    parser.add_argument("--target", help="Overrides input.target_ontology_path")
    parser.add_argument("--reference", help="Overrides input.reference_matching_path")
    parser.add_argument("--output-dir", help="Overrides output.output_dir")
    parser.add_argument("--output-format", choices=["xml", "json"], help="Overrides output.output_format")
    parser.add_argument("--method", help="Overrides method (lightweight|retrieval|llm|rag|fewshot-rag|icv-rag)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    cfg = apply_cli_overrides(cfg, args)

    if not cfg["input"]["source_ontology_path"] or not cfg["input"]["target_ontology_path"]:
        parser.error(
            "input.source_ontology_path and input.target_ontology_path must "
            "be set (in the config or via --source/--target)."
        )

    # Import only here so that --help also works without the heavy dependencies installed.
    import ontoaligner
    from ontoaligner import aligner as aligner_mod
    from ontoaligner import encoder as encoder_mod
    from ontoaligner import ontology as ontology_mod

    task_class_name = TASK_CLASSES[cfg["input"]["task_class"]]
    task_class = resolve(ontology_mod, task_class_name)

    pipeline = ontoaligner.OntoAlignerPipeline(
        task_class=task_class,
        source_ontology_path=cfg["input"]["source_ontology_path"],
        target_ontology_path=cfg["input"]["target_ontology_path"],
        reference_matching_path=cfg["input"]["reference_matching_path"],
        output_dir=cfg["output"]["output_dir"],
        output_format=cfg["output"]["output_format"],
    )

    pipeline_kwargs = build_pipeline_kwargs(cfg, aligner_mod, encoder_mod)
    result = pipeline(**pipeline_kwargs)

    if cfg["output"]["evaluate"] and cfg["output"]["return_matching"]:
        matchings, evaluation = result
        print(json.dumps(evaluation, indent=2, ensure_ascii=False))
    elif cfg["output"]["evaluate"]:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        n = len(result) if hasattr(result, "__len__") else "?"
        print(f"Done. {n} matchings produced.")

    if cfg["output"]["save_matchings"]:
        out_path = (
            Path(cfg["output"]["output_dir"])
            / cfg["method"]
            / f"{cfg['output']['output_file_name']}.{cfg['output']['output_format']}"
        )
        print(f"Result saved to: {out_path}")


if __name__ == "__main__":
    main()