from pathlib import Path

import yaml

from kgpipe.common import KgTask, TaskInput, TaskOutput, BasicDataFormats, BasicTaskCategoryCatalog, Registry
from kgpipe.common.model.configuration import ConfigurationDefinition, Parameter, ParameterType, ConfigurationProfile

from kgpipe.common.io import get_docker_volume_bindings, remap_data_path_for_container
from kgpipe.execution import docker_client

from kgpipe.common import Data

_OA_INPUT_SPEC = {"source": BasicDataFormats.RDF, "target": BasicDataFormats.RDF}
_OA_OUTPUT_SPEC = {"output": BasicDataFormats.XML}

_ENCODER_LIGHTWEIGHT_RETRIEVAL = ["concept", "concept_children", "concept_parent", "doc_concept", "mila"]
_ENCODER_LLM_RAG = ["concept", "concept_children", "concept_parent"]

_LIGHTWEIGHT_MATCHERS = ["simple_fuzzy", "weighted_fuzzy", "token_set_fuzzy"]
_RETRIEVAL_MATCHERS = ["sbert", "tfidf", "bm25", "svm_bert", "ada"]
_LLM_MATCHERS = ["auto_decoder", "flan_t5", "gpt_openai"]
_LLM_DATASETS = ["concept", "concept_parent", "concept_children"]

_RAG_VARIANTS = ["rag", "fewshot-rag", "icv-rag"]
_RAG_MATCHERS = [
    "llama_ada", "llama_bert",
    "mistral_ada", "mistral_bert",
    "gpt_openai_ada", "gpt_openai_bert",
    "falcon_ada", "falcon_bert",
    "vicuna_ada", "vicuna_bert",
    "mpt_ada", "mpt_bert",
    "mamba_ada", "mamba_bert",
]
_RAG_ICV_ALLOWED_MATCHERS = [
    "llama_ada", "llama_bert",
    "falcon_ada", "falcon_bert",
    "vicuna_ada", "vicuna_bert",
    "mpt_ada", "mpt_bert",
]


