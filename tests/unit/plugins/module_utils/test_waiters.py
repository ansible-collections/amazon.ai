#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

from ansible_collections.amazon.ai.plugins.module_utils.waiters import get_waiter
from ansible_collections.amazon.ai.plugins.module_utils.waiters import wait_for_model_package_group_deletion


class SageMaker:
    def describe_model_package_group(self, **kwargs):
        return kwargs


def test_get_waiter_returns_model_package_group_deletion_waiter():
    waiter = get_waiter(SageMaker(), "model_package_group_deleted")

    assert waiter.name == "model_package_group_deleted"


@patch("ansible_collections.amazon.ai.plugins.module_utils.waiters.get_waiter")
def test_wait_for_model_package_group_deletion_uses_timeout(mock_get_waiter):
    waiter = MagicMock()
    mock_get_waiter.return_value = waiter
    module = MagicMock()
    module.params = {"wait": True}

    wait_for_model_package_group_deletion(
        MagicMock(),
        module,
        "example-group",
        wait_timeout=30,
    )

    mock_get_waiter.assert_called_once()
    waiter.wait.assert_called_once_with(
        ModelPackageGroupName="example-group",
        WaiterConfig={"Delay": 15, "MaxAttempts": 2},
    )
