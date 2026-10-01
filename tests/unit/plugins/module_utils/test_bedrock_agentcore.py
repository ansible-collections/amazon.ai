#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for bedrock_agentcore module_utils and the runtime endpoint module."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import AgentRuntimeEndpointStatus
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import _create_agent_runtime_endpoint_api
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import create_agent_runtime_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import wait_for_agent_runtime_endpoint_status
from ansible_collections.amazon.ai.plugins.modules.bedrock_agentcore_runtime_endpoint import _runtime_endpoint_status_check


class FailJsonException(Exception):
    """Stand-in for AnsibleModule.fail_json, which terminates execution via sys.exit."""


class ExitJsonException(Exception):
    """Stand-in for AnsibleModule.exit_json, which terminates execution via sys.exit."""


def _make_module(check_mode=False, wait=True, wait_timeout=600):
    module = MagicMock()
    module.check_mode = check_mode
    module.params = {"wait": wait, "wait_timeout": wait_timeout}
    module.fail_json.side_effect = FailJsonException()
    module.exit_json.side_effect = ExitJsonException()
    return module


# ---------------------------------------------------------------------------
# wait_for_agent_runtime_endpoint_status
# ---------------------------------------------------------------------------


@patch("ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore.get_agent_runtime_endpoint")
def test_wait_returns_cleanly_when_deleting_endpoint_disappears(mock_get):
    """A DELETED wait target is satisfied when the endpoint is gone (the DELETING regression)."""
    mock_get.return_value = None
    module = _make_module()

    wait_for_agent_runtime_endpoint_status(
        MagicMock(), module, "rt-id", "ep-name", AgentRuntimeEndpointStatus.DELETED
    )

    module.fail_json.assert_not_called()


@patch("ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore.get_agent_runtime_endpoint")
def test_wait_fails_when_endpoint_missing_but_target_is_ready(mock_get):
    """A missing endpoint while waiting for READY is a genuine error."""
    mock_get.return_value = None
    module = _make_module()

    with pytest.raises(FailJsonException):
        wait_for_agent_runtime_endpoint_status(
            MagicMock(), module, "rt-id", "ep-name", AgentRuntimeEndpointStatus.READY
        )

    module.fail_json.assert_called_once()


@patch("ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore.get_agent_runtime_endpoint")
def test_wait_returns_when_target_status_reached(mock_get):
    mock_get.return_value = {"name": "ep-name", "status": "READY"}
    module = _make_module()

    wait_for_agent_runtime_endpoint_status(
        MagicMock(), module, "rt-id", "ep-name", AgentRuntimeEndpointStatus.READY
    )

    module.fail_json.assert_not_called()


@patch("ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore.get_agent_runtime_endpoint")
def test_wait_fails_on_failed_status_by_default(mock_get):
    mock_get.return_value = {"name": "ep-name", "status": "CREATE_FAILED", "failure_reason": "boom"}
    module = _make_module()

    with pytest.raises(FailJsonException):
        wait_for_agent_runtime_endpoint_status(
            MagicMock(), module, "rt-id", "ep-name", AgentRuntimeEndpointStatus.READY
        )

    module.fail_json.assert_called_once()


@patch("ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore.get_agent_runtime_endpoint")
def test_wait_returns_on_failed_status_when_fail_disabled(mock_get):
    """With fail_on_failed_status=False a terminal *_FAILED state settles instead of failing."""
    mock_get.return_value = {"name": "ep-name", "status": "UPDATE_FAILED", "failure_reason": "boom"}
    module = _make_module()

    wait_for_agent_runtime_endpoint_status(
        MagicMock(),
        module,
        "rt-id",
        "ep-name",
        AgentRuntimeEndpointStatus.DELETED,
        fail_on_failed_status=False,
    )

    module.fail_json.assert_not_called()


# ---------------------------------------------------------------------------
# _runtime_endpoint_status_check (module level)
# ---------------------------------------------------------------------------

_MODULE = "ansible_collections.amazon.ai.plugins.modules.bedrock_agentcore_runtime_endpoint"


def test_status_check_returns_none_for_missing_endpoint():
    module = _make_module()
    assert _runtime_endpoint_status_check(MagicMock(), None, module, "rt-id", "present") is None


@patch(f"{_MODULE}.wait_for_agent_runtime_endpoint_status")
def test_status_check_passes_through_settled_endpoint(mock_wait):
    module = _make_module()
    endpoint = {"name": "ep-name", "status": "READY"}

    result = _runtime_endpoint_status_check(MagicMock(), endpoint, module, "rt-id", "present")

    assert result is endpoint
    mock_wait.assert_not_called()


