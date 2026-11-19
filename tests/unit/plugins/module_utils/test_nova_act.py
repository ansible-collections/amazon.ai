#!/usr/bin/env python

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for nova_act module_utils."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from ansible_collections.amazon.ai.plugins.module_utils import nova_act
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import create_workflow_definition
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import delete_workflow_definition
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import get_workflow_definition
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import list_workflow_definitions
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import validate_workflow_definition_name
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import wait_for_workflow_definition_deleted
from ansible_collections.amazon.ai.plugins.modules import nova_act_workflow_definition
from ansible_collections.amazon.ai.plugins.modules import nova_act_workflow_definition_info
from ansible_collections.amazon.ai.plugins.modules.nova_act_workflow_definition import _workflow_definition_status_check
from botocore.exceptions import ClientError

NAME = "sample-workflow"
ARN = f"arn:aws:nova-act:us-east-1:123456789012:workflow-definition/{NAME}"


class FailJson(Exception):
    pass


def _module(check_mode=False, **params):
    module = MagicMock()
    module.check_mode = check_mode
    module.params = {
        "workflow_definition_name": NAME,
        "state": "present",
        "description": None,
        "export_config": None,
        "client_token": None,
        "wait": True,
        "wait_timeout": 600,
    }
    module.params.update(params)
    module.fail_json.side_effect = FailJson
    module.fail_json_aws.side_effect = FailJson
    return module


def _client_error(code, operation):
    return ClientError({"Error": {"Code": code, "Message": code}}, operation)


def _get_response(**extra):
    response = {
        "name": NAME,
        "arn": ARN,
        "status": "ACTIVE",
        "exportConfig": {"s3BucketName": "bucket", "s3KeyPrefix": "prefix/"},
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }
    response.update(extra)
    return response


@pytest.mark.parametrize(
    "module_main,module_path",
    [
        (
            nova_act_workflow_definition.main,
            "ansible_collections.amazon.ai.plugins.modules.nova_act_workflow_definition",
        ),
        (
            nova_act_workflow_definition_info.main,
            "ansible_collections.amazon.ai.plugins.modules.nova_act_workflow_definition_info",
        ),
    ],
)
def test_nova_act_modules_require_supported_botocore_before_client(module_main, module_path):
    module = _module()
    module.botocore_at_least.return_value = False

    with patch(f"{module_path}.AnsibleAWSModule", return_value=module):
        with pytest.raises(FailJson):
            module_main()

    module.botocore_at_least.assert_called_once_with("1.42.1")
    module.fail_json.assert_called_once_with(
        msg="Nova Act requires botocore >= 1.42.1 to provide the nova-act service model."
    )
    module.client.assert_not_called()


@pytest.mark.parametrize("name", ["a", "Valid_name-1", "x" * 40, None])
def test_validate_workflow_definition_name_accepts_valid(name):
    module = _module()
    validate_workflow_definition_name(module, name)
    module.fail_json.assert_not_called()


@pytest.mark.parametrize("name", ["", "x" * 41, "has space", "dot.name", "slash/name"])
def test_validate_workflow_definition_name_rejects_invalid(name):
    module = _module()
    with pytest.raises(FailJson):
        validate_workflow_definition_name(module, name)


def test_get_workflow_definition_converts_strips_metadata_and_adds_aliases():
    client = MagicMock()
    client.get_workflow_definition.return_value = _get_response()

    result = get_workflow_definition(client, _module(), NAME)

    assert result == {
        "name": NAME,
        "workflow_definition_name": NAME,
        "arn": ARN,
        "workflow_definition_arn": ARN,
        "status": "ACTIVE",
        "export_config": {"s3_bucket_name": "bucket", "s3_key_prefix": "prefix/"},
    }
    client.get_workflow_definition.assert_called_once_with(workflowDefinitionName=NAME)


def test_get_workflow_definition_returns_none_when_missing():
    client = MagicMock()
    client.get_workflow_definition.side_effect = _client_error("ResourceNotFoundException", "GetWorkflowDefinition")

    assert get_workflow_definition(client, _module(), NAME) is None


def test_get_workflow_definition_fails_on_other_errors():
    client = MagicMock()
    client.get_workflow_definition.side_effect = _client_error("ValidationException", "GetWorkflowDefinition")
    module = _module()

    with pytest.raises(FailJson):
        get_workflow_definition(client, module, NAME)
    module.fail_json_aws.assert_called_once()


def test_list_workflow_definitions_adds_aliases_and_passes_sort_order():
    client = MagicMock()
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value.build_full_result.return_value = {
        "workflowDefinitionSummaries": [
            {"workflowDefinitionName": NAME, "workflowDefinitionArn": ARN, "status": "ACTIVE"},
        ]
    }

    result = list_workflow_definitions(client, _module(), sort_order="Descending")

    assert result == [
        {"name": NAME, "workflow_definition_name": NAME, "arn": ARN, "workflow_definition_arn": ARN, "status": "ACTIVE"}
    ]
    paginator.paginate.assert_called_once_with(sortOrder="Descending")


