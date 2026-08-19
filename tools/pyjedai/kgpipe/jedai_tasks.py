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

from kgpipe.common import KgTask, TaskInput, TaskOutput, BasicDataFormats, BasicTaskCategoryCatalog, Registry
from kgpipe.common.model.configuration import ConfigurationDefinition, Parameter, ParameterType, ConfigurationProfile

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


def jedai_syntactic_matching(inputs: TaskInput, outputs: TaskOutput, config: ConfigurationProfile):
    pass  # TODO: generate matcher yaml and run Docker wrapper


def jedai_semantic_matching(inputs: TaskInput, outputs: TaskOutput, config: ConfigurationProfile):
    pass  # TODO: generate matcher yaml and run Docker wrapper


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
