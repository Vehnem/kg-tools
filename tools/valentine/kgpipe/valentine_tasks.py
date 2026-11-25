"""KGpipe task definitions for wrapping Valentine (schema matching).

Valentine matches the columns of a source table against the columns of a
target table. It ships five matchers (Coma, Cupid, DistributionBased,
JaccardDistanceMatcher, SimilarityFlooding); each of them can be enabled
and configured separately. The matching result can be post-processed
(1:1 selection, score filter, top-n cut) and evaluated against an optional
ground-truth mapping.

The wrapper exposes the configuration supported by valentine_example.py.
The source table, the target table and the (optional) ground-truth mapping
are passed as separate task inputs ("source", "target", "mapping");
everything else is configured via the parameters below.
"""

import tempfile
from pathlib import Path

import yaml
from kgpipe.common import Data
from kgpipe.common import KgTask, TaskInput, TaskOutput, BasicDataFormats, BasicTaskCategoryCatalog, Registry
from kgpipe.common.io import get_docker_volume_bindings, remap_data_path_for_container
from kgpipe.common.model.configuration import ConfigurationDefinition, Parameter, ParameterType, ConfigurationProfile
from kgpipe.execution import docker_client

_VALENTINE_INPUT_SPEC = {
    "source": BasicDataFormats.CSV,
    "target": BasicDataFormats.CSV,
    "mapping": BasicDataFormats.ANY,
}

_VALENTINE_OUTPUT_SPEC = {
    "output": BasicDataFormats.CSV,
}

_UNSET = object()

_VALENTINE_FLOAT_KEYS = set()
_VALENTINE_LIST_KEYS = set()
_VALENTINE_NULLABLE_INT_KEYS = set()


def _param(
    name,
    native_key,
    datatype,
    default=_UNSET,
    allowed_values=None,
    kind=None,
):
    """Build a Parameter.

    kind marks how the raw value is converted before it is written to the
    YAML config: "float" (transported as string), "list" (comma separated
    string or YAML list) or "nullable_int" (integer or "none").
    """
    if kind == "float":
        _VALENTINE_FLOAT_KEYS.add(name)
    elif kind == "list":
        _VALENTINE_LIST_KEYS.add(name)
    elif kind == "nullable_int":
        _VALENTINE_NULLABLE_INT_KEYS.add(name)

    kwargs = dict(
        name=name,
        native_keys=[native_key],
        datatype=datatype,
        required=False,
    )
    if default is not _UNSET:
        kwargs["default_value"] = default
    if allowed_values is not None:
        kwargs["allowed_values"] = allowed_values
    return Parameter(**kwargs)


