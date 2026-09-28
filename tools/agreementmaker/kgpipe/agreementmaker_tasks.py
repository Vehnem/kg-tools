"""KGpipe task definitions for wrapping AgreementMakerLight ontology matching.

AgreementMakerLight (AML) is one Docker pipeline (two ontologies in, an RDF
alignment out). Stages that do not change that contract — word matching,
string matching, structural matching, background knowledge, correspondence
selection, and coherence repair — are ConfigurationDefinition parameters.

The matching strategy itself is controlled through the AML configuration and
does not currently require separate KgTasks. The wrapper-level `mode` selects
between automatic matching, manual configuration, and repair of an existing
alignment.
"""

import tempfile
from pathlib import Path

from kgpipe.common import Data, KgTask, TaskInput, TaskOutput, BasicDataFormats, BasicTaskCategoryCatalog, Registry
from kgpipe.common.io import get_docker_volume_bindings, remap_data_path_for_container
from kgpipe.common.model.configuration import ConfigurationDefinition, Parameter, ParameterType, ConfigurationProfile
from kgpipe.execution import docker_client

_AGREEMENTMAKER_OM_INPUT_SPEC = {"source": BasicDataFormats.RDF, "target": BasicDataFormats.OWL}
_AGREEMENTMAKER_OM_OUTPUT_SPEC = {"output": BasicDataFormats.RDF}

def _matching_parameters() -> list[Parameter]:
    return [
        Parameter(
            name="mode",
            native_keys=["matching.mode"],
            datatype=ParameterType.string,
            default_value="auto",
            required=False,
            allowed_values=["auto", "manual", "repair"],
        ),
        Parameter(
            name="use_translator",
            native_keys=["matching.use_translator"],
            datatype=ParameterType.string,
            default_value="auto",
            required=False,
            allowed_values=["auto", "true", "false"],
        ),
        #TODO Not implemented yet
        Parameter(
            name="bk_sources",
            native_keys=["matching.bk_sources"],
            datatype=ParameterType.string,
            default_value="all",
            required=False,
        ),
        Parameter(
            name="word_matcher",
            native_keys=["matching.word_matcher"],
            datatype=ParameterType.string,
            default_value="auto",
            required=False,
            allowed_values=[
                "auto",
                "none",
                "by_class",
                "by_name",
                "average",
                "maximum",
                "mininum",
            ],
        ),
        Parameter(
            name="string_matcher",
            native_keys=["matching.string_matcher"],
            datatype=ParameterType.string,
            default_value="auto",
            required=False,
            allowed_values=["auto", "none", "global", "local"],
        ),
        Parameter(
            name="string_measure",
            native_keys=["matching.string_measure"],
            datatype=ParameterType.string,
            default_value="ISub",
            required=False,
            allowed_values=["ISub", "Levenstein", "Jaro-Winkler", "Q-gram"],
        ),
        Parameter(
            name="struct_matcher",
            native_keys=["matching.struct_matcher"],
            datatype=ParameterType.string,
            default_value="auto",
            required=False,
            allowed_values=[
                "auto",
                "none",
                "ancestors",
                "descendants",
                "average",
                "maximum",
                "minimum",
            ],
        ),
        Parameter(
            name="match_properties",
            native_keys=["matching.match_properties"],
            datatype=ParameterType.string,
            default_value="auto",
            required=False,
            allowed_values=["true", "false", "auto"],
        ),
        Parameter(
            name="selection_type",
            native_keys=["matching.selection_type"],
            datatype=ParameterType.string,
            default_value="auto",
            required=False,
            allowed_values=["auto", "none", "strict", "permissive", "hybrid"],
        ),
        Parameter(
            name="repair_alignment",
            native_keys=["matching.repair_alignment"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
    ]

agreementmaker_ontology_matching_config = ConfigurationDefinition(
    name="agreementmaker_ontology_matching",
    description="Ontology matching with AgreementMakerLight",
    parameters=_matching_parameters,
)


def _ini_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _build_settings(config: ConfigurationProfile) -> str:
    lines = []
    for param in _matching_parameters():
        value = config.get_parameter_value(param.name)
        allowed = getattr(param, "allowed_values", None)
        if allowed and _ini_value(value) not in allowed:
            raise ValueError(
                f"Invalid value {value!r} for '{param.name}', allowed: {allowed}"
            )
        lines.append(f"{param.name}={_ini_value(value)}")
    return "\n".join(lines) + "\n"


def agreementmaker_ontology_matching(inputs: TaskInput, outputs: TaskOutput, config: ConfigurationProfile):
    with tempfile.TemporaryDirectory(prefix="agreementmaker_") as tmp:
        config_host_path = Path(tmp) / "settings.ini"
        config_host_path.write_text(_build_settings(config), encoding="utf-8")

        config_data = Data(str(config_host_path), BasicDataFormats.ANY)

        all_data = list(inputs.values()) + list(outputs.values()) + [config_data]
        volumes, host_to_container = get_docker_volume_bindings(all_data)

        source_path = remap_data_path_for_container(inputs["source"], host_to_container)
        target_path = remap_data_path_for_container(inputs["target"], host_to_container)
        output_path = remap_data_path_for_container(outputs["output"], host_to_container)
        config_container_path = remap_data_path_for_container(config_data, host_to_container)

        command = [
            "bash", "agreementmaker.sh",
            str(config_container_path.path),
            str(source_path.path),
            str(target_path.path),
            str(output_path.path),
        ]

        client = docker_client(
            image="kgt/agreementmaker:latest",
            command=command,
            volumes=volumes,
        )

        result = client()

agreementmaker_ontology_matching_task = KgTask(
    name="agreementmaker_ontology_matching",
    description="Ontology matching with AgreementMakerLight",
    input_spec=_AGREEMENTMAKER_OM_INPUT_SPEC,
    output_spec=_AGREEMENTMAKER_OM_OUTPUT_SPEC,
    function=agreementmaker_ontology_matching,
    config_spec=agreementmaker_ontology_matching_config,
    category=[BasicTaskCategoryCatalog.ontology_matching],
    tools=["agreementmaker"],
)

Registry.add_task(agreementmaker_ontology_matching_task.name, agreementmaker_ontology_matching_task)
