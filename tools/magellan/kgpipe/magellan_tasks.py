"""KGpipe task definitions for wrapping Magellan (py_entitymatching).

Magellan, exposed through the py_entitymatching package, provides a
traditional entity-matching pipeline consisting of:

    tables
      -> blocking
      -> candidate set
      -> labeling
      -> feature generation
      -> matching
      -> evaluation

Multiple blockers can be combined via union or chain. Matching supports
classical machine-learning matchers as well as rule-based matching.

The wrapper exposes the configuration supported by run_magellan.py.
Interactive candidate labeling via label_candidates.py is intentionally
not part of this task because it requires a GUI and is not suitable for
the headless KGpipe execution model.
"""

import tempfile
from pathlib import Path

import yaml
from kgpipe.common import Data
from kgpipe.common import KgTask, TaskInput, TaskOutput, BasicDataFormats, BasicTaskCategoryCatalog, Registry
from kgpipe.common.io import get_docker_volume_bindings, remap_data_path_for_container
from kgpipe.common.model.configuration import ConfigurationDefinition, Parameter, ParameterType, ConfigurationProfile
from kgpipe.execution import docker_client

_MAGELLAN_INPUT_SPEC = {
    "input": BasicDataFormats.CSV,
}

_MAGELLAN_OUTPUT_SPEC = {
    "output": BasicDataFormats.CSV,
}


