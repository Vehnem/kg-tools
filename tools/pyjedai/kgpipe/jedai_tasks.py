"""KGpipe task definitions for wrapping pyJedAI entity matching.

JedAI is one Docker pipeline (two CSVs in, ER JSON out). Stages that do not
change that contract — cleaning, blocking, block/comparison cleaning, clustering —
are ConfigurationDefinition parameters. The matcher family *does* change the
task identity in KGpipe, so it is split into two KgTasks:

- syntactic: TF-IDF / n-gram string similarity (`method: entity_matching`)
- semantic: pretrained embeddings (`method: vector`)

Blocking / clustering stay parameters until intermediate artifacts (blocks,
pair graphs) are first-class KGpipe formats. Then they can become their own
KgTasks under BasicTaskCategoryCatalog.blocking / .clustering.
"""

from pathlib import Path

import yaml

from kgpipe.common import KgTask, TaskInput, TaskOutput, BasicDataFormats, BasicTaskCategoryCatalog, Registry
from kgpipe.common.model.configuration import ConfigurationDefinition, Parameter, ParameterType, ConfigurationProfile

from kgpipe.common.io import get_docker_volume_bindings, remap_data_path_for_container
from kgpipe.execution import docker_client

from kgpipe.common import Data

_JEDAI_ER_INPUT_SPEC = {"source": BasicDataFormats.CSV, "target": BasicDataFormats.CSV}
_JEDAI_ER_OUTPUT_SPEC = {"output": BasicDataFormats.ER_JSON}

_BLOCKING_METHODS = [
    "standard_blocking",
    "qgrams_blocking",
    "extended_qgrams_blocking",
    "suffix_arrays_blocking",
    "extended_suffix_arrays_blocking",
]
_COMPARISON_CLEANING_METHODS = [
    "weighted_edge_pruning",
    "weighted_node_pruning",
    "cardinality_edge_pruning",
    "cardinality_node_pruning",
    "blast",
    "reciprocal_cardinality_node_pruning",
    "reciprocal_weighted_node_pruning",
    "comparison_propagation",
]
_WEIGHTING_SCHEMES = [
    "CBS", "CN-CBS", "SN-CBS", "ECBS", "JS", "EJS", "X2",
    "COSINE", "DICE", "CNC", "SNC", "CND", "SND", "CNJ", "SNJ",
]
_CLUSTERING_METHODS = [
    "best_match_clustering",
    "center_clustering",
    "connected_components_clustering",
    "correlation_clustering",
    "cut_clustering",
    "exact_clustering",
    "kiraly_msm_approximate_clustering",
    "markov_clustering",
    "merge_center_clustering",
    "ricochet_sr_clustering",
    "row_column_clustering",
    "unique_mapping_clustering",
]


