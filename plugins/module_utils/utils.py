# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import json
from typing import Any
from typing import Dict
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
