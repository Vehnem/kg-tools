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

# Ditto consumes candidate entity pairs in JSONL and produces
# JSONL match predictions.
_DITTO_INPUT_SPEC = {
    "input": BasicDataFormats.JSON,
}

_DITTO_OUTPUT_SPEC = {
    "output": BasicDataFormats.JSON,
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

        Parameter(
            name="task_name",
            native_keys=["task.name"],
            datatype=ParameterType.string,
            default_value=None,
            required=True,
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
            default_value=None,
            required=False,
        ),

        Parameter(
            name="output_path",
            native_keys=["paths.output_path"],
            datatype=ParameterType.string,
            default_value=None,
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
            datatype=ParameterType.float,
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
            default_value=None,
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
            datatype=ParameterType.float,
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
            default_value=None,
            required=False,
        ),

        Parameter(
            name="blocking_valid_fn",
            native_keys=["blocking.train.valid_fn"],
            datatype=ParameterType.string,
            default_value=None,
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
            default_value=None,
            required=False,
        ),

        Parameter(
            name="blocking_apply_right_fn",
            native_keys=["blocking.apply.right_fn"],
            datatype=ParameterType.string,
            default_value=None,
            required=False,
        ),

        Parameter(
            name="blocking_apply_output_fn",
            native_keys=["blocking.apply.output_fn"],
            datatype=ParameterType.string,
            default_value=None,
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


ditto_entity_matching_config = ConfigurationDefinition(
    name="ditto_entity_matching",
    description="Entity matching with Ditto",
    parameters=_ditto_parameters(),
)


def _set_nested(tree: dict, dotted_key: str, value) -> None:
    *parents, leaf = dotted_key.split(".")
    node = tree
    for part in parents:
        node = node.setdefault(part, {})
    node[leaf] = value


def _build_ditto_config(config: ConfigurationProfile) -> str:
    tree: dict = {}
    for param in _ditto_parameters():
        value = config.get_parameter_value(param.name)
        native_key = param.native_keys[0]

        _set_nested(tree, native_key, value)

    return yaml.safe_dump(tree, sort_keys=False, default_flow_style=False)


def ditto_entity_matching(
    inputs: TaskInput,
    outputs: TaskOutput,
    config: ConfigurationProfile,
):
    Path(outputs["output"].path).parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ditto_") as tmp:
        config_host_path = Path(tmp) / "config.yaml"
        config_host_path.write_text(_build_ditto_config(config), encoding="utf-8")

        config_data = Data(str(config_host_path), BasicDataFormats.ANY)

        all_data = list(inputs.values()) + list(outputs.values()) + [config_data]
        volumes, host_to_container = get_docker_volume_bindings(all_data)

        def remap(data):
            return str(remap_data_path_for_container(data, host_to_container).path)

        command = [
            "bash", "ditto.sh",
            remap(inputs["input"]),
            remap(outputs["output"]),
            remap(config_data),
        ]

        client = docker_client(
            image="kgt/ditto:latest",
            command=command,
            volumes=volumes,
        )

        result = client()

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
    ditto_entity_matching_task.name,
    ditto_entity_matching_task,
)