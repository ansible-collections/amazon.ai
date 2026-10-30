# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import json
from datetime import date
from datetime import datetime
from typing import Union

import pytest
from ansible_collections.amazon.ai.plugins.module_utils.utils import convert_time_ranges
from ansible_collections.amazon.ai.plugins.module_utils.utils import encode_body
from ansible_collections.amazon.ai.plugins.module_utils.utils import feature_group_properties_to_update
from ansible_collections.amazon.ai.plugins.module_utils.utils import merge_data
from ansible_collections.amazon.ai.plugins.module_utils.utils import normalize_url


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
    with pytest.raises(ValueError, match="feature_definitions"):
        feature_group_properties_to_update(EXISTING_FEATURE_GROUP, _desired(feature_definitions=features + [feature]))


def test_feature_group_removed_feature():
    features = _desired()["feature_definitions"][:2]
    with pytest.raises(ValueError, match="cannot be removed"):
        feature_group_properties_to_update(EXISTING_FEATURE_GROUP, _desired(feature_definitions=features))


def test_feature_group_ttl_changed():
    online = {"ttl_duration": {"unit": "Days", "value": 1}}
    result = feature_group_properties_to_update(EXISTING_FEATURE_GROUP, _desired(online_store_config=online))
    assert result == {"online_store_config": {"ttl_duration": {"unit": "Days", "value": 1}}}


def test_feature_group_storage_type_standard_to_v2():
    online = {"storage_type": "Standard_V2"}
    result = feature_group_properties_to_update(EXISTING_FEATURE_GROUP, _desired(online_store_config=online))
    assert result == {"online_store_config": {"storage_type": "Standard_V2"}}


def test_feature_group_storage_type_other_transition():
    with pytest.raises(ValueError, match="storage_type"):
        feature_group_properties_to_update(
            EXISTING_FEATURE_GROUP, _desired(online_store_config={"storage_type": "InMemory"})
        )


@pytest.mark.parametrize(
    "online",
    [{"enable_online_store": False}, {"security_config": {"kms_key_id": "alias/key"}}],
)
def test_feature_group_online_store_create_only(online):
    with pytest.raises(ValueError, match="online_store_config"):
        feature_group_properties_to_update(EXISTING_FEATURE_GROUP, _desired(online_store_config=online))


def test_feature_group_online_store_added_to_offline_only_group():
    existing = {key: value for key, value in EXISTING_FEATURE_GROUP.items() if key != "online_store_config"}
    with pytest.raises(ValueError, match="online_store_config"):
        feature_group_properties_to_update(
            existing, {"online_store_config": {"ttl_duration": {"unit": "Days", "value": 1}}}
        )


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
    with pytest.raises(ValueError, match=option):
        feature_group_properties_to_update(EXISTING_FEATURE_GROUP, _desired(**{option: value}))
