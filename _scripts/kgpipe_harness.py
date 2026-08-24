"""Run a KGpipe task test case: inputs, outputs, optional config."""

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from kgpipe_catalog import discover_test_cases  # noqa: E402


def _import_kgpipe():
    try:
        from kgpipe.common import Data, Registry
        from kgpipe.common.model.configuration import (
            ConfigurationProfile,
            ParameterBinding,
        )
    except ImportError as exc:
        raise ImportError(
            "KGpipe is required to execute task tests. Install it, then retry."
        ) from exc
    return Data, Registry, ConfigurationProfile, ParameterBinding


def import_tool_task_modules():
    import importlib.util

    from catalog_util import TOOLS_DIR

    for path in sorted(TOOLS_DIR.glob("*/kgpipe/*.py")):
        if path.parent.parent.name == "_template":
            continue
        module_name = "kgtools_{}_{}".format(path.parent.parent.name, path.stem)
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)


def resolve_case_path(case, relative):
    path = Path(relative)
    if path.is_absolute():
        return path
    return (case["path"].parent / path).resolve()


def profile_from_mapping(config_spec, values):
    Data, Registry, ConfigurationProfile, ParameterBinding = _import_kgpipe()
    del Data, Registry
    by_name = {parameter.name: parameter for parameter in config_spec.parameters}
    bindings = []
    for name, value in (values or {}).items():
        if name not in by_name:
            raise KeyError(
                "Unknown config parameter '{}' for spec '{}'".format(
                    name, config_spec.name
                )
            )
        bindings.append(ParameterBinding(parameter=by_name[name], value=value))
    return ConfigurationProfile(
        name=config_spec.name,
        definition=config_spec,
        bindings=bindings,
    )


def _same_artifact(actual, expected):
    if expected.suffix.lower() == ".json" or actual.suffix.lower() == ".json":
        actual_data = json.loads(actual.read_text(encoding="utf-8"))
        expected_data = json.loads(expected.read_text(encoding="utf-8"))
        if actual_data != expected_data:
            raise AssertionError(
                "JSON output mismatch for {}\n actual: {}\n expected: {}".format(
                    actual.name, actual_data, expected_data
                )
            )
        return
    if actual.read_bytes() != expected.read_bytes():
        raise AssertionError("Output mismatch for {}".format(actual.name))


def run_case(case, tmp_path):
    """Execute one YAML case against its KgTask using inputs, outputs, and config."""
    Data, Registry, ConfigurationProfile, ParameterBinding = _import_kgpipe()
    del ConfigurationProfile, ParameterBinding
    import_tool_task_modules()
    try:
        task = Registry.get_task(case["task"])
    except KeyError as exc:
        raise KeyError("Task '{}' is not registered".format(case["task"])) from exc

    named_inputs = {}
    for slot, relative in case["inputs"].items():
        if slot not in task.input_spec:
            raise KeyError(
                "Input slot '{}' is not in {} input_spec".format(slot, task.name)
            )
        source = resolve_case_path(case, relative)
        if not source.is_file():
            raise FileNotFoundError("Missing input {}: {}".format(slot, source))
        named_inputs[slot] = Data(source, task.input_spec[slot])

    named_outputs = {}
    expected_by_slot = {}
    for slot, relative in case["outputs"].items():
        if slot not in task.output_spec:
            raise KeyError(
                "Output slot '{}' is not in {} output_spec".format(slot, task.name)
            )
        expected = resolve_case_path(case, relative)
        actual = Path(tmp_path) / slot / expected.name
        actual.parent.mkdir(parents=True, exist_ok=True)
        named_outputs[slot] = Data(actual, task.output_spec[slot])
        expected_by_slot[slot] = expected

    if task.config_spec is not None:
        profile = profile_from_mapping(task.config_spec, case.get("config") or {})
        task.function(named_inputs, named_outputs, config=profile)
    else:
        if case.get("config"):
            raise ValueError(
                "Case provides config but task '{}' has no config_spec".format(task.name)
            )
        task.function(named_inputs, named_outputs)

    for slot, expected in expected_by_slot.items():
        actual = named_outputs[slot].path
        if not actual.exists():
            raise AssertionError(
                "Task '{}' did not write output slot '{}' to {}".format(
                    task.name, slot, actual
                )
            )
        if expected.is_file():
            _same_artifact(actual, expected)


def pytest_cases():
    return discover_test_cases()
