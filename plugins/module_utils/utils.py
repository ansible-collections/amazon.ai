# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import json
from datetime import date
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Union


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


def extract_completion(response_body: Union[Dict[str, Any], str]) -> Union[str, None]:
    """
    Extract a human-readable answer from the Bedrock model response.

    Supports:
      - Anthropic: response_body["completion"]
      - Nova / Amazon: response_body["output"]["message"]["content"][0]["text"]
      - Cohere-style: response_body["generations"][0]["text"]

    Args:
        response_body: Parsed response (dict) or raw string.

    Returns:
        Normalized text string or None if extraction fails.
    """
    if isinstance(response_body, dict):
        if "completion" in response_body:  # Anthropic
            return response_body["completion"]
        if "output" in response_body:  # OpenAI-style
            try:
                return response_body["output"]["message"]["content"][0]["text"]
            except (KeyError, IndexError, TypeError):
                return None
        if "generations" in response_body:  # Cohere
            try:
                return response_body["generations"][0]["text"]
            except (KeyError, IndexError, TypeError):
                return None
    return str(response_body) if isinstance(response_body, str) else None


def merge_data(target: Union[Dict[str, Any], List[Dict[str, Any]]], source: Dict[str, Any]) -> None:
    """Merges data into a dictionary or list of dictionaries."""
    if isinstance(target, dict):
        target.update(source)
    elif isinstance(target, list):
        for item in target:
            item.update(source)


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
