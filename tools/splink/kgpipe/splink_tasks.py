"""KGpipe task definitions for wrapping Splink entity matching.

Splink is one Docker pipeline (two CSVs in, matching CSV out). Backend,
linking mode, blocking, comparisons, training, output thresholds and
clustering are ConfigurationDefinition parameters because they configure
the same Splink execution contract.

Unlike pyJedAI, Splink does not need separate KGpipe tasks for syntactic
and semantic matching: the comparison definitions determine how records
are compared. Therefore this module exposes a single task:

- splink_entity_matching: Splink entity resolution / record linkage
"""

from pathlib import Path

import yaml

from kgpipe.common import (
    KgTask,
    TaskInput,
    TaskOutput,
    BasicDataFormats,
    BasicTaskCategoryCatalog,
    Registry,
    Data,
)
from kgpipe.common.model.configuration import (
    ConfigurationDefinition,
    Parameter,
    ParameterType,
    ConfigurationProfile,
)

from kgpipe.common.io import (
    get_docker_volume_bindings,
    remap_data_path_for_container,
)
from kgpipe.execution import docker_client


_SPLINK_ER_INPUT_SPEC = {
    "input": BasicDataFormats.CSV,
    "input2": BasicDataFormats.CSV,
}

_SPLINK_ER_OUTPUT_SPEC = {
    "output": BasicDataFormats.JSON,
}


_LINK_TYPES = [
    "dedupe_only",
    "link_only",
    "link_and_dedupe",
]

_BACKENDS = [
    "duckdb",
    "sqlite",
    "spark",
    "postgres",
]

_COMPARISON_TYPES = [
    "exact_match",
    "levenshtein",
    "damerau_levenshtein",
    "jaro",
    "jaro_winkler",
    "jaccard",
    "cosine_similarity",
    "distance_function",
    "pairwise_string_distance",
    "distance_in_km",
    "array_intersect",
    "name_comparison",
    "forename_surname",
    "date_of_birth",
    "absolute_time_difference",
    "absolute_date_difference",
    "postcode",
    "email",
]

_DISTANCE_FUNCTIONS = [
    "levenshtein",
    "damerau_levenshtein",
    "jaro",
    "jaro_winkler",
    "jaccard",
    "cosine_similarity",
]

_DATETIME_METRICS = [
    "day",
    "month",
    "year",
]


