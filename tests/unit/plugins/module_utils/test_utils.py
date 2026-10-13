# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import json
from datetime import date
from datetime import datetime
from typing import Union

import pytest
from ansible_collections.amazon.ai.plugins.module_utils.utils import camel_dict_to_snake_dict_keeping
from ansible_collections.amazon.ai.plugins.module_utils.utils import config_block_differs
from ansible_collections.amazon.ai.plugins.module_utils.utils import convert_time_ranges
from ansible_collections.amazon.ai.plugins.module_utils.utils import encode_body
from ansible_collections.amazon.ai.plugins.module_utils.utils import merge_data
from ansible_collections.amazon.ai.plugins.module_utils.utils import normalize_url
from ansible_collections.amazon.ai.plugins.module_utils.utils import snake_dict_to_camel_dict_keeping
from ansible_collections.amazon.ai.plugins.module_utils.utils import stringify_values


# -----------------------
# Tests for encode_body
# -----------------------
@pytest.mark.parametrize(
    "input_value,expected_bytes",
    [
        ({"key": "value"}, json.dumps({"key": "value"}).encode("utf-8")),
        ([1, 2, 3], json.dumps([1, 2, 3]).encode("utf-8")),
        ("hello", b"hello"),
    ],
)
def test_encode_body_valid(input_value: Union[dict, list, str], expected_bytes: bytes):
    assert encode_body(input_value) == expected_bytes


def test_encode_body_invalid_type():
    with pytest.raises(TypeError, match="body must be a dict, list, or string"):
        encode_body(123)  # Invalid type


# --------------------
# Tests for merge_data
# --------------------
@pytest.mark.parametrize(
    "target, source, expected",
    [
        ({"a": 1, "b": 2}, {"b": 3, "c": 4}, {"a": 1, "b": 3, "c": 4}),
        ([{"a": 1}, {"b": 2}], {"c": 3}, [{"a": 1, "c": 3}, {"b": 2, "c": 3}]),
        ({}, {"x": 1}, {"x": 1}),
        ([], {"x": 1}, []),
    ],
)
def test_merge_data(target, source, expected):
    merge_data(target, source)
    assert target == expected


# -----------------------
# Tests for normalize_url
# -----------------------
@pytest.mark.parametrize(
    "url,expected",
    [
        (
            "https://github.com/ansible/repo.git",
            "https://github.com/ansible/repo.git",
        ),
        (
            "https://github.com/ansible/repo.git/",
            "https://github.com/ansible/repo.git",
        ),
        (
            "https://github.com/ansible/repo.git///",
            "https://github.com/ansible/repo.git",
        ),
        (
            "https://GITHUB.com/ansible/repo.git",
            "https://github.com/ansible/repo.git",
        ),
        (
            "HTTPS://github.com/ansible/repo.git",
            "https://github.com/ansible/repo.git",
        ),
        (
            "HTTPS://GITHUB.COM/ansible/repo.git/",
            "https://github.com/ansible/repo.git",
        ),
        (
            "https://github.com/Ansible/Repo.git",
            "https://github.com/Ansible/Repo.git",
        ),
        (
            "ssh://git@github.com/ansible/repo.git",
            "ssh://git@github.com/ansible/repo.git",
        ),
    ],
    ids=[
        "no-change",
        "trailing-slash",
        "multiple-trailing-slashes",
        "mixed-case-host",
        "mixed-case-scheme",
        "all-normalizations",
        "path-case-preserved",
        "ssh-scheme",
    ],
)
def test_normalize_url(url, expected):
    assert normalize_url(url) == expected