def _valentine_parameters() -> list[Parameter]:
    S, B, I = ParameterType.string, ParameterType.boolean, ParameterType.integer

    return [
        # ==================================================================
        # IO
        # ==================================================================

        _param("nrows", "io.nrows", I),
        _param("encoding", "io.encoding", S, "utf-8"),
        _param("separator", "io.separator", S, ","),
        _param("source_name", "io.source_name", S),
        _param("target_name", "io.target_name", S),
        _param("instance_sample_size", "io.instance_sample_size", S, "1000", kind="nullable_int"),

        # ==================================================================
        # Coma
        # ==================================================================

        _param("coma_enabled", "matchers.Coma.enabled", B, True),
        _param("coma_max_n", "matchers.Coma.params.max_n", I, 0),
        _param("coma_use_instances", "matchers.Coma.params.use_instances", B, False),
        _param("coma_use_schema", "matchers.Coma.params.use_schema", B, True),
        _param("coma_delta", "matchers.Coma.params.delta", S, "0.15", kind="float"),
        _param("coma_threshold", "matchers.Coma.params.threshold", S, "0.0", kind="float"),
        _param("coma_instance_weight", "matchers.Coma.params.instance_weight", S, "1.0", kind="float"),

        # ==================================================================
        # Cupid
        # ==================================================================

        _param("cupid_enabled", "matchers.Cupid.enabled", B, True),
        _param("cupid_leaf_w_struct", "matchers.Cupid.params.leaf_w_struct", S, "0.2", kind="float"),
        _param("cupid_w_struct", "matchers.Cupid.params.w_struct", S, "0.2", kind="float"),
        _param("cupid_th_accept", "matchers.Cupid.params.th_accept", S, "0.7", kind="float"),
        _param("cupid_th_high", "matchers.Cupid.params.th_high", S, "0.6", kind="float"),
        _param("cupid_th_low", "matchers.Cupid.params.th_low", S, "0.35", kind="float"),
        _param("cupid_c_inc", "matchers.Cupid.params.c_inc", S, "1.2", kind="float"),
        _param("cupid_c_dec", "matchers.Cupid.params.c_dec", S, "0.9", kind="float"),
        _param("cupid_th_ns", "matchers.Cupid.params.th_ns", S, "0.7", kind="float"),
        _param("cupid_process_num", "matchers.Cupid.params.process_num", I, 1),

        # ==================================================================
        # DistributionBased
        # ==================================================================

        _param("distribution_based_enabled", "matchers.DistributionBased.enabled", B, True),
        _param("distribution_based_threshold1", "matchers.DistributionBased.params.threshold1", S, "0.15", kind="float"),
        _param("distribution_based_threshold2", "matchers.DistributionBased.params.threshold2", S, "0.15", kind="float"),
        _param("distribution_based_quantiles", "matchers.DistributionBased.params.quantiles", I, 256),
        _param("distribution_based_process_num", "matchers.DistributionBased.params.process_num", I, 1),
        _param("distribution_based_use_bloom_filters", "matchers.DistributionBased.params.use_bloom_filters", B, False),

        # ==================================================================
        # JaccardDistanceMatcher
        # ==================================================================

        _param("jaccard_enabled", "matchers.JaccardDistanceMatcher.enabled", B, True),
        _param("jaccard_threshold_dist", "matchers.JaccardDistanceMatcher.params.threshold_dist", S, "0.8", kind="float"),
        _param(
            "jaccard_distance_fun",
            "matchers.JaccardDistanceMatcher.params.distance_fun",
            S,
            "Levenshtein",
            allowed_values=[
                "Levenshtein",
                "DamerauLevenshtein",
                "Jaro",
                "JaroWinkler",
                "Hamming",
                "Exact",
                "Embedding",
            ],
        ),
        _param("jaccard_process_num", "matchers.JaccardDistanceMatcher.params.process_num", I, 1),
        _param("jaccard_embedding_model", "matchers.JaccardDistanceMatcher.params.embedding_model", S, "all-MiniLM-L6-v2"),
        _param("jaccard_embedding_device", "matchers.JaccardDistanceMatcher.params.embedding_device", S),
        _param("jaccard_embedding_batch_size", "matchers.JaccardDistanceMatcher.params.embedding_batch_size", I),
        _param("jaccard_tversky_alpha", "matchers.JaccardDistanceMatcher.params.tversky_alpha", S, "1.0", kind="float"),
        _param("jaccard_tversky_beta", "matchers.JaccardDistanceMatcher.params.tversky_beta", S, "1.0", kind="float"),

        # ==================================================================
        # SimilarityFlooding
        # ==================================================================

        _param("similarity_flooding_enabled", "matchers.SimilarityFlooding.enabled", B, True),
        _param(
            "similarity_flooding_coeff_policy",
            "matchers.SimilarityFlooding.params.coeff_policy",
            S,
            "INVERSE_AVERAGE",
            allowed_values=["INVERSE_AVERAGE", "INVERSE_PRODUCT"],
        ),
        _param(
            "similarity_flooding_formula",
            "matchers.SimilarityFlooding.params.formula",
            S,
            "FORMULA_C",
            allowed_values=["BASIC", "FORMULA_A", "FORMULA_B", "FORMULA_C"],
        ),
        _param(
            "similarity_flooding_string_matcher",
            "matchers.SimilarityFlooding.params.string_matcher",
            S,
            "PREFIX_SUFFIX",
            allowed_values=["PREFIX_SUFFIX", "PREFIX_SUFFIX_TFIDF", "LEVENSHTEIN"],
        ),
        _param(
            "similarity_flooding_tfidf_corpus",
            "matchers.SimilarityFlooding.params.tfidf_corpus",
            S,
            kind="list",
        ),

        # ==================================================================
        # Selection
        # ==================================================================

        _param(
            "selection_method",
            "selection.method",
            S,
            "one_to_one_greedy",
            allowed_values=[
                "none",
                "one_to_one_greedy",
                "one_to_one_hungarian",
                "one_to_one_mutual_top",
            ],
        ),
        _param("selection_threshold", "selection.threshold", S, kind="float"),
        _param("selection_mutual_top_n", "selection.mutual_top_n", I),
        _param("selection_min_score", "selection.min_score", S, kind="float"),
        _param("selection_top_percent", "selection.top_percent", I),
        _param("selection_top_n", "selection.top_n", I),
        _param("selection_top_n_per_source", "selection.top_n_per_source", I),

        # ==================================================================
        # Output
        # ==================================================================

        _param("include_details", "output.include_details", B, False),
        _param("evaluation_csv", "output.evaluation_csv", S, "evaluation.csv"),

        # ==================================================================
        # Evaluation
        # ==================================================================

        _param("evaluation_enabled", "evaluation.enabled", B, True),
        _param("valentine_metrics_enabled", "evaluation.valentine_metrics.enabled", B, False),
        _param(
            "valentine_metrics",
            "evaluation.valentine_metrics.metrics",
            S,
            "Precision,Recall,F1Score,PrecisionTopNPercent,RecallAtSizeofGroundTruth,MeanReciprocalRank",
            kind="list",
        ),
        _param("valentine_metrics_one_to_one", "evaluation.valentine_metrics.one_to_one", B, True),
        _param(
            "valentine_metrics_one_to_one_method",
            "evaluation.valentine_metrics.one_to_one_method",
            S,
            "hungarian",
            allowed_values=["greedy", "hungarian", "mutual_top"],
        ),
        _param("valentine_metrics_top_n_percent", "evaluation.valentine_metrics.top_n_percent", I, 10),
    ]