@patch(f"{_MODULE}.get_agent_runtime_endpoint")
@patch(f"{_MODULE}.wait_for_agent_runtime_endpoint_status")
def test_status_check_deleting_waits_for_deleted_without_failing(mock_wait, mock_get):
    """DELETING + state=absent waits for DELETED and tolerates *_FAILED states."""
    mock_get.return_value = None
    module = _make_module()
    endpoint = {"name": "ep-name", "status": "DELETING"}

    result = _runtime_endpoint_status_check(MagicMock(), endpoint, module, "rt-id", "absent")

    assert result is None
    args = mock_wait.call_args.args
    kwargs = mock_wait.call_args.kwargs
    assert args[4] == AgentRuntimeEndpointStatus.DELETED
    assert kwargs["fail_on_failed_status"] is False


@patch(f"{_MODULE}.get_agent_runtime_endpoint")
@patch(f"{_MODULE}.wait_for_agent_runtime_endpoint_status")
def test_status_check_creating_waits_for_ready_and_fails_on_failure(mock_wait, mock_get):
    """CREATING + state=present waits for READY and surfaces *_FAILED states."""
    refreshed = {"name": "ep-name", "status": "READY"}
    mock_get.return_value = refreshed
    module = _make_module()
    endpoint = {"name": "ep-name", "status": "CREATING"}

    result = _runtime_endpoint_status_check(MagicMock(), endpoint, module, "rt-id", "present")

    assert result is refreshed
    args = mock_wait.call_args.args
    kwargs = mock_wait.call_args.kwargs
    assert args[4] == AgentRuntimeEndpointStatus.READY
    assert kwargs["fail_on_failed_status"] is True


@patch(f"{_MODULE}.wait_for_agent_runtime_endpoint_status")
def test_status_check_check_mode_short_circuits(mock_wait):
    module = _make_module(check_mode=True)
    endpoint = {"name": "ep-name", "status": "DELETING"}

    with pytest.raises(ExitJsonException):
        _runtime_endpoint_status_check(MagicMock(), endpoint, module, "rt-id", "absent")

    mock_wait.assert_not_called()
    module.exit_json.assert_called_once()


@patch(f"{_MODULE}.wait_for_agent_runtime_endpoint_status")
def test_status_check_no_wait_short_circuits(mock_wait):
    module = _make_module(wait=False)
    endpoint = {"name": "ep-name", "status": "CREATING"}

    with pytest.raises(ExitJsonException):
        _runtime_endpoint_status_check(MagicMock(), endpoint, module, "rt-id", "present")

    mock_wait.assert_not_called()
    module.exit_json.assert_called_once()


# ---------------------------------------------------------------------------
# create_agent_runtime_endpoint ConflictException retry
# ---------------------------------------------------------------------------


@patch("ansible_collections.amazon.aws.plugins.module_utils.cloud.time.sleep", return_value=None)
def test_create_endpoint_api_retries_on_conflict(_mock_sleep):
    """A ConflictException on an immediate re-create is retried until it succeeds."""
    client = MagicMock()
    conflict = ClientError(
        {"Error": {"Code": "ConflictException", "Message": "still deleting"}},
        "CreateAgentRuntimeEndpoint",
    )
    client.create_agent_runtime_endpoint.side_effect = [conflict, {"name": "ep-name"}]

    result = _create_agent_runtime_endpoint_api(client, agentRuntimeId="rt-id", name="ep-name")

    assert result == {"name": "ep-name"}
    assert client.create_agent_runtime_endpoint.call_count == 2


@patch("ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore._create_agent_runtime_endpoint_api")
@patch("ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore.wait_for_agent_runtime_endpoint_status")
def test_create_endpoint_uses_retrying_api(mock_wait, mock_api):
    mock_api.return_value = {"name": "ep-name"}
    module = _make_module()
    module.params.update({"endpoint_name": "ep-name", "agent_runtime_version": None, "description": None})
    client = MagicMock()

    changed, name, _msg = create_agent_runtime_endpoint(module, client, "rt-id")

    assert changed is True
    assert name == "ep-name"
    mock_api.assert_called_once()
    client.create_agent_runtime_endpoint.assert_not_called()
    mock_wait.assert_called_once()


def test_create_endpoint_check_mode_does_not_call_aws():
    module = _make_module(check_mode=True)
    module.params.update({"endpoint_name": "ep-name"})
    client = MagicMock()

    changed, name, _msg = create_agent_runtime_endpoint(module, client, "rt-id")

    assert changed is True
    assert name is None
    client.create_agent_runtime_endpoint.assert_not_called()
