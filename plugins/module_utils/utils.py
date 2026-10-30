# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import json
from datetime import date
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from urllib.parse import urlparse
from urllib.parse import urlunparse


def parse_json(value: str, module, option: str) -> Any:
    """Parse an option's JSON value, reporting malformed input through the module."""
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError) as e:
        module.fail_json(msg=f"Option {option} must contain valid JSON: {e}")


def encode_body(body: Union[dict, list, str]) -> bytes:
    """
    Convert the body into bytes for invoke_model.

    Args:
        body: Input request body (dict, list, or string).

    Returns:
        Bytes representation of the body.
    """
    if isinstance(body, (dict, list)):
        return json.dumps(body).encode("utf-8")
    elif isinstance(body, str):
        return body.encode("utf-8")
    else:
        raise TypeError("body must be a dict, list, or string")


def merge_data(target: Union[Dict[str, Any], List[Dict[str, Any]]], source: Dict[str, Any]) -> None:
    """Merges data into a dictionary or list of dictionaries."""
    if isinstance(target, dict):
        target.update(source)
    elif isinstance(target, list):
        for item in target:
            item.update(source)


def normalize_url(url: str) -> str:
    """Normalize a URL by lowercasing the scheme and host, and stripping trailing slashes from the path."""
    parsed = urlparse(url)
    return urlunparse(
        parsed._replace(
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower(),
            path=parsed.path.rstrip("/"),
        )
    )


