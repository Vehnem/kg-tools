"""KGpipe task definitions for wrapping OntoEA.

OntoEA is an ontology-guided entity alignment approach for knowledge graphs
(https://github.com/ZihengZZH/OntoEA). Training consists of:

    benchmark folder
      -> relation / attribute / ontology triples + membership links
      -> joint embedding training (entity, ontology, membership, alignment)
      -> fusion of entity- and class-similarity
      -> alignment of the test entities

The wrapper exposes the configuration supported by run_ontoea.py. The whole
benchmark (KG triples, ontology files, membership links and the train/valid/test
split) is passed as a single directory input ("benchmark"); see
CONFIG_REFERENCE.md section 1 for its layout. The output directory receives
alignment.tsv (URI pairs), evaluation.csv, the raw OntoEA result files and,
optionally, the embeddings.

Parameter notes: decimal parameters are declared as strings and converted to
numbers before the YAML is written; list parameters are comma-separated; for
parameters that accept null, pass the text "null".
"""

import tempfile
from pathlib import Path

import yaml
from kgpipe.common import Data
from kgpipe.common import KgTask, TaskInput, TaskOutput, BasicDataFormats, BasicTaskCategoryCatalog, Registry
from kgpipe.common.io import get_docker_volume_bindings, remap_data_path_for_container
from kgpipe.common.model.configuration import ConfigurationDefinition, Parameter, ParameterType, ConfigurationProfile
from kgpipe.execution import docker_client

_ONTOEA_INPUT_SPEC = {
    "benchmark": BasicDataFormats.ANY,
}

_ONTOEA_OUTPUT_SPEC = {
    "output": BasicDataFormats.ANY,
}


