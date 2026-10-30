#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import boto3
import pytest
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import SpaceStatus
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_space_status
from ansible_collections.amazon.ai.plugins.module_utils.waiters import get_waiter
from ansible_collections.amazon.ai.plugins.module_utils.waiters import wait_for_image_version_deletion
from ansible_collections.amazon.ai.plugins.module_utils.waiters import wait_for_model_package_group_deletion
from botocore.exceptions import WaiterError
from botocore.stub import Stubber


class SageMaker:
    def describe_model_package_group(self, **kwargs):
        return kwargs

    def describe_space(self, **kwargs):
        return kwargs


def test_get_waiter_returns_model_package_group_deletion_waiter():
    waiter = get_waiter(SageMaker(), "model_package_group_deleted")

    assert waiter.name == "model_package_group_deleted"


@pytest.mark.parametrize("waiter_name", ["space_in_service", "space_deleted"])
def test_get_waiter_returns_space_waiter(waiter_name):
    waiter = get_waiter(SageMaker(), waiter_name)

    assert waiter.name == waiter_name


@patch("ansible_collections.amazon.ai.plugins.module_utils.waiters.get_waiter")
def test_wait_for_model_package_group_deletion_uses_timeout(mock_get_waiter):
    waiter = MagicMock()
    mock_get_waiter.return_value = waiter
    module = MagicMock()
    module.params = {"wait": True, "image_name": "img", "version": 1, "wait_timeout": 30}

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


# --------------------------------------------------------------------------------------
# Custom image_version_deleted waiter (botocore's own waits for ResourceNotFoundException,
# but DescribeImageVersion raises ResourceNotFound)
# --------------------------------------------------------------------------------------
def _sagemaker_client():
    return boto3.client(
        "sagemaker", region_name="eu-north-1", aws_access_key_id="testing", aws_secret_access_key="testing"
    )


def _delete_waiter_module():
    module = MagicMock()
    module.params = {"wait": True, "image_name": "img", "version": 1, "wait_timeout": 30}
    module.fail_json.side_effect = SystemExit
    return module


def test_image_version_deleted_waiter_succeeds_on_resource_not_found():
    client = _sagemaker_client()
    stubber = Stubber(client)
    stubber.add_response("describe_image_version", {"ImageVersionStatus": "DELETING"})
    stubber.add_client_error("describe_image_version", service_error_code="ResourceNotFound", http_status_code=400)

    with stubber:
        get_waiter(client, "image_version_deleted").wait(
            ImageName="img", Version=1, WaiterConfig={"Delay": 0, "MaxAttempts": 3}
        )

    stubber.assert_no_pending_responses()


def test_image_version_deleted_waiter_fails_on_delete_failed():
    client = _sagemaker_client()
    stubber = Stubber(client)
    stubber.add_response("describe_image_version", {"ImageVersionStatus": "DELETE_FAILED", "FailureReason": "boom"})

    with stubber, pytest.raises(WaiterError):
        get_waiter(client, "image_version_deleted").wait(
            ImageName="img", Version=1, WaiterConfig={"Delay": 0, "MaxAttempts": 3}
        )


def test_botocore_image_version_deleted_waiter_does_not_accept_resource_not_found():
    """Documents why the custom waiter exists: the native one reports a finished delete as an error."""
    client = _sagemaker_client()
    stubber = Stubber(client)
    stubber.add_client_error("describe_image_version", service_error_code="ResourceNotFound", http_status_code=400)

    with stubber, pytest.raises(WaiterError):
        client.get_waiter("image_version_deleted").wait(
            ImageName="img", Version=1, WaiterConfig={"Delay": 0, "MaxAttempts": 2}
        )


def test_wait_for_image_version_deletion_is_skipped_when_wait_is_false():
    client = MagicMock()
    module = _delete_waiter_module()
    module.params = {"wait": False}

    wait_for_image_version_deletion(client, module)

    client.describe_image_version.assert_not_called()


def test_wait_for_image_version_deletion_reports_delete_failed_with_the_reason():
    client = _sagemaker_client()
    module = _delete_waiter_module()
    stubber = Stubber(client)
    stubber.add_response("describe_image_version", {"ImageVersionStatus": "DELETE_FAILED", "FailureReason": "boom"})

    with stubber, pytest.raises(SystemExit):
        wait_for_image_version_deletion(client, module)

    msg = module.fail_json.call_args.kwargs["msg"]
    assert "DELETE_FAILED" in msg
    assert "boom" in msg


def test_wait_for_image_version_deletion_reports_other_waiter_errors():
    client = _sagemaker_client()
    module = _delete_waiter_module()
    stubber = Stubber(client)
    stubber.add_client_error("describe_image_version", service_error_code="ValidationException", http_status_code=400)

    with stubber, pytest.raises(SystemExit):
        wait_for_image_version_deletion(client, module)

    assert "Error waiting for SageMaker image version img:1" in module.fail_json.call_args.kwargs["msg"]


@patch("ansible_collections.amazon.ai.plugins.module_utils.waiters.get_waiter")
def test_wait_for_space_status_uses_timeout(mock_get_waiter):
    waiter = MagicMock()
    mock_get_waiter.return_value = waiter
    module = MagicMock()
    module.params = {"wait_timeout": 30}

    wait_for_space_status(
        MagicMock(),
        module,
        "d-example",
        "example-space",
        SpaceStatus.IN_SERVICE,
    )

    mock_get_waiter.assert_called_once()
    waiter.wait.assert_called_once_with(
        DomainId="d-example",
        SpaceName="example-space",
        WaiterConfig={"Delay": 15, "MaxAttempts": 2},
    )