def convert_time_ranges(status_filter: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert FromTime/ToTime fields in nested AWS DevOps Guru time range filters into datetime objects.
    Supports both CamelCase-style (`StartTimeRange`, `EndTimeRange`) and snake_case-style
    (`start_time_range`, `end_time_range`) keys, as well as `FromTime` / `from_time`
    and `ToTime` / `to_time` variants.
    Args:
        status_filter: A dictionary representing status filters for DevOps Guru insights.
    Returns:
        The same dictionary, but with all recognized date strings replaced by datetime objects.
    Raises:
        ValueError: If a date string is in an invalid format or unsupported type.
    """

    def convert_time(date_input: Any, set_midnight: bool = False) -> datetime:
        """Convert a date string or date/datetime object to a datetime object, optionally setting midnight."""
        if isinstance(date_input, datetime):
            dt = date_input
        elif isinstance(date_input, date):
            dt = datetime.combine(date_input, datetime.min.time())
        elif isinstance(date_input, str):
            try:
                dt = datetime.strptime(date_input, "%Y-%m-%d")
            except Exception as e:
                raise ValueError(f"Invalid date format for '{date_input}': {e}")
        else:
            raise ValueError(f"Unsupported type for date conversion: {type(date_input)}")

        if set_midnight:
            dt = dt.replace(hour=0, minute=0, second=0)
        return dt

    # Iterate through all top-level keys
    for key, subdict in status_filter.items():
        if not isinstance(subdict, dict):
            continue

        # Check for all possible time range keys
        for time_range_key in ["StartTimeRange", "EndTimeRange", "start_time_range", "end_time_range"]:
            if time_range_key not in subdict:
                continue

            time_range_dict = subdict[time_range_key]
            if not isinstance(time_range_dict, dict):
                continue

            for time_key in ["FromTime", "ToTime", "from_time", "to_time"]:
                if time_key not in time_range_dict:
                    continue

                # "ToTime"/"to_time" should set midnight
                set_midnight = "to_time" in time_key.lower()
                time_range_dict[time_key] = convert_time(time_range_dict[time_key], set_midnight)

    return status_filter


def _is_subset(desired: Any, existing: Any) -> bool:
    """Return True when every value set in desired is present and equal in existing, recursing into dicts."""
    if isinstance(desired, dict):
        if not isinstance(existing, dict):
            return False
        return all(_is_subset(value, existing.get(key)) for key, value in desired.items())
    return desired == existing


def _feature_additions(existing: List[Dict[str, Any]], desired: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return the desired features missing from existing; raise ValueError on a changed or removed feature."""
    existing_by_name = {feature["feature_name"]: feature for feature in existing}
    desired_names = {feature["feature_name"] for feature in desired}
    removed = [name for name in existing_by_name if name not in desired_names]
    if removed:
        raise ValueError(
            f"feature_definitions: features cannot be removed from a feature group ({', '.join(removed)}); "
            "delete and recreate the feature group instead."
        )
    feature_additions = []
    for feature in desired:
        current = existing_by_name.get(feature["feature_name"])
        if current is None:
            feature_additions.append(feature)
            continue
        for key in ("feature_type", "collection_type", "collection_config"):
            if key in feature and not _is_subset(feature[key], current.get(key)):
                raise ValueError(
                    f"feature_definitions: {key} of feature {feature['feature_name']} cannot be changed; "
                    "delete and recreate the feature group instead."
                )
    return feature_additions


def _online_store_config_update(existing: Optional[Dict[str, Any]], desired: Dict[str, Any]) -> Dict[str, Any]:
    """Return the online store fields to update; raise ValueError on a change the API cannot apply in place."""
    existing = existing or {}
    for key in ("enable_online_store", "security_config"):
        if key in desired and not _is_subset(desired[key], existing.get(key)):
            raise ValueError(
                f"online_store_config.{key} cannot be changed on an existing feature group; "
                "delete and recreate the feature group instead."
            )
    if not existing:
        raise ValueError(
            "online_store_config cannot be added to a feature group created without an online store; "
            "delete and recreate the feature group instead."
        )
    online_store_config = {}
    if "storage_type" in desired and desired["storage_type"] != existing.get("storage_type"):
        if (existing.get("storage_type"), desired["storage_type"]) != ("Standard", "Standard_V2"):
            raise ValueError(
                f"online_store_config.storage_type can only be changed from Standard to Standard_V2, "
                f"not from {existing.get('storage_type')} to {desired['storage_type']}."
            )
        online_store_config["storage_type"] = desired["storage_type"]
    if "ttl_duration" in desired and desired["ttl_duration"] != existing.get("ttl_duration"):
        online_store_config["ttl_duration"] = desired["ttl_duration"]
    return online_store_config


def _throughput_config_update(existing: Optional[Dict[str, Any]], desired: Dict[str, Any]) -> Dict[str, Any]:
    """Return the throughput fields to update; switching to Provisioned sends the mode and both units together."""
    existing = existing or {}
    throughput_config = {key: value for key, value in desired.items() if existing.get(key) != value}
    if throughput_config and desired.get("throughput_mode") == "Provisioned":
        if existing.get("throughput_mode") != "Provisioned":
            return dict(desired)
    return throughput_config


def feature_group_properties_to_update(existing: Dict[str, Any], desired: Dict[str, Any]) -> Dict[str, Any]:
    """
    Diff a SageMaker feature group against the desired configuration.

    Both arguments are snake_case: existing is the converted describe_feature_group() output, desired holds the
    module options with None values scrubbed. Options absent from desired are never compared.

    Args:
        existing: The current feature group.
        desired: The requested configuration.

    Returns:
        A dict with any of the keys feature_additions, online_store_config and throughput_config, each holding
        what must be sent to UpdateFeatureGroup. Empty when nothing differs.

    Raises:
        ValueError: If a requested change cannot be applied in place; the message names the option.
    """
    for key in (
        "record_identifier_feature_name",
        "event_time_feature_name",
        "description",
        "role_arn",
        "offline_store_config",
    ):
        if key in desired and not _is_subset(desired[key], existing.get(key)):
            raise ValueError(
                f"{key} cannot be changed on an existing feature group; delete and recreate the feature group instead."
            )

    properties_to_update = {}
    if "feature_definitions" in desired:
        feature_additions = _feature_additions(existing.get("feature_definitions", []), desired["feature_definitions"])
        if feature_additions:
            properties_to_update["feature_additions"] = feature_additions
    if "online_store_config" in desired:
        online_store_config = _online_store_config_update(
            existing.get("online_store_config"), desired["online_store_config"]
        )
        if online_store_config:
            properties_to_update["online_store_config"] = online_store_config
    if "throughput_config" in desired:
        throughput_config = _throughput_config_update(existing.get("throughput_config"), desired["throughput_config"])
        if throughput_config:
            properties_to_update["throughput_config"] = throughput_config
    return properties_to_update
