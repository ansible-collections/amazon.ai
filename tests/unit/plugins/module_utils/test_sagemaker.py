#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for sagemaker module_utils."""

from unittest.mock import DEFAULT
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _endpoint_config_properties_differ
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _fresh_training_job
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _manage_training_job_absent
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _manage_training_job_present
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _manage_training_job_stopped
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _prepare_training_job_deletion
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _replace_training_job
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _training_job_mapping_differs
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _wait_for_warm_pool_termination
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_training_job
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_endpoint_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_model_package_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_training_job
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_endpoint_configs
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_model_package_groups
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_models
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_needs_replacement
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_package_group_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_endpoint_config_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_sagemaker_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import training_job_params
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_model_package_group_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_training_job
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_training_job
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_training_job_deletion
from ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_group_info import find_model_package_groups
from botocore.exceptions import ClientError
from botocore.exceptions import WaiterError


@pytest.mark.parametrize("wait", [False, True])
def test_fresh_training_job_returns_none_when_not_found(wait):
    client = MagicMock()
    module = MagicMock()
    module.params = {"training_job_name": "test-job", "wait": wait}
    prefix = "ansible_collections.amazon.ai.plugins.module_utils.sagemaker."
    read_function = "wait_for_training_job" if wait else "describe_training_job"

    with patch(prefix + read_function, return_value=None) as read_job:
        assert _fresh_training_job(client, module) is None

    if wait:
        read_job.assert_called_once_with(client, module, "test-job")
    else:
        read_job.assert_called_once_with(client, "test-job")


def test_delete_training_job_requires_supported_botocore():
    client = MagicMock()
    module = MagicMock()
    module.botocore_at_least.return_value = False
    module.fail_json.side_effect = RuntimeError("unsupported botocore")

    with pytest.raises(RuntimeError, match="unsupported botocore"):
        delete_training_job(client, module, "test-job")

    module.fail_json.assert_called_once_with(
        msg="Cannot delete training job test-job: deleting SageMaker training jobs requires botocore >= 1.40.61."
    )
    client.delete_training_job.assert_not_called()


def test_delete_training_job_calls_api_with_supported_botocore():
    client = MagicMock()
    module = MagicMock()
    module.botocore_at_least.return_value = True

    delete_training_job(client, module, "test-job")

    client.delete_training_job.assert_called_once_with(TrainingJobName="test-job")


def test_delete_training_job_reports_aws_error_message():
    client = MagicMock()
    module = MagicMock()
    module.botocore_at_least.return_value = True
    module.fail_json.side_effect = RuntimeError("delete failed")
    client.delete_training_job.side_effect = ClientError(
        {"Error": {"Code": "ResourceInUse", "Message": "The training job is not terminal."}},
        "DeleteTrainingJob",
    )

    with pytest.raises(RuntimeError, match="delete failed"):
        delete_training_job(client, module, "test-job")

    module.fail_json.assert_called_once_with(
        msg=(
            "Cannot delete training job test-job; it must be Completed, Failed, or Stopped "
            "and must not have an Available warm pool. AWS returned: The training job is not terminal."
        )
    )


def test_describe_training_job_returns_none_when_missing():
    client = MagicMock()
    client.describe_training_job.side_effect = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "Requested resource not found."}},
        "DescribeTrainingJob",
    )

    assert describe_training_job(client, "missing-job") is None


def test_describe_training_job_reraises_other_validation_errors():
    client = MagicMock()
    client.describe_training_job.side_effect = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "Some other validation problem."}},
        "DescribeTrainingJob",
    )

    with pytest.raises(ClientError):
        describe_training_job(client, "bad-job")


def test_wait_for_training_job_handles_status_response_without_error_key():
    client = MagicMock()
    module = MagicMock()
    module.params = {"wait_timeout": 10}
    client.get_waiter.return_value.wait.side_effect = WaiterError(
        name="training_job_completed_or_stopped",
        reason="Waiter encountered a terminal failure state.",
        last_response={"TrainingJobStatus": "Failed"},
    )
    expected = {"TrainingJobStatus": "Failed"}

    with patch(
        "ansible_collections.amazon.ai.plugins.module_utils.sagemaker.describe_training_job", return_value=expected
    ) as describe:
        assert wait_for_training_job(client, module, "test-job", allow_failed=True) == expected

    describe.assert_called_once_with(client, "test-job")


def test_wait_for_training_job_handles_error_response():
    client = MagicMock()
    module = MagicMock()
    module.params = {"wait_timeout": 10}
    client.get_waiter.return_value.wait.side_effect = WaiterError(
        name="training_job_completed_or_stopped",
        reason="An error occurred (ResourceNotFound): Job not found.",
        last_response={"Error": {"Code": "ResourceNotFound", "Message": "Job not found."}},
    )

    assert wait_for_training_job(client, module, "missing-job") is None


