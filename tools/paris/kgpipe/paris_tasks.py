"""KGpipe task definitions for wrapping PARIS knowledge-base alignment.

PARIS is a probabilistic alignment system for knowledge bases. It takes
two RDF/N-Triples fact stores and produces entity, relation, and class
alignments.

Unlike classical ontology matching systems, PARIS does not expose
separate matcher, blocker, or feature-generation stages. Its behaviour
is controlled through the PARIS settings.ini parameters, which mainly
control:

- iteration and convergence behaviour
- relation/join exploration
- literal/string matching
- sampling and parallelism
- equality propagation and aggregation
- smoothing and thresholding

The wrapper invokes the detailed one-argument PARIS configuration mode.
The fact-store paths and output directory are supplied by KGpipe and
override the corresponding values from settings.ini.
"""

from kgpipe.common import (
    KgTask,
    TaskInput,
    TaskOutput,
    BasicDataFormats,
    BasicTaskCategoryCatalog,
    Registry,
)
from kgpipe.common.model.configuration import (
    ConfigurationDefinition,
    Parameter,
    ParameterType,
    ConfigurationProfile,
)


_PARIS_INPUT_SPEC = {
    "source": BasicDataFormats.RDF,
    "target": BasicDataFormats.RDF,
}

_PARIS_OUTPUT_SPEC = {
    "output": BasicDataFormats.TSV,
}


