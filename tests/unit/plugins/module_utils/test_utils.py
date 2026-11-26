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
from ansible_collections.amazon.ai.plugins.module_utils.utils import feature_group_has_store
from ansible_collections.amazon.ai.plugins.module_utils.utils import feature_group_in_memory_violations
from ansible_collections.amazon.ai.plugins.module_utils.utils import feature_group_properties_to_update
from ansible_collections.amazon.ai.plugins.module_utils.utils import feature_group_status_decision
from ansible_collections.amazon.ai.plugins.module_utils.utils import feature_group_wait_timeout
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


# -------------------------------------------
# Tests for feature_group_properties_to_update
# -------------------------------------------
EXISTING_FEATURE_GROUP = {
    "feature_group_name": "fg",
    "record_identifier_feature_name": "id",
    "event_time_feature_name": "ts",
    "description": "probe",
    "role_arn": "arn:aws:iam::123456789012:role/fg",
    "feature_definitions": [
        {"feature_name": "id", "feature_type": "String"},
        {"feature_name": "ts", "feature_type": "Fractional"},
        {
            "feature_name": "embedding",
            "feature_type": "Fractional",
            "collection_type": "Vector",
            "collection_config": {"vector_config": {"dimension": 4}},
        },
    ],
    "online_store_config": {
        "enable_online_store": True,
        "storage_type": "Standard",
        "ttl_duration": {"unit": "Hours", "value": 2},
    },
    "offline_store_config": {
        "s3_storage_config": {"s3_uri": "s3://bucket/fg", "resolved_output_s3_uri": "s3://bucket/fg/data"},
        "disable_glue_table_creation": True,
    },
    "throughput_config": {"throughput_mode": "OnDemand"},
}


def _desired(**overrides):
    desired = {
        "feature_group_name": "fg",
        "record_identifier_feature_name": "id",
        "event_time_feature_name": "ts",
        "feature_definitions": [dict(feature) for feature in EXISTING_FEATURE_GROUP["feature_definitions"]],
        "online_store_config": {"enable_online_store": True, "ttl_duration": {"unit": "Hours", "value": 2}},
        "offline_store_config": {"s3_storage_config": {"s3_uri": "s3://bucket/fg"}},
    }
    desired.update(overrides)
    return desired


def test_feature_group_no_difference():
    assert feature_group_properties_to_update(EXISTING_FEATURE_GROUP, _desired()) == {}


def test_feature_group_unset_options_are_ignored():
    assert feature_group_properties_to_update(EXISTING_FEATURE_GROUP, {"feature_group_name": "fg"}) == {}


def test_feature_group_new_feature():
    features = _desired()["feature_definitions"] + [{"feature_name": "extra", "feature_type": "String"}]
    result = feature_group_properties_to_update(EXISTING_FEATURE_GROUP, _desired(feature_definitions=features))
    assert result == {"feature_additions": [{"feature_name": "extra", "feature_type": "String"}]}


@pytest.mark.parametrize(
    "feature",
    [
        {"feature_name": "ts", "feature_type": "String"},
        {"feature_name": "embedding", "feature_type": "Fractional", "collection_type": "List"},
        {
            "feature_name": "embedding",
            "feature_type": "Fractional",
            "collection_config": {"vector_config": {"dimension": 8}},
        },
    ],
)
def test_feature_group_changed_feature(feature):
    features = [f for f in _desired()["feature_definitions"] if f["feature_name"] != feature["feature_name"]]
    desired = _desired(feature_definitions=features + [feature])
    with pytest.raises(ValueError, match="feature_definitions"):
        feature_group_properties_to_update(EXISTING_FEATURE_GROUP, desired)


def test_feature_group_removed_feature():
    features = _desired()["feature_definitions"][:2]
    desired = _desired(feature_definitions=features)
    with pytest.raises(ValueError, match="cannot be removed"):
        feature_group_properties_to_update(EXISTING_FEATURE_GROUP, desired)


