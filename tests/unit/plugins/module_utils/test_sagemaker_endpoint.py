# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for the SageMaker endpoint helpers in the sagemaker module_utils."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import endpoint_params
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_endpoints
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_endpoint_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_endpoint
from botocore.exceptions import ClientError
from botocore.exceptions import WaiterError

SAGEMAKER = "ansible_collections.amazon.ai.plugins.module_utils.sagemaker"
ENDPOINT_ARN = "arn:aws:sagemaker:us-east-1:123456789012:endpoint/my-endpoint"


class FailJson(Exception):
    """Raised by the mocked module.fail_json, which exits the module in real life."""


def make_module(check_mode=False, **params):
    module = MagicMock()
    module.check_mode = check_mode
    module.params = dict(
        endpoint_name="my-endpoint",
        endpoint_config_name="my-config",
        tags=None,
        purge_tags=True,
        wait_timeout=600,
    )
    module.params.update(params)
    module.fail_json.side_effect = FailJson
    return module


def validation_error(message):
    return ClientError({"Error": {"Code": "ValidationException", "Message": message}}, "DescribeEndpoint")


# --------------------------------------------------------------------------------------
# describe_endpoint
# --------------------------------------------------------------------------------------
def test_describe_endpoint_returns_the_endpoint():
    client = MagicMock()
    client.describe_endpoint.return_value = {"EndpointName": "my-endpoint", "EndpointStatus": "InService"}

    assert describe_endpoint(client, "my-endpoint") == {"EndpointName": "my-endpoint", "EndpointStatus": "InService"}
    client.describe_endpoint.assert_called_once_with(EndpointName="my-endpoint")


@pytest.mark.parametrize(
    "message",
    [
        f'Could not find endpoint "{ENDPOINT_ARN}".',
        "Could not find endpoint",
    ],
)
def test_describe_endpoint_returns_none_when_missing(message):
    client = MagicMock()
    client.describe_endpoint.side_effect = validation_error(message)

    assert describe_endpoint(client, "my-endpoint") is None


def test_describe_endpoint_reraises_other_validation_errors():
    client = MagicMock()
    client.describe_endpoint.side_effect = validation_error("Some other validation problem.")

    with pytest.raises(ClientError):
        describe_endpoint(client, "my-endpoint")


# --------------------------------------------------------------------------------------
# list_endpoints
# --------------------------------------------------------------------------------------
def test_list_endpoints_forwards_filters_and_returns_endpoints():
    client = MagicMock()
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value.build_full_result.return_value = {
        "Endpoints": [{"EndpointName": "endpoint-a"}, {"EndpointName": "endpoint-b"}]
    }

    assert list_endpoints(client, NameContains="endpoint", StatusEquals="InService") == [
        {"EndpointName": "endpoint-a"},
        {"EndpointName": "endpoint-b"},
    ]
    client.get_paginator.assert_called_once_with("list_endpoints")
    paginator.paginate.assert_called_once_with(NameContains="endpoint", StatusEquals="InService")


def test_list_endpoints_max_results_limits_total_items():
    client = MagicMock()
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value.build_full_result.return_value = {"Endpoints": [{"EndpointName": "endpoint-a"}]}

    assert list_endpoints(client, NameContains="endpoint", MaxResults=1) == [{"EndpointName": "endpoint-a"}]
    paginator.paginate.assert_called_once_with(NameContains="endpoint", PaginationConfig={"MaxItems": 1})


# --------------------------------------------------------------------------------------
# endpoint_params / create / update / delete
# --------------------------------------------------------------------------------------
def test_endpoint_params_keeps_only_endpoint_fields():
    module = make_module(tags={"team": "ai"})

    assert endpoint_params(module) == {"EndpointName": "my-endpoint", "EndpointConfigName": "my-config"}


def test_endpoint_params_omits_unset_endpoint_config_name():
    module = make_module(endpoint_config_name=None)

    assert endpoint_params(module) == {"EndpointName": "my-endpoint"}


def test_create_endpoint_sends_tags_as_boto3_tag_list():
    client = MagicMock()

    create_endpoint(client, make_module(tags={"team": "ai"}))

    client.create_endpoint.assert_called_once_with(
        EndpointName="my-endpoint", EndpointConfigName="my-config", Tags=[{"Key": "team", "Value": "ai"}]
    )


def test_create_endpoint_without_tags_does_not_send_tags():
    client = MagicMock()

    create_endpoint(client, make_module())

    client.create_endpoint.assert_called_once_with(EndpointName="my-endpoint", EndpointConfigName="my-config")


def test_update_endpoint_swaps_the_endpoint_config():
    client = MagicMock()

    update_endpoint(client, make_module(endpoint_config_name="new-config"))

    client.update_endpoint.assert_called_once_with(EndpointName="my-endpoint", EndpointConfigName="new-config")


def test_delete_endpoint_deletes_by_name():
    client = MagicMock()

    delete_endpoint(client, make_module())

    client.delete_endpoint.assert_called_once_with(EndpointName="my-endpoint")


# --------------------------------------------------------------------------------------
# wait_for_endpoint
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("deleted,waiter_name", [(False, "endpoint_in_service"), (True, "endpoint_deleted")])
def test_wait_for_endpoint_uses_the_waiter_for_the_desired_state(deleted, waiter_name):
    client = MagicMock()

    wait_for_endpoint(client, make_module(), deleted=deleted)

    client.get_waiter.assert_called_once_with(waiter_name)