# -----------------------------
# Tests for convert_time_ranges
# -----------------------------
@pytest.mark.parametrize(
    "status_filter,expected_from,expected_to",
    [
        (
            # AWS-style string keys
            {"Any": {"Type": "REACTIVE", "StartTimeRange": {"FromTime": "2025-02-10", "ToTime": "2025-02-12"}}},
            datetime(2025, 2, 10),
            datetime(2025, 2, 12, 0, 0, 0),
        ),
        (
            # Ansible-style string keys
            {"Any": {"Type": "PROACTIVE", "start_time_range": {"from_time": "2024-01-01", "to_time": "2024-01-02"}}},
            datetime(2024, 1, 1),
            datetime(2024, 1, 2, 0, 0, 0),
        ),
        (
            # AWS-style date objects (YAML may parse dates)
            {"Any": {"Type": "REACTIVE", "StartTimeRange": {"FromTime": date(2025, 3, 1), "ToTime": date(2025, 3, 2)}}},
            datetime(2025, 3, 1),
            datetime(2025, 3, 2, 0, 0, 0),
        ),
    ],
)
def test_convert_time_ranges_valid(status_filter, expected_from, expected_to):
    """Test conversion of valid date strings and date objects into datetime objects."""
    result = convert_time_ranges(status_filter)

    # Explicitly pick the time range dict
    top_key = next(iter(result))
    time_range = result[top_key].get("StartTimeRange") or result[top_key].get("start_time_range")

    assert time_range is not None, "No time range found in result"

    from_time = time_range.get("FromTime") or time_range.get("from_time")
    to_time = time_range.get("ToTime") or time_range.get("to_time")

    assert isinstance(from_time, datetime)
    assert isinstance(to_time, datetime)
    assert from_time == expected_from
    assert to_time == expected_to


def test_convert_time_ranges_invalid_format():
    """Ensure ValueError is raised when date format is invalid."""
    invalid_filter = {"Any": {"StartTimeRange": {"FromTime": "02/10/2025", "ToTime": "2025-02-12"}}}

    with pytest.raises(ValueError, match=r"Invalid date format for '02/10/2025'"):
        convert_time_ranges(invalid_filter)


def test_convert_time_ranges_no_time_keys():
    """If no time keys are present, the function should return unchanged input."""
    no_time_filter = {"Any": {"Type": "REACTIVE"}}
    original_id = id(no_time_filter)
    result = convert_time_ranges(no_time_filter)

    # Should return the same object (mutated in-place)
    assert result is no_time_filter
    assert result == {"Any": {"Type": "REACTIVE"}}


def test_convert_time_ranges_multiple_top_keys():
    """Ensure all nested time ranges in multiple top-level keys are converted correctly."""
    multi_filter = {
        "Any": {"Type": "REACTIVE", "StartTimeRange": {"FromTime": "2025-02-10", "ToTime": "2025-02-12"}},
        "Some": {"Type": "PROACTIVE", "start_time_range": {"from_time": "2024-01-01", "to_time": "2024-01-02"}},
    }

    expected_values = {
        "Any": (datetime(2025, 2, 10), datetime(2025, 2, 12, 0, 0, 0)),
        "Some": (datetime(2024, 1, 1), datetime(2024, 1, 2, 0, 0, 0)),
    }

    result = convert_time_ranges(multi_filter)

    for top_key, (expected_from, expected_to) in expected_values.items():
        time_range = result[top_key].get("StartTimeRange") or result[top_key].get("start_time_range")
        assert time_range is not None, f"No time range found for key '{top_key}'"

        from_time = time_range.get("FromTime") or time_range.get("from_time")
        to_time = time_range.get("ToTime") or time_range.get("to_time")

        assert isinstance(from_time, datetime)
        assert isinstance(to_time, datetime)
        assert from_time == expected_from
        assert to_time == expected_to


