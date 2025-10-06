# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import json
from typing import Union

import pytest
from ansible_collections.amazon.ai.plugins.module_utils.utils import encode_body

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
