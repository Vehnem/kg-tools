"""KGpipe task definition for wrapping the DeepMatcher pipeline.

DeepMatcher is invoked through the repository's deepmatcher.sh wrapper:

    bash deepmatcher.sh \
        <data_dir> \
        <train.csv> \
        <validation.csv> \
        <test.csv> \
        <best_model.pth> \
        <unlabeled.csv> \
        <output.csv> \
        [<config.yaml>]

The configuration mirrors deepmatcher_config.example.yaml and is divided
into the following sections:

    process
    process_unlabeled
    model
    train
    eval
    prediction
    threshold

The threshold section is handled by run_deepmatcher.py and is therefore
included in the KGpipe configuration even though it is not passed directly
to DeepMatcher.
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


# ---------------------------------------------------------------------------
# Input / output
# ---------------------------------------------------------------------------

_DEEPMATCHER_INPUT_SPEC = {
    "data_dir": BasicDataFormats.DIRECTORY,
    "train": BasicDataFormats.CSV,
    "validation": BasicDataFormats.CSV,
    "test": BasicDataFormats.CSV,
    "unlabeled": BasicDataFormats.CSV,
}

_DEEPMATCHER_OUTPUT_SPEC = {
    "model": BasicDataFormats.FILE,
    "prediction": BasicDataFormats.CSV,
}


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _process_parameters() -> list[Parameter]:
    return [
        Parameter(
            name="cache",
            native_keys=["process.cache"],
            datatype=ParameterType.string,
            default_value="cacheddata.pth",
            required=False,
        ),
        Parameter(
            name="check_cached_data",
            native_keys=["process.check_cached_data"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),
        Parameter(
            name="auto_rebuild_cache",
            native_keys=["process.auto_rebuild_cache"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),
        Parameter(
            name="tokenize",
            native_keys=["process.tokenize"],
            datatype=ParameterType.string,
            default_value="nltk",
            required=False,
        ),
        Parameter(
            name="lowercase",
            native_keys=["process.lowercase"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),
        Parameter(
            name="embeddings",
            native_keys=["process.embeddings"],
            datatype=ParameterType.string,
            default_value="glove.6B.50d",
            required=False,
        ),
        Parameter(
            name="embeddings_cache_path",
            native_keys=["process.embeddings_cache_path"],
            datatype=ParameterType.string,
            default_value="~/.vector_cache",
            required=False,
        ),
        Parameter(
            name="ignore_columns",
            native_keys=["process.ignore_columns"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
        Parameter(
            name="include_lengths",
            native_keys=["process.include_lengths"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),
        Parameter(
            name="id_attr",
            native_keys=["process.id_attr"],
            datatype=ParameterType.string,
            default_value="id",
            required=False,
        ),
        Parameter(
            name="label_attr",
            native_keys=["process.label_attr"],
            datatype=ParameterType.string,
            default_value="label",
            required=False,
        ),
        Parameter(
            name="left_prefix",
            native_keys=["process.left_prefix"],
            datatype=ParameterType.string,
            default_value="left_",
            required=False,
        ),
        Parameter(
            name="right_prefix",
            native_keys=["process.right_prefix"],
            datatype=ParameterType.string,
            default_value="right_",
            required=False,
        ),
        Parameter(
            name="use_magellan_convention",
            native_keys=["process.use_magellan_convention"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="pca",
            native_keys=["process.pca"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),
    ]


def _process_unlabeled_parameters() -> list[Parameter]:
    return [
        Parameter(
            name="ignore_columns",
            native_keys=["process_unlabeled.ignore_columns"],
            datatype=ParameterType.string,
            default_value="",
            required=False,
        ),
    ]


def _model_parameters() -> list[Parameter]:
    return [
        Parameter(
            name="attr_summarizer",
            native_keys=["model.attr_summarizer"],
            datatype=ParameterType.string,
            default_value="hybrid",
            required=False,
            allowed_values=[
                "sif",
                "rnn",
                "attention",
                "hybrid",
            ],
        ),
        Parameter(
            name="attr_condense_factor",
            native_keys=["model.attr_condense_factor"],
            datatype=ParameterType.string,
            default_value="auto",
            required=False,
        ),
        Parameter(
            name="attr_comparator",
            native_keys=["model.attr_comparator"],
            datatype=ParameterType.string,
            default_value="null",
            required=False,
            allowed_values=[
                "null",
                "abs-diff",
                "diff",
                "concat",
                "concat-diff",
                "concat-abs-diff",
                "mul",
            ],
        ),
        Parameter(
            name="attr_merge",
            native_keys=["model.attr_merge"],
            datatype=ParameterType.string,
            default_value="concat",
            required=False,
            allowed_values=[
                "concat",
                "diff",
                "abs-diff",
                "concat-diff",
                "concat-abs-diff",
                "mul",
            ],
        ),
        Parameter(
            name="classifier",
            native_keys=["model.classifier"],
            datatype=ParameterType.string,
            default_value="2-layer-highway",
            required=False,
        ),
        Parameter(
            name="hidden_size",
            native_keys=["model.hidden_size"],
            datatype=ParameterType.integer,
            default_value=300,
            required=False,
        ),
    ]


def _train_parameters() -> list[Parameter]:
    return [
        Parameter(
            name="epochs",
            native_keys=["train.epochs"],
            datatype=ParameterType.integer,
            default_value=30,
            required=False,
        ),
        Parameter(
            name="pos_neg_ratio",
            native_keys=["train.pos_neg_ratio"],
            datatype=ParameterType.integer,
            default_value=None,
            required=False,
        ),
        Parameter(
            name="pos_weight",
            native_keys=["train.pos_weight"],
            datatype=ParameterType.float,
            default_value=None,
            required=False,
        ),
        Parameter(
            name="label_smoothing",
            native_keys=["train.label_smoothing"],
            datatype=ParameterType.float,
            default_value=0.05,
            required=False,
        ),
        Parameter(
            name="save_every_prefix",
            native_keys=["train.save_every_prefix"],
            datatype=ParameterType.string,
            default_value=None,
            required=False,
        ),
        Parameter(
            name="save_every_freq",
            native_keys=["train.save_every_freq"],
            datatype=ParameterType.integer,
            default_value=1,
            required=False,
        ),
        Parameter(
            name="batch_size",
            native_keys=["train.batch_size"],
            datatype=ParameterType.integer,
            default_value=32,
            required=False,
        ),
        Parameter(
            name="device",
            native_keys=["train.device"],
            datatype=ParameterType.string,
            default_value=None,
            required=False,
            allowed_values=["cpu", "cuda"],
        ),
        Parameter(
            name="progress_style",
            native_keys=["train.progress_style"],
            datatype=ParameterType.string,
            default_value="bar",
            required=False,
            allowed_values=["bar", "log"],
        ),
        Parameter(
            name="log_freq",
            native_keys=["train.log_freq"],
            datatype=ParameterType.integer,
            default_value=5,
            required=False,
        ),
        Parameter(
            name="sort_in_buckets",
            native_keys=["train.sort_in_buckets"],
            datatype=ParameterType.boolean,
            default_value=None,
            required=False,
        ),
    ]


def _eval_parameters() -> list[Parameter]:
    return [
        Parameter(
            name="batch_size",
            native_keys=["eval.batch_size"],
            datatype=ParameterType.integer,
            default_value=32,
            required=False,
        ),
        Parameter(
            name="device",
            native_keys=["eval.device"],
            datatype=ParameterType.string,
            default_value=None,
            required=False,
            allowed_values=["cpu", "cuda"],
        ),
        Parameter(
            name="progress_style",
            native_keys=["eval.progress_style"],
            datatype=ParameterType.string,
            default_value="bar",
            required=False,
            allowed_values=["bar", "log"],
        ),
        Parameter(
            name="log_freq",
            native_keys=["eval.log_freq"],
            datatype=ParameterType.integer,
            default_value=5,
            required=False,
        ),
        Parameter(
            name="sort_in_buckets",
            native_keys=["eval.sort_in_buckets"],
            datatype=ParameterType.boolean,
            default_value=None,
            required=False,
        ),
    ]


def _prediction_parameters() -> list[Parameter]:
    return [
        Parameter(
            name="output_attributes",
            native_keys=["prediction.output_attributes"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="batch_size",
            native_keys=["prediction.batch_size"],
            datatype=ParameterType.integer,
            default_value=32,
            required=False,
        ),
        Parameter(
            name="device",
            native_keys=["prediction.device"],
            datatype=ParameterType.string,
            default_value=None,
            required=False,
            allowed_values=["cpu", "cuda"],
        ),
        Parameter(
            name="progress_style",
            native_keys=["prediction.progress_style"],
            datatype=ParameterType.string,
            default_value="bar",
            required=False,
            allowed_values=["bar", "log"],
        ),
        Parameter(
            name="log_freq",
            native_keys=["prediction.log_freq"],
            datatype=ParameterType.integer,
            default_value=5,
            required=False,
        ),
        Parameter(
            name="sort_in_buckets",
            native_keys=["prediction.sort_in_buckets"],
            datatype=ParameterType.boolean,
            default_value=None,
            required=False,
        ),
    ]


def _threshold_parameters() -> list[Parameter]:
    return [
        Parameter(
            name="enabled",
            native_keys=["threshold.enabled"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),
        Parameter(
            name="mode",
            native_keys=["threshold.mode"],
            datatype=ParameterType.string,
            default_value="fixed",
            required=False,
            allowed_values=[
                "fixed",
                "relative_to_mean",
                "relative_to_max",
                "mean_minus_std",
                "percentile",
            ],
        ),
        Parameter(
            name="value",
            native_keys=["threshold.value"],
            datatype=ParameterType.float,
            default_value=0.8,
            required=False,
        ),
        Parameter(
            name="fraction",
            native_keys=["threshold.fraction"],
            datatype=ParameterType.float,
            default_value=0.1,
            required=False,
        ),
        Parameter(
            name="std_multiplier",
            native_keys=["threshold.std_multiplier"],
            datatype=ParameterType.float,
            default_value=1.0,
            required=False,
        ),
        Parameter(
            name="percentile",
            native_keys=["threshold.percentile"],
            datatype=ParameterType.float,
            default_value=90.0,
            required=False,
        ),
        Parameter(
            name="output_mode",
            native_keys=["threshold.output_mode"],
            datatype=ParameterType.string,
            default_value="filter",
            required=False,
            allowed_values=["filter", "flag"],
        ),
    ]


def _deepmatcher_parameters() -> list[Parameter]:
    return (
        _process_parameters()
        + _process_unlabeled_parameters()
        + _model_parameters()
        + _train_parameters()
        + _eval_parameters()
        + _prediction_parameters()
        + _threshold_parameters()
    )


deepmatcher_entity_matching_config = ConfigurationDefinition(
    name="deepmatcher_entity_matching",
    description="Entity matching with DeepMatcher",
    parameters=_deepmatcher_parameters(),
)


# ---------------------------------------------------------------------------
# Task implementation
# ---------------------------------------------------------------------------

def deepmatcher_entity_matching(
    inputs: TaskInput,
    outputs: TaskOutput,
    config: ConfigurationProfile,
):
    """Run the DeepMatcher shell wrapper.

    The actual command is:

        bash deepmatcher.sh \
            <data_dir> \
            <train.csv> \
            <validation.csv> \
            <test.csv> \
            <best_model.pth> \
            <unlabeled.csv> \
            <output.csv> \
            [<config.yaml>]

    The configuration profile is expected to be serialized to a YAML file
    before invoking the wrapper.
    """

    # TODO:
    # 1. Resolve the input/output paths from TaskInput/TaskOutput.
    # 2. Serialize `config` to the DeepMatcher YAML structure:
    #
    #       process:
    #         ...
    #       process_unlabeled:
    #         ...
    #       model:
    #         ...
    #       train:
    #         ...
    #       eval:
    #         ...
    #       prediction:
    #         ...
    #       threshold:
    #         ...
    #
    # 3. Invoke:
    #
    #       bash deepmatcher.sh \
    #           data_dir \
    #           train.csv \
    #           validation.csv \
    #           test.csv \
    #           best_model.pth \
    #           unlabeled.csv \
    #           output.csv \
    #           config.yaml
    #
    # 4. Return the generated model and prediction output.


deepmatcher_entity_matching_task = KgTask(
    name="deepmatcher_entity_matching",
    description="Entity matching with DeepMatcher",
    input_spec=_DEEPMATCHER_INPUT_SPEC,
    output_spec=_DEEPMATCHER_OUTPUT_SPEC,
    function=deepmatcher_entity_matching,
    config_spec=deepmatcher_entity_matching_config,
    category=[BasicTaskCategoryCatalog.entity_matching],
    tools=["deepmatcher"],
)

Registry.add_task(
    deepmatcher_entity_matching_task.name,
    deepmatcher_entity_matching_task,
)