def test_list_workflow_definitions_omits_unset_sort_order():
    client = MagicMock()
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value.build_full_result.return_value = {"workflowDefinitionSummaries": []}

    assert list_workflow_definitions(client, _module()) == []
    paginator.paginate.assert_called_once_with()


def test_status_check_passes_through_active():
    existing = {"status": "ACTIVE"}
    assert _workflow_definition_status_check(MagicMock(), _module(), existing) is existing


def test_status_check_fails_present_when_deleting():
    client = MagicMock()
    module = _module(state="present")
    existing = {"status": "DELETING"}
    with pytest.raises(FailJson):
        _workflow_definition_status_check(client, module, existing)


@pytest.mark.parametrize("check_mode,wait", [(True, True), (False, False)])
def test_status_check_absent_deleting_returns_existing_without_waiting(check_mode, wait):
    client = MagicMock()
    existing = {"status": "DELETING"}
    module = _module(check_mode=check_mode, state="absent", wait=wait)

    assert _workflow_definition_status_check(client, module, existing) is existing
    client.get_workflow_definition.assert_not_called()


def test_status_check_absent_deleting_waits_until_gone():
    client = MagicMock()
    client.get_workflow_definition.side_effect = _client_error("ResourceNotFoundException", "GetWorkflowDefinition")
    module = _module(state="absent")
    existing = {"status": "DELETING"}

    assert _workflow_definition_status_check(client, module, existing) is None


def test_wait_for_deleted_times_out():
    client = MagicMock()
    client.get_workflow_definition.return_value = _get_response(status="DELETING")
    module = _module(wait_timeout=0)

    with pytest.raises(FailJson):
        wait_for_workflow_definition_deleted(client, module, NAME)
    assert "Timed out" in module.fail_json.call_args.kwargs["msg"]


def test_create_check_mode_does_not_call_api():
    client = MagicMock()

    changed, definition, msg = create_workflow_definition(client, _module(check_mode=True))

    assert changed is True
    assert definition == {}
    assert msg.startswith("Check mode: would have ")
    client.create_workflow_definition.assert_not_called()


def test_create_converts_params_and_returns_definition():
    client = MagicMock()
    client.create_workflow_definition.return_value = {"status": "ACTIVE"}
    client.get_workflow_definition.return_value = _get_response()
    module = _module(
        description="desc",
        export_config={"s3_bucket_name": "bucket", "s3_key_prefix": None},
    )

    changed, definition, msg = create_workflow_definition(client, module)

    client.create_workflow_definition.assert_called_once_with(
        name=NAME,
        description="desc",
        exportConfig={"s3BucketName": "bucket"},
    )
    assert changed is True
    assert definition["workflow_definition_arn"] == ARN
    assert "created successfully" in msg


def test_create_fails_on_client_error():
    client = MagicMock()
    client.create_workflow_definition.side_effect = _client_error("ConflictException", "CreateWorkflowDefinition")
    module = _module()

    with pytest.raises(FailJson):
        create_workflow_definition(client, module)
    module.fail_json_aws.assert_called_once()


def test_delete_check_mode_does_not_call_api():
    client = MagicMock()
    existing = {"name": NAME, "status": "ACTIVE"}

    changed, definition, msg = delete_workflow_definition(client, _module(check_mode=True, state="absent"), existing)

    assert (changed, definition) == (True, existing)
    assert msg.startswith("Check mode: would have ")
    client.delete_workflow_definition.assert_not_called()


def test_delete_without_wait_returns_status_from_response():
    client = MagicMock()
    client.delete_workflow_definition.return_value = {"status": "DELETING"}
    existing = {"name": NAME, "arn": ARN, "status": "ACTIVE"}

    with patch.object(nova_act, "wait_for_workflow_definition_deleted") as waiter:
        changed, definition, _msg = delete_workflow_definition(client, _module(state="absent", wait=False), existing)

    assert changed is True
    assert definition == {"name": NAME, "arn": ARN, "status": "DELETING"}
    waiter.assert_not_called()
    client.delete_workflow_definition.assert_called_once_with(workflowDefinitionName=NAME)


def test_delete_fails_on_client_error():
    client = MagicMock()
    client.delete_workflow_definition.side_effect = _client_error("ConflictException", "DeleteWorkflowDefinition")
    module = _module(state="absent")
    existing = {"name": NAME}

    with pytest.raises(FailJson):
        delete_workflow_definition(client, module, existing)
    module.fail_json_aws.assert_called_once()


def test_delete_returns_noop_when_workflow_definition_is_already_absent():
    client = MagicMock()
    client.delete_workflow_definition.side_effect = _client_error(
        "ResourceNotFoundException", "DeleteWorkflowDefinition"
    )
    module = _module(state="absent")
    existing = {"name": NAME}

    with patch.object(nova_act, "wait_for_workflow_definition_deleted") as waiter:
        changed, definition, msg = delete_workflow_definition(client, module, existing)

    assert changed is False
    assert definition == {}
    assert msg == f"Workflow definition '{NAME}' does not exist."
    waiter.assert_not_called()
    module.fail_json_aws.assert_not_called()