valentine_schema_matching_config = ConfigurationDefinition(
    name="valentine_schema_matching",
    description="Schema matching with Valentine",
    parameters=_valentine_parameters(),
)


def _parse_list(value):
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return None
        parsed = yaml.safe_load(value)
        if isinstance(parsed, list):
            return parsed
        return [c.strip() for c in value.split(",") if c.strip()]
    return list(value)


def _coerce(param: Parameter, value):
    if value is None:
        return None
    if param.name in _VALENTINE_FLOAT_KEYS:
        if isinstance(value, str) and not value.strip():
            return None
        return float(value)
    if param.name in _VALENTINE_LIST_KEYS:
        return _parse_list(value)
    if param.name in _VALENTINE_NULLABLE_INT_KEYS:
        if isinstance(value, str) and value.strip().lower() in ("", "none", "null"):
            return None
        return int(value)
    if param.datatype == ParameterType.string and isinstance(value, str) and value == "":
        return None
    return value


def _build_valentine_config(config: ConfigurationProfile) -> str:
    sections: dict = {}
    for param in _valentine_parameters():
        try:
            value = config.get_parameter_value(param.name)
        except (ValueError, KeyError):
            value = param.default_value
        value = _coerce(param, value)

        node = sections
        *path, leaf = param.native_keys[0].split(".")
        for part in path:
            node = node.setdefault(part, {})
        node[leaf] = value

    return yaml.safe_dump(sections, sort_keys=False, default_flow_style=False)


def valentine_schema_matching(
    inputs: TaskInput,
    outputs: TaskOutput,
    config: ConfigurationProfile,
):
    Path(outputs["output"].path).mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="valentine_") as tmp:
        config_host_path = Path(tmp) / "config.yaml"
        config_host_path.write_text(_build_valentine_config(config), encoding="utf-8")

        config_data = Data(str(config_host_path), BasicDataFormats.ANY)

        mapping = inputs["mapping"] if "mapping" in inputs else None

        all_data = list(inputs.values()) + list(outputs.values()) + [config_data]
        volumes, host_to_container = get_docker_volume_bindings(all_data)

        def remap(data):
            return str(remap_data_path_for_container(data, host_to_container).path)

        command = [
            "bash", "valentine.sh",
            remap(inputs["source"]),
            remap(inputs["target"]),
            remap(outputs["output"]),
            remap(config_data),
        ]
        if mapping is not None:
            command.append(remap(mapping))

        client = docker_client(
            image="kgt/valentine:latest",
            command=command,
            volumes=volumes,
        )

        result = client()


valentine_schema_matching_task = KgTask(
    name="valentine_schema_matching",
    description="Schema matching with Valentine",
    input_spec=_VALENTINE_INPUT_SPEC,
    output_spec=_VALENTINE_OUTPUT_SPEC,
    function=valentine_schema_matching,
    config_spec=valentine_schema_matching_config,
    category=[
        getattr(
            BasicTaskCategoryCatalog,
            "schema_matching",
            BasicTaskCategoryCatalog.entity_matching,
        )
    ],
    tools=["valentine"],
)


Registry.add_task(
    valentine_schema_matching_task.name,
    valentine_schema_matching_task,
)