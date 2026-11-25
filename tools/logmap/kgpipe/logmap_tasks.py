"""KGpipe task definitions for wrapping LogMap.

LogMap is a Java ontology matching system with built-in reasoning and
alignment repair:

    ontology1 + ontology2
      -> lexical indexing and anchor extraction
      -> mapping discovery
      -> reasoning-based repair
      -> mappings (OWL / RDF / TXT / TSV / TTL)

The wrapper exposes the configuration supported by run_logmap.sh. The two
ontologies and the (optional) reference alignment are passed as separate task
inputs ("ontology1", "ontology2", "reference"); everything else is configured
via the parameters below. If a reference alignment is given, LogMap runs in
EVALUATION mode and additionally writes evaluation.csv into the output folder.
The LogMap facilities MATCHER-BIO, LITE, DEBUGGER and RDF2OWL are intentionally
not part of this task.
"""

import tempfile
from pathlib import Path

from kgpipe.common import Data
from kgpipe.common import KgTask, TaskInput, TaskOutput, BasicDataFormats, BasicTaskCategoryCatalog, Registry
from kgpipe.common.io import get_docker_volume_bindings, remap_data_path_for_container
from kgpipe.common.model.configuration import ConfigurationDefinition, Parameter, ParameterType, ConfigurationProfile
from kgpipe.execution import docker_client

_LOGMAP_INPUT_SPEC = {
    "ontology1": BasicDataFormats.ANY,
    "ontology2": BasicDataFormats.ANY,
    "reference": BasicDataFormats.ANY,
}

_LOGMAP_OUTPUT_SPEC = {
    "output": BasicDataFormats.ANY,
}


def _bool(name, default):
    return Parameter(
        name=name,
        native_keys=[name],
        datatype=ParameterType.boolean,
        default_value=default,
        required=False,
    )


def _int(name, default):
    return Parameter(
        name=name,
        native_keys=[name],
        datatype=ParameterType.integer,
        default_value=default,
        required=False,
    )


def _str(name, default=None, required=False, allowed_values=None):
    kwargs = {}
    if allowed_values is not None:
        kwargs["allowed_values"] = allowed_values
    if default is not None:
        kwargs["default_value"] = default
    return Parameter(
        name=name,
        native_keys=[name],
        datatype=ParameterType.string,
        required=required,
        **kwargs,
    )


def _logmap_parameters() -> list[Parameter]:
    return [
        # ==================================================================
        # Run-level
        # ==================================================================

        _bool("classify", True),
        _str("java_xms"),
        _str("java_xmx", required=True),
        _int("entity_expansion_limit", 10000000),

        # ==================================================================
        # Reasoning and repair
        # ==================================================================

        _str("reasoner", "HermiT", allowed_values=["HermiT", "ELK", "Structural"]),
        _int("timeout", 25),
        _bool("reason_datatypes", False),
        _bool("perform_repair", True),
        _bool("glogal_info", True),
        _bool("second_chance_conflicts", True),
        _int("ratio_second_chance_discarded", 10),

        # ==================================================================
        # Output selection
        # ==================================================================

        _bool("output_equivalences_only", False),
        _bool("output_class_mappings", True),
        _bool("output_prop_mappings", True),
        _bool("output_instance_mappings", True),
        _bool("output_instance_mapping_files", False),
        _bool("print_output", False),

        # ==================================================================
        # Matching scope
        # ==================================================================

        _bool("property_matching", True),
        _bool("instance_matching", True),
        _bool("restrict_individual_types", False),
        _bool("index_undeclared_abox_predicates", True),
        _bool("index_undeclared_abox_use_both_props", True),
        _bool("use_overlapping", False),
        _int("min_size_overlapping", 15000),

        # ==================================================================
        # Lexical and scoring thresholds (decimal values are passed as strings)
        # ==================================================================

        _str("good_isub_anchors", "0.98"),
        _str("good_isub_candidates", "0.95"),
        _str("good_confidence", "0.50"),
        _str("good_sim_coocurrence", "0.08"),
        _str("bad_score_scope", "0.0"),
        _str("min_conf_pro_map", "0.80"),
        _str("confidence_composed_mappings1", "0.8"),
        _str("confidence_composed_mappings2", "0.7"),
        _bool("avoid_redundant_labels", True),
        _int("max_redundancy_labels", 3),
        _int("max_ambiguity", 4),
        _int("good_ambiguity", 2),
        _bool("use_stemming", False),
        _bool("reverse_labels", False),
        _bool("use_umls_lexicon", True),

        # ==================================================================
        # Multilingual, BioPortal, interactivity
        # ==================================================================

        _bool("allow_multilingual", False),
        _bool("is_test_mode_multilingual", False),
        _bool("use_local_dict", False),
        _bool("call_online_translator", False),
        _str("target_lang", "en"),
        _int("translator_id", 9),
        _str("path_chinese_segmenter_dict"),
        _str("path_multilingual_tmp"),
        _str("path_multilingual_local"),
        _str("path_mappings_categories"),
        _bool("allow_bioportal", False),
        _int("max_mediating_ontologies", 10),
        _bool("allow_interactivity", False),

        # ==================================================================
        # List keys (comma-separated; unset keeps the shipped LogMap lists)
        # ==================================================================

        _str("annotation_URI"),
        _str("category_URI"),
        _str("data_assertion_URI_Indiv"),
        _str("data_assertion_URI_Indiv_deep2"),
        _str("object_assertion_URI_Indiv"),
        _str("allowed_individual_type"),
        _str("filter_entity"),
    ]