def test_feature_group_ttl_changed():
    online = {"ttl_duration": {"unit": "Days", "value": 1}}
    result = feature_group_properties_to_update(EXISTING_FEATURE_GROUP, _desired(online_store_config=online))
    assert result == {"online_store_config": {"ttl_duration": {"unit": "Days", "value": 1}}}


def test_feature_group_storage_type_standard_to_v2():
    online = {"storage_type": "Standard_V2"}
    result = feature_group_properties_to_update(EXISTING_FEATURE_GROUP, _desired(online_store_config=online))
    assert result == {"online_store_config": {"storage_type": "Standard_V2"}}


def test_feature_group_storage_type_other_transition():
    desired = _desired(online_store_config={"storage_type": "InMemory"})
    with pytest.raises(ValueError, match="storage_type"):
        feature_group_properties_to_update(EXISTING_FEATURE_GROUP, desired)


@pytest.mark.parametrize(
    "online",
    [{"enable_online_store": False}, {"security_config": {"kms_key_id": "alias/key"}}],
)
def test_feature_group_online_store_create_only(online):
    desired = _desired(online_store_config=online)
    with pytest.raises(ValueError, match="online_store_config"):
        feature_group_properties_to_update(EXISTING_FEATURE_GROUP, desired)


def test_feature_group_online_store_added_to_offline_only_group():
    existing = {key: value for key, value in EXISTING_FEATURE_GROUP.items() if key != "online_store_config"}
    desired = {"online_store_config": {"ttl_duration": {"unit": "Days", "value": 1}}}
    with pytest.raises(ValueError, match="online_store_config"):
        feature_group_properties_to_update(existing, desired)


def test_feature_group_throughput_only_differing_fields():
    existing = dict(
        EXISTING_FEATURE_GROUP,
        throughput_config={
            "throughput_mode": "Provisioned",
            "provisioned_read_capacity_units": 1,
            "provisioned_write_capacity_units": 1,
        },
    )
    desired = {
        "throughput_config": {
            "throughput_mode": "Provisioned",
            "provisioned_read_capacity_units": 1,
            "provisioned_write_capacity_units": 2,
        }
    }
    assert feature_group_properties_to_update(existing, desired) == {
        "throughput_config": {"provisioned_write_capacity_units": 2}
    }


def test_feature_group_throughput_switch_to_provisioned_sends_all():
    existing = dict(EXISTING_FEATURE_GROUP, throughput_config={"throughput_mode": "OnDemand"})
    throughput = {
        "throughput_mode": "Provisioned",
        "provisioned_read_capacity_units": 1,
        "provisioned_write_capacity_units": 1,
    }
    assert feature_group_properties_to_update(existing, {"throughput_config": throughput}) == {
        "throughput_config": throughput
    }


def test_feature_group_throughput_switch_to_on_demand():
    existing = dict(
        EXISTING_FEATURE_GROUP,
        throughput_config={
            "throughput_mode": "Provisioned",
            "provisioned_read_capacity_units": 1,
            "provisioned_write_capacity_units": 1,
        },
    )
    result = feature_group_properties_to_update(existing, {"throughput_config": {"throughput_mode": "OnDemand"}})
    assert result == {"throughput_config": {"throughput_mode": "OnDemand"}}


@pytest.mark.parametrize(
    "option,value",
    [
        ("record_identifier_feature_name", "other"),
        ("event_time_feature_name", "other"),
        ("description", "changed"),
        ("role_arn", "arn:aws:iam::123456789012:role/other"),
        ("offline_store_config", {"s3_storage_config": {"s3_uri": "s3://other/fg"}}),
    ],
)
def test_feature_group_create_only_property_changed(option, value):
    desired = _desired(**{option: value})
    with pytest.raises(ValueError, match=option):
        feature_group_properties_to_update(EXISTING_FEATURE_GROUP, desired)


