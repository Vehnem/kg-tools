"""KGpipe task definitions for wrapping Ditto entity matching.

Ditto is a pretrained-language-model-based entity matching pipeline.
It consumes candidate record pairs in JSONL format and produces match
predictions. Training and matching are controlled through the Ditto
configuration.
The matching behaviour is mainly determined by the language-model
backbone and Ditto's optional optimizations:

- domain knowledge
- summarization
- data augmentation (training only)
"""

import tempfile
from pathlib import Path

import yaml
from kgpipe.common import Data
from kgpipe.common import KgTask, TaskInput, TaskOutput, BasicDataFormats, BasicTaskCategoryCatalog, Registry
from kgpipe.common.io import get_docker_volume_bindings, remap_data_path_for_container
from kgpipe.common.model.configuration import ConfigurationDefinition, Parameter, ParameterType, ConfigurationProfile
from kgpipe.execution import docker_client

# Matching: Ditto consumes candidate entity pairs in JSONL and produces
# JSONL match predictions. "checkpoint" is the checkpoint directory written
# by the training task (its "output").
_DITTO_INPUT_SPEC = {
    "input": BasicDataFormats.JSON,
    "checkpoint": BasicDataFormats.ANY,
}

_DITTO_OUTPUT_SPEC = {
    "output": BasicDataFormats.JSON,
}

# Training: Ditto reads its train/valid/test files (tab-separated Ditto
# format) and writes a checkpoint directory (<output>/<task.name>/model.pt).
_DITTO_TRAIN_INPUT_SPEC = {
    "train": BasicDataFormats.ANY,
    "valid": BasicDataFormats.ANY,
    "test": BasicDataFormats.ANY,
}

_DITTO_TRAIN_OUTPUT_SPEC = {
    "output": BasicDataFormats.ANY,
}