def test_convert_time_ranges_edge_cases():
    """Test edge cases with partially defined time ranges and mixed key types."""
    edge_case_filter = {
        "Any": {"Type": "REACTIVE", "StartTimeRange": {"FromTime": "2025-02-10", "ToTime": "2025-02-12"}},
        "Some": {"Type": "PROACTIVE", "start_time_range": {"from_time": "2024-01-01"}},  # missing to_time
        "None": {"Type": "REACTIVE"},  # no time range
        "Mixed": {"Type": "PROACTIVE", "EndTimeRange": {"ToTime": "2023-05-05"}},  # only ToTime
    }

    expected_results = {
        "Any": (datetime(2025, 2, 10), datetime(2025, 2, 12, 0, 0, 0)),
        "Some": (datetime(2024, 1, 1), None),
        "None": (None, None),
        "Mixed": (None, datetime(2023, 5, 5, 0, 0, 0)),
    }

    result = convert_time_ranges(edge_case_filter)

    for top_key, (expected_from, expected_to) in expected_results.items():
        time_range = (
            result[top_key].get("StartTimeRange")
            or result[top_key].get("start_time_range")
            or result[top_key].get("EndTimeRange")
            or result[top_key].get("end_time_range")
        )

        if expected_from is None and expected_to is None:
            assert time_range in (None, {}), f"Unexpected time range for key '{top_key}'"
            continue

        from_time = time_range.get("FromTime") or time_range.get("from_time")
        to_time = time_range.get("ToTime") or time_range.get("to_time")

        if expected_from is not None:
            assert isinstance(from_time, datetime)
            assert from_time == expected_from
        else:
            assert from_time is None

        if expected_to is not None:
            assert isinstance(to_time, datetime)
            assert to_time == expected_to
        else:
            assert to_time is None


# -----------------------------
# Tests for config_block_differs
# -----------------------------
@pytest.mark.parametrize(
    "existing,desired,expected",
    [
        ({"A": {"B": 1, "C": ["x", "y"]}}, {"A": {"B": 1, "C": ["x", "y"]}}, False),
        ({"A": 1, "B": 2}, {"A": 1}, True),
        ({"A": 1}, {"A": 1, "B": 2}, True),
        ({"A": 1}, {"A": 2}, True),
        ({"A": {"B": 1}}, {"A": {"B": 2}}, True),
        ({"A": ["x", "y"]}, {"A": ["y", "x"]}, True),
        ({"A": ["x"]}, {"A": ["x", "y"]}, True),
        (None, {"A": 1}, True),
        (None, {}, True),
        ({}, {}, False),
        ({"A": 1}, {}, True),
    ],
)
def test_config_block_differs(existing, desired, expected):
    assert config_block_differs(existing, desired) is expected


# ----------------------------------------------------
# Tests for snake_dict_to_camel_dict_keeping / reverse
# ----------------------------------------------------
SNAKE_BLOCK = {
    "jupyter_lab_app_image_config": {
        "container_config": {
            "container_arguments": ["a"],
            "container_environment_variables": {"my_var": "v", "MyOther": "w"},
        },
        "file_system_config": {"default_uid": 1000},
    },
    "kernel_specs": [{"name": "python3", "display_name": "Py"}],
}
CAMEL_BLOCK = {
    "JupyterLabAppImageConfig": {
        "ContainerConfig": {
            "ContainerArguments": ["a"],
            "ContainerEnvironmentVariables": {"my_var": "v", "MyOther": "w"},
        },
        "FileSystemConfig": {"DefaultUid": 1000},
    },
    "KernelSpecs": [{"Name": "python3", "DisplayName": "Py"}],
}


def test_snake_dict_to_camel_dict_keeping_preserves_kept_subtree():
    result = snake_dict_to_camel_dict_keeping(SNAKE_BLOCK, ["container_environment_variables"])
    assert result == CAMEL_BLOCK


def test_camel_dict_to_snake_dict_keeping_preserves_kept_subtree():
    result = camel_dict_to_snake_dict_keeping(CAMEL_BLOCK, ["container_environment_variables"])
    assert result == SNAKE_BLOCK


def test_keeping_without_keep_keys_converts_everything():
    assert snake_dict_to_camel_dict_keeping({"a_b": {"c_d": 1}}, []) == {"AB": {"CD": 1}}
    assert camel_dict_to_snake_dict_keeping({"AbC": {"CdE": 1}}, []) == {"ab_c": {"cd_e": 1}}


def test_stringify_values():
    assert stringify_values({"a": True, "b": False, "c": 8080, "d": 1.5, "E_f": "x"}) == {
        "a": "true",
        "b": "false",
        "c": "8080",
        "d": "1.5",
        "E_f": "x",
    }
