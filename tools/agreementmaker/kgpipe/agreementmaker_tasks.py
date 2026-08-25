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

from kgpipe.common import KgTask, TaskInput, TaskOutput, BasicDataFormats, BasicTaskCategoryCatalog, Registry
from kgpipe.common.model.configuration import ConfigurationDefinition, Parameter, ParameterType, ConfigurationProfile

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


def agreementmaker_ontology_matching(inputs: TaskInput, outputs: TaskOutput, config: ConfigurationProfile):
    pass  # TODO: generate matcher yaml and run Docker wrapper


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