@pytest.mark.parametrize(
    ("manage", "message"),
    [
        (_manage_training_job_present, "Cannot manage training job test-job while it is being deleted."),
        (_manage_training_job_stopped, "Cannot stop training job test-job while it is being deleted."),
    ],
)
def test_training_job_deleting_status_fails_clearly(manage, message):
    client = MagicMock()
    module = MagicMock()
    module.params = {"training_job_name": "test-job", "force": False}
    module.check_mode = False
    module.fail_json.side_effect = RuntimeError(message)

    with pytest.raises(RuntimeError, match=message):
        manage(client, module, {"TrainingJobStatus": "Deleting"})

    module.fail_json.assert_called_once_with(msg=message)
    client.create_training_job.assert_not_called()
    client.stop_training_job.assert_not_called()


def test_training_job_mapping_differs_limits_recursion_depth():
    cyclic_mapping = {}
    cyclic_mapping["self"] = cyclic_mapping

    with pytest.raises(ValueError, match="Maximum recursion depth exceeded"):
        _training_job_mapping_differs(cyclic_mapping, {})


@pytest.mark.parametrize(
    ("wait_function", "responses", "expected"),
    [
        (
            wait_for_training_job_deletion,
            [{"TrainingJobStatus": "Deleting"}, {"TrainingJobStatus": "Deleting"}, None],
            None,
        ),
        (
            _wait_for_warm_pool_termination,
            [
                {"WarmPoolStatus": {"Status": "Available"}},
                {"WarmPoolStatus": {"Status": "Available"}},
                {"WarmPoolStatus": {"Status": "Terminating"}},
            ],
            {"WarmPoolStatus": {"Status": "Terminating"}},
        ),
    ],
)
def test_training_job_waits_through_final_poll(wait_function, responses, expected):
    client = MagicMock()
    module = MagicMock()
    module.params = {"wait_timeout": 20}
    current_time = [0]

    def sleep(duration):
        current_time[0] += duration

    prefix = "ansible_collections.amazon.ai.plugins.module_utils.sagemaker."
    with patch(prefix + "time.monotonic", side_effect=lambda: current_time[0]):
        with patch(prefix + "time.sleep", side_effect=sleep) as sleep_mock:
            with patch(prefix + "describe_training_job", side_effect=responses) as describe:
                assert wait_function(client, module, "test-job") == expected

    assert sleep_mock.call_args_list == [call(15), call(5)]
    assert describe.call_count == 3


def test_training_job_params_uses_sagemaker_volume_size_casing():
    module = MagicMock()
    module.params = {
        "training_job_name": "test-job",
        "role_arn": "arn:aws:iam::123456789012:role/test-role",
        "resource_config": {
            "instance_type": "ml.m5.large",
            "instance_count": 1,
            "volume_size_in_gb": 10,
        },
    }

    resource_config = training_job_params(module)["ResourceConfig"]

    assert resource_config == {
        "InstanceType": "ml.m5.large",
        "InstanceCount": 1,
        "VolumeSizeInGB": 10,
    }


def test_training_job_params_uses_sagemaker_profiler_rule_volume_size_casing():
    module = MagicMock()
    module.params = {
        "training_job_name": "test-job",
        "profiler_rule_configurations": [
            {
                "rule_configuration_name": "test-rule",
                "rule_evaluator_image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/rule:latest",
                "volume_size_in_gb": 30,
            }
        ],
    }

    profiler_rule = training_job_params(module)["ProfilerRuleConfigurations"][0]

    assert profiler_rule["VolumeSizeInGB"] == 30
    assert "VolumeSizeInGb" not in profiler_rule


def test_update_training_job_uses_sagemaker_profiler_rule_volume_size_casing():
    client = MagicMock()
    module = MagicMock()
    module.params = {
        "training_job_name": "test-job",
        "profiler_rule_configurations": [
            {
                "rule_configuration_name": "test-rule",
                "rule_evaluator_image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/rule:latest",
                "volume_size_in_gb": 30,
            }
        ],
    }
    module.check_mode = False

    assert update_training_job(client, module, {"ProfilerRuleConfigurations": []})
    client.update_training_job.assert_called_once_with(
        TrainingJobName="test-job",
        ProfilerRuleConfigurations=[
            {
                "RuleConfigurationName": "test-rule",
                "RuleEvaluatorImage": "123456789012.dkr.ecr.us-east-1.amazonaws.com/rule:latest",
                "VolumeSizeInGB": 30,
            }
        ],
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("profiler_config", {}),
        ("remote_debug_config", {"enable_remote_debug": None}),
    ],
)
def test_update_training_job_skips_empty_nested_update_params(field, value):
    client = MagicMock()
    module = MagicMock()
    module.params = {"training_job_name": "test-job", field: value}
    module.check_mode = False

    assert not update_training_job(client, module, {})
    client.update_training_job.assert_not_called()


def test_update_training_job_warm_pool_retention_check_mode():
    client = MagicMock()
    module = MagicMock()
    module.params = {
        "training_job_name": "test-job",
        "resource_config": {"keep_alive_period_in_seconds": 600},
        "wait": True,
    }
    module.check_mode = True
    existing = {
        "ResourceConfig": {"KeepAlivePeriodInSeconds": 300},
        "WarmPoolStatus": {"Status": "Available"},
    }

    assert update_training_job(client, module, existing)
    client.update_training_job.assert_not_called()