def _paris_parameters() -> list[Parameter]:
    return [
        # ==================================================================
        # Iteration / convergence
        # ==================================================================

        Parameter(
            name="end_iteration",
            native_keys=["endIteration"],
            datatype=ParameterType.integer,
            default_value=10,
            required=False,
        ),

        Parameter(
            name="report_interval",
            native_keys=["reportInterval"],
            datatype=ParameterType.integer,
            default_value=5000,
            required=False,
        ),

        # ==================================================================
        # Parallelism
        # ==================================================================

        Parameter(
            name="n_threads",
            native_keys=["nThreads"],
            datatype=ParameterType.integer,
            default_value=None,
            required=False,
        ),

        Parameter(
            name="parallel_file_load",
            native_keys=["parallelFileLoad"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        # ==================================================================
        # Join / relation-path exploration
        # ==================================================================

        Parameter(
            name="join_length_limit",
            native_keys=["joinLengthLimit"],
            datatype=ParameterType.integer,
            default_value=1,
            required=False,
        ),

        Parameter(
            name="sum_join_length_limit",
            native_keys=["sumJoinLengthLimit"],
            datatype=ParameterType.integer,
            default_value=None,
            required=False,
        ),

        Parameter(
            name="join_threshold",
            native_keys=["joinThreshold"],
            datatype=ParameterType.float,
            default_value=0.1,
            required=False,
        ),

        Parameter(
            name="allow_loops",
            native_keys=["allowLoops"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        Parameter(
            name="optimize_no_joins",
            native_keys=["optimizeNoJoins"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        Parameter(
            name="interestingness_threshold",
            native_keys=["interestingnessThreshold"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        # ==================================================================
        # Alignment direction / aggregation
        # ==================================================================

        Parameter(
            name="both_ways",
            native_keys=["bothWays"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        Parameter(
            name="take_max",
            native_keys=["takeMax"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        Parameter(
            name="take_max_max",
            native_keys=["takeMaxMax"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        Parameter(
            name="last_pass_threshold",
            native_keys=["lastPassThreshold"],
            datatype=ParameterType.integer,
            default_value=0,
            required=False,
        ),

        Parameter(
            name="use_new_equality_product",
            native_keys=["useNewEqualityProduct"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        Parameter(
            name="matrix_sub_relation_stores",
            native_keys=["matrixSubRelationStores"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        # ==================================================================
        # Literal / string normalization
        # ==================================================================

        Parameter(
            name="normalize_strings",
            native_keys=["normalizeStrings"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        Parameter(
            name="normalize_dates_to_years",
            native_keys=["normalizeDatesToYears"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        Parameter(
            name="literal_distance",
            native_keys=["literalDistance"],
            datatype=ParameterType.string,
            default_value="identity",
            required=False,
            allowed_values=["identity", "shingling"],
        ),

        Parameter(
            name="post_literal_distance_threshold",
            native_keys=["postLiteralDistanceThreshold"],
            datatype=ParameterType.float,
            default_value=0.78,
            required=False,
        ),

        Parameter(
            name="penalize_approx_matches",
            native_keys=["penalizeApproxMatches"],
            datatype=ParameterType.float,
            default_value=1.1,
            required=False,
        ),

        Parameter(
            name="no_approx_if_exact",
            native_keys=["noApproxIfExact"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        # ==================================================================
        # Shingling
        # ==================================================================

        Parameter(
            name="shingling_size",
            native_keys=["shinglingSize"],
            datatype=ParameterType.integer,
            default_value=4,
            required=False,
        ),

        Parameter(
            name="shingling_functions",
            native_keys=["shinglingFunctions"],
            datatype=ParameterType.integer,
            default_value=30,
            required=False,
        ),

        Parameter(
            name="shingling_table_size",
            native_keys=["shinglingTableSize"],
            datatype=ParameterType.integer,
            default_value=10485760,
            required=False,
        ),

        Parameter(
            name="shingling_threads",
            native_keys=["shinglingThreads"],
            datatype=ParameterType.integer,
            default_value=4,
            required=False,
        ),

        Parameter(
            name="precompute_shinglings",
            native_keys=["precomputeShinglings"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        Parameter(
            name="shingling_square",
            native_keys=["shinglingSquare"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        # ==================================================================
        # Smoothing
        # ==================================================================

        Parameter(
            name="smooth_numerator",
            native_keys=["smoothNumerator"],
            datatype=ParameterType.float,
            default_value=0.0,
            required=False,
        ),

        Parameter(
            name="smooth_denominator",
            native_keys=["smoothDenominator"],
            datatype=ParameterType.float,
            default_value=10.0,
            required=False,
        ),

        Parameter(
            name="smooth_numerator_sampling",
            native_keys=["smoothNumeratorSampling"],
            datatype=ParameterType.float,
            default_value=0.0,
            required=False,
        ),

        Parameter(
            name="smooth_denominator_sampling",
            native_keys=["smoothDenominatorSampling"],
            datatype=ParameterType.float,
            default_value=1.0,
            required=False,
        ),

        # ==================================================================
        # Entity sampling
        # ==================================================================

        Parameter(
            name="sample_entities",
            native_keys=["sampleEntities"],
            datatype=ParameterType.integer,
            default_value=0,
            required=False,
        ),

        Parameter(
            name="shuffle_entities",
            native_keys=["shuffleEntities"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        Parameter(
            name="all_length_one_after_sample",
            native_keys=["allLengthOneAfterSample"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        # ==================================================================
        # Internal matching behaviour
        # ==================================================================

        Parameter(
            name="clever_matching",
            native_keys=["cleverMatching"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        # ==================================================================
        # Debugging
        # ==================================================================

        Parameter(
            name="debug_entity",
            native_keys=["debugEntity"],
            datatype=ParameterType.string,
            default_value=None,
            required=False,
        ),

        Parameter(
            name="print_neighborhoods_sampling",
            native_keys=["printNeighborhoodsSampling"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        Parameter(
            name="debug_sampling",
            native_keys=["debugSampling"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
    ]


paris_entity_matching_config = ConfigurationDefinition(
    name="paris_entity_matching",
    description="Knowledge-base alignment with PARIS",
    parameters=_paris_parameters(),
)


def paris_entity_matching(
    inputs: TaskInput,
    outputs: TaskOutput,
    config: ConfigurationProfile,
):
    pass  # TODO: generate settings.ini and run PARIS wrapper


paris_entity_matching_task = KgTask(
    name="paris_entity_matching",
    description="Knowledge-base alignment with PARIS",
    input_spec=_PARIS_INPUT_SPEC,
    output_spec=_PARIS_OUTPUT_SPEC,
    function=paris_entity_matching,
    config_spec=paris_entity_matching_config,
    category=[BasicTaskCategoryCatalog.ontology_matching],
    tools=["paris"],
)


Registry.add_task(
    paris_entity_matching_task.name,
    paris_entity_matching_task,
)