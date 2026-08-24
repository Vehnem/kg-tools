import os
import tempfile

import pytest

from kgpipe.common import Data, DataFormat
from kgpipe.common.model.configuration import ConfigurationProfile, ParameterBinding

from jedai_tasks import (
    jedai_syntactic_matching_task,
    jedai_semantic_matching_task,
    jedai_syntactic_matching_config,
    jedai_semantic_matching_config,
)


def _write_csv(path, header: list[str], rows: list[list[str]], sep: str = "|") -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(sep.join(header) + "\n")
        for row in rows:
            f.write(sep.join(row) + "\n")


def _build_profile(definition, overrides: dict) -> ConfigurationProfile:
    bindings = [
        ParameterBinding(
            parameter=param,
            value=overrides.get(param.name, param.default_value),
        )
        for param in definition.parameters
    ]
    return ConfigurationProfile(
        name=f"{definition.name}_test_profile",
        definition=definition,
        bindings=bindings,
    )


@pytest.fixture
def jedai_csv_inputs(tmp_path):
    source_path = tmp_path / "source.csv"
    target_path = tmp_path / "target.csv"

    _write_csv(
        source_path,
        ["id", "name", "city"],
        [
            ["1", "Acme Corp", "Berlin"],
            ["2", "Foo GmbH", "Munich"],
        ],
    )
    _write_csv(
        target_path,
        ["id", "name", "city"],
        [
            ["a", "Acme Corporation", "Berlin"],
            ["b", "Foo GmbH", "Muenchen"],
        ],
    )
    return source_path, target_path


def _run_matching_task(task, source_path, target_path, config: ConfigurationProfile):
    output_dir = tempfile.mkdtemp()
    task_output_path = os.path.join(output_dir, "output.json")

    data_source = Data(str(source_path), DataFormat.CSV)
    data_target = Data(str(target_path), DataFormat.CSV)
    data_output = Data(task_output_path, DataFormat.ER_JSON)

    report = task.run(
        [data_source, data_target],
        [data_output],
        configProfile=config,
        stable_files_override=True,
    )

    return report, task_output_path


def test_jedai_syntactic_matching_produces_output(jedai_csv_inputs):
    source_path, target_path = jedai_csv_inputs
    config = _build_profile(jedai_syntactic_matching_config, overrides={})

    report, task_output_path = _run_matching_task(
        jedai_syntactic_matching_task, source_path, target_path, config=config
    )

    assert report is not None
    assert os.path.exists(task_output_path)
    assert os.path.getsize(task_output_path) > 0


def test_jedai_semantic_matching_produces_output(jedai_csv_inputs):
    source_path, target_path = jedai_csv_inputs
    config = _build_profile(jedai_semantic_matching_config, overrides={})

    report, task_output_path = _run_matching_task(
        jedai_semantic_matching_task, source_path, target_path, config=config
    )

    assert report is not None
    assert os.path.exists(task_output_path)
    assert os.path.getsize(task_output_path) > 0


def test_jedai_syntactic_matching_with_custom_config(tmp_path):
    source_path = tmp_path / "source.csv"
    target_path = tmp_path / "target.csv"

    _write_csv(
        source_path,
        ["id", "name", "city"],
        [
            ["1", "Acme Corp", "Berlin"],
            ["2", "Foo GmbH", "Munich"],
        ],
        sep=",",
    )
    _write_csv(
        target_path,
        ["id", "name", "city"],
        [
            ["a", "Acme Corporation", "Berlin"],
            ["b", "Foo GmbH", "Muenchen"],
        ],
        sep=",",
    )

    config = _build_profile(
        jedai_syntactic_matching_config,
        overrides={
            "csv_separator": ",",
            "attributes_1": "name",
            "attributes_2": "name",
            "blocking_method": "qgrams_blocking",
            "blocking_qgrams": 4,
            "comparison_cleaning_enabled": True,
            "comparison_cleaning_method": "cardinality_edge_pruning",
            "weighting_scheme": "JS",
            "tokenizer": "word_tokenizer",
            "qgram": 1,
            "similarity_threshold": 0.9,
        },
    )

    report, task_output_path = _run_matching_task(
        jedai_syntactic_matching_task, source_path, target_path, config=config
    )

    assert report is not None
    assert os.path.exists(task_output_path)
    assert os.path.getsize(task_output_path) > 0