def test_update_training_job_warm_pool_retention_updates_value():
    client = MagicMock()
    module = MagicMock()
    module.params = {
        "training_job_name": "test-job",
        "resource_config": {"keep_alive_period_in_seconds": 600},
        "wait": True,
    }
    module.check_mode = False
    existing = {
        "ResourceConfig": {"KeepAlivePeriodInSeconds": 300},
        "WarmPoolStatus": {"Status": "Available"},
    }

    assert update_training_job(client, module, existing)
    client.update_training_job.assert_called_once_with(
        TrainingJobName="test-job",
        ResourceConfig={"KeepAlivePeriodInSeconds": 600},
    )


def test_update_training_job_warm_pool_retention_is_idempotent():
    client = MagicMock()
    module = MagicMock()
    module.params = {
        "training_job_name": "test-job",
        "resource_config": {"keep_alive_period_in_seconds": 600},
        "wait": True,
    }
    module.check_mode = False
    existing = {
        "ResourceConfig": {"KeepAlivePeriodInSeconds": 600},
        "WarmPoolStatus": {"Status": "Available"},
    }

    assert not update_training_job(client, module, existing)
    client.update_training_job.assert_not_called()


def test_update_training_job_zero_retention_without_warm_pool():
    client = MagicMock()
    module = MagicMock()
    module.params = {
        "training_job_name": "test-job",
        "resource_config": {"keep_alive_period_in_seconds": 0},
        "wait": False,
    }
    module.check_mode = False
    existing = {"ResourceConfig": {}}

    assert update_training_job(client, module, existing)
    client.update_training_job.assert_called_once_with(
        TrainingJobName="test-job",
        ResourceConfig={"KeepAlivePeriodInSeconds": 0},
    )


def test_update_training_job_nonzero_retention_requires_available_warm_pool():
    client = MagicMock()
    module = MagicMock()
    module.params = {
        "training_job_name": "test-job",
        "resource_config": {"keep_alive_period_in_seconds": 600},
        "wait": True,
    }
    module.check_mode = False
    module.fail_json.side_effect = RuntimeError("warm pool must be available")
    existing = {"ResourceConfig": {"KeepAlivePeriodInSeconds": 0}}

    with pytest.raises(RuntimeError, match="warm pool must be available"):
        update_training_job(client, module, existing)

    module.fail_json.assert_called_once()
    client.update_training_job.assert_not_called()


@pytest.mark.parametrize("replace", [False, True])
@pytest.mark.parametrize("status", ["InProgress", "Stopping"])
def test_training_job_deletion_stops_before_proceeding_without_wait(replace, status):
    client = MagicMock()
    module = MagicMock()
    module.params = {"training_job_name": "test-job", "wait": False}
    module.check_mode = False
    existing = {"TrainingJobStatus": status}
    refreshed = {"TrainingJobStatus": "Stopping" if status == "InProgress" else "Completed"}
    purpose = "replacement" if replace else "deletion"
    manage = _replace_training_job if replace else _manage_training_job_absent

    with patch("ansible_collections.amazon.ai.plugins.module_utils.sagemaker.stop_training_job") as stop:
        with patch(
            "ansible_collections.amazon.ai.plugins.module_utils.sagemaker.describe_training_job",
            return_value=refreshed,
        ):
            job, changed, msg = manage(client, module, existing)

    assert job == refreshed
    assert changed == (status == "InProgress")
    if status == "InProgress":
        stop.assert_called_once_with(client, "test-job")
        assert msg == f"Training job test-job is stopping before {purpose}."
    else:
        stop.assert_not_called()
        assert msg == f"Training job test-job is already stopping before {purpose}."
    client.delete_training_job.assert_not_called()


def test_training_job_deletion_refreshes_status_before_deleting():
    client = MagicMock()
    module = MagicMock()
    module.params = {"training_job_name": "test-job", "wait": True}
    module.fail_json.side_effect = RuntimeError("job became active")
    stale_job = {"TrainingJobStatus": "Completed"}
    refreshed_job = {"TrainingJobStatus": "InProgress"}

    with patch(
        "ansible_collections.amazon.ai.plugins.module_utils.sagemaker.describe_training_job",
        return_value=refreshed_job,
    ) as describe:
        with pytest.raises(RuntimeError, match="job became active"):
            _prepare_training_job_deletion(client, module, stale_job, "delete")

    describe.assert_called_once_with(client, "test-job")
    module.fail_json.assert_called_once_with(msg="Cannot delete training job test-job while it is in state InProgress.")
    client.delete_training_job.assert_not_called()


def test_training_job_deletion_handles_job_disappearing_before_delete():
    client = MagicMock()
    module = MagicMock()
    module.params = {"training_job_name": "test-job", "wait": True}
    stale_job = {"TrainingJobStatus": "Completed"}

    with patch(
        "ansible_collections.amazon.ai.plugins.module_utils.sagemaker.describe_training_job", return_value=None
    ) as describe:
        job, changed, msg = _prepare_training_job_deletion(client, module, stale_job, "delete")

    describe.assert_called_once_with(client, "test-job")
    assert job is None
    assert not changed
    assert msg == "Training job test-job no longer exists before deletion."
    client.delete_training_job.assert_not_called()


