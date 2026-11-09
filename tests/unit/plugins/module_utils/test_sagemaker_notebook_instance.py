#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for the sagemaker_notebook_instance module's status check."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import NotebookInstanceStatus
from ansible_collections.amazon.ai.plugins.modules.sagemaker_notebook_instance import _notebook_instance_status_check

_MODULE = "ansible_collections.amazon.ai.plugins.modules.sagemaker_notebook_instance"
_NAME = "my-notebook"


class FailJsonException(Exception):
    """Stand-in for AnsibleModule.fail_json, which terminates execution via sys.exit."""


class ExitJsonException(Exception):
    """Stand-in for AnsibleModule.exit_json, which terminates execution via sys.exit."""


def _make_module(state="present", check_mode=False, wait=True, wait_timeout=600):
    module = MagicMock()
    module.check_mode = check_mode
    module.params = {"state": state, "wait": wait, "wait_timeout": wait_timeout}
    module.fail_json.side_effect = FailJsonException()
    module.exit_json.side_effect = ExitJsonException()
    return module


def _notebook(status):
    return {"NotebookInstanceName": _NAME, "NotebookInstanceStatus": status}


@patch(f"{_MODULE}.describe_notebook_instance")
@patch(f"{_MODULE}.wait_for_notebook_instance_status")
def test_status_check_returns_none_for_missing_notebook(mock_wait, mock_describe):
    module = _make_module()

    assert _notebook_instance_status_check(MagicMock(), None, module) is None

    mock_wait.assert_not_called()
    mock_describe.assert_not_called()


@pytest.mark.parametrize("state", ["present", "absent"])
@pytest.mark.parametrize(
    "status",
    [NotebookInstanceStatus.IN_SERVICE, NotebookInstanceStatus.STOPPED, NotebookInstanceStatus.FAILED],
)
@patch(f"{_MODULE}.describe_notebook_instance")
@patch(f"{_MODULE}.wait_for_notebook_instance_status")
def test_status_check_passes_through_settled_notebook(mock_wait, mock_describe, status, state):
    module = _make_module(state=state, check_mode=True, wait=False)
    notebook = _notebook(status.value)

    result = _notebook_instance_status_check(MagicMock(), notebook, module)

    assert result is notebook
    mock_wait.assert_not_called()
    mock_describe.assert_not_called()
    module.exit_json.assert_not_called()
    module.fail_json.assert_not_called()


@pytest.mark.parametrize(
    "status",
    [
        NotebookInstanceStatus.PENDING,
        NotebookInstanceStatus.STOPPING,
        NotebookInstanceStatus.UPDATING,
        NotebookInstanceStatus.DELETING,
        NotebookInstanceStatus.PENDING_MAINTENANCE,
        NotebookInstanceStatus.IN_MAINTENANCE,
    ],
)
@patch(f"{_MODULE}.wait_for_notebook_instance_status")
def test_status_check_check_mode_short_circuits_transitional_states(mock_wait, status):
    module = _make_module(check_mode=True)

    with pytest.raises(ExitJsonException):
        _notebook_instance_status_check(MagicMock(), _notebook(status.value), module)

    mock_wait.assert_not_called()
    module.fail_json.assert_not_called()
    kwargs = module.exit_json.call_args.kwargs
    assert kwargs["changed"] is False
    assert "check mode" in kwargs["msg"]


@pytest.mark.parametrize(
    "status",
    [NotebookInstanceStatus.PENDING_MAINTENANCE, NotebookInstanceStatus.IN_MAINTENANCE],
)
@patch(f"{_MODULE}.wait_for_notebook_instance_status")
def test_status_check_fails_during_maintenance(mock_wait, status):
    module = _make_module()

    with pytest.raises(FailJsonException):
        _notebook_instance_status_check(MagicMock(), _notebook(status.value), module)

    mock_wait.assert_not_called()
    assert status.value in module.fail_json.call_args.kwargs["msg"]


@pytest.mark.parametrize(
    "status",
    [
        NotebookInstanceStatus.PENDING,
        NotebookInstanceStatus.STOPPING,
        NotebookInstanceStatus.UPDATING,
        NotebookInstanceStatus.DELETING,
    ],
)
@patch(f"{_MODULE}.wait_for_notebook_instance_status")
def test_status_check_no_wait_short_circuits(mock_wait, status):
    module = _make_module(wait=False)

    with pytest.raises(ExitJsonException):
        _notebook_instance_status_check(MagicMock(), _notebook(status.value), module)

    mock_wait.assert_not_called()
    kwargs = module.exit_json.call_args.kwargs
    assert kwargs["changed"] is False
    assert "not waiting" in kwargs["msg"]


@patch(f"{_MODULE}.describe_notebook_instance")
@patch(f"{_MODULE}.wait_for_notebook_instance_status")
def test_status_check_deleting_absent_waits_and_exits(mock_wait, mock_describe):
    module = _make_module(state="absent")
    client = MagicMock()

    with pytest.raises(ExitJsonException):
        _notebook_instance_status_check(client, _notebook(NotebookInstanceStatus.DELETING.value), module)

    mock_wait.assert_called_once_with(client, module, NotebookInstanceStatus.DELETED)
    mock_describe.assert_not_called()
    kwargs = module.exit_json.call_args.kwargs
    assert kwargs["changed"] is False
    assert "is deleted" in kwargs["msg"]


@patch(f"{_MODULE}.describe_notebook_instance")
@patch(f"{_MODULE}.wait_for_notebook_instance_status")
def test_status_check_deleting_present_waits_and_returns_refreshed(mock_wait, mock_describe):
    """After the deletion completes, state=present proceeds with no existing notebook (create path)."""
    mock_describe.return_value = None
    module = _make_module(state="present")
    client = MagicMock()

    result = _notebook_instance_status_check(client, _notebook(NotebookInstanceStatus.DELETING.value), module)

    assert result is None
    mock_wait.assert_called_once_with(client, module, NotebookInstanceStatus.DELETED)
    mock_describe.assert_called_once_with(client, _NAME)
    module.exit_json.assert_not_called()


@pytest.mark.parametrize("state", ["present", "absent"])
@pytest.mark.parametrize(
    "status, target",
    [
        (NotebookInstanceStatus.STOPPING, NotebookInstanceStatus.STOPPED),
        (NotebookInstanceStatus.UPDATING, NotebookInstanceStatus.STOPPED),
        (NotebookInstanceStatus.PENDING, NotebookInstanceStatus.IN_SERVICE),
    ],
)
@patch(f"{_MODULE}.describe_notebook_instance")
@patch(f"{_MODULE}.wait_for_notebook_instance_status")
def test_status_check_waits_for_settled_state_and_returns_refreshed(mock_wait, mock_describe, status, target, state):
    refreshed = _notebook(target.value)
    mock_describe.return_value = refreshed
    module = _make_module(state=state)
    client = MagicMock()

    result = _notebook_instance_status_check(client, _notebook(status.value), module)

    assert result is refreshed
    mock_wait.assert_called_once_with(client, module, target)
    mock_describe.assert_called_once_with(client, _NAME)
    module.exit_json.assert_not_called()
    module.fail_json.assert_not_called()