@pytest.mark.parametrize("wait_timeout,delay,attempts", [(600, 30, 20), (10, 10, 1), (0, 1, 1)])
def test_wait_for_endpoint_derives_delay_and_attempts_from_the_timeout(wait_timeout, delay, attempts):
    client = MagicMock()

    wait_for_endpoint(client, make_module(wait_timeout=wait_timeout))

    client.get_waiter.return_value.wait.assert_called_once_with(
        EndpointName="my-endpoint", WaiterConfig={"Delay": delay, "MaxAttempts": attempts}
    )


def test_wait_for_endpoint_failure_reports_the_failure_reason():
    client = MagicMock()
    client.get_waiter.return_value.wait.side_effect = WaiterError("EndpointInService", "terminal failure", {})
    client.describe_endpoint.return_value = {"EndpointStatus": "Failed", "FailureReason": "image pull failed"}
    module = make_module()

    with pytest.raises(FailJson):
        wait_for_endpoint(client, module)

    module.fail_json.assert_called_once_with(
        msg="Error waiting for endpoint my-endpoint to reach the desired state: image pull failed"
    )


@pytest.mark.parametrize(
    "describe",
    [
        {"return_value": {"EndpointStatus": "Creating"}},
        {"side_effect": validation_error("Could not find endpoint")},
    ],
    ids=["no-failure-reason", "endpoint-gone"],
)
def test_wait_for_endpoint_failure_without_reason_reports_the_waiter_error(describe):
    client = MagicMock()
    error = WaiterError("EndpointInService", "Max attempts exceeded", {})
    client.get_waiter.return_value.wait.side_effect = error
    client.describe_endpoint.configure_mock(**describe)
    module = make_module()

    with pytest.raises(FailJson):
        wait_for_endpoint(client, module)

    module.fail_json.assert_called_once_with(
        msg=f"Error waiting for endpoint my-endpoint to reach the desired state: {error}"
    )


def test_wait_for_endpoint_deletion_failure_does_not_describe_the_endpoint():
    client = MagicMock()
    error = WaiterError("EndpointDeleted", "Max attempts exceeded", {})
    client.get_waiter.return_value.wait.side_effect = error
    module = make_module()

    with pytest.raises(FailJson):
        wait_for_endpoint(client, module, deleted=True)

    client.describe_endpoint.assert_not_called()
    module.fail_json.assert_called_once_with(
        msg=f"Error waiting for endpoint my-endpoint to reach the desired state: {error}"
    )


# --------------------------------------------------------------------------------------
# reconcile_endpoint_tags
# --------------------------------------------------------------------------------------
@patch(f"{SAGEMAKER}.list_tags")
def test_reconcile_endpoint_tags_skips_reads_when_tags_omitted(mock_list_tags):
    client = MagicMock()

    assert reconcile_endpoint_tags(client, make_module(), {"EndpointArn": ENDPOINT_ARN}) is False

    mock_list_tags.assert_not_called()


@pytest.mark.parametrize("purge_tags", [False, True])
@patch(f"{SAGEMAKER}.list_tags")
def test_reconcile_endpoint_tags_preserves_or_removes_unrequested_tags(mock_list_tags, purge_tags):
    client = MagicMock()
    mock_list_tags.return_value = {"team": "ml", "owner": "data"}
    module = make_module(tags={"team": "ai"}, purge_tags=purge_tags)

    assert reconcile_endpoint_tags(client, module, {"EndpointArn": ENDPOINT_ARN}) is True

    mock_list_tags.assert_called_once_with(client, ENDPOINT_ARN)
    client.add_tags.assert_called_once_with(ResourceArn=ENDPOINT_ARN, Tags=[{"Key": "team", "Value": "ai"}])
    if purge_tags:
        client.delete_tags.assert_called_once_with(ResourceArn=ENDPOINT_ARN, TagKeys=["owner"])
    else:
        client.delete_tags.assert_not_called()


@patch(f"{SAGEMAKER}.list_tags")
def test_reconcile_endpoint_tags_check_mode_does_not_modify_tags(mock_list_tags):
    client = MagicMock()
    mock_list_tags.return_value = {"team": "ml", "owner": "data"}
    module = make_module(check_mode=True, tags={"team": "ai"})

    assert reconcile_endpoint_tags(client, module, {"EndpointArn": ENDPOINT_ARN}) is True

    client.add_tags.assert_not_called()
    client.delete_tags.assert_not_called()


@pytest.mark.parametrize("check_mode", [False, True])
@patch(f"{SAGEMAKER}.list_tags")
def test_reconcile_endpoint_tags_empty_tags_with_purge_removes_all_tags(mock_list_tags, check_mode):
    client = MagicMock()
    mock_list_tags.return_value = {"team": "ml", "owner": "data"}
    module = make_module(check_mode=check_mode, tags={})

    assert reconcile_endpoint_tags(client, module, {"EndpointArn": ENDPOINT_ARN}) is True

    client.add_tags.assert_not_called()
    if check_mode:
        client.delete_tags.assert_not_called()
    else:
        client.delete_tags.assert_called_once_with(ResourceArn=ENDPOINT_ARN, TagKeys=["team", "owner"])


@pytest.mark.parametrize("check_mode", [False, True])
@patch(f"{SAGEMAKER}.list_tags")
def test_reconcile_endpoint_tags_returns_false_when_tags_match(mock_list_tags, check_mode):
    client = MagicMock()
    mock_list_tags.return_value = {"team": "ai", "owner": "data"}
    module = make_module(check_mode=check_mode, tags={"team": "ai"}, purge_tags=False)

    assert reconcile_endpoint_tags(client, module, {"EndpointArn": ENDPOINT_ARN}) is False

    client.add_tags.assert_not_called()
    client.delete_tags.assert_not_called()