@pytest.mark.parametrize("wait", [False, True])
@pytest.mark.parametrize("replace", [False, True])
def test_training_job_deletion_handles_warm_pool_and_replacement(replace, wait):
    client = MagicMock()
    module = MagicMock()
    module.params = {"training_job_name": "test-job", "wait": wait}
    module.check_mode = False
    existing = {"TrainingJobStatus": "Completed", "WarmPoolStatus": {"Status": "Available"}}
    final_job = {"TrainingJobStatus": "Completed"}
    manage = _replace_training_job if replace else _manage_training_job_absent
    with patch.multiple(
        "ansible_collections.amazon.ai.plugins.module_utils.sagemaker",
        _set_training_job_warm_pool_retention=DEFAULT,
        _wait_for_warm_pool_termination=DEFAULT,
        describe_training_job=DEFAULT,
        delete_training_job=DEFAULT,
        wait_for_training_job_deletion=DEFAULT,
        _fresh_training_job=DEFAULT,
    ) as helpers:
        helpers["_wait_for_warm_pool_termination"].return_value = final_job
        helpers["describe_training_job"].side_effect = [existing, final_job]
        helpers["_fresh_training_job"].return_value = final_job
        job, changed, msg = manage(client, module, existing)

    helpers["_set_training_job_warm_pool_retention"].assert_called_once_with(client, "test-job", 0)
    assert changed
    if not wait:
        purpose = "replacement" if replace else "deletion"
        assert job == final_job
        assert msg == f"Training job test-job warm pool is terminating before {purpose}."
        helpers["_wait_for_warm_pool_termination"].assert_not_called()
        helpers["delete_training_job"].assert_not_called()
        client.create_training_job.assert_not_called()
        return
    helpers["_wait_for_warm_pool_termination"].assert_called_once_with(client, module, "test-job")
    helpers["delete_training_job"].assert_called_once_with(client, module, "test-job")
    helpers["wait_for_training_job_deletion"].assert_called_once_with(client, module, "test-job")
    assert job == final_job
    if replace:
        client.create_training_job.assert_called_once_with(**training_job_params(module))
        assert msg == "Training job test-job replaced with a new execution."
    else:
        client.create_training_job.assert_not_called()
        assert msg == "Training job test-job deleted successfully."


@pytest.mark.parametrize("changed", [False, True])
@pytest.mark.parametrize("check_mode", [False, True])
def test_training_job_present_preserves_update_results(changed, check_mode):
    module = MagicMock()
    module.params = {"training_job_name": "test-job", "force": False}
    module.check_mode = check_mode
    existing = {"TrainingJobStatus": "Completed"}
    prefix = "ansible_collections.amazon.ai.plugins.module_utils.sagemaker."
    with patch(prefix + "training_job_needs_replacement", return_value=[]):
        with patch(prefix + "update_training_job", return_value=changed):
            with patch(prefix + "reconcile_training_job_tags", return_value=False):
                with patch(prefix + "describe_training_job", return_value=existing) as describe:
                    job, result_changed, msg = _manage_training_job_present(MagicMock(), module, existing)
    assert job == existing
    assert result_changed == changed
    assert describe.call_count == (0 if check_mode else 1)
    if not changed:
        assert msg == "Training job test-job is already up to date."
    elif check_mode:
        assert msg == "Check mode: would have updated training job test-job."
    else:
        assert msg == "Training job test-job updated successfully."


@pytest.mark.parametrize(
    "message",
    [
        'Could not find endpoint configuration "missing-config".',
        "Could not find endpoint configuration",
    ],
)
def test_describe_endpoint_config_returns_none_when_missing(message):
    client = MagicMock()
    client.describe_endpoint_config.side_effect = ClientError(
        {"Error": {"Code": "ValidationException", "Message": message}},
        "DescribeEndpointConfig",
    )

    assert describe_endpoint_config(client, "missing-config") is None


def test_describe_endpoint_config_reraises_other_validation_errors():
    client = MagicMock()
    client.describe_endpoint_config.side_effect = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "Some other validation problem."}},
        "DescribeEndpointConfig",
    )

    with pytest.raises(ClientError):
        describe_endpoint_config(client, "bad-config")


def test_reconcile_endpoint_config_tags_check_mode_does_not_modify_tags():
    client = MagicMock()
    module = MagicMock()
    module.check_mode = True
    module.params = {"tags": {"environment": "test"}, "purge_tags": True}
    existing = {"EndpointConfigArn": "arn:aws:sagemaker:region:account:endpoint-config/test"}

    client.get_paginator.return_value.paginate.return_value.build_full_result.return_value = {
        "Tags": [{"Key": "environment", "Value": "production"}, {"Key": "owner", "Value": "team"}]
    }

    assert reconcile_endpoint_config_tags(client, module, existing)
    client.add_tags.assert_not_called()
    client.delete_tags.assert_not_called()


def test_reconcile_sagemaker_tags_skips_lookup_when_tags_are_omitted():
    client = MagicMock()
    module = MagicMock()
    module.params = {"tags": None}

    assert not reconcile_sagemaker_tags(client, module, "arn:aws:sagemaker:region:account:resource/test")
    client.get_paginator.assert_not_called()