def _jedai_pipeline_parameters() -> list[Parameter]:
    """Flattened wrapper YAML stages that both matcher tasks share."""
    return [
        Parameter(
            name="csv_separator",
            native_keys=["--sep"],
            datatype=ParameterType.string,
            default_value="|",
            required=False,
        ),
        Parameter(
            name="data_cleaning_enabled",
            native_keys=["data_cleaning.enabled"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="remove_stopwords",
            native_keys=["data_cleaning.params.remove_stopwords"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),
        Parameter(
            name="remove_punctuation",
            native_keys=["data_cleaning.params.remove_punctuation"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),
        Parameter(
            name="remove_numbers",
            native_keys=["data_cleaning.params.remove_numbers"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),
        Parameter(
            name="remove_unicodes",
            native_keys=["data_cleaning.params.remove_unicodes"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),
        Parameter(
            name="blocking_method",
            native_keys=["blocking.method"],
            datatype=ParameterType.string,
            default_value="standard_blocking",
            required=False,
            allowed_values=_BLOCKING_METHODS,
        ),
        Parameter(
            name="attributes_1",
            native_keys=["blocking.attributes_1", "--attr1"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="attributes_2",
            native_keys=["blocking.attributes_2", "--attr2"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="blocking_qgrams",
            native_keys=["blocking.method_params.qgrams"],
            datatype=ParameterType.integer,
            default_value=3,
            required=False,
            minimum=1,
        ),
        Parameter(
            name="blocking_threshold",
            native_keys=["blocking.method_params.threshold"],
            datatype=ParameterType.number,
            default_value=0.95,
            required=False,
            minimum=0.0,
            maximum=1.0,
        ),
        Parameter(
            name="suffix_length",
            native_keys=["blocking.method_params.suffix_length"],
            datatype=ParameterType.integer,
            default_value=6,
            required=False,
            minimum=1,
        ),
        Parameter(
            name="max_block_size",
            native_keys=["blocking.method_params.max_block_size"],
            datatype=ParameterType.integer,
            default_value=53,
            required=False,
            minimum=1,
        ),
        Parameter(
            name="block_purging_enabled",
            native_keys=["block_purging.enabled"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        # Nur eine Klasse (BlockPurging) implementiert diese Stufe -> "method"
        # ist konstant, aber als echter Parameter statt Sonderfall im Code.
        Parameter(
            name="block_purging_method",
            native_keys=["block_purging.method"],
            datatype=ParameterType.string,
            default_value="block_purging",
            required=False,
            allowed_values=["block_purging"],
        ),
        Parameter(
            name="smoothing_factor",
            native_keys=["block_purging.method_params.smoothing_factor"],
            datatype=ParameterType.number,
            default_value=1.025,
            required=False,
            minimum=0.0,
        ),
        Parameter(
            name="block_filtering_enabled",
            native_keys=["block_cleaning.enabled"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        # Nur eine Klasse (BlockFiltering) implementiert diese Stufe -> "method"
        # ist konstant, aber als echter Parameter statt Sonderfall im Code.
        Parameter(
            name="block_cleaning_method",
            native_keys=["block_cleaning.method"],
            datatype=ParameterType.string,
            default_value="block_filtering",
            required=False,
            allowed_values=["block_filtering"],
        ),
        Parameter(
            name="block_filtering_ratio",
            native_keys=["block_cleaning.method_params.ratio"],
            datatype=ParameterType.number,
            default_value=0.8,
            required=False,
            minimum=0.0,
            maximum=1.0,
        ),
        Parameter(
            name="comparison_cleaning_enabled",
            native_keys=["comparison_cleaning.enabled"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="comparison_cleaning_method",
            native_keys=["comparison_cleaning.method"],
            datatype=ParameterType.string,
            default_value="weighted_edge_pruning",
            required=False,
            allowed_values=_COMPARISON_CLEANING_METHODS,
        ),
        Parameter(
            name="weighting_scheme",
            native_keys=["comparison_cleaning.method_params.weighting_scheme"],
            datatype=ParameterType.string,
            default_value="EJS",
            required=False,
            allowed_values=_WEIGHTING_SCHEMES,
        ),
        Parameter(
            name="clustering_enabled",
            native_keys=["clustering.enabled"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="clustering_method",
            native_keys=["clustering.method"],
            datatype=ParameterType.string,
            default_value="unique_mapping_clustering",
            required=False,
            allowed_values=_CLUSTERING_METHODS,
        ),
        Parameter(
            name="clustering_similarity_threshold",
            native_keys=["clustering.method_params.similarity_threshold"],
            datatype=ParameterType.number,
            default_value=0.17,
            required=False,
            minimum=0.0,
            maximum=1.0,
        ),
    ]


def _syntactic_matching_parameters() -> list[Parameter]:
    return [
        # EntityMatching-Klasse -> "method" ist fuer diesen Parametersatz
        # konstant (siehe CONFIG_REFERENCE.md, 6a).
        Parameter(
            name="method",
            native_keys=["matching.matchers.char_bigram_tfidf.method"],
            datatype=ParameterType.string,
            default_value="entity_matching",
            required=False,
            allowed_values=["entity_matching"],
        ),
        Parameter(
            name="metric",
            native_keys=["matching.matchers.char_bigram_tfidf.metric"],
            datatype=ParameterType.string,
            default_value="cosine",
            required=False,
            allowed_values=["cosine", "dice", "sorensen_dice", "jaccard"],
        ),
        Parameter(
            name="tokenizer",
            native_keys=["matching.matchers.char_bigram_tfidf.tokenizer"],
            datatype=ParameterType.string,
            default_value="char_tokenizer",
            required=False,
            allowed_values=["char_tokenizer", "word_tokenizer"],
        ),
        Parameter(
            name="vectorizer",
            native_keys=["matching.matchers.char_bigram_tfidf.vectorizer"],
            datatype=ParameterType.string,
            default_value="tfidf",
            required=False,
            allowed_values=["tfidf", "tf", "boolean"],
        ),
        Parameter(
            name="qgram",
            native_keys=["matching.matchers.char_bigram_tfidf.qgram"],
            datatype=ParameterType.integer,
            default_value=2,
            required=False,
            minimum=1,
        ),
        Parameter(
            name="similarity_threshold",
            native_keys=["matching.matchers.char_bigram_tfidf.similarity_threshold"],
            datatype=ParameterType.number,
            default_value=0.8,
            required=False,
            minimum=0.0,
            maximum=1.0,
        ),
        Parameter(
            name="matching_attributes",
            native_keys=["matching.matchers.char_bigram_tfidf.attributes"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
    ]


def _semantic_matching_parameters() -> list[Parameter]:
    return [
        # VectorBasedMatching-Klasse -> "method" ist fuer diesen Parametersatz
        # konstant (siehe CONFIG_REFERENCE.md, 6b).
        Parameter(
            name="method",
            native_keys=["matching.matchers.vector_cosine.method"],
            datatype=ParameterType.string,
            default_value="vector",
            required=False,
            allowed_values=["vector"],
        ),
        Parameter(
            name="embedding_model",
            native_keys=["matching.matchers.vector_cosine.embedding_model"],
            datatype=ParameterType.string,
            default_value="all-MiniLM-L6-v2",
            required=False,
        ),
        Parameter(
            name="metric",
            native_keys=["matching.matchers.vector_cosine.metric"],
            datatype=ParameterType.string,
            default_value="cosine",
            required=False,
            allowed_values=["cosine", "dice", "sorensen_dice", "jaccard"],
        ),
        Parameter(
            name="similarity_threshold",
            native_keys=["matching.matchers.vector_cosine.similarity_threshold"],
            datatype=ParameterType.number,
            default_value=0.8,
            required=False,
            minimum=0.0,
            maximum=1.0,
        ),
        Parameter(
            name="text_column_1",
            native_keys=["matching.matchers.vector_cosine.text_column_1"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="text_column_2",
            native_keys=["matching.matchers.vector_cosine.text_column_2"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
    ]


jedai_syntactic_matching_config = ConfigurationDefinition(
    name="jedai_syntactic_matching",
    description="pyJedAI syntactic (TF-IDF / n-gram) entity matching",
    parameters=_jedai_pipeline_parameters() + _syntactic_matching_parameters(),
)

jedai_semantic_matching_config = ConfigurationDefinition(
    name="jedai_semantic_matching",
    description="pyJedAI semantic (embedding) entity matching",
    parameters=_jedai_pipeline_parameters() + _semantic_matching_parameters(),
)

_CLI_ONLY_FLAGS = {"--sep": "sep", "--attr1": "attr1", "--attr2": "attr2"}

_BLOCKING_METHOD_PARAM_KEYS = {
    "standard_blocking": [],
    "qgrams_blocking": ["qgrams"],
    "extended_qgrams_blocking": ["qgrams", "threshold"],
    "suffix_arrays_blocking": ["suffix_length", "max_block_size"],
    "extended_suffix_arrays_blocking": ["suffix_length", "max_block_size"],
}
_COMPARISON_CLEANING_METHOD_PARAM_KEYS = {
    method: ([] if method == "comparison_propagation" else ["weighting_scheme"])
    for method in _COMPARISON_CLEANING_METHODS
}
_CLUSTERING_METHOD_PARAM_KEYS = {
    method: (["similarity_threshold"] if method == "unique_mapping_clustering" else [])
    for method in _CLUSTERING_METHODS
}


def _set_dotted(d: dict, dotted_key: str, value) -> None:
    parts = dotted_key.split(".")
    node = d
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value


def _filter_method_params(nested: dict, block_key: str, allowed_by_method: dict) -> None:
    block = nested.get(block_key)
    if not block or "method_params" not in block:
        return

    allowed = allowed_by_method.get(block.get("method"))
    if allowed is None:
        return

    block["method_params"] = {
        k: v
        for k, v in block["method_params"].items()
        if k in allowed
    }


def _build_config_from_profile(config: ConfigurationProfile) -> tuple[dict, dict]:
    nested: dict = {}
    cli_extra: dict = {}

    for param in config.definition.parameters:
        try:
            value = config.get_parameter_value(param.name)
        except ValueError:
            value = param.default_value

        if "text_column" in param.name:
            if not value or value == "":
                continue

        for native_key in param.native_keys:
            if native_key in _CLI_ONLY_FLAGS:
                cli_extra[_CLI_ONLY_FLAGS[native_key]] = value
            elif "." in native_key:
                _set_dotted(nested, native_key, value)

    _filter_method_params(nested, "blocking", _BLOCKING_METHOD_PARAM_KEYS)
    _filter_method_params(
        nested,
        "comparison_cleaning",
        _COMPARISON_CLEANING_METHOD_PARAM_KEYS,
    )
    _filter_method_params(
        nested,
        "clustering",
        _CLUSTERING_METHOD_PARAM_KEYS,
    )

    return nested, cli_extra


def _write_config_yaml(config_dict: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config_dict, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
    return path


def _run_jedai_matching(inputs: TaskInput, outputs: TaskOutput, config: ConfigurationProfile):

    print(f"Jedai entity matching with inputs: {inputs}")

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

    sep = cli_extra.get("sep") or "|"
    attr1 = cli_extra.get("attr1") or ""
    attr2 = cli_extra.get("attr2") or ""
    gt = ""

    command = ["bash", "pyjedai.sh",
               str(source_path.path),
               str(target_path.path),
               str(output_path.path),
               str(config_container_path.path)]

    needs_gt_slot = bool(gt) or sep != "|" or bool(attr1) or bool(attr2)
    if needs_gt_slot:
        command.append(gt)

    needs_sep_slot = sep != "|" or bool(attr1) or bool(attr2)
    if needs_sep_slot:
        command.append(sep)

    needs_attr1_slot = bool(attr1) or bool(attr2)
    if needs_attr1_slot:
        command.append(attr1)

    if attr2:
        command.append(attr2)

    # Create Docker client with proper volume bindings
    client = docker_client(
        image="kgt/pyjedai:latest",
        command=command,
        volumes=volumes,
    )

    # Execute the container
    result = client()
    print(f"Jedai entity matching completed: {result}")


def jedai_syntactic_matching(inputs: TaskInput, outputs: TaskOutput, config: ConfigurationProfile):
    _run_jedai_matching(inputs, outputs, config)


def jedai_semantic_matching(inputs: TaskInput, outputs: TaskOutput, config: ConfigurationProfile):
    _run_jedai_matching(inputs, outputs, config)


jedai_syntactic_matching_task = KgTask(
    name="jedai_syntactic_matching",
    description="JedAI syntactic entity matching (TF-IDF / n-gram similarity)",
    input_spec=_JEDAI_ER_INPUT_SPEC,
    output_spec=_JEDAI_ER_OUTPUT_SPEC,
    function=jedai_syntactic_matching,
    config_spec=jedai_syntactic_matching_config,
    category=[BasicTaskCategoryCatalog.entity_matching],
    tools=["pyjedai"],
)

jedai_semantic_matching_task = KgTask(
    name="jedai_semantic_matching",
    description="JedAI semantic entity matching (pretrained LM embeddings)",
    input_spec=_JEDAI_ER_INPUT_SPEC,
    output_spec=_JEDAI_ER_OUTPUT_SPEC,
    function=jedai_semantic_matching,
    config_spec=jedai_semantic_matching_config,
    category=[BasicTaskCategoryCatalog.entity_matching],
    tools=["pyjedai"],
)

Registry.add_task(jedai_syntactic_matching_task.name, jedai_syntactic_matching_task)
Registry.add_task(jedai_semantic_matching_task.name, jedai_semantic_matching_task)