def _io_parameters() -> list[Parameter]:
    """Input/output config shared by all four method families (§1, §2)."""
    return [
        Parameter(
            name="source_ontology_path",
            native_keys=["input.source_ontology_path", "--source"],
            datatype=ParameterType.string,
            required=True,
        ),
        Parameter(
            name="target_ontology_path",
            native_keys=["input.target_ontology_path", "--target"],
            datatype=ParameterType.string,
            required=True,
        ),
        Parameter(
            name="reference_matching_path",
            native_keys=["input.reference_matching_path", "--reference"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="task_class",
            native_keys=["input.task_class"],
            datatype=ParameterType.string,
            default_value="generic",
            required=False,
            allowed_values=["generic", "generic_olala"],
        ),
        Parameter(
            name="output_dir",
            native_keys=["output.output_dir", "--output-dir"],
            datatype=ParameterType.string,
            required=True,
        ),
        Parameter(
            name="output_format",
            native_keys=["output.output_format", "--output-format"],
            datatype=ParameterType.string,
            default_value="xml",
            required=False,
            allowed_values=["xml", "json"],
        ),
        Parameter(
            name="output_file_name",
            native_keys=["output.output_file_name"],
            datatype=ParameterType.string,
            required=True,
        ),
        Parameter(
            name="save_matchings",
            native_keys=["output.save_matchings"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),
        Parameter(
            name="return_matching",
            native_keys=["output.return_matching"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="evaluate",
            native_keys=["output.evaluate"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
    ]


def _encoder_parameter(allowed_values: list[str]) -> Parameter:
    return Parameter(
        name="encoder_name",
        native_keys=["encoder.name"],
        datatype=ParameterType.string,
        required=True,
        allowed_values=allowed_values,
    )


def _lightweight_parameters() -> list[Parameter]:
    return [
        Parameter(
            name="method",
            native_keys=["method", "--method"],
            datatype=ParameterType.string,
            default_value="lightweight",
            required=False,
            allowed_values=["lightweight"],
        ),
        _encoder_parameter(_ENCODER_LIGHTWEIGHT_RETRIEVAL),
        Parameter(
            name="matcher",
            native_keys=["lightweight.matcher"],
            datatype=ParameterType.string,
            required=True,
            allowed_values=_LIGHTWEIGHT_MATCHERS,
        ),
        Parameter(
            name="fuzzy_sm_threshold",
            native_keys=["lightweight.fuzzy_sm_threshold"],
            datatype=ParameterType.number,
            required=True,
            minimum=0.0,
            maximum=1.0,
        ),
    ]


def _retrieval_parameters() -> list[Parameter]:
    return [
        Parameter(
            name="method",
            native_keys=["method", "--method"],
            datatype=ParameterType.string,
            default_value="retrieval",
            required=False,
            allowed_values=["retrieval"],
        ),
        _encoder_parameter(_ENCODER_LIGHTWEIGHT_RETRIEVAL),
        Parameter(
            name="matcher",
            native_keys=["retrieval.matcher"],
            datatype=ParameterType.string,
            required=True,
            allowed_values=_RETRIEVAL_MATCHERS,
        ),
        # Ignored by OntoAligner for tfidf/bm25 -- filtered out at
        # config-build time in _build_config_from_profile.
        Parameter(
            name="retriever_path",
            native_keys=["retrieval.retriever_path"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        # Only relevant for sbert/svm_bert.
        Parameter(
            name="device",
            native_keys=["retrieval.device"],
            datatype=ParameterType.string,
            default_value="cpu",
            required=False,
        ),
        Parameter(
            name="top_k",
            native_keys=["retrieval.top_k"],
            datatype=ParameterType.integer,
            required=True,
            minimum=1,
        ),
        Parameter(
            name="ir_threshold",
            native_keys=["retrieval.ir_threshold"],
            datatype=ParameterType.number,
            required=True,
            minimum=0.0,
        ),
        # Only relevant for matcher: ada.
        Parameter(
            name="openai_key",
            native_keys=["retrieval.openai_key"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
    ]


def _llm_parameters() -> list[Parameter]:
    return [
        Parameter(
            name="method",
            native_keys=["method", "--method"],
            datatype=ParameterType.string,
            default_value="llm",
            required=False,
            allowed_values=["llm"],
        ),
        _encoder_parameter(_ENCODER_LLM_RAG),
        Parameter(
            name="matcher",
            native_keys=["llm.matcher"],
            datatype=ParameterType.string,
            required=True,
            allowed_values=_LLM_MATCHERS,
        ),
        Parameter(
            name="llm_path",
            native_keys=["llm.llm_path"],
            datatype=ParameterType.string,
            required=True,
        ),
        Parameter(
            name="dataset",
            native_keys=["llm.dataset"],
            datatype=ParameterType.string,
            required=True,
            allowed_values=_LLM_DATASETS,
        ),
        # Only relevant for local models (auto_decoder/flan_t5).
        Parameter(
            name="device",
            native_keys=["llm.device"],
            datatype=ParameterType.string,
            default_value="cpu",
            required=False,
        ),
        Parameter(
            name="batch_size",
            native_keys=["llm.batch_size"],
            datatype=ParameterType.integer,
            required=True,
            minimum=1,
        ),
        Parameter(
            name="max_length",
            native_keys=["llm.max_length"],
            datatype=ParameterType.integer,
            required=True,
            minimum=1,
        ),
        Parameter(
            name="max_new_tokens",
            native_keys=["llm.max_new_tokens"],
            datatype=ParameterType.integer,
            required=True,
            minimum=1,
        ),
        Parameter(
            name="llm_threshold",
            native_keys=["llm.llm_threshold"],
            datatype=ParameterType.number,
            required=True,
            minimum=0.0,
        ),
        Parameter(
            name="llm_mapper_interested_class",
            native_keys=["llm.llm_mapper_interested_class"],
            datatype=ParameterType.string,
            default_value="yes",
            required=False,
        ),
        # answer_set (dict of yes/no wordlists) intentionally omitted --
        # see module docstring, point 4.
        Parameter(
            name="huggingface_access_token",
            native_keys=["llm.huggingface_access_token"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        # Only relevant for matcher: gpt_openai.
        Parameter(
            name="openai_key",
            native_keys=["llm.openai_key"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
    ]


def _rag_parameters() -> list[Parameter]:
    return [
        Parameter(
            name="rag_variant",
            native_keys=["method", "--method"],
            datatype=ParameterType.string,
            default_value="rag",
            required=False,
            allowed_values=_RAG_VARIANTS,
        ),
        _encoder_parameter(_ENCODER_LLM_RAG),
        Parameter(
            name="matcher",
            native_keys=["rag.matcher"],
            datatype=ParameterType.string,
            required=True,
            allowed_values=_RAG_MATCHERS,
        ),
        Parameter(
            name="retriever_path",
            native_keys=["rag.retriever_path"],
            datatype=ParameterType.string,
            required=True,
        ),
        Parameter(
            name="llm_path",
            native_keys=["rag.llm_path"],
            datatype=ParameterType.string,
            required=True,
        ),
        Parameter(
            name="device",
            native_keys=["rag.device"],
            datatype=ParameterType.string,
            default_value="cpu",
            required=False,
        ),
        Parameter(
            name="batch_size",
            native_keys=["rag.batch_size"],
            datatype=ParameterType.integer,
            required=True,
            minimum=1,
        ),
        Parameter(
            name="max_length",
            native_keys=["rag.max_length"],
            datatype=ParameterType.integer,
            required=True,
            minimum=1,
        ),
        Parameter(
            name="max_new_tokens",
            native_keys=["rag.max_new_tokens"],
            datatype=ParameterType.integer,
            required=True,
            minimum=1,
        ),
        Parameter(
            name="top_k",
            native_keys=["rag.top_k"],
            datatype=ParameterType.integer,
            required=True,
            minimum=1,
        ),
        Parameter(
            name="ir_rag_threshold",
            native_keys=["rag.ir_rag_threshold"],
            datatype=ParameterType.number,
            required=True,
            minimum=0.0,
        ),
        Parameter(
            name="llm_threshold",
            native_keys=["rag.llm_threshold"],
            datatype=ParameterType.number,
            required=True,
            minimum=0.0,
        ),
        Parameter(
            name="device_map",
            native_keys=["rag.device_map"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="huggingface_access_token",
            native_keys=["rag.huggingface_access_token"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        # Relevant for *_ada retrievers and gpt_openai_* LLM backbones.
        Parameter(
            name="openai_key",
            native_keys=["rag.openai_key"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        # answer_set intentionally omitted -- see module docstring, point 4.
        # fewshot-rag only; requires reference_matching_path (checked below).
        Parameter(
            name="n_shots",
            native_keys=["rag.n_shots"],
            datatype=ParameterType.integer,
            default_value=0,
            required=False,
            minimum=0,
        ),
        Parameter(
            name="positive_ratio",
            native_keys=["rag.positive_ratio"],
            datatype=ParameterType.number,
            default_value=0.5,
            required=False,
            minimum=0.0,
            maximum=1.0,
        ),
    ]


ontoaligner_lightweight_matching_config = ConfigurationDefinition(
    name="ontoaligner_lightweight_matching",
    description="OntoAligner lightweight (fuzzy string) ontology matching",
    parameters=_io_parameters() + _lightweight_parameters(),
)

ontoaligner_retrieval_matching_config = ConfigurationDefinition(
    name="ontoaligner_retrieval_matching",
    description="OntoAligner retrieval-based (TF-IDF/BM25/bi-encoder) ontology matching",
    parameters=_io_parameters() + _retrieval_parameters(),
)

ontoaligner_llm_matching_config = ConfigurationDefinition(
    name="ontoaligner_llm_matching",
    description="OntoAligner LLM-based ontology matching",
    parameters=_io_parameters() + _llm_parameters(),
)

ontoaligner_rag_matching_config = ConfigurationDefinition(
    name="ontoaligner_rag_matching",
    description="OntoAligner RAG-based ontology matching (rag / fewshot-rag / icv-rag)",
    parameters=_io_parameters() + _rag_parameters(),
)

_CLI_ONLY_FLAGS = {
    "--source": "source",
    "--target": "target",
    "--reference": "reference",
    "--output-dir": "output_dir",
    "--output-format": "output_format",
    "--method": "method",
}


def _set_dotted(d: dict, dotted_key: str, value) -> None:
    parts = dotted_key.split(".")
    node = d
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value


def _drop_keys(block: dict, keep: set[str]) -> None:
    if not block:
        return
    for key in list(block.keys()):
        if key != "matcher" and key not in keep:
            block.pop(key)


_RETRIEVAL_MATCHER_KEYS = {
    "tfidf": set(),
    "bm25": set(),
    "sbert": {"retriever_path", "device"},
    "svm_bert": {"retriever_path", "device"},
    "ada": {"retriever_path", "openai_key"},
}

_LLM_MATCHER_KEYS = {
    "auto_decoder": {"llm_path", "dataset", "device", "batch_size", "max_length",
                      "max_new_tokens", "llm_threshold", "llm_mapper_interested_class",
                      "huggingface_access_token"},
    "flan_t5": {"llm_path", "dataset", "device", "batch_size", "max_length",
                "max_new_tokens", "llm_threshold", "llm_mapper_interested_class",
                "huggingface_access_token"},
    "gpt_openai": {"llm_path", "dataset", "llm_threshold", "llm_mapper_interested_class",
                   "openai_key"},
}


def _rag_relevant_keys(matcher: str) -> set[str]:
    """Derived from CONFIG_REFERENCE.md §8: field relevance depends on the
    `_ada` (OpenAI embeddings) vs. `_bert` (SBERT) retriever suffix and the
    `gpt_openai_*` vs. local-model LLM backbone -- not itself an explicit
    table in the doc, so double-check against the wrapper's actual code."""
    keys = {"retriever_path", "llm_path", "batch_size", "max_length",
            "max_new_tokens", "top_k", "ir_rag_threshold", "llm_threshold"}
    if matcher.endswith("_ada"):
        keys.add("openai_key")
    if not matcher.startswith("gpt_openai_"):
        keys.update({"device", "device_map", "huggingface_access_token"})
    else:
        keys.add("openai_key")
    return keys


def _build_config_from_profile(config: ConfigurationProfile, rag_variant: str | None = None) -> tuple[dict, dict]:
    nested: dict = {}
    cli_extra: dict = {}

    for param in config.definition.parameters:
        try:
            value = config.get_parameter_value(param.name)
        except ValueError:
            value = param.default_value

        for native_key in param.native_keys:
            if native_key in _CLI_ONLY_FLAGS:
                cli_extra[_CLI_ONLY_FLAGS[native_key]] = value
            elif "." in native_key:
                _set_dotted(nested, native_key, value)

    if "retrieval" in nested:
        matcher = nested["retrieval"].get("matcher")
        _drop_keys(nested["retrieval"], _RETRIEVAL_MATCHER_KEYS.get(matcher, set()))

    if "llm" in nested:
        matcher = nested["llm"].get("matcher")
        _drop_keys(nested["llm"], _LLM_MATCHER_KEYS.get(matcher, set()))

    if "rag" in nested:
        matcher = nested["rag"].get("matcher")
        _drop_keys(nested["rag"], _rag_relevant_keys(matcher))

        if rag_variant == "fewshot-rag":
            nested["rag"]["n_shots"] = config.get_parameter_value("n_shots")
            nested["rag"]["positive_ratio"] = config.get_parameter_value("positive_ratio")
        else:
            nested["rag"].pop("n_shots", None)
            nested["rag"].pop("positive_ratio", None)

        if rag_variant in ("fewshot-rag", "icv-rag"):
            if not nested.get("input", {}).get("reference_matching_path"):
                raise ValueError(f"{rag_variant} requires input.reference_matching_path (CONFIG_REFERENCE.md §8)")

        if rag_variant == "icv-rag" and matcher not in _RAG_ICV_ALLOWED_MATCHERS:
            raise ValueError(
                f"matcher '{matcher}' is not valid for icv-rag "
                f"(CONFIG_REFERENCE.md §8 table); allowed: {_RAG_ICV_ALLOWED_MATCHERS}"
            )

    return nested, cli_extra


def _write_config_yaml(config_dict: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config_dict, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
    return path


def _run_ontoaligner_matching(inputs: TaskInput, outputs: TaskOutput, config: ConfigurationProfile):

    print(f"OntoAligner matching with inputs: {inputs}")

    config_dict, cli_extra = _build_config_from_profile(config)
    config_host_path = outputs["output"].path.parent / f"{config.name}.yaml"
    config_data = Data(str(config_host_path), BasicDataFormats.ANY)
    _write_config_yaml(config_dict, config_host_path)

    all_data = list(inputs.values()) + list(outputs.values()) + [config_data]
    volumes, host_to_container = get_docker_volume_bindings(all_data)

    # Extract input paths
    source_path = remap_data_path_for_container(inputs["source"], host_to_container)
    target_path = remap_data_path_for_container(inputs["target"], host_to_container)
    output_path = remap_data_path_for_container(outputs["output"], host_to_container)
    config_container_path = remap_data_path_for_container(config_data, host_to_container)

    # Ensure output directory exists
    outputs["output"].path.parent.mkdir(parents=True, exist_ok=True)

    command = ["bash", "ontoaligner.sh",
               str(source_path.path),
               str(target_path.path),
               str(output_path.path),
               str(config_container_path.path)]

    # Create Docker client with proper volume bindings
    client = docker_client(
        image="kgt/ontoaligner:latest",
        command=command,
        volumes=volumes,
    )

    # Execute the container
    result = client()
    print(f"OntoAligner matching completed: {result}")


def ontoaligner_lightweight_matching(inputs: TaskInput, outputs: TaskOutput, config: ConfigurationProfile):
    _run_ontoaligner_matching(inputs, outputs, config)


def ontoaligner_retrieval_matching(inputs: TaskInput, outputs: TaskOutput, config: ConfigurationProfile):
    _run_ontoaligner_matching(inputs, outputs, config)


def ontoaligner_llm_matching(inputs: TaskInput, outputs: TaskOutput, config: ConfigurationProfile):
    _run_ontoaligner_matching(inputs, outputs, config)


def ontoaligner_rag_matching(inputs: TaskInput, outputs: TaskOutput, config: ConfigurationProfile):
    _run_ontoaligner_matching(inputs, outputs, config)


ontoaligner_lightweight_matching_task = KgTask(
    name="ontoaligner_lightweight_matching",
    description="OntoAligner lightweight (fuzzy string) ontology matching",
    input_spec=_OA_INPUT_SPEC,
    output_spec=_OA_OUTPUT_SPEC,
    function=ontoaligner_lightweight_matching,
    config_spec=ontoaligner_lightweight_matching_config,
    category=[BasicTaskCategoryCatalog.ontology_matching],
    tools=["ontoaligner"],
)

ontoaligner_retrieval_matching_task = KgTask(
    name="ontoaligner_retrieval_matching",
    description="OntoAligner retrieval-based ontology matching",
    input_spec=_OA_INPUT_SPEC,
    output_spec=_OA_OUTPUT_SPEC,
    function=ontoaligner_retrieval_matching,
    config_spec=ontoaligner_retrieval_matching_config,
    category=[BasicTaskCategoryCatalog.ontology_matching],
    tools=["ontoaligner"],
)

ontoaligner_llm_matching_task = KgTask(
    name="ontoaligner_llm_matching",
    description="OntoAligner LLM-based ontology matching",
    input_spec=_OA_INPUT_SPEC,
    output_spec=_OA_OUTPUT_SPEC,
    function=ontoaligner_llm_matching,
    config_spec=ontoaligner_llm_matching_config,
    category=[BasicTaskCategoryCatalog.ontology_matching],
    tools=["ontoaligner"],
)

ontoaligner_rag_matching_task = KgTask(
    name="ontoaligner_rag_matching",
    description="OntoAligner RAG-based ontology matching (rag / fewshot-rag / icv-rag)",
    input_spec=_OA_INPUT_SPEC,
    output_spec=_OA_OUTPUT_SPEC,
    function=ontoaligner_rag_matching,
    config_spec=ontoaligner_rag_matching_config,
    category=[BasicTaskCategoryCatalog.ontology_matching],
    tools=["ontoaligner"],
)

Registry.add_task(ontoaligner_lightweight_matching_task.name, ontoaligner_lightweight_matching_task)
Registry.add_task(ontoaligner_retrieval_matching_task.name, ontoaligner_retrieval_matching_task)
Registry.add_task(ontoaligner_llm_matching_task.name, ontoaligner_llm_matching_task)
Registry.add_task(ontoaligner_rag_matching_task.name, ontoaligner_rag_matching_task)