def test_reconcile_endpoint_config_tags_modifies_tags():
    client = MagicMock()
    module = MagicMock()
    module.check_mode = False
    module.params = {"tags": {"environment": "test"}, "purge_tags": True}
    existing = {"EndpointConfigArn": "arn:aws:sagemaker:region:account:endpoint-config/test"}

    client.get_paginator.return_value.paginate.return_value.build_full_result.return_value = {
        "Tags": [{"Key": "environment", "Value": "production"}, {"Key": "owner", "Value": "team"}]
    }

    assert reconcile_endpoint_config_tags(client, module, existing)
    client.add_tags.assert_called_once_with(
        ResourceArn="arn:aws:sagemaker:region:account:endpoint-config/test",
        Tags=[{"Key": "environment", "Value": "test"}],
    )
    client.delete_tags.assert_called_once_with(
        ResourceArn="arn:aws:sagemaker:region:account:endpoint-config/test",
        TagKeys=["owner"],
    )


def test_reconcile_endpoint_config_tags_purge_false_only_adds_tags():
    client = MagicMock()
    module = MagicMock()
    module.check_mode = False
    module.params = {"tags": {"environment": "test"}, "purge_tags": False}
    existing = {"EndpointConfigArn": "arn:aws:sagemaker:region:account:endpoint-config/test"}

    client.get_paginator.return_value.paginate.return_value.build_full_result.return_value = {
        "Tags": [{"Key": "environment", "Value": "production"}, {"Key": "owner", "Value": "team"}]
    }

    assert reconcile_endpoint_config_tags(client, module, existing)
    client.add_tags.assert_called_once_with(
        ResourceArn="arn:aws:sagemaker:region:account:endpoint-config/test",
        Tags=[{"Key": "environment", "Value": "test"}],
    )
    client.delete_tags.assert_not_called()


def test_list_endpoint_configs_limits_total_results():
    client = MagicMock()
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value.build_full_result.return_value = {"EndpointConfigs": []}

    list_endpoint_configs(client, MaxResults=1)

    paginator.paginate.assert_called_once_with(PaginationConfig={"MaxItems": 1})


def test_endpoint_config_properties_differ_ignores_name_and_tags():
    desired = {
        "EndpointConfigName": "config",
        "Tags": [{"Key": "environment", "Value": "test"}],
        "KmsKeyId": "key",
    }
    existing = {"EndpointConfigName": "config", "Tags": [{"Key": "owner", "Value": "team"}], "KmsKeyId": "key"}

    assert not _endpoint_config_properties_differ(desired, existing)


def test_endpoint_config_properties_differ_detects_variant_changes():
    desired = {"ProductionVariants": [{"VariantName": "AllTraffic", "InitialInstanceCount": 2}]}
    existing = {"ProductionVariants": [{"VariantName": "AllTraffic", "InitialInstanceCount": 1}]}

    assert _endpoint_config_properties_differ(desired, existing)


def test_endpoint_config_properties_differ_matches_variants_by_name():
    desired = {
        "ProductionVariants": [
            {"VariantName": "Blue", "ModelName": "blue-model"},
            {"VariantName": "Green", "ModelName": "green-model"},
        ]
    }
    existing = {
        "ProductionVariants": [
            {"VariantName": "Green", "ModelName": "green-model", "InitialInstanceCount": 1},
            {"VariantName": "Blue", "ModelName": "blue-model", "InitialInstanceCount": 1},
        ]
    }

    assert not _endpoint_config_properties_differ(desired, existing)


def test_endpoint_config_properties_differ_ignores_aws_nested_defaults():
    desired = {
        "ProductionVariants": [
            {
                "VariantName": "Serverless",
                "ServerlessConfig": {"MemorySizeInMB": 2048},
            }
        ]
    }
    existing = {
        "ProductionVariants": [
            {
                "VariantName": "Serverless",
                "ServerlessConfig": {
                    "MemorySizeInMB": 2048,
                    "MaxConcurrency": 10,
                },
            }
        ]
    }

    assert not _endpoint_config_properties_differ(desired, existing)


def test_endpoint_config_properties_differ_matches_shadow_variants_by_name():
    desired = {
        "ShadowProductionVariants": [
            {"VariantName": "Blue", "ModelName": "blue-model"},
            {"VariantName": "Green", "ModelName": "green-model"},
        ]
    }
    existing = {
        "ShadowProductionVariants": [
            {"VariantName": "Green", "ModelName": "green-model", "InitialInstanceCount": 1},
            {"VariantName": "Blue", "ModelName": "blue-model", "InitialInstanceCount": 1},
        ]
    }

    assert not _endpoint_config_properties_differ(desired, existing)


def test_endpoint_config_properties_differ_ignores_shadow_variant_nested_defaults():
    desired = {
        "ShadowProductionVariants": [
            {
                "VariantName": "Serverless",
                "ServerlessConfig": {"MemorySizeInMB": 2048},
            }
        ]
    }
    existing = {
        "ShadowProductionVariants": [
            {
                "VariantName": "Serverless",
                "ServerlessConfig": {
                    "MemorySizeInMB": 2048,
                    "MaxConcurrency": 10,
                    "ProvisionedConcurrency": 5,
                },
            }
        ]
    }

    assert not _endpoint_config_properties_differ(desired, existing)