@pytest.mark.parametrize(
    "wait_timeout, storage_type, expected",
    [
        (None, None, 600),
        (None, "Standard", 600),
        (None, "InMemory", 1200),
        (300, "InMemory", 300),
        (300, None, 300),
    ],
)
def test_feature_group_wait_timeout(wait_timeout, storage_type, expected):
    assert feature_group_wait_timeout(wait_timeout, storage_type) == expected


@pytest.mark.parametrize(
    "desired, expected",
    [
        ({}, False),
        ({"online_store_config": {"storage_type": "Standard"}}, False),
        ({"online_store_config": {"enable_online_store": False}}, False),
        ({"online_store_config": {"enable_online_store": True}}, True),
        ({"offline_store_config": {"s3_storage_config": {"s3_uri": "s3://b/p"}}}, True),
        (
            {"online_store_config": {"storage_type": "Standard"}, "offline_store_config": {"s3_storage_config": {}}},
            True,
        ),
    ],
)
def test_feature_group_has_store(desired, expected):
    assert feature_group_has_store(desired) is expected


IN_MEMORY = {"enable_online_store": True, "storage_type": "InMemory"}


@pytest.mark.parametrize(
    "desired, expected_options",
    [
        ({}, []),
        ({"online_store_config": {"enable_online_store": True, "storage_type": "Standard"}}, []),
        (
            {
                "online_store_config": {"storage_type": "Standard", "security_config": {"kms_key_id": "k"}},
                "offline_store_config": {"s3_storage_config": {"s3_uri": "s3://b/p"}},
                "throughput_config": {"throughput_mode": "Provisioned"},
            },
            [],
        ),
        ({"online_store_config": IN_MEMORY}, []),
        ({"online_store_config": IN_MEMORY, "throughput_config": {"throughput_mode": "OnDemand"}}, []),
        (
            {"online_store_config": IN_MEMORY, "offline_store_config": {"s3_storage_config": {}}},
            ["offline_store_config"],
        ),
        (
            {"online_store_config": dict(IN_MEMORY, security_config={"kms_key_id": "k"})},
            ["security_config.kms_key_id"],
        ),
        ({"online_store_config": IN_MEMORY, "throughput_config": {"throughput_mode": "Provisioned"}}, ["Provisioned"]),
        (
            {
                "online_store_config": dict(IN_MEMORY, security_config={"kms_key_id": "k"}),
                "offline_store_config": {"s3_storage_config": {}},
                "throughput_config": {"throughput_mode": "Provisioned"},
            },
            ["offline_store_config", "security_config.kms_key_id", "Provisioned"],
        ),
    ],
)
def test_feature_group_in_memory_violations(desired, expected_options):
    violations = feature_group_in_memory_violations(desired)
    assert len(violations) == len(expected_options)
    for violation, option in zip(violations, expected_options):
        assert option in violation


def test_feature_group_provisioned_throughput_on_existing_in_memory_group():
    existing = dict(EXISTING_FEATURE_GROUP, online_store_config=dict(IN_MEMORY))
    desired = {
        "throughput_config": {
            "throughput_mode": "Provisioned",
            "provisioned_read_capacity_units": 1,
            "provisioned_write_capacity_units": 1,
        }
    }
    with pytest.raises(ValueError, match="InMemory"):
        feature_group_properties_to_update(existing, desired)


def test_feature_group_remove_ttl_duration():
    result = feature_group_properties_to_update(
        EXISTING_FEATURE_GROUP, {"online_store_config": {"remove_ttl_duration": True}}
    )
    assert result == {"online_store_config": {"ttl_duration": {}}}


@pytest.mark.parametrize("clear", [True, False, None])
def test_feature_group_remove_ttl_duration_without_ttl_is_a_no_op(clear):
    online = {
        key: value for key, value in EXISTING_FEATURE_GROUP["online_store_config"].items() if key != "ttl_duration"
    }
    existing = dict(EXISTING_FEATURE_GROUP, online_store_config=online)
    desired = {"online_store_config": {"remove_ttl_duration": clear}}
    assert feature_group_properties_to_update(existing, desired) == {}