def _splink_parameters() -> list[Parameter]:
    """All supported Splink config.yaml parameters."""

    return [
        # ------------------------------------------------------------------
        # Backend
        # ------------------------------------------------------------------
        Parameter(
            name="backend",
            native_keys=["backend"],
            datatype=ParameterType.string,
            default_value="duckdb",
            required=False,
            allowed_values=_BACKENDS,
        ),
        Parameter(
            name="postgres_connection_string",
            native_keys=["postgres_connection_string"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="postgres_schema",
            native_keys=["postgres_schema"],
            datatype=ParameterType.string,
            default_value="splink",
            required=False,
        ),
        Parameter(
            name="postgres_other_schemas_to_search",
            native_keys=["postgres_other_schemas_to_search"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),

        # ------------------------------------------------------------------
        # Core SettingsCreator settings
        # ------------------------------------------------------------------
        Parameter(
            name="link_type",
            native_keys=["link_type"],
            datatype=ParameterType.string,
            default_value="link_only",
            required=False,
            allowed_values=_LINK_TYPES,
        ),
        Parameter(
            name="unique_id_column_name",
            native_keys=["unique_id_column_name"],
            datatype=ParameterType.string,
            default_value="id",
            required=False,
        ),
        Parameter(
            name="source_dataset_column_name",
            native_keys=["source_dataset_column_name"],
            datatype=ParameterType.string,
            default_value="source_dataset",
            required=False,
        ),
        Parameter(
            name="probability_two_random_records_match",
            native_keys=["probability_two_random_records_match"],
            datatype=ParameterType.number,
            default_value=0.0001,
            required=False,
            minimum=0.0,
            maximum=1.0,
        ),
        Parameter(
            name="em_convergence",
            native_keys=["em_convergence"],
            datatype=ParameterType.number,
            default_value=0.0001,
            required=False,
            minimum=0.0,
        ),
        Parameter(
            name="max_iterations",
            native_keys=["max_iterations"],
            datatype=ParameterType.integer,
            default_value=25,
            required=False,
            minimum=1,
        ),
        Parameter(
            name="retain_matching_columns",
            native_keys=["retain_matching_columns"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),
        Parameter(
            name="retain_intermediate_calculation_columns",
            native_keys=["retain_intermediate_calculation_columns"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="additional_columns_to_retain",
            native_keys=["additional_columns_to_retain"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="bayes_factor_column_prefix",
            native_keys=["bayes_factor_column_prefix"],
            datatype=ParameterType.string,
            default_value="bf_",
            required=False,
        ),
        Parameter(
            name="term_frequency_adjustment_column_prefix",
            native_keys=["term_frequency_adjustment_column_prefix"],
            datatype=ParameterType.string,
            default_value="tf_",
            required=False,
        ),
        Parameter(
            name="comparison_vector_value_column_prefix",
            native_keys=["comparison_vector_value_column_prefix"],
            datatype=ParameterType.string,
            default_value="gamma_",
            required=False,
        ),

        # ------------------------------------------------------------------
        # Blocking
        # ------------------------------------------------------------------
        Parameter(
            name="blocking_rules_to_generate_predictions",
            native_keys=["blocking_rules_to_generate_predictions"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),

        # ------------------------------------------------------------------
        # Comparisons
        #
        # The wrapper supports a single configurable comparison as a
        # parameterized entry. Additional comparisons can be supplied as
        # YAML via `raw_comparisons`.
        # ------------------------------------------------------------------
        Parameter(
            name="comparison_output_column_name",
            native_keys=["comparisons.0.output_column_name"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="comparison_input_columns",
            native_keys=["comparisons.0.input_columns"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="comparison_type",
            native_keys=["comparisons.0.comparison_type"],
            datatype=ParameterType.string,
            default_value="jaro_winkler",
            required=False,
            allowed_values=_COMPARISON_TYPES,
        ),

        # ------------------------------------------------------------------
        # Common comparison parameters
        # ------------------------------------------------------------------
        Parameter(
            name="comparison_thresholds",
            native_keys=["comparisons.0.params.score_threshold_or_thresholds"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="distance_thresholds",
            native_keys=[
                "comparisons.0.params.distance_threshold_or_thresholds"
            ],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="distance_function_name",
            native_keys=["comparisons.0.params.distance_function_name"],
            datatype=ParameterType.string,
            default_value="levenshtein",
            required=False,
            allowed_values=_DISTANCE_FUNCTIONS,
        ),
        Parameter(
            name="higher_is_more_similar",
            native_keys=["comparisons.0.params.higher_is_more_similar"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        # ------------------------------------------------------------------
        # Geographic / array / date comparison parameters
        # ------------------------------------------------------------------
        Parameter(
            name="km_thresholds",
            native_keys=["comparisons.0.params.km_threshold_or_thresholds"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="size_thresholds",
            native_keys=["comparisons.0.params.size_threshold_or_thresholds"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="jaro_winkler_thresholds",
            native_keys=["comparisons.0.params.jaro_winkler_thresholds"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="datetime_format",
            native_keys=["comparisons.0.params.datetime_format"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="datetime_thresholds",
            native_keys=["comparisons.0.params.datetime_thresholds"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="datetime_metrics",
            native_keys=["comparisons.0.params.datetime_metrics"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="input_is_string",
            native_keys=["comparisons.0.params.input_is_string"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="dmeta_col_name",
            native_keys=["comparisons.0.params.dmeta_col_name"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="lat_col",
            native_keys=["comparisons.0.params.lat_col"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="long_col",
            native_keys=["comparisons.0.params.long_col"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),

        # ------------------------------------------------------------------
        # Comparison configure() parameters
        # ------------------------------------------------------------------
        Parameter(
            name="term_frequency_adjustments",
            native_keys=[
                "comparisons.0.term_frequency_adjustments"
            ],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="m_probabilities",
            native_keys=["comparisons.0.m_probabilities"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="u_probabilities",
            native_keys=["comparisons.0.u_probabilities"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),

        # ------------------------------------------------------------------
        # Additional comparisons
        #
        # These are deliberately exposed as raw YAML because Splink allows
        # arbitrary comparison dictionaries, including CustomComparison.
        # ------------------------------------------------------------------
        Parameter(
            name="raw_comparisons",
            native_keys=["comparisons"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),

        # ------------------------------------------------------------------
        # Term frequency adjustments
        # ------------------------------------------------------------------
        Parameter(
            name="term_frequency_columns",
            native_keys=["term_frequency_adjustments.columns"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),

        # ------------------------------------------------------------------
        # Training: probability of random match
        # ------------------------------------------------------------------
        Parameter(
            name="estimate_probability_two_random_records_match_enabled",
            native_keys=[
                "training.estimate_probability_two_random_records_match.enabled"
            ],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="deterministic_matching_rules",
            native_keys=[
                "training.estimate_probability_two_random_records_match.deterministic_matching_rules"
            ],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="probability_match_recall",
            native_keys=[
                "training.estimate_probability_two_random_records_match.recall"
            ],
            datatype=ParameterType.number,
            default_value=0.7,
            required=False,
            minimum=0.0,
            maximum=1.0,
        ),
        Parameter(
            name="probability_match_max_rows_limit",
            native_keys=[
                "training.estimate_probability_two_random_records_match.max_rows_limit"
            ],
            datatype=ParameterType.integer,
            default_value=0,
            required=False,
            minimum=0,
        ),

        # ------------------------------------------------------------------
        # Training: random sampling
        # ------------------------------------------------------------------
        Parameter(
            name="estimate_u_using_random_sampling_enabled",
            native_keys=[
                "training.estimate_u_using_random_sampling.enabled"
            ],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="estimate_u_max_pairs",
            native_keys=[
                "training.estimate_u_using_random_sampling.max_pairs"
            ],
            datatype=ParameterType.integer,
            default_value=1000000,
            required=False,
            minimum=1,
        ),
        Parameter(
            name="estimate_u_seed",
            native_keys=[
                "training.estimate_u_using_random_sampling.seed"
            ],
            datatype=ParameterType.integer,
            default_value=0,
            required=False,
            minimum=0,
        ),

        # ------------------------------------------------------------------
        # Training: EM
        # ------------------------------------------------------------------
        Parameter(
            name="estimate_parameters_using_em_enabled",
            native_keys=[
                "training.estimate_parameters_using_expectation_maximisation.enabled"
            ],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="em_blocking_rule",
            native_keys=[
                "training.estimate_parameters_using_expectation_maximisation.blocking_rule"
            ],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="estimate_without_term_frequencies",
            native_keys=[
                "training.estimate_parameters_using_expectation_maximisation.estimate_without_term_frequencies"
            ],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="fix_probability_two_random_records_match",
            native_keys=[
                "training.estimate_parameters_using_expectation_maximisation.fix_probability_two_random_records_match"
            ],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="fix_m_probabilities",
            native_keys=[
                "training.estimate_parameters_using_expectation_maximisation.fix_m_probabilities"
            ],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="fix_u_probabilities",
            native_keys=[
                "training.estimate_parameters_using_expectation_maximisation.fix_u_probabilities"
            ],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="populate_probability_two_random_records_match_from_trained_values",
            native_keys=[
                "training.estimate_parameters_using_expectation_maximisation.populate_probability_two_random_records_match_from_trained_values"
            ],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        # ------------------------------------------------------------------
        # Training: labels
        # ------------------------------------------------------------------
        Parameter(
            name="estimate_m_from_label_column",
            native_keys=["training.estimate_m_from_label_column"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),

        # ------------------------------------------------------------------
        # Output
        # ------------------------------------------------------------------
        Parameter(
            name="threshold_match_probability",
            native_keys=["output.threshold_match_probability"],
            datatype=ParameterType.number,
            default_value=0.0,
            required=False,
            minimum=0.0,
            maximum=1.0,
        ),
        Parameter(
            name="threshold_match_weight",
            native_keys=["output.threshold_match_weight"],
            datatype=ParameterType.number,
            default_value=0.0,
            required=False,
        ),
        Parameter(
            name="clustering_enabled",
            native_keys=["output.clustering.enabled"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="clustering_threshold_match_probability",
            native_keys=[
                "output.clustering.threshold_match_probability"
            ],
            datatype=ParameterType.number,
            default_value=0.0,
            required=False,
            minimum=0.0,
            maximum=1.0,
        ),
    ]


splink_entity_matching_config = ConfigurationDefinition(
    name="splink_entity_matching",
    description="Splink entity resolution and record linkage",
    parameters=_splink_parameters(),
)


_LIST_PARAMETERS = {
    "additional_columns_to_retain",
    "blocking_rules_to_generate_predictions",
    "comparison_input_columns",
    "comparison_thresholds",
    "distance_thresholds",
    "km_thresholds",
    "size_thresholds",
    "jaro_winkler_thresholds",
    "datetime_thresholds",
    "datetime_metrics",
    "m_probabilities",
    "u_probabilities",
    "term_frequency_columns",
    "deterministic_matching_rules",
}


def _parse_list_value(value):
    """Parse a KGpipe string parameter into a YAML list.

    Accepts either a JSON/YAML list or a simple comma-separated string.
    """
    if value is None or value == "":
        return None

    if isinstance(value, list):
        return value

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return None

        try:
            parsed = yaml.safe_load(value)
            if isinstance(parsed, list):
                return parsed
        except yaml.YAMLError:
            pass

        return [
            item.strip()
            for item in value.split(",")
            if item.strip()
        ]

    return value


def _set_dotted(d: dict, dotted_key: str, value) -> None:
    """Set a value at a dotted path, creating dicts/lists as needed.

    A purely numeric path segment (e.g. "0") addresses a *list index* in
    the parent container instead of a dict key. This lets native_keys
    like "comparisons.0.params.score_threshold_or_thresholds" build
        {"comparisons": [{"params": {...}}]}
    instead of
        {"comparisons": {"0": {"params": {...}}}}.
    """
    parts = dotted_key.split(".")
    container = d

    for i, part in enumerate(parts[:-1]):
        next_is_index = parts[i + 1].isdigit()

        if part.isdigit():
            idx = int(part)
            while len(container) <= idx:
                container.append([] if next_is_index else {})
            container = container[idx]
        else:
            if part not in container or not isinstance(
                container[part], list if next_is_index else dict
            ):
                container[part] = [] if next_is_index else {}
            container = container[part]

    last = parts[-1]
    if last.isdigit():
        idx = int(last)
        while len(container) <= idx:
            container.append(None)
        container[idx] = value
    else:
        container[last] = value

def _parse_raw_comparisons(value):
    """Parse the raw_comparisons YAML string into a list of comparison dicts."""
    if value is None or value == "":
        return []

    if isinstance(value, list):
        return value

    try:
        parsed = yaml.safe_load(value)
    except yaml.YAMLError:
        return []

    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        return [parsed]
    return []

def _get_parameter_value(config: ConfigurationProfile, param: Parameter):
    try:
        return config.get_parameter_value(param.name)
    except ValueError:
        return param.default_value


def _build_config_from_profile(config: ConfigurationProfile) -> dict:
    nested: dict = {}
    raw_comparisons_value = None

    for param in config.definition.parameters:
        value = _get_parameter_value(config, param)

        if value == "" or value is None:
            continue

        # Handled separately below — must not clobber comparisons[0].
        if param.name == "raw_comparisons":
            raw_comparisons_value = value
            continue

        if param.name in _LIST_PARAMETERS:
            value = _parse_list_value(value)
            if value is None:
                continue

        if param.name in {
            "threshold_match_probability",
            "threshold_match_weight",
        } and value == 0.0:
            continue

        _set_dotted(nested, param.native_keys[0], value)

    extra_comparisons = _parse_raw_comparisons(raw_comparisons_value)
    if extra_comparisons:
        nested.setdefault("comparisons", [])
        nested["comparisons"].extend(extra_comparisons)
    comparisons = nested.get("comparisons")

    if comparisons and isinstance(comparisons, list):
        cleaned_comparisons = []

        for comparison in comparisons:
            if not isinstance(comparison, dict):
                continue

            # `raw` entries are passed through unchanged — Splink handles
            # the full comparison dict itself.
            if "raw" in comparison:
                cleaned_comparisons.append(comparison)
                continue

            output_column_name = comparison.get("output_column_name")
            if not output_column_name:
                continue

            params = comparison.get("params", {})
            if not isinstance(params, dict):
                params = {}

            comparison_type = comparison.get("comparison_type")

            # Only retain parameters that are relevant to the selected
            # comparison type.
            if comparison_type not in {
                "levenshtein",
                "damerau_levenshtein",
                "jaro",
                "jaro_winkler",
                "jaccard",
                "cosine_similarity",
            }:
                params.pop("score_threshold_or_thresholds", None)
                params.pop("distance_threshold_or_thresholds", None)

            if comparison_type not in {
                "distance_function",
            }:
                params.pop("distance_function_name", None)
                params.pop("higher_is_more_similar", None)

            if comparison_type not in {
                "distance_in_km",
            }:
                params.pop("km_threshold_or_thresholds", None)
                params.pop("lat_col", None)
                params.pop("long_col", None)

            if comparison_type not in {
                "array_intersect",
            }:
                params.pop("size_threshold_or_thresholds", None)

            if comparison_type not in {
                "name_comparison",
                "forename_surname",
            }:
                params.pop("jaro_winkler_thresholds", None)
                params.pop("dmeta_col_name", None)

            if comparison_type not in {
                "date_of_birth",
                "absolute_time_difference",
                "absolute_date_difference",
            }:
                params.pop("datetime_format", None)
                params.pop("datetime_thresholds", None)
                params.pop("datetime_metrics", None)
                params.pop("input_is_string", None)

            if params:
                comparison["params"] = params
            else:
                comparison.pop("params", None)

            cleaned_comparisons.append(comparison)

        nested["comparisons"] = cleaned_comparisons

    # ------------------------------------------------------------------
    # Remove empty optional PostgreSQL settings unless postgres is used.
    # ------------------------------------------------------------------
    if nested.get("backend") != "postgres":
        nested.pop("postgres_connection_string", None)
        nested.pop("postgres_schema", None)
        nested.pop("postgres_other_schemas_to_search", None)

    # ------------------------------------------------------------------
    # Remove disabled training sections.
    # ------------------------------------------------------------------
    training = nested.get("training")

    if training:
        for key in (
                "estimate_probability_two_random_records_match",
                "estimate_u_using_random_sampling",
                "estimate_parameters_using_expectation_maximisation",
        ):
            block = training.get(key)
            if not block:
                continue
            if not block.get("enabled"):
                training.pop(key, None)
            else:
                block.pop("enabled", None)
                if key == "estimate_parameters_using_expectation_maximisation":
                    training[key] = [block]

        if not training:
            nested.pop("training", None)

    # ------------------------------------------------------------------
    # Remove disabled clustering.
    # ------------------------------------------------------------------
    output = nested.get("output")

    if output:
        clustering = output.get("clustering")

        if clustering and not clustering.get("enabled"):
            output.pop("clustering", None)

        if not output:
            nested.pop("output", None)

    final: dict = {"splink": nested}
    return final


def _write_config_yaml(config_dict: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            config_dict,
            f,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )

    return path


def _run_splink_matching(
    inputs: TaskInput,
    outputs: TaskOutput,
    config: ConfigurationProfile,
):
    print(f"Splink entity matching with inputs: {inputs}")

    config_dict = _build_config_from_profile(config)

    config_host_path = (
        outputs["output"].path.parent / f"{config.name}.yaml"
    )

    config_data = Data(
        str(config_host_path),
        BasicDataFormats.ANY,
    )

    _write_config_yaml(config_dict, config_host_path)

    all_data = (
        list(inputs.values())
        + list(outputs.values())
        + [config_data]
    )

    volumes, host_to_container = get_docker_volume_bindings(all_data)

    input_path = remap_data_path_for_container(
        inputs["input"],
        host_to_container,
    )

    output_path = remap_data_path_for_container(
        outputs["output"],
        host_to_container,
    )

    config_container_path = remap_data_path_for_container(
        config_data,
        host_to_container,
    )

    outputs["output"].path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "bash",
        "splink.sh",
        str(input_path.path),
    ]

    if "input2" in inputs:
        input2_path = remap_data_path_for_container(
            inputs["input2"],
            host_to_container,
        )

        command.extend(
            [
                str(input2_path.path),
            ]
        )

    command.extend(
        [
            str(output_path.path),
            str(config_container_path.path),
        ]
    )

    threshold = config.get_parameter_value(
        "threshold_match_probability"
    )

    if threshold not in (None, "", 0.0):
        command.extend(
            [
                str(threshold),
            ]
        )

    client = docker_client(
        image="kgt/splink:latest",
        command=command,
        volumes=volumes,
    )

    result = client()

    print(f"Splink entity matching completed: {result}")


def splink_entity_matching(
    inputs: TaskInput,
    outputs: TaskOutput,
    config: ConfigurationProfile,
):
    _run_splink_matching(inputs, outputs, config)


splink_entity_matching_task = KgTask(
    name="splink_entity_matching",
    description="Splink entity resolution and record linkage",
    input_spec=_SPLINK_ER_INPUT_SPEC,
    output_spec=_SPLINK_ER_OUTPUT_SPEC,
    function=splink_entity_matching,
    config_spec=splink_entity_matching_config,
    category=[BasicTaskCategoryCatalog.entity_matching],
    tools=["splink"],
)


Registry.add_task(
    splink_entity_matching_task.name,
    splink_entity_matching_task,
)