def test_endpoint_config_properties_differ_detects_shadow_variant_changes():
    desired = {
        "ShadowProductionVariants": [
            {
                "VariantName": "Serverless",
                "ServerlessConfig": {"MemorySizeInMB": 4096},
            }
        ]
    }
    existing = {
        "ShadowProductionVariants": [
            {
                "VariantName": "Serverless",
                "ServerlessConfig": {"MemorySizeInMB": 2048, "MaxConcurrency": 10},
            }
        ]
    }

    assert _endpoint_config_properties_differ(desired, existing)


def test_endpoint_config_properties_differ_detects_renamed_shadow_variant():
    desired = {"ShadowProductionVariants": [{"VariantName": "Green", "ModelName": "green-model"}]}
    existing = {"ShadowProductionVariants": [{"VariantName": "Blue", "ModelName": "green-model"}]}

    assert _endpoint_config_properties_differ(desired, existing)


def test_endpoint_config_properties_differ_ignores_omitted_network_isolation():
    desired = {"EnableNetworkIsolation": False}
    existing = {"EnableNetworkIsolation": False}

    assert not _endpoint_config_properties_differ(desired, existing)


def test_endpoint_config_properties_differ_treats_missing_network_isolation_as_false():
    desired = {"EnableNetworkIsolation": False}
    existing = {}

    assert not _endpoint_config_properties_differ(desired, existing)


class TestListModels:
    """Test cases for list_models function."""

    def test_list_models_forwards_params_and_extracts_models(self):
        """list_models should forward filter params to the paginator and return the Models list."""
        client = MagicMock()
        paginator = MagicMock()
        client.get_paginator.return_value = paginator
        paginator.paginate.return_value.build_full_result.return_value = {
            "Models": [{"ModelName": "model-a"}, {"ModelName": "model-b"}],
        }

        result = list_models(client, NameContains="test")

        client.get_paginator.assert_called_once_with("list_models")
        paginator.paginate.assert_called_once_with(NameContains="test")
        assert result == [{"ModelName": "model-a"}, {"ModelName": "model-b"}]

    def test_list_models_empty_result(self):
        """list_models should return an empty list when there are no models."""
        client = MagicMock()
        paginator = MagicMock()
        client.get_paginator.return_value = paginator
        paginator.paginate.return_value.build_full_result.return_value = {"Models": []}

        assert list_models(client) == []

    def test_list_models_max_results_uses_pagination_config(self):
        """MaxResults should be translated into PaginationConfig={'MaxItems': ...} to cap total results."""
        client = MagicMock()
        paginator = MagicMock()
        client.get_paginator.return_value = paginator
        paginator.paginate.return_value.build_full_result.return_value = {
            "Models": [{"ModelName": "model-a"}],
        }

        result = list_models(client, NameContains="test", MaxResults=5)

        paginator.paginate.assert_called_once_with(NameContains="test", PaginationConfig={"MaxItems": 5})
        assert result == [{"ModelName": "model-a"}]


class TestListModelPackageGroups:
    """Test cases for list_model_package_groups function."""

    def test_list_model_package_groups_forwards_params_and_extracts_groups(self):
        """list_model_package_groups should forward paging params and return the group list."""
        client = MagicMock()
        paginator = MagicMock()
        client.get_paginator.return_value = paginator
        paginator.paginate.return_value.build_full_result.return_value = {
            "ModelPackageGroupSummaryList": [
                {"ModelPackageGroupName": "group-a"},
                {"ModelPackageGroupName": "group-b"},
            ],
        }

        result = list_model_package_groups(client, NameContains="demo")

        client.get_paginator.assert_called_once_with("list_model_package_groups")
        paginator.paginate.assert_called_once_with(NameContains="demo")
        assert result == [{"ModelPackageGroupName": "group-a"}, {"ModelPackageGroupName": "group-b"}]

    def test_list_model_package_groups_max_items_uses_pagination_config(self):
        """max_items should be translated into PaginationConfig={'MaxItems': ...}."""
        client = MagicMock()
        paginator = MagicMock()
        client.get_paginator.return_value = paginator
        paginator.paginate.return_value.build_full_result.return_value = {
            "ModelPackageGroupSummaryList": [{"ModelPackageGroupName": "group-a"}],
        }

        result = list_model_package_groups(client, NameContains="demo", max_items=5)

        paginator.paginate.assert_called_once_with(NameContains="demo", PaginationConfig={"MaxItems": 5})
        assert result == [{"ModelPackageGroupName": "group-a"}]


class TestDescribeModelPackageGroup:
    """Test cases for describe_model_package_group function."""

    def test_describe_model_package_group_returns_none_for_missing_group(self):
        """A missing model package group should be treated as a non-fatal lookup miss."""
        client = MagicMock()
        client.describe_model_package_group.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ValidationException",
                    "Message": "Model package group does not exist.",
                }
            },
            "DescribeModelPackageGroup",
        )

        assert describe_model_package_group(client, "missing-group") is None