def test_feature_group_remove_ttl_duration_false_keeps_the_ttl():
    desired = {"online_store_config": {"remove_ttl_duration": False}}
    assert feature_group_properties_to_update(EXISTING_FEATURE_GROUP, desired) == {}


def test_feature_group_remove_ttl_duration_on_offline_only_group_is_a_no_op():
    existing = {key: value for key, value in EXISTING_FEATURE_GROUP.items() if key != "online_store_config"}
    desired = {"online_store_config": {"remove_ttl_duration": True}}
    assert feature_group_properties_to_update(existing, desired) == {}


# -------------------------------------------
# Tests for feature_group_status_decision
# -------------------------------------------
def _described(status, update_status=None, **extra):
    described = {"FeatureGroupStatus": status, **extra}
    if update_status:
        described["LastUpdateStatus"] = {"Status": update_status}
    return described


@pytest.mark.parametrize(
    "status, update_status, state, wait, check_mode, action, waiter, message",
    [
        # settled
        ("Created", None, "present", True, False, "proceed", None, None),
        ("Created", None, "absent", True, False, "proceed", None, None),
        ("Created", "Successful", "present", True, False, "proceed", None, None),
        ("Created", "Failed", "present", True, False, "proceed", None, None),
        # being deleted
        ("Deleting", None, "present", True, False, "fail", None, "is being deleted"),
        ("Deleting", None, "present", False, False, "fail", None, "is being deleted"),
        ("Deleting", None, "absent", True, False, "wait_and_exit", "feature_group_deleted", "already being deleted"),
        ("Deleting", None, "absent", False, False, "exit", None, "already being deleted"),
        ("Deleting", None, "absent", True, True, "exit", None, "already being deleted"),
        ("Deleting", "InProgress", "absent", True, False, "wait_and_exit", "feature_group_deleted", "already"),
        # being created
        ("Creating", None, "present", True, False, "wait", "feature_group_created", None),
        ("Creating", None, "absent", True, False, "wait", "feature_group_created", None),
        ("Creating", None, "present", False, False, "exit", None, "is being created"),
        ("Creating", None, "absent", False, False, "fail", None, "cannot be deleted while it is being created"),
        ("Creating", None, "present", True, True, "proceed", None, None),
        ("Creating", None, "absent", False, True, "proceed", None, None),
        # being updated
        ("Created", "InProgress", "present", True, False, "wait", "feature_group_updated", None),
        ("Created", "InProgress", "absent", True, False, "wait", "feature_group_updated", None),
        ("Created", "InProgress", "present", False, False, "exit", None, "is being updated"),
        ("Created", "InProgress", "absent", False, False, "fail", None, "cannot be deleted while it is being updated"),
        ("Created", "InProgress", "present", True, True, "proceed", None, None),
        # failed
        ("CreateFailed", None, "present", True, False, "fail", None, "CreateFailed"),
        ("DeleteFailed", None, "present", True, False, "fail", None, "DeleteFailed"),
        ("CreateFailed", None, "absent", True, False, "proceed", None, None),
        ("DeleteFailed", None, "absent", False, False, "proceed", None, None),
    ],
)
def test_feature_group_status_decision(status, update_status, state, wait, check_mode, action, waiter, message):
    existing = _described(status, update_status)
    decision = feature_group_status_decision("fg", existing, state, wait, check_mode)
    assert decision.action == action
    assert decision.waiter == waiter
    if message is None:
        assert decision.message is None
    else:
        assert message in decision.message
        assert "fg" in decision.message


@pytest.mark.parametrize(
    "extra, reason",
    [({"FailureReason": "The role is invalid."}, "The role is invalid."), ({}, "no reason reported")],
)
def test_feature_group_status_decision_reports_the_failure_reason(extra, reason):
    existing = _described("CreateFailed", **extra)
    decision = feature_group_status_decision("fg", existing, "present", True, False)
    assert reason in decision.message
    assert "state=absent" in decision.message