logmap_ontology_matching_config = ConfigurationDefinition(
    name="logmap_ontology_matching",
    description="Ontology matching with LogMap",
    parameters=_logmap_parameters(),
)


def _format_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return ",".join(str(v) for v in value)
    return str(value)


def _build_logmap_config(config: ConfigurationProfile) -> str:
    lines = []
    for param in _logmap_parameters():
        try:
            value = config.get_parameter_value(param.name)
        except (ValueError, KeyError):
            value = param.default_value

        if value is None or (isinstance(value, str) and not value.strip()):
            if param.required:
                raise ValueError(f"'{param.name}' is required")
            continue

        lines.append(f"{param.native_keys[0]}={_format_value(value)}")
    return "\n".join(lines) + "\n"


def logmap_ontology_matching(
    inputs: TaskInput,
    outputs: TaskOutput,
    config: ConfigurationProfile,
):
    Path(outputs["output"].path).mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="logmap_") as tmp:
        config_host_path = Path(tmp) / "config.conf"
        config_host_path.write_text(_build_logmap_config(config), encoding="utf-8")

        config_data = Data(str(config_host_path), BasicDataFormats.ANY)

        reference = inputs["reference"] if "reference" in inputs else None

        all_data = list(inputs.values()) + list(outputs.values()) + [config_data]
        volumes, host_to_container = get_docker_volume_bindings(all_data)

        def remap(data):
            return str(remap_data_path_for_container(data, host_to_container).path)

        command = [
            "bash", "run_logmap.sh",
            remap(inputs["ontology1"]),
            remap(inputs["ontology2"]),
            remap(outputs["output"]),
            remap(config_data),
        ]
        if reference is not None:
            command.append(remap(reference))

        client = docker_client(
            image="kgt/logmap:latest",
            command=command,
            volumes=volumes,
        )

        result = client()

logmap_ontology_matching_task = KgTask(
    name="logmap_ontology_matching",
    description="Ontology matching with LogMap",
    input_spec=_LOGMAP_INPUT_SPEC,
    output_spec=_LOGMAP_OUTPUT_SPEC,
    function=logmap_ontology_matching,
    config_spec=logmap_ontology_matching_config,
    category=[BasicTaskCategoryCatalog.ontology_matching],
    tools=["logmap"],
)


Registry.add_task(
    logmap_ontology_matching_task.name,
    logmap_ontology_matching_task,
)