class TestModelPackageGroupNeedsUpdate:
    """Test cases for model_package_group_needs_update function."""

    def test_description_drift_requires_update(self):
        """Changing the model package group description should require replacement semantics."""
        existing = {"ModelPackageGroupDescription": "old"}
        module = MagicMock()
        module.params = {"model_package_group_description": "new"}

        assert model_package_group_needs_update(existing, module)

    def test_missing_desired_description_is_not_drift(self):
        """An omitted desired description should not trigger drift when existing data is present."""
        existing = {"ModelPackageGroupDescription": "same"}
        module = MagicMock()
        module.params = {"model_package_group_description": None}

        assert not model_package_group_needs_update(existing, module)


class TestUpdateModelPackageGroupTags:
    """Test cases for update_model_package_group_tags function."""

    @patch(
        "ansible_collections.amazon.ai.plugins.module_utils.sagemaker.list_tags",
        return_value={"keep": "value", "remove": "old"},
    )
    def test_purge_tags_false_keeps_unmentioned_keys(self, mock_list_tags):
        """When purge_tags is false, extra tags should stay untouched."""
        client = MagicMock()
        module = MagicMock()
        module.check_mode = False
        module.params = {"tags": {"keep": "new"}, "purge_tags": False}

        result = update_model_package_group_tags(
            client,
            module,
            "arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo",
        )

        client.add_tags.assert_called_once_with(
            ResourceArn="arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo",
            Tags=[{"Key": "keep", "Value": "new"}],
        )
        client.delete_tags.assert_not_called()
        assert result == (True, "Model package group tags updated successfully.")
        mock_list_tags.assert_called_once_with(
            client, "arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo"
        )

    @patch(
        "ansible_collections.amazon.ai.plugins.module_utils.sagemaker.list_tags",
        return_value={"keep": "old", "remove": "old"},
    )
    def test_purge_tags_true_removes_unmentioned_keys(self, mock_list_tags):
        """When purge_tags is true, tags omitted from the desired set should be removed."""
        client = MagicMock()
        module = MagicMock()
        module.check_mode = False
        module.params = {"tags": {"keep": "new"}, "purge_tags": True}

        result = update_model_package_group_tags(
            client,
            module,
            "arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo",
        )

        client.add_tags.assert_called_once_with(
            ResourceArn="arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo",
            Tags=[{"Key": "keep", "Value": "new"}],
        )
        client.delete_tags.assert_called_once_with(
            ResourceArn="arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo", TagKeys=["remove"]
        )
        assert result == (True, "Model package group tags updated successfully.")
        mock_list_tags.assert_called_once_with(
            client, "arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo"
        )


class TestFindModelPackageGroups:
    """Test model package group info tag filtering."""

    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_group_info.list_tags")
    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_group_info.list_model_package_groups")
    def test_tag_filter_excludes_mismatched_values(self, mock_list_model_package_groups, mock_list_tags):
        """A desired tag value must match the group's actual tag value."""
        client = MagicMock()
        module = MagicMock()
        module.params = {
            "model_package_group_name": None,
            "tags": {"project": "demo"},
        }
        mock_list_model_package_groups.return_value = [
            {
                "ModelPackageGroupName": "group-a",
                "ModelPackageGroupArn": "arn:a",
            }
        ]
        mock_list_tags.return_value = {"project": "other"}

        assert find_model_package_groups(client, module) == []


