import os
import tempfile

import pytest

from kgpipe.common import Data, DataFormat
from kgpipe.common.model.configuration import ConfigurationProfile, ParameterBinding

from splink_tasks import splink_entity_matching_task, splink_entity_matching_config


def _write_csv(path, header: list[str], rows: list[list[str]], sep: str = ",") -> None:
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
def splink_csv_inputs(tmp_path):
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
    data_output = Data(task_output_path, DataFormat.JSON)

    report = task.run(
        [data_source, data_target],
        [data_output],
        configProfile=config,
        stable_files_override=True,
    )

    return report, task_output_path


def test_splink_entity_matching_produces_output(csv_inputs):
    source_path, target_path = csv_inputs
    config = _build_profile(splink_entity_matching_config, overrides={
        "raw_comparisons": """
    - output_column_name: name
      input_columns: [name]
      comparison_type: jaro_winkler
      params:
        score_threshold_or_thresholds: [0.95, 0.9, 0.8]
        term_frequency_adjustments: true

    - output_column_name: city
      input_columns: [city]
      comparison_type: jaccard
      params:
        score_threshold_or_thresholds: [0.9, 0.7]
        term_frequency_adjustments: true
    """,
        "estimate_u_using_random_sampling_enabled": True,
        "estimate_u_max_pairs": 1000000,

        "estimate_parameters_using_em_enabled": True,
        "em_blocking_rule": "l.name = r.name",
    })
    report, task_output_path = _run_matching_task(
        splink_entity_matching_task, source_path, target_path, config=config
    )

    assert report is not None
    assert os.path.exists(task_output_path)
    assert os.path.getsize(task_output_path) > 0
