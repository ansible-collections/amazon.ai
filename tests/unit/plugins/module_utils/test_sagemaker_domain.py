#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for the sagemaker_domain module."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import DomainStatus
from ansible_collections.amazon.ai.plugins.modules.sagemaker_domain import _domain_status_check

MODULE_PATH = "ansible_collections.amazon.ai.plugins.modules.sagemaker_domain"


class ExitJson(Exception):
    pass


def _module(state="present", wait=True, check_mode=False):
    module = MagicMock()
    module.params = {"state": state, "wait": wait, "wait_timeout": 600}
    module.check_mode = check_mode
    module.exit_json.side_effect = ExitJson
    return module


def _domain(status):
    return {"DomainId": "d-123", "DomainName": "example-domain", "Status": status.value}


@pytest.fixture(name="wait_for_domain_status")
def fixture_wait_for_domain_status():
    with patch(f"{MODULE_PATH}.wait_for_domain_status") as mock:
        yield mock


@pytest.fixture(name="describe_domain")
def fixture_describe_domain():
    with patch(f"{MODULE_PATH}.describe_domain") as mock:
        yield mock


@pytest.mark.parametrize("state", ["present", "absent"])
def test_returns_none_when_domain_missing(state, wait_for_domain_status, describe_domain):
    module = _module(state=state)

    assert _domain_status_check(MagicMock(), module, None) is None
    wait_for_domain_status.assert_not_called()
    describe_domain.assert_not_called()
    module.exit_json.assert_not_called()


@pytest.mark.parametrize(
    "status",
    [DomainStatus.IN_SERVICE, DomainStatus.FAILED, DomainStatus.UPDATE_FAILED, DomainStatus.DELETE_FAILED],
)
@pytest.mark.parametrize("check_mode", [False, True])
@pytest.mark.parametrize("wait", [False, True])
def test_returns_domain_unchanged_when_status_is_manageable(
    status, check_mode, wait, wait_for_domain_status, describe_domain
):
    module = _module(check_mode=check_mode, wait=wait)
    domain = _domain(status)

    assert _domain_status_check(MagicMock(), module, domain) is domain
    wait_for_domain_status.assert_not_called()
    describe_domain.assert_not_called()
    module.exit_json.assert_not_called()


@pytest.mark.parametrize("status", [DomainStatus.PENDING, DomainStatus.UPDATING, DomainStatus.DELETING])
def test_exits_without_waiting_in_check_mode(status, wait_for_domain_status, describe_domain):
    module = _module(check_mode=True)

    with pytest.raises(ExitJson):
        _domain_status_check(MagicMock(), module, _domain(status))

    module.exit_json.assert_called_once_with(
        changed=False,
        msg=f"Domain example-domain is currently in {status.value} state (check mode).",
    )
    wait_for_domain_status.assert_not_called()
    describe_domain.assert_not_called()


@pytest.mark.parametrize("status", [DomainStatus.PENDING, DomainStatus.UPDATING, DomainStatus.DELETING])
def test_exits_when_wait_disabled(status, wait_for_domain_status, describe_domain):
    module = _module(wait=False)

    with pytest.raises(ExitJson):
        _domain_status_check(MagicMock(), module, _domain(status))

    module.exit_json.assert_called_once_with(
        changed=False,
        msg=f"Domain example-domain is currently in {status.value} state (not waiting).",
    )
    wait_for_domain_status.assert_not_called()
    describe_domain.assert_not_called()


@pytest.mark.parametrize("state", ["present", "absent"])
@pytest.mark.parametrize("status", [DomainStatus.PENDING, DomainStatus.UPDATING])
def test_waits_for_in_service_and_returns_refreshed_domain(state, status, wait_for_domain_status, describe_domain):
    client = MagicMock()
    module = _module(state=state)
    refreshed = _domain(DomainStatus.IN_SERVICE)
    describe_domain.return_value = refreshed

    assert _domain_status_check(client, module, _domain(status)) is refreshed

    wait_for_domain_status.assert_called_once_with(client, module, "d-123", DomainStatus.IN_SERVICE)
    describe_domain.assert_called_once_with(client, "d-123")
    module.exit_json.assert_not_called()


def test_deleting_domain_with_state_absent_exits_after_deletion(wait_for_domain_status, describe_domain):
    client = MagicMock()
    module = _module(state="absent")

    with pytest.raises(ExitJson):
        _domain_status_check(client, module, _domain(DomainStatus.DELETING))

    wait_for_domain_status.assert_called_once_with(client, module, "d-123", DomainStatus.DELETED)
    module.exit_json.assert_called_once_with(changed=False, msg="Domain example-domain is deleted.")
    describe_domain.assert_not_called()


def test_deleting_domain_with_state_present_returns_none_once_deleted(wait_for_domain_status, describe_domain):
    client = MagicMock()
    module = _module(state="present")
    describe_domain.return_value = None

    assert _domain_status_check(client, module, _domain(DomainStatus.DELETING)) is None

    wait_for_domain_status.assert_called_once_with(client, module, "d-123", DomainStatus.DELETED)
    describe_domain.assert_called_once_with(client, "d-123")
    module.exit_json.assert_not_called()