def _magellan_parameters() -> list[Parameter]:
    return [
        # ==================================================================
        # IO
        # ==================================================================

        Parameter(
            name="ltable",
            native_keys=["io.ltable"],
            datatype=ParameterType.string,
            required=True,
        ),

        Parameter(
            name="rtable",
            native_keys=["io.rtable"],
            datatype=ParameterType.string,
            required=True,
        ),

        Parameter(
            name="l_key",
            native_keys=["io.l_key"],
            datatype=ParameterType.string,
            required=True,
        ),

        Parameter(
            name="r_key",
            native_keys=["io.r_key"],
            datatype=ParameterType.string,
            required=True,
        ),

        Parameter(
            name="labeled_data",
            native_keys=["io.labeled_data"],
            datatype=ParameterType.string,
            default_value=None,
            required=False,
        ),

        # ==================================================================
        # Blocking
        # ==================================================================

        Parameter(
            name="blocking_combine",
            native_keys=["blocking.combine"],
            datatype=ParameterType.string,
            default_value="union",
            required=False,
            allowed_values=["union", "chain"],
        ),

        Parameter(
            name="blockers",
            native_keys=["blocking.blockers"],
            datatype=ParameterType.string,
            default_value=None,
            required=True,
        ),

        # ==================================================================
        # Candidate set
        # ==================================================================

        Parameter(
            name="drop_duplicates",
            native_keys=["candidate_set.drop_duplicates"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        # ==================================================================
        # Debug blocker
        # ==================================================================

        Parameter(
            name="debug_blocker_enabled",
            native_keys=["debug_blocker.enabled"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        Parameter(
            name="debug_blocker_output_size",
            native_keys=["debug_blocker.output_size"],
            datatype=ParameterType.integer,
            default_value=200,
            required=False,
        ),

        Parameter(
            name="debug_blocker_n_jobs",
            native_keys=["debug_blocker.n_jobs"],
            datatype=ParameterType.integer,
            default_value=1,
            required=False,
        ),

        Parameter(
            name="debug_blocker_output_path",
            native_keys=["debug_blocker.output_path"],
            datatype=ParameterType.string,
            default_value="debug_blocker_output.csv",
            required=False,
        ),

        # ==================================================================
        # Labeling
        # ==================================================================

        Parameter(
            name="labeling_strategy",
            native_keys=["labeling.strategy"],
            datatype=ParameterType.string,
            default_value="none",
            required=False,
            allowed_values=["from_file", "none"],
        ),

        Parameter(
            name="label_column",
            native_keys=["labeling.label_column"],
            datatype=ParameterType.string,
            default_value="label",
            required=False,
        ),

        # ==================================================================
        # Feature generation
        # ==================================================================

        Parameter(
            name="validate_inferred_attr_types",
            native_keys=[
                "feature_generation.validate_inferred_attr_types"
            ],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        Parameter(
            name="select_features",
            native_keys=["feature_generation.select_features"],
            datatype=ParameterType.string,
            default_value=None,
            required=False,
        ),

        Parameter(
            name="attrs_before",
            native_keys=["feature_generation.attrs_before"],
            datatype=ParameterType.string,
            default_value=None,
            required=False,
        ),

        Parameter(
            name="attrs_after",
            native_keys=["feature_generation.attrs_after"],
            datatype=ParameterType.string,
            default_value=None,
            required=False,
        ),

        Parameter(
            name="blackbox_features",
            native_keys=["feature_generation.blackbox_features"],
            datatype=ParameterType.string,
            default_value=None,
            required=False,
        ),

        Parameter(
            name="feature_show_progress",
            native_keys=["feature_generation.show_progress"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        Parameter(
            name="feature_n_jobs",
            native_keys=["feature_generation.n_jobs"],
            datatype=ParameterType.integer,
            default_value=1,
            required=False,
        ),

        # ==================================================================
        # Matching
        # ==================================================================

        Parameter(
            name="matchers",
            native_keys=["matching.matchers"],
            datatype=ParameterType.string,
            default_value=None,
            required=True,
        ),

        # ==================================================================
        # Matcher selection
        # ==================================================================

        Parameter(
            name="matcher_selection_enabled",
            native_keys=["matcher_selection.enabled"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        Parameter(
            name="matcher_selection_candidates",
            native_keys=["matcher_selection.candidates"],
            datatype=ParameterType.string,
            default_value=None,
            required=False,
        ),

        Parameter(
            name="matcher_selection_metric",
            native_keys=[
                "matcher_selection.metric_to_select_matcher"
            ],
            datatype=ParameterType.string,
            default_value="precision",
            required=False,
            allowed_values=["precision", "recall", "f1"],
        ),

        Parameter(
            name="matcher_selection_metrics",
            native_keys=["matcher_selection.metrics_to_display"],
            datatype=ParameterType.string,
            default_value="precision,recall,f1",
            required=False,
        ),

        Parameter(
            name="matcher_selection_k",
            native_keys=["matcher_selection.k"],
            datatype=ParameterType.integer,
            default_value=5,
            required=False,
        ),

        Parameter(
            name="matcher_selection_random_state",
            native_keys=["matcher_selection.random_state"],
            datatype=ParameterType.integer,
            default_value=None,
            required=False,
        ),

        Parameter(
            name="matcher_selection_output_csv",
            native_keys=["matcher_selection.output_csv"],
            datatype=ParameterType.string,
            default_value="matcher_selection.csv",
            required=False,
        ),

        # ==================================================================
        # Evaluation
        # ==================================================================

        Parameter(
            name="evaluation_output_csv",
            native_keys=["evaluation.output_csv"],
            datatype=ParameterType.string,
            default_value="evaluation.csv",
            required=False,
        ),
    ]


magellan_entity_matching_config = ConfigurationDefinition(
    name="magellan_entity_matching",
    description="Entity matching with Magellan (py_entitymatching)",
    parameters=_magellan_parameters(),
)


_MAGELLAN_STRUCT_KEYS = {"blockers", "matchers", "blackbox_features"}
_MAGELLAN_LIST_KEYS = {
    "select_features",
    "attrs_before",
    "attrs_after",
    "matcher_selection_candidates",
    "matcher_selection_metrics",
}


def _parse_struct(value):
    if isinstance(value, str):
        return yaml.safe_load(value) if value.strip() else None
    return value


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


def _build_magellan_config(config: ConfigurationProfile) -> str:
    sections: dict[str, dict] = {}
    for param in _magellan_parameters():
        value = config.get_parameter_value(param.name)
        native_key = param.native_keys[0]

        if param.name in _MAGELLAN_STRUCT_KEYS:
            value = _parse_struct(value)
            if param.name == "blackbox_features" and value is None:
                value = []
        elif param.name in _MAGELLAN_LIST_KEYS:
            value = _parse_list(value)

        section, key = native_key.split(".", 1)
        sections.setdefault(section, {})[key] = value

    blockers = sections["blocking"]["blockers"]
    matchers = sections["matching"]["matchers"]
    if not isinstance(blockers, list) or not blockers:
        raise ValueError("'blockers' must be a non-empty list of blocker definitions")
    if not isinstance(matchers, dict) or not matchers:
        raise ValueError("'matchers' must be a non-empty mapping of matcher definitions")

    selection = sections["matcher_selection"]
    if selection["enabled"]:
        unknown = set(selection["candidates"] or []) - set(matchers)
        if unknown:
            raise ValueError(f"matcher_selection.candidates not in matchers: {sorted(unknown)}")

    return yaml.safe_dump(sections, sort_keys=False, default_flow_style=False)


def magellan_entity_matching(
    inputs: TaskInput,
    outputs: TaskOutput,
    config: ConfigurationProfile,
):
    Path(outputs["output"].path).mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="magellan_") as tmp:
        config_host_path = Path(tmp) / "config.yaml"
        config_host_path.write_text(_build_magellan_config(config), encoding="utf-8")

        config_data = Data(str(config_host_path), BasicDataFormats.ANY)

        all_data = list(inputs.values()) + list(outputs.values()) + [config_data]
        volumes, host_to_container = get_docker_volume_bindings(all_data)

        def remap(data):
            return str(remap_data_path_for_container(data, host_to_container).path)

        command = [
            "bash", "magellan.sh",
            remap(inputs["input"]),
            remap(outputs["output"]),
            remap(config_data),
        ]

        client = docker_client(
            image="kgt/magellan:latest",
            command=command,
            volumes=volumes,
        )

        result = client()

magellan_entity_matching_task = KgTask(
    name="magellan_entity_matching",
    description="Entity matching with Magellan (py_entitymatching)",
    input_spec=_MAGELLAN_INPUT_SPEC,
    output_spec=_MAGELLAN_OUTPUT_SPEC,
    function=magellan_entity_matching,
    config_spec=magellan_entity_matching_config,
    category=[BasicTaskCategoryCatalog.entity_matching],
    tools=["magellan", "py_entitymatching"],
)


Registry.add_task(
    magellan_entity_matching_task.name,
    magellan_entity_matching_task,
)