def _ontoea_parameters() -> list[Parameter]:
    return [
        # ==================================================================
        # IO
        # ==================================================================

        Parameter(
            name="dataset_division",
            native_keys=["io.dataset_division"],
            datatype=ParameterType.string,
            default_value="721_5fold/1/",
            required=False,
        ),

        Parameter(
            name="ordered",
            native_keys=["io.ordered"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        # ==================================================================
        # Runtime
        # ==================================================================

        Parameter(
            name="cuda_visible_devices",
            native_keys=["runtime.cuda_visible_devices"],
            datatype=ParameterType.string,
            required=True,
        ),

        Parameter(
            name="batch_threads_num",
            native_keys=["runtime.batch_threads_num"],
            datatype=ParameterType.integer,
            default_value=4,
            required=False,
        ),

        Parameter(
            name="test_threads_num",
            native_keys=["runtime.test_threads_num"],
            datatype=ParameterType.integer,
            default_value=8,
            required=False,
        ),

        # ==================================================================
        # Word embeddings
        # ==================================================================

        Parameter(
            name="word_embed",
            native_keys=["word_embeddings.word_embed"],
            datatype=ParameterType.string,
            default_value="../../benchmarks/wiki-news-300d-1M.vec",
            required=False,
        ),

        Parameter(
            name="use_word_embed_init",
            native_keys=["word_embeddings.use_word_embed_init"],
            datatype=ParameterType.integer,
            default_value=0,
            required=False,
        ),

        Parameter(
            name="use_word_embed_init_onto",
            native_keys=["word_embeddings.use_word_embed_init_onto"],
            datatype=ParameterType.integer,
            default_value=0,
            required=False,
        ),

        Parameter(
            name="word_embed_init_zh",
            native_keys=["word_embeddings.word_embed_init_zh"],
            datatype=ParameterType.integer,
            default_value=0,
            required=False,
        ),

        Parameter(
            name="use_alter_label",
            native_keys=["word_embeddings.use_alter_label"],
            datatype=ParameterType.integer,
            default_value=0,
            required=False,
        ),

        # ==================================================================
        # Model
        # ==================================================================

        Parameter(
            name="embedding_module",
            native_keys=["model.embedding_module"],
            datatype=ParameterType.string,
            default_value="OntoEA",
            required=False,
            allowed_values=["OntoEA"],
        ),

        Parameter(
            name="alignment_module",
            native_keys=["model.alignment_module"],
            datatype=ParameterType.string,
            default_value="mapping",
            required=False,
            allowed_values=["mapping"],
        ),

        Parameter(
            name="ent_emb_loss",
            native_keys=["model.ent_emb_loss"],
            datatype=ParameterType.string,
            default_value="limit_loss",
            required=False,
            allowed_values=["limit_loss", "pos_loss"],
        ),

        Parameter(
            name="onto_training_method",
            native_keys=["model.onto_training_method"],
            datatype=ParameterType.string,
            default_value="hier",
            required=False,
            allowed_values=["hier", "transe", "linear"],
        ),

        Parameter(
            name="fusion_way",
            native_keys=["model.fusion_way"],
            datatype=ParameterType.string,
            default_value="add",
            required=False,
        ),

        Parameter(
            name="dim",
            native_keys=["model.dim"],
            datatype=ParameterType.integer,
            default_value=300,
            required=False,
        ),

        Parameter(
            name="onto_dim",
            native_keys=["model.onto_dim"],
            datatype=ParameterType.integer,
            default_value=300,
            required=False,
        ),

        Parameter(
            name="init",
            native_keys=["model.init"],
            datatype=ParameterType.string,
            default_value="unit",
            required=False,
            allowed_values=["unit"],
        ),

        Parameter(
            name="ent_l2_norm",
            native_keys=["model.ent_l2_norm"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
            allowed_values=[True],
        ),

        Parameter(
            name="rel_l2_norm",
            native_keys=["model.rel_l2_norm"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        Parameter(
            name="loss_norm",
            native_keys=["model.loss_norm"],
            datatype=ParameterType.string,
            default_value="L2",
            required=False,
            allowed_values=["L1", "L2"],
        ),

        Parameter(
            name="alpha",
            native_keys=["model.alpha"],
            datatype=ParameterType.string,
            default_value="5.0",
            required=False,
        ),

        Parameter(
            name="beta",
            native_keys=["model.beta"],
            datatype=ParameterType.string,
            default_value="0.0",
            required=False,
        ),

        Parameter(
            name="gamma",
            native_keys=["model.gamma"],
            datatype=ParameterType.string,
            default_value="1.0",
            required=False,
        ),

        Parameter(
            name="sigma",
            native_keys=["model.sigma"],
            datatype=ParameterType.string,
            default_value="1.0",
            required=False,
        ),

        # ==================================================================
        # Ontology
        # ==================================================================

        Parameter(
            name="cvlink_module",
            native_keys=["ontology.cvlink_module"],
            datatype=ParameterType.string,
            required=False,
        ),

        Parameter(
            name="check_version",
            native_keys=["ontology.check_version"],
            datatype=ParameterType.integer,
            default_value=4,
            required=False,
            allowed_values=[0, 1, 2, 3, 4, 5],
        ),

        Parameter(
            name="onto_neg_sampling",
            native_keys=["ontology.onto_neg_sampling"],
            datatype=ParameterType.string,
            required=False,
        ),

        Parameter(
            name="likelihood_vaild",
            native_keys=["ontology.likelihood_vaild"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        Parameter(
            name="onto_likelihood_epochs",
            native_keys=["ontology.onto_likelihood_epochs"],
            datatype=ParameterType.integer,
            default_value=5,
            required=False,
        ),

        Parameter(
            name="likelihood_slice",
            native_keys=["ontology.likelihood_slice"],
            datatype=ParameterType.integer,
            default_value=10,
            required=False,
        ),

        # ==================================================================
        # Sampling
        # ==================================================================

        Parameter(
            name="neg_sampling",
            native_keys=["sampling.neg_sampling"],
            datatype=ParameterType.string,
            default_value="truncated",
            required=False,
        ),

        Parameter(
            name="neg_triple_num",
            native_keys=["sampling.neg_triple_num"],
            datatype=ParameterType.integer,
            default_value=10,
            required=False,
        ),

        Parameter(
            name="truncated_epsilon",
            native_keys=["sampling.truncated_epsilon"],
            datatype=ParameterType.string,
            default_value="0.9",
            required=False,
        ),

        Parameter(
            name="alignment_neg_sampling",
            native_keys=["sampling.alignment_neg_sampling"],
            datatype=ParameterType.string,
            default_value="type_based",
            required=False,
            allowed_values=["type_based", "random"],
        ),

        Parameter(
            name="pos_margin",
            native_keys=["sampling.pos_margin"],
            datatype=ParameterType.string,
            default_value="0.01",
            required=False,
        ),

        Parameter(
            name="neg_margin",
            native_keys=["sampling.neg_margin"],
            datatype=ParameterType.string,
            default_value="2.0",
            required=False,
        ),

        Parameter(
            name="neg_margin_balance",
            native_keys=["sampling.neg_margin_balance"],
            datatype=ParameterType.string,
            default_value="0.2",
            required=False,
        ),

        # ==================================================================
        # Training
        # ==================================================================

        Parameter(
            name="optimizer",
            native_keys=["training.optimizer"],
            datatype=ParameterType.string,
            default_value="Adagrad",
            required=False,
            allowed_values=["Adagrad"],
        ),

        Parameter(
            name="learning_rate",
            native_keys=["training.learning_rate"],
            datatype=ParameterType.string,
            default_value="0.01",
            required=False,
        ),

        Parameter(
            name="cv_link_lr",
            native_keys=["training.cv_link_lr"],
            datatype=ParameterType.string,
            default_value="0.001",
            required=False,
        ),

        Parameter(
            name="likelihood_lr",
            native_keys=["training.likelihood_lr"],
            datatype=ParameterType.string,
            default_value="0.001",
            required=False,
        ),

        Parameter(
            name="max_epoch",
            native_keys=["training.max_epoch"],
            datatype=ParameterType.integer,
            default_value=2000,
            required=False,
        ),

        Parameter(
            name="sub_epoch",
            native_keys=["training.sub_epoch"],
            datatype=ParameterType.integer,
            default_value=10,
            required=False,
        ),

        Parameter(
            name="align_sub_epoch",
            native_keys=["training.align_sub_epoch"],
            datatype=ParameterType.integer,
            default_value=5,
            required=False,
        ),

        Parameter(
            name="batch_size",
            native_keys=["training.batch_size"],
            datatype=ParameterType.integer,
            default_value=4500,
            required=False,
        ),

        Parameter(
            name="onto_batch_size",
            native_keys=["training.onto_batch_size"],
            datatype=ParameterType.integer,
            default_value=64,
            required=False,
        ),

        Parameter(
            name="cvlink_batch_size",
            native_keys=["training.cvlink_batch_size"],
            datatype=ParameterType.integer,
            default_value=2000,
            required=False,
        ),

        # ==================================================================
        # Evaluation
        # ==================================================================

        Parameter(
            name="start_valid",
            native_keys=["evaluation.start_valid"],
            datatype=ParameterType.integer,
            default_value=50,
            required=False,
        ),

        Parameter(
            name="eval_freq",
            native_keys=["evaluation.eval_freq"],
            datatype=ParameterType.integer,
            default_value=10,
            required=False,
        ),

        Parameter(
            name="stop_metric",
            native_keys=["evaluation.stop_metric"],
            datatype=ParameterType.string,
            default_value="hits1",
            required=False,
            allowed_values=["hits1", "mrr"],
        ),

        Parameter(
            name="eval_metric",
            native_keys=["evaluation.eval_metric"],
            datatype=ParameterType.string,
            default_value="inner",
            required=False,
            allowed_values=["inner"],
        ),

        Parameter(
            name="eval_norm",
            native_keys=["evaluation.eval_norm"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),

        Parameter(
            name="csls",
            native_keys=["evaluation.csls"],
            datatype=ParameterType.integer,
            default_value=10,
            required=False,
        ),

        Parameter(
            name="top_k",
            native_keys=["evaluation.top_k"],
            datatype=ParameterType.string,
            default_value="1,5,10,50",
            required=False,
        ),

        # ==================================================================
        # Output
        # ==================================================================

        Parameter(
            name="keep_embeddings",
            native_keys=["output.keep_embeddings"],
            datatype=ParameterType.boolean,
            default_value=True,
            required=False,
        ),
    ]


ontoea_entity_alignment_config = ConfigurationDefinition(
    name="ontoea_entity_alignment",
    description="Ontology-guided entity alignment with OntoEA",
    parameters=_ontoea_parameters(),
)


_ONTOEA_FLOAT_KEYS = {"alpha", "beta", "gamma", "sigma", "truncated_epsilon", "pos_margin", "neg_margin", "neg_margin_balance", "learning_rate", "cv_link_lr", "likelihood_lr"}
_ONTOEA_LIST_KEYS = {"top_k"}
_ONTOEA_NULLABLE_KEYS = {"fusion_way", "cvlink_module", "onto_neg_sampling"}


def _build_ontoea_config(config: ConfigurationProfile) -> str:
    sections: dict[str, dict] = {}
    for param in _ontoea_parameters():
        try:
            value = config.get_parameter_value(param.name)
        except (ValueError, KeyError):
            value = param.default_value

        if value is None:
            if param.required:
                raise ValueError(f"'{param.name}' is required")
            continue

        if param.name in _ONTOEA_FLOAT_KEYS:
            value = float(value)
        elif param.name in _ONTOEA_LIST_KEYS:
            value = [int(v) for v in value.split(",") if v.strip()] if isinstance(value, str) else list(value)
        elif param.name in _ONTOEA_NULLABLE_KEYS and isinstance(value, str) and value.strip().lower() == "null":
            value = None

        section, key = param.native_keys[0].split(".", 1)
        sections.setdefault(section, {})[key] = value

    return yaml.safe_dump(sections, sort_keys=False, default_flow_style=False)


def ontoea_entity_alignment(
    inputs: TaskInput,
    outputs: TaskOutput,
    config: ConfigurationProfile,
):
    Path(outputs["output"].path).mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ontoea_") as tmp:
        config_host_path = Path(tmp) / "config.yaml"
        config_host_path.write_text(_build_ontoea_config(config), encoding="utf-8")

        config_data = Data(str(config_host_path), BasicDataFormats.ANY)

        all_data = list(inputs.values()) + list(outputs.values()) + [config_data]
        volumes, host_to_container = get_docker_volume_bindings(all_data)

        def remap(data):
            return str(remap_data_path_for_container(data, host_to_container).path)

        command = [
            "bash", "ontoea.sh",
            remap(inputs["benchmark"]),
            remap(outputs["output"]),
            remap(config_data),
        ]

        client = docker_client(
            image="kgt/ontoea:latest",
            command=command,
            volumes=volumes,
        )

        result = client()

ontoea_entity_alignment_task = KgTask(
    name="ontoea_entity_alignment",
    description="Ontology-guided entity alignment with OntoEA",
    input_spec=_ONTOEA_INPUT_SPEC,
    output_spec=_ONTOEA_OUTPUT_SPEC,
    function=ontoea_entity_alignment,
    config_spec=ontoea_entity_alignment_config,
    category=[BasicTaskCategoryCatalog.entity_matching],
    tools=["ontoea"],
)


Registry.add_task(
    ontoea_entity_alignment_task.name,
    ontoea_entity_alignment_task,
)