def _ditto_parameters() -> list[Parameter]:
    return [
        # ------------------------------------------------------------------
        # General / execution mode
        # ------------------------------------------------------------------
        Parameter(
            name="mode",
            native_keys=["mode"],
            datatype=ParameterType.string,
            default_value="match",
            required=False,
            allowed_values=["match", "train"],
        ),

        # ------------------------------------------------------------------
        # Task (written to Ditto's configs.json by run_ditto.py)
        # ------------------------------------------------------------------
        Parameter(
            name="task_name",
            native_keys=["task.name"],
            datatype=ParameterType.string,
            required=True,
        ),

        Parameter(
            name="task_type",
            native_keys=["task.task_type"],
            datatype=ParameterType.string,
            default_value="classification",
            required=False,
            allowed_values=["classification"],
        ),

        # Label vocabulary, comma-separated (e.g. "0,1"); converted to a YAML
        # list in _build_ditto_config().
        Parameter(
            name="vocab",
            native_keys=["task.vocab"],
            datatype=ParameterType.string,
            default_value="0,1",
            required=False,
        ),

        # trainset / validset / testset are relative to paths.ditto_repo.
        # validset is also used by matcher.py to tune the decision threshold.
        Parameter(
            name="trainset",
            native_keys=["task.trainset"],
            datatype=ParameterType.string,
            required=False,
        ),

        Parameter(
            name="validset",
            native_keys=["task.validset"],
            datatype=ParameterType.string,
            required=False,
        ),

        Parameter(
            name="testset",
            native_keys=["task.testset"],
            datatype=ParameterType.string,
            required=False,
        ),

        # ------------------------------------------------------------------
        # Paths
        # ------------------------------------------------------------------
        Parameter(
            name="ditto_repo",
            native_keys=["paths.ditto_repo"],
            datatype=ParameterType.string,
            default_value="./ditto",
            required=False,
        ),

        Parameter(
            name="checkpoint_path",
            native_keys=["paths.checkpoint_path"],
            datatype=ParameterType.string,
            default_value="checkpoints/",
            required=False,
        ),

        Parameter(
            name="input_path",
            native_keys=["paths.input_path"],
            datatype=ParameterType.string,
            required=False,
        ),

        Parameter(
            name="output_path",
            native_keys=["paths.output_path"],
            datatype=ParameterType.string,
            required=False,
        ),

        # ------------------------------------------------------------------
        # Model
        # ------------------------------------------------------------------
        Parameter(
            name="lm",
            native_keys=["model.lm"],
            datatype=ParameterType.string,
            default_value="distilbert",
            required=False,
            allowed_values=[
                "bert",
                "distilbert",
                "albert",
                "roberta",
                "xlnet",
            ],
        ),

        Parameter(
            name="max_len",
            native_keys=["model.max_len"],
            datatype=ParameterType.integer,
            default_value=256,
            required=False,
        ),

        Parameter(
            name="use_gpu",
            native_keys=["model.use_gpu"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        Parameter(
            name="fp16",
            native_keys=["model.fp16"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        # ------------------------------------------------------------------
        # Training
        # ------------------------------------------------------------------
        Parameter(
            name="run_id",
            native_keys=["training.run_id"],
            datatype=ParameterType.integer,
            default_value=0,
            required=False,
        ),

        Parameter(
            name="batch_size",
            native_keys=["training.batch_size"],
            datatype=ParameterType.integer,
            default_value=64,
            required=False,
        ),

        Parameter(
            name="lr",
            native_keys=["training.lr"],
            datatype=ParameterType.number,
            default_value=3e-5,
            required=False,
        ),

        Parameter(
            name="n_epochs",
            native_keys=["training.n_epochs"],
            datatype=ParameterType.integer,
            default_value=20,
            required=False,
        ),

        Parameter(
            name="finetuning",
            native_keys=["training.finetuning"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        Parameter(
            name="save_model",
            native_keys=["training.save_model"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        Parameter(
            name="logdir",
            native_keys=["training.logdir"],
            datatype=ParameterType.string,
            default_value="checkpoints/",
            required=False,
        ),

        Parameter(
            name="size",
            native_keys=["training.size"],
            datatype=ParameterType.integer,
            required=False,
        ),

        # ------------------------------------------------------------------
        # Optimizations: data augmentation
        # ------------------------------------------------------------------
        Parameter(
            name="data_augmentation",
            native_keys=["optimizations.data_augmentation.enabled"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        Parameter(
            name="augmentation_operator",
            native_keys=["optimizations.data_augmentation.operator"],
            datatype=ParameterType.string,
            default_value="del",
            required=False,
            allowed_values=[
                "del",
                "swap",
                "drop_col",
                "append_col",
                "all",
            ],
        ),

        Parameter(
            name="alpha_aug",
            native_keys=["optimizations.data_augmentation.alpha_aug"],
            datatype=ParameterType.number,
            default_value=0.8,
            required=False,
        ),

        # ------------------------------------------------------------------
        # Optimizations: domain knowledge
        # ------------------------------------------------------------------
        Parameter(
            name="domain_knowledge",
            native_keys=["optimizations.domain_knowledge.enabled"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        Parameter(
            name="domain_knowledge_mode",
            native_keys=["optimizations.domain_knowledge.mode"],
            datatype=ParameterType.string,
            default_value="general",
            required=False,
            allowed_values=["general", "product"],
        ),

        # ------------------------------------------------------------------
        # Optimizations: summarization
        # ------------------------------------------------------------------
        Parameter(
            name="summarization",
            native_keys=["optimizations.summarization.enabled"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        # ------------------------------------------------------------------
        # Runtime
        # ------------------------------------------------------------------
        Parameter(
            name="python_bin",
            native_keys=["runtime.python_bin"],
            datatype=ParameterType.string,
            default_value="python",
            required=False,
        ),

        Parameter(
            name="cuda_visible_devices",
            native_keys=["runtime.cuda_visible_devices"],
            datatype=ParameterType.string,
            default_value="0",
            required=False,
        ),

        # ------------------------------------------------------------------
        # Blocking: train
        # ------------------------------------------------------------------
        Parameter(
            name="blocking_train_fn",
            native_keys=["blocking.train.train_fn"],
            datatype=ParameterType.string,
            required=False,
        ),

        Parameter(
            name="blocking_valid_fn",
            native_keys=["blocking.train.valid_fn"],
            datatype=ParameterType.string,
            required=False,
        ),

        Parameter(
            name="blocking_train_model_fn",
            native_keys=["blocking.train.model_fn"],
            datatype=ParameterType.string,
            default_value="model.pth",
            required=False,
        ),

        Parameter(
            name="blocking_train_batch_size",
            native_keys=["blocking.train.batch_size"],
            datatype=ParameterType.integer,
            default_value=64,
            required=False,
        ),

        Parameter(
            name="blocking_train_n_epochs",
            native_keys=["blocking.train.n_epochs"],
            datatype=ParameterType.integer,
            default_value=40,
            required=False,
        ),

        Parameter(
            name="blocking_train_lm",
            native_keys=["blocking.train.lm"],
            datatype=ParameterType.string,
            default_value="bert",
            required=False,
            allowed_values=[
                "bert",
                "distilbert",
                "albert",
                "roberta",
                "xlnet",
            ],
        ),

        Parameter(
            name="blocking_train_fp16",
            native_keys=["blocking.train.fp16"],
            datatype=ParameterType.boolean,
            default_value=False,
            required=False,
        ),

        # ------------------------------------------------------------------
        # Blocking: apply
        # ------------------------------------------------------------------
        Parameter(
            name="blocking_apply_input_path",
            native_keys=["blocking.apply.input_path"],
            datatype=ParameterType.string,
            default_value="input/",
            required=False,
        ),

        Parameter(
            name="blocking_apply_left_fn",
            native_keys=["blocking.apply.left_fn"],
            datatype=ParameterType.string,
            required=False,
        ),

        Parameter(
            name="blocking_apply_right_fn",
            native_keys=["blocking.apply.right_fn"],
            datatype=ParameterType.string,
            required=False,
        ),

        Parameter(
            name="blocking_apply_output_fn",
            native_keys=["blocking.apply.output_fn"],
            datatype=ParameterType.string,
            required=False,
        ),

        Parameter(
            name="blocking_apply_model_fn",
            native_keys=["blocking.apply.model_fn"],
            datatype=ParameterType.string,
            default_value="model.pth",
            required=False,
        ),

        Parameter(
            name="blocking_apply_k",
            native_keys=["blocking.apply.k"],
            datatype=ParameterType.integer,
            default_value=10,
            required=False,
        ),
    ]


# Parameters that are not user-configurable per task: they are either fixed
# by the task itself (mode), come from the task inputs/outputs (paths) or
# only apply to the other mode. They are still written to the generated
# config.yaml with their defaults, so the file keeps the full layout.
_TRAIN_EXCLUDED = {
    "mode",
    "input_path", "output_path",           # matching only
    "use_gpu",                             # matching only
    "trainset", "validset", "testset",     # task inputs
    "checkpoint_path", "logdir",           # task output
}

_MATCH_EXCLUDED = {
    "mode",
    "input_path", "output_path",           # task input / output
    "checkpoint_path",                     # task input (checkpoint)
    "trainset", "testset",                 # training only
    "run_id", "batch_size", "lr", "n_epochs", "finetuning", "save_model",
    "logdir", "size",                      # training only
    "data_augmentation", "augmentation_operator", "alpha_aug",  # training only
}


def _params_without(excluded: set[str]) -> list[Parameter]:
    return [p for p in _ditto_parameters() if p.name not in excluded]


ditto_train_config = ConfigurationDefinition(
    name="ditto_entity_matching_train",
    description="Train a Ditto entity matching model",
    parameters=_params_without(_TRAIN_EXCLUDED),
)

ditto_entity_matching_config = ConfigurationDefinition(
    name="ditto_entity_matching",
    description="Entity matching with Ditto",
    parameters=_params_without(_MATCH_EXCLUDED),
)


def _set_nested(tree: dict, dotted_key: str, value) -> None:
    *parents, leaf = dotted_key.split(".")
    node = tree
    for part in parents:
        node = node.setdefault(part, {})
    node[leaf] = value


def _build_ditto_config(
    config: ConfigurationProfile,
    mode: str,
    overrides: dict | None = None,
) -> str:
    tree: dict = {}
    for param in _ditto_parameters():
        try:
            value = config.get_parameter_value(param.name)
        except (ValueError, KeyError):
            value = param.default_value
        native_key = param.native_keys[0]

        # task.vocab is a YAML list in the Ditto config, but a plain string
        # parameter here.
        if native_key == "task.vocab" and isinstance(value, str):
            value = [v.strip() for v in value.split(",") if v.strip()]

        _set_nested(tree, native_key, value)

    # The mode is fixed by the task; overrides carry the container paths.
    _set_nested(tree, "mode", mode)
    for native_key, value in (overrides or {}).items():
        _set_nested(tree, native_key, value)

    return yaml.safe_dump(tree, sort_keys=False, default_flow_style=False)


def _run_ditto(
    inputs: TaskInput,
    outputs: TaskOutput,
    config: ConfigurationProfile,
    *,
    mode: str,
    input_key: str | None,
    overrides_fn,
    output_is_dir: bool,
):
    """Run ditto.sh in the Ditto container.

    overrides_fn(remap) returns the config values (container paths) that
    are written into the generated config.yaml.
    input_key=None passes an empty string as the script's input argument.
    """
    out_path = Path(outputs["output"].path)
    (out_path if output_is_dir else out_path.parent).mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ditto_") as tmp:
        config_host_path = Path(tmp) / "config.yaml"
        # Create the file first so it can be mounted; the content needs the
        # container paths and is written after the volume bindings exist.
        config_host_path.touch()
        config_data = Data(str(config_host_path), BasicDataFormats.ANY)

        all_data = list(inputs.values()) + list(outputs.values()) + [config_data]
        volumes, host_to_container = get_docker_volume_bindings(all_data)

        def remap(data):
            return str(remap_data_path_for_container(data, host_to_container).path)

        config_host_path.write_text(
            _build_ditto_config(config, mode, overrides_fn(remap)),
            encoding="utf-8",
        )

        command = [
            "bash", "ditto.sh",
            remap(inputs[input_key]) if input_key else "",
            remap(outputs["output"]),
            remap(config_data),
        ]

        client = docker_client(
            image="kgt/ditto:latest",
            command=command,
            volumes=volumes,
        )

        result = client()


def ditto_entity_matching_train(
    inputs: TaskInput,
    outputs: TaskOutput,
    config: ConfigurationProfile,
):
    def overrides(remap):
        checkpoint_dir = remap(outputs["output"])
        return {
            "task.trainset": remap(inputs["train"]),
            "task.validset": remap(inputs["valid"]),
            "task.testset": remap(inputs["test"]),
            # --logdir (train) / --checkpoint_path (match): the model ends up in
            # <output>/<task.name>/model.pt
            "paths.checkpoint_path": checkpoint_dir,
            "training.logdir": checkpoint_dir,
        }

    _run_ditto(
        inputs, outputs, config,
        mode="train",
        input_key=None,
        overrides_fn=overrides,
        output_is_dir=True,
    )


def ditto_entity_matching(
    inputs: TaskInput,
    outputs: TaskOutput,
    config: ConfigurationProfile,
):
    def overrides(remap):
        return {
            "paths.input_path": remap(inputs["input"]),
            "paths.output_path": remap(outputs["output"]),
            # Output directory of the training task; matcher.py loads
            # <checkpoint_path>/<task.name>/model.pt from it.
            "paths.checkpoint_path": remap(inputs["checkpoint"]),
        }

    _run_ditto(
        inputs, outputs, config,
        mode="match",
        input_key="input",
        overrides_fn=overrides,
        output_is_dir=False,
    )


ditto_entity_matching_train_task = KgTask(
    name="ditto_entity_matching_train",
    description="Train a Ditto entity matching model",
    input_spec=_DITTO_TRAIN_INPUT_SPEC,
    output_spec=_DITTO_TRAIN_OUTPUT_SPEC,
    function=ditto_entity_matching_train,
    config_spec=ditto_train_config,
    category=[BasicTaskCategoryCatalog.entity_matching],
    tools=["ditto"],
)

ditto_entity_matching_task = KgTask(
    name="ditto_entity_matching",
    description="Entity matching with Ditto",
    input_spec=_DITTO_INPUT_SPEC,
    output_spec=_DITTO_OUTPUT_SPEC,
    function=ditto_entity_matching,
    config_spec=ditto_entity_matching_config,
    category=[BasicTaskCategoryCatalog.entity_matching],
    tools=["ditto"],
)


Registry.add_task(
    ditto_entity_matching_train_task.name,
    ditto_entity_matching_train_task,
)

Registry.add_task(
    ditto_entity_matching_task.name,
    ditto_entity_matching_task,
)