class TestModelNeedsReplacement:
    """Test cases for model_needs_replacement function."""

    def _create_mock_module(
        self,
        model_name="test-model",
        primary_container=None,
        execution_role_arn="arn:role",
        vpc_config=None,
        enable_network_isolation=None,
    ):
        """Create a mock module with test parameters."""
        module = MagicMock()
        default_primary_container = {
            "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
            "environment": {},
        }
        primary_container = dict(default_primary_container, **(primary_container or {}))
        module.params = {
            "model_name": model_name,
            "primary_container": primary_container,
            "execution_role_arn": execution_role_arn,
            "vpc_config": vpc_config,
            "enable_network_isolation": enable_network_isolation,
            "tags": None,
        }
        return module

    def test_same_container_no_replacement(self):
        """Model with identical container should not need replacement."""
        existing = {
            "ModelName": "test-model",
            "PrimaryContainer": {
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
            },
            "ExecutionRoleArn": "arn:role",
        }
        module = self._create_mock_module()

        assert not model_needs_replacement(existing, module)

    def test_default_empty_environment_missing_from_existing_no_replacement(self):
        """Default empty environment is equivalent to an omitted AWS Environment."""
        existing = {
            "ModelName": "test-model",
            "PrimaryContainer": {
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
            },
            "ExecutionRoleArn": "arn:role",
        }
        module = self._create_mock_module()

        assert not model_needs_replacement(existing, module)

    def test_different_image_needs_replacement(self):
        """Model with different image should need replacement."""
        existing = {
            "ModelName": "test-model",
            "PrimaryContainer": {
                "Image": "old-image:old",
            },
            "ExecutionRoleArn": "arn:role",
        }
        module = self._create_mock_module()

        assert model_needs_replacement(existing, module)

    def test_different_execution_role_needs_replacement(self):
        """Model with different execution role should need replacement."""
        existing = {
            "ModelName": "test-model",
            "PrimaryContainer": {
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
            },
            "ExecutionRoleArn": "arn:old-role",
        }
        module = self._create_mock_module(execution_role_arn="arn:new-role")

        assert model_needs_replacement(existing, module)

    def test_existing_model_data_url_desired_has_none(self):
        """
        When user omits model_data_url/source but existing has ModelDataUrl,
        this is NOT drift because the model hasn't actually changed.
        """
        existing = {
            "ModelName": "test-model",
            "PrimaryContainer": {
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
                "ModelDataUrl": "s3://bucket/model.tar.gz",
            },
            "ExecutionRoleArn": "arn:role",
        }
        module = self._create_mock_module()

        assert not model_needs_replacement(existing, module)

    def test_existing_model_data_source_desired_has_none(self):
        """
        When user omits model_data_url/source but existing has ModelDataSource,
        this is NOT drift. AWS transforms ModelDataUrl to ModelDataSource.
        """
        existing = {
            "ModelName": "test-model",
            "PrimaryContainer": {
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
                "ModelDataSource": {
                    "S3DataSource": {
                        "S3Uri": "s3://bucket/model.tar.gz",
                        "S3DataType": "S3Object",
                        "CompressionType": "None",
                    }
                },
            },
            "ExecutionRoleArn": "arn:role",
        }
        module = self._create_mock_module()

        assert not model_needs_replacement(existing, module)

    def test_model_data_url_vs_model_data_source_switch(self):
        """
        When both point to same S3 URI, AWS field format transformation is not drift.
        """
        existing = {
            "ModelName": "test-model",
            "PrimaryContainer": {
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
                "ModelDataUrl": "s3://bucket/model.tar.gz",
            },
            "ExecutionRoleArn": "arn:role",
        }
        module = self._create_mock_module(
            primary_container={
                "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
                "model_data_source": {
                    "s3_data_source": {
                        "s3_uri": "s3://bucket/model.tar.gz",
                        "s3_data_type": "S3Object",
                        "compression_type": "None",
                    }
                },
            }
        )

        # Same S3 URI, different field format - not drift
        assert not model_needs_replacement(existing, module)

    def test_vpc_config_change_needs_replacement(self):
        """Model with different VPC config should need replacement."""
        existing = {
            "ModelName": "test-model",
            "PrimaryContainer": {
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
            },
            "ExecutionRoleArn": "arn:role",
            "VpcConfig": {
                "Subnets": ["subnet-old"],
            },
        }
        module = self._create_mock_module(
            vpc_config={
                "subnets": ["subnet-new"],
            }
        )

        assert model_needs_replacement(existing, module)

    def test_vpc_config_reordered_lists_no_replacement(self):
        """VPC subnets/security groups returned in a different order should not need replacement."""
        existing = {
            "ModelName": "test-model",
            "PrimaryContainer": {
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
            },
            "ExecutionRoleArn": "arn:role",
            "VpcConfig": {
                "Subnets": ["subnet-b", "subnet-a"],
                "SecurityGroupIds": ["sg-2", "sg-1"],
            },
        }
        module = self._create_mock_module(
            vpc_config={
                "subnets": ["subnet-a", "subnet-b"],
                "security_group_ids": ["sg-1", "sg-2"],
            }
        )

        assert not model_needs_replacement(existing, module)

    def test_enable_network_isolation_change_needs_replacement(self):
        """Model with different network isolation should need replacement."""
        existing = {
            "ModelName": "test-model",
            "PrimaryContainer": {
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
            },
            "ExecutionRoleArn": "arn:role",
            "EnableNetworkIsolation": False,
        }
        module = self._create_mock_module(enable_network_isolation=True)

        assert model_needs_replacement(existing, module)

    def test_enable_network_isolation_explicit_false_vs_missing_no_replacement(self):
        """Explicitly desired False network isolation should not need replacement when AWS omits the key."""
        existing = {
            "ModelName": "test-model",
            "PrimaryContainer": {
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
            },
            "ExecutionRoleArn": "arn:role",
        }
        module = self._create_mock_module(enable_network_isolation=False)

        assert not model_needs_replacement(existing, module)

    def test_enable_network_isolation_desired_true_vs_missing_needs_replacement(self):
        """Desired True network isolation should need replacement when AWS omits the key (implying False)."""
        existing = {
            "ModelName": "test-model",
            "PrimaryContainer": {
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
            },
            "ExecutionRoleArn": "arn:role",
        }
        module = self._create_mock_module(enable_network_isolation=True)

        assert model_needs_replacement(existing, module)

    def test_different_s3_uri_needs_replacement(self):
        """Model with different S3 data location should need replacement."""
        existing = {
            "ModelName": "test-model",
            "PrimaryContainer": {
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
                "ModelDataUrl": "s3://bucket/old-model.tar.gz",
            },
            "ExecutionRoleArn": "arn:role",
        }
        module = self._create_mock_module(
            primary_container={
                "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
                "model_data_url": "s3://bucket/new-model.tar.gz",
            }
        )

        assert model_needs_replacement(existing, module)
