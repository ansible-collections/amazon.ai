#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for sagemaker module_utils."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _build_model_package_group_params
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _build_model_package_params
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _build_model_package_update_params
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _endpoint_config_properties_differ
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _model_package_values_match
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _normalize_model_package_compare_value
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_model_package
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_model_package_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_model_package
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_model_package_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_endpoint_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_model_package
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_model_package_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import get_model_package_tag_arn
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_endpoint_configs
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_model_package_groups
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_model_packages
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_models
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_needs_replacement
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_package_group_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_package_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_endpoint_config_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_model_package
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_model_package_group_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_model_package_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_model_package_status
from ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package import _ensure_absent
from ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package import _ensure_present
from ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package import (
    _normalize_model_package as normalize_model_package_result,
)
from ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package import _validate_model_package_create_params
from ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package import _wait_for_model_package_status
from ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package import main as model_package_main
from ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_group_info import find_model_package_groups
from ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info import (
    _normalize_model_package as normalize_model_package_info_result,
)
from ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info import find_model_packages
from ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info import main as model_package_info_main
from botocore.exceptions import ClientError


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


def test_describe_model_package_returns_none_when_missing():
    client = MagicMock()
    client.describe_model_package.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFound", "Message": "Model package not found."}},
        "DescribeModelPackage",
    )

    assert describe_model_package(client, "missing-package") is None


def test_list_model_packages_limits_total_results():
    client = MagicMock()
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value.build_full_result.return_value = {"ModelPackageSummaryList": []}

    list_model_packages(client, MaxResults=2)

    paginator.paginate.assert_called_once_with(PaginationConfig={"MaxItems": 2})


def test_build_model_package_params_preserves_aws_mime_key_name():
    module = MagicMock()
    module.params = {
        "model_package_name": "demo-package",
        "inference_specification": {
            "containers": [{"image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo:latest"}],
            "supported_content_types": ["application/json"],
            "supported_response_mime_types": ["application/json"],
        },
        "model_package_group_name": "demo-group",
    }

    result = _build_model_package_params(module)

    assert result["InferenceSpecification"]["SupportedResponseMIMETypes"] == ["application/json"]
    assert "SupportedResponseMimeTypes" not in result["InferenceSpecification"]


def test_build_model_package_params_preserves_customer_metadata_keys():
    module = MagicMock()
    module.params = {
        "model_package_name": "demo-package",
        "customer_metadata_properties": {
            "snake_case_key": "value",
            "MixedCase-Key": "other-value",
        },
    }

    result = _build_model_package_params(module)

    assert result["CustomerMetadataProperties"] == {
        "snake_case_key": "value",
        "MixedCase-Key": "other-value",
    }


def test_build_model_package_update_params_preserves_customer_metadata_keys():
    module = MagicMock()
    module.params = {
        "model_approval_status": None,
        "approval_description": None,
        "customer_metadata_properties": {
            "snake_case_key": "value",
            "MixedCase-Key": "other-value",
        },
        "customer_metadata_properties_to_remove": None,
        "model_life_cycle": None,
        "additional_inference_specifications_to_add": None,
    }

    result = _build_model_package_update_params(module, "arn:package")

    assert result["CustomerMetadataProperties"] == {
        "snake_case_key": "value",
        "MixedCase-Key": "other-value",
    }


@pytest.mark.parametrize(
    "normalize",
    [normalize_model_package_result, normalize_model_package_info_result],
)
def test_model_package_results_preserve_customer_metadata_keys(normalize):
    package = {
        "ModelPackageName": "demo-package",
        "CustomerMetadataProperties": {
            "snake_case_key": "value",
            "MixedCase-Key": "other-value",
        },
    }

    result = normalize(package, {})

    assert result["model_package_name"] == "demo-package"
    assert result["customer_metadata_properties"] == package["CustomerMetadataProperties"]


def test_normalize_model_package_compare_value_preserves_aws_mime_key_name():
    value = {
        "containers": [{"image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo:latest"}],
        "supported_content_types": ["application/json"],
        "supported_response_mime_types": ["application/json"],
    }

    result = _normalize_model_package_compare_value(value)

    assert result["SupportedResponseMIMETypes"] == ["application/json"]
    assert "SupportedResponseMimeTypes" not in result


def test_model_package_needs_update_does_not_repeat_completed_delta_updates():
    module = MagicMock()
    module.params = {
        "model_approval_status": None,
        "approval_description": None,
        "customer_metadata_properties": None,
        "customer_metadata_properties_to_remove": ["obsolete"],
        "model_life_cycle": None,
        "additional_inference_specifications_to_add": [
            {"containers": [{"image": "example"}]},
        ],
    }
    existing = {
        "ModelPackageArn": "arn:package",
        "CustomerMetadataProperties": {},
        "AdditionalInferenceSpecifications": [
            {"Containers": [{"Image": "example"}]},
        ],
    }

    assert not model_package_needs_update(existing, module)


def test_model_package_needs_update_detects_pending_delta_updates():
    module = MagicMock()
    module.params = {
        "model_approval_status": None,
        "approval_description": None,
        "customer_metadata_properties": None,
        "customer_metadata_properties_to_remove": ["obsolete"],
        "model_life_cycle": None,
        "additional_inference_specifications_to_add": [
            {"containers": [{"image": "new-example"}]},
        ],
    }
    existing = {
        "ModelPackageArn": "arn:package",
        "CustomerMetadataProperties": {"obsolete": "value"},
        "AdditionalInferenceSpecifications": [],
    }

    assert model_package_needs_update(existing, module)


def test_build_model_package_params_allows_group_name_without_package_name():
    module = MagicMock()
    module.params = {
        "model_package_group_name": "demo-group",
        "model_package_description": "demo description",
        "inference_specification": {
            "containers": [{"image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo:latest"}],
            "supported_response_mime_types": ["application/json"],
        },
    }

    result = _build_model_package_params(module)

    assert result["ModelPackageGroupName"] == "demo-group"
    assert "ModelPackageName" not in result
    assert result["InferenceSpecification"]["SupportedResponseMIMETypes"] == ["application/json"]


def test_model_package_values_match_ignores_list_order_and_aws_only_container_fields():
    desired = {
        "Containers": [
            {
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo:latest",
                "ModelDataUrl": "s3://bucket/model.tar.gz",
            },
        ],
        "SupportedContentTypes": ["application/json"],
        "SupportedRealtimeInferenceInstanceTypes": ["ml.m5.large"],
        "SupportedTransformInstanceTypes": ["ml.m5.large"],
        "SupportedResponseMIMETypes": ["application/json"],
    }
    actual = {
        "SupportedResponseMIMETypes": ["application/json"],
        "SupportedTransformInstanceTypes": ["ml.m5.large"],
        "SupportedRealtimeInferenceInstanceTypes": ["ml.m5.large"],
        "SupportedContentTypes": ["application/json"],
        "Containers": [
            {
                "ModelDataUrl": "s3://bucket/model.tar.gz",
                "ImageDigest": "sha256:abc",
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo:latest",
                "ModelDataETag": "etag",
                "IsCheckpoint": False,
            },
        ],
    }

    assert _model_package_values_match(actual, desired)


def test_model_package_tag_arn_prefers_group_arn_when_present():
    package = {
        "ModelPackageArn": "arn:aws:sagemaker:us-east-1:123456789012:model-package/demo-package",
        "ModelPackageGroupArn": "arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo-group",
    }

    assert (
        get_model_package_tag_arn(package) == "arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo-group"
    )


def test_model_package_tag_arn_derives_group_arn_for_versioned_package():
    package = {"ModelPackageArn": "arn:aws:sagemaker:us-east-1:123456789012:model-package/demo-group/1"}

    assert (
        get_model_package_tag_arn(package) == "arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo-group"
    )


def test_build_model_package_params_includes_standalone_package_tags():
    module = MagicMock()
    module.params = {
        "model_package_name": "demo-package",
        "tags": {"project": "demo"},
        "inference_specification": {
            "containers": [{"image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo:latest"}],
            "supported_response_mime_types": ["application/json"],
        },
    }

    result = _build_model_package_params(module)

    assert result["Tags"] == [{"Key": "project", "Value": "demo"}]
    assert result["InferenceSpecification"]["SupportedResponseMIMETypes"] == ["application/json"]


def test_create_model_package_returns_created_package_arn():
    client = MagicMock()
    client.create_model_package.return_value = {"ModelPackageArn": "arn:package/demo-group/1"}
    module = MagicMock()
    module.check_mode = False
    module.params = {
        "model_package_group_name": "demo-group",
        "inference_specification": {"containers": [{"image": "image"}]},
    }

    assert create_model_package(client, module) == (
        True,
        "Model package in group demo-group created successfully.",
        "arn:package/demo-group/1",
    )


def _model_package_module(**overrides):
    module = MagicMock()
    module.check_mode = False
    module.params = {
        "model_package_name": "demo-package",
        "model_package_group_name": None,
        "model_package_description": None,
        "model_package_registration_type": None,
        "inference_specification": {"containers": [{"image": "image"}]},
        "validation_specification": None,
        "source_algorithm_specification": None,
        "certify_for_marketplace": None,
        "additional_inference_specifications": None,
        "model_card": None,
        "model_metrics": None,
        "domain": None,
        "task": None,
        "sample_payload_url": None,
        "skip_model_validation": None,
        "drift_check_baselines": None,
        "security_config": None,
        "source_uri": None,
        "metadata_properties": None,
        "model_package_approval_status": None,
        "model_approval_status": None,
        "approval_description": None,
        "model_life_cycle": None,
        "customer_metadata_properties": None,
        "customer_metadata_properties_to_remove": None,
        "additional_inference_specifications_to_add": None,
        "tags": None,
        "purge_tags": True,
        "wait": False,
        "wait_timeout": 1,
    }
    module.params.update(overrides)
    return module


def test_create_model_package_check_mode_does_not_call_boto3():
    client = MagicMock()
    module = _model_package_module()
    module.check_mode = True

    result = create_model_package(client, module)

    assert result == (True, "Check mode: would have created model package demo-package.", None)
    client.create_model_package.assert_not_called()


def test_update_model_package_check_mode_does_not_call_boto3():
    client = MagicMock()
    module = _model_package_module(model_approval_status="Approved")
    module.check_mode = True

    result = update_model_package(client, module, "arn:package")

    assert result == (True, "Check mode: would have updated model package demo-package.")
    client.update_model_package.assert_not_called()


def test_update_model_package_calls_boto3_with_desired_fields():
    client = MagicMock()
    module = _model_package_module(model_approval_status="Approved")

    result = update_model_package(client, module, "arn:package")

    assert result == (True, "Model package demo-package updated successfully.")
    client.update_model_package.assert_called_once_with(ModelPackageArn="arn:package", ModelApprovalStatus="Approved")


def test_update_model_package_requires_name():
    module = _model_package_module(model_package_name=None)

    with pytest.raises(ValueError, match="model_package_name is required"):
        update_model_package(MagicMock(), module, "arn:package")


def test_delete_model_package_check_mode_does_not_call_boto3():
    client = MagicMock()
    module = _model_package_module()
    module.check_mode = True

    result = delete_model_package(client, module)

    assert result == (True, "Check mode: would have deleted model package demo-package.")
    client.delete_model_package.assert_not_called()


def test_delete_model_package_calls_boto3():
    client = MagicMock()
    module = _model_package_module()

    result = delete_model_package(client, module)

    assert result == (True, "Model package demo-package deleted successfully.")
    client.delete_model_package.assert_called_once_with(ModelPackageName="demo-package")


def test_delete_model_package_requires_name():
    module = _model_package_module(model_package_name=None)

    with pytest.raises(ValueError, match="model_package_name is required"):
        delete_model_package(MagicMock(), module)


@patch("ansible_collections.amazon.ai.plugins.module_utils.sagemaker.list_tags")
def test_update_model_package_tags_adds_changed_values_and_purges_omitted_keys(mock_list_tags):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = False
    mock_list_tags.return_value = {"project": "old", "owner": "platform"}

    result = update_model_package_tags(client, module, "arn:package", {"project": "demo"})

    assert result == (True, "Model package tags updated successfully.")
    client.add_tags.assert_called_once_with(
        ResourceArn="arn:package",
        Tags=[{"Key": "project", "Value": "demo"}],
    )
    client.delete_tags.assert_called_once_with(ResourceArn="arn:package", TagKeys=["owner"])


@patch("ansible_collections.amazon.ai.plugins.module_utils.sagemaker.list_tags")
def test_update_model_package_tags_check_mode_does_not_modify_tags(mock_list_tags):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = True
    mock_list_tags.return_value = {"project": "old"}

    result = update_model_package_tags(client, module, "arn:package", {"project": "demo"})

    assert result == (True, "Check mode: would have updated model package tags.")
    client.add_tags.assert_not_called()
    client.delete_tags.assert_not_called()


@patch("ansible_collections.amazon.ai.plugins.module_utils.sagemaker.list_tags")
def test_update_model_package_tags_matching_values_are_noop(mock_list_tags):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = False
    mock_list_tags.return_value = {"project": "demo"}

    result = update_model_package_tags(client, module, "arn:package", {"project": "demo"})

    assert result == (False, "No updates needed.")
    client.add_tags.assert_not_called()
    client.delete_tags.assert_not_called()


@patch("ansible_collections.amazon.ai.plugins.module_utils.sagemaker.list_tags")
def test_update_model_package_tags_purge_false_preserves_unmentioned_keys(mock_list_tags):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = False
    mock_list_tags.return_value = {"owner": "platform"}

    result = update_model_package_tags(
        client,
        module,
        "arn:package",
        {"project": "demo"},
        purge_tags=False,
    )

    assert result == (True, "Model package tags updated successfully.")
    client.add_tags.assert_called_once_with(
        ResourceArn="arn:package",
        Tags=[{"Key": "project", "Value": "demo"}],
    )
    client.delete_tags.assert_not_called()


def test_ensure_present_creates_package_and_returns_described_package():
    client = MagicMock()
    module = _model_package_module()
    package = {
        "ModelPackageName": "demo-package",
        "ModelPackageArn": "arn:package",
        "ModelApprovalStatus": "PendingManualApproval",
    }
    with patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.create_model_package",
        return_value=(True, "created", "arn:package"),
    ), patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.describe_model_package",
        return_value=package,
    ) as describe:
        changed, result = _ensure_present(client, module, None)

    assert changed
    assert result["model_package"] == {
        "model_package_name": "demo-package",
        "model_package_arn": "arn:package",
        "model_approval_status": "PendingManualApproval",
    }
    assert "tags" not in result
    describe.assert_called_once_with(client, "arn:package")


def test_ensure_present_create_check_mode_does_not_describe_package():
    client = MagicMock()
    module = _model_package_module()
    module.check_mode = True
    with patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.describe_model_package"
    ) as describe:
        changed, result = _ensure_present(client, module, None)

    assert changed
    assert result["msg"] == "Check mode: would have created model package demo-package."
    assert result["model_package"] == {}
    describe.assert_not_called()


def test_ensure_present_rejects_tags_for_group_package_creation():
    module = _model_package_module(
        model_package_name=None,
        model_package_group_name="demo-group",
        tags={"project": "demo"},
    )
    module.fail_json.side_effect = RuntimeError("fail_json")

    with pytest.raises(RuntimeError, match="fail_json"):
        _ensure_present(MagicMock(), module, None)

    module.fail_json.assert_called_once()
    assert "Tags cannot be specified" in module.fail_json.call_args.kwargs["msg"]


def test_ensure_present_rejects_in_place_changes_to_create_only_fields():
    module = _model_package_module(
        inference_specification={"containers": [{"image": "new-image"}]},
    )
    module.fail_json.side_effect = RuntimeError("fail_json")
    existing = {
        "ModelPackageName": "demo-package",
        "ModelPackageArn": "arn:package",
        "InferenceSpecification": {"Containers": [{"Image": "old-image"}]},
    }

    with pytest.raises(RuntimeError, match="fail_json"):
        _ensure_present(MagicMock(), module, existing)

    assert "inference_specification is create-only" in module.fail_json.call_args.kwargs["msg"]


def test_ensure_present_rejects_package_already_being_deleted():
    module = _model_package_module()
    module.fail_json.side_effect = RuntimeError("fail_json")
    existing = {"ModelPackageName": "demo-package", "ModelPackageStatus": "Deleting"}

    with pytest.raises(RuntimeError, match="fail_json"):
        _ensure_present(MagicMock(), module, existing)

    assert "currently being deleted" in module.fail_json.call_args.kwargs["msg"]


@patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.list_tags")
@patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.update_model_package_tags")
def test_ensure_present_reconciles_standalone_tags_and_returns_refreshed_package(mock_update_tags, mock_list_tags):
    client = MagicMock()
    module = _model_package_module(tags={"project": "demo"})
    existing = {"ModelPackageName": "demo-package", "ModelPackageArn": "arn:package"}
    mock_update_tags.return_value = (True, "Model package tags updated successfully.")
    mock_list_tags.return_value = {"project": "demo"}
    with patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.model_package_needs_update",
        return_value=False,
    ), patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.describe_model_package",
        return_value=existing,
    ) as describe:
        changed, result = _ensure_present(client, module, existing)

    assert changed
    assert result["msg"] == "Model package tags updated successfully."
    assert result["tags"] == {"project": "demo"}
    mock_update_tags.assert_called_once_with(client, module, "arn:package", {"project": "demo"}, purge_tags=True)
    describe.assert_called_once_with(client, "demo-package")
    mock_list_tags.assert_called_once_with(client, "arn:package")


@patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.update_model_package")
def test_ensure_present_updates_package_and_waits_for_status(mock_update, monkeypatch):
    client = MagicMock()
    module = _model_package_module(model_approval_status="Approved", wait=True)
    existing = {"ModelPackageName": "demo-package", "ModelPackageArn": "arn:package"}
    mock_update.return_value = (True, "Model package demo-package updated successfully.")
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.model_package_needs_update",
        lambda package, params: True,
    )
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.describe_model_package",
        lambda client, name: existing,
    )
    with patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package._wait_for_model_package_status"
    ) as wait:
        changed, result = _ensure_present(client, module, existing)

    assert changed
    assert result["msg"] == "Model package demo-package updated successfully."
    mock_update.assert_called_once_with(client, module, "arn:package")
    wait.assert_called_once_with(client, module, "demo-package")


def test_ensure_absent_returns_noop_when_package_is_missing():
    changed, result = _ensure_absent(MagicMock(), _model_package_module(), None)

    assert not changed
    assert result == {"msg": "Model package does not exist."}


@patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package._wait_for_model_package_status")
def test_ensure_absent_waits_for_package_already_deleting(mock_wait):
    client = MagicMock()
    module = _model_package_module(wait=True)

    changed, result = _ensure_absent(
        client,
        module,
        {"ModelPackageName": "demo-package", "ModelPackageStatus": "Deleting"},
    )

    assert not changed
    assert result == {"msg": "Model package is already being deleted."}
    mock_wait.assert_called_once_with(client, module, "demo-package")


@patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.delete_model_package")
@patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package._wait_for_model_package_status")
def test_ensure_absent_deletes_package_and_waits(mock_wait, mock_delete):
    client = MagicMock()
    module = _model_package_module(wait=True)
    mock_delete.return_value = (True, "deleted")

    changed, result = _ensure_absent(client, module, {"ModelPackageName": "demo-package"})

    assert changed
    assert result == {"msg": "deleted"}
    mock_delete.assert_called_once_with(client, module)
    mock_wait.assert_called_once_with(client, module, "demo-package")


def test_wait_for_model_package_status_returns_when_completed():
    client = MagicMock()
    client.describe_model_package.return_value = {"ModelPackageStatus": "Completed"}

    wait_for_model_package_status(client, "demo-package", wait_timeout=1)

    client.describe_model_package.assert_called_once_with(ModelPackageName="demo-package")


def test_wait_for_model_package_status_fails_on_failed_status():
    client = MagicMock()
    client.describe_model_package.return_value = {"ModelPackageStatus": "Failed"}

    with pytest.raises(RuntimeError, match="entered a failed state"):
        wait_for_model_package_status(client, "demo-package", wait_timeout=1)


def test_wait_for_model_package_status_returns_when_package_disappears():
    client = MagicMock()
    client.describe_model_package.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFound", "Message": "Model package not found."}},
        "DescribeModelPackage",
    )

    wait_for_model_package_status(client, "demo-package", wait_timeout=1)


def test_wait_for_model_package_status_fails_after_timeout(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.module_utils.sagemaker.time.time",
        MagicMock(side_effect=[0, 2]),
    )

    with pytest.raises(TimeoutError, match="Timed out waiting"):
        wait_for_model_package_status(client, "demo-package", wait_timeout=1)


def test_module_wait_helper_reports_wait_failures():
    module = MagicMock()
    module.params = {"wait_timeout": 1}
    module.fail_json.side_effect = RuntimeError("fail_json")
    with patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.wait_for_model_package_status",
        side_effect=TimeoutError("wait timed out"),
    ):
        with pytest.raises(RuntimeError, match="fail_json"):
            _wait_for_model_package_status(MagicMock(), module, "demo-package")

    module.fail_json.assert_called_once_with(msg="wait timed out")


def test_model_package_main_requires_name_for_absent_state():
    with patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.AnsibleAWSModule",
        side_effect=RuntimeError("required_if"),
    ) as ansible_module:
        with pytest.raises(RuntimeError, match="required_if"):
            model_package_main()

    assert ansible_module.call_args.kwargs["required_if"] == [("state", "absent", ["model_package_name"])]


def test_model_package_main_returns_noop_result():
    client = MagicMock()
    module = MagicMock()
    module.params = {"state": "present", "model_package_name": "demo-package"}
    module.client.return_value = client
    with patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.AnsibleAWSModule",
        return_value=module,
    ), patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.describe_model_package",
        return_value={"ModelPackageName": "demo-package"},
    ), patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package._ensure_present",
        return_value=(False, {"msg": "No updates needed."}),
    ):
        model_package_main()

    module.exit_json.assert_called_once_with(changed=False, msg="No updates needed.")


def test_model_package_main_reports_connection_errors():
    module = MagicMock()
    module.params = {"state": "present", "model_package_name": "demo-package"}
    error = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "Access denied."}},
        "CreateClient",
    )
    module.client.side_effect = error
    module.fail_json_aws.side_effect = RuntimeError("fail_json_aws")
    with patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package.AnsibleAWSModule",
        return_value=module,
    ):
        with pytest.raises(RuntimeError, match="fail_json_aws"):
            model_package_main()

    module.fail_json_aws.assert_called_once_with(error, msg="Failed to connect to AWS.")


def test_validate_model_package_create_params_requires_identifier():
    module = MagicMock()
    module.params = {
        "model_package_name": None,
        "model_package_group_name": None,
        "inference_specification": {"containers": [{"image": "image"}]},
        "source_algorithm_specification": None,
        "additional_inference_specifications_to_add": None,
        "customer_metadata_properties_to_remove": None,
    }

    _validate_model_package_create_params(module)

    module.fail_json.assert_called_once_with(
        msg="One of model_package_name or model_package_group_name must be provided."
    )


def test_validate_model_package_create_params_requires_model_source():
    module = MagicMock()
    module.params = {
        "model_package_name": "demo-package",
        "model_package_group_name": None,
        "inference_specification": None,
        "source_algorithm_specification": None,
        "additional_inference_specifications_to_add": None,
        "customer_metadata_properties_to_remove": None,
    }

    _validate_model_package_create_params(module)

    module.fail_json.assert_called_once_with(
        msg="One of inference_specification or source_algorithm_specification is required when creating a model package."
    )


def test_validate_model_package_create_params_rejects_update_only_fields():
    module = MagicMock()
    module.params = {
        "model_package_name": "demo-package",
        "model_package_group_name": None,
        "inference_specification": {"containers": [{"image": "image"}]},
        "source_algorithm_specification": None,
        "additional_inference_specifications_to_add": [{"name": "extra"}],
        "customer_metadata_properties_to_remove": None,
    }

    _validate_model_package_create_params(module)

    module.fail_json.assert_called_once_with(
        msg="additional_inference_specifications_to_add can only be used when updating an existing model package."
    )


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


class TestBuildModelPackageGroupParams:
    """Test cases for _build_model_package_group_params function."""

    def test_tags_use_boto3_key_value_shape(self):
        """Create parameters should serialize tags in SageMaker's boto3 shape."""
        module = MagicMock()
        module.params = {
            "model_package_group_name": "demo-group",
            "model_package_group_description": "demo description",
            "tags": {"project": "demo", "environment": "test"},
        }

        result = _build_model_package_group_params(module)

        assert result == {
            "ModelPackageGroupName": "demo-group",
            "ModelPackageGroupDescription": "demo description",
            "Tags": [
                {"Key": "project", "Value": "demo"},
                {"Key": "environment", "Value": "test"},
            ],
        }


class TestCreateModelPackageGroup:
    """Test cases for create_model_package_group function."""

    def test_check_mode_does_not_call_boto3(self):
        """Check mode should report the pending create without invoking SageMaker."""
        client = MagicMock()
        module = MagicMock()
        module.check_mode = True
        module.params = {"model_package_group_name": "demo-group"}

        result = create_model_package_group(client, module)

        client.create_model_package_group.assert_not_called()
        assert result == (True, "Check mode: would have created model package group demo-group.")

    def test_real_mode_calls_create_model_package_group(self):
        """Real mode should call SageMaker with the generated create payload."""
        client = MagicMock()
        module = MagicMock()
        module.check_mode = False
        module.params = {
            "model_package_group_name": "demo-group",
            "model_package_group_description": "demo description",
            "tags": {"project": "demo"},
        }

        result = create_model_package_group(client, module)

        client.create_model_package_group.assert_called_once_with(
            ModelPackageGroupName="demo-group",
            ModelPackageGroupDescription="demo description",
            Tags=[{"Key": "project", "Value": "demo"}],
        )
        assert result == (True, "Model package group demo-group created successfully.")


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


class TestDeleteModelPackageGroup:
    """Test cases for delete_model_package_group function."""

    def test_check_mode_does_not_call_boto3(self):
        """Check mode should report the pending delete without invoking SageMaker."""
        client = MagicMock()
        module = MagicMock()
        module.check_mode = True
        module.params = {"model_package_group_name": "demo-group"}

        result = delete_model_package_group(client, module)

        client.delete_model_package_group.assert_not_called()
        assert result == (True, "Check mode: would have deleted model package group demo-group.")

    def test_real_mode_calls_delete_model_package_group(self):
        """Real mode should call SageMaker with the model package group name."""
        client = MagicMock()
        module = MagicMock()
        module.check_mode = False
        module.params = {"model_package_group_name": "demo-group", "wait": False}

        result = delete_model_package_group(client, module)

        client.delete_model_package_group.assert_called_once_with(ModelPackageGroupName="demo-group")
        assert result == (True, "Model package group demo-group deleted successfully.")


class TestUpdateModelPackageGroupTags:
    """Test cases for update_model_package_group_tags function."""

    @patch(
        "ansible_collections.amazon.ai.plugins.module_utils.sagemaker.list_tags",
        return_value={"keep": "value"},
    )
    def test_matching_tags_are_noop(self, mock_list_tags):
        """When desired tags match current tags, no SageMaker tag APIs should be called."""
        client = MagicMock()
        module = MagicMock()
        module.check_mode = False

        result = update_model_package_group_tags(
            client,
            module,
            "arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo",
            {"keep": "value"},
        )

        client.add_tags.assert_not_called()
        client.delete_tags.assert_not_called()
        assert result == (False, "No updates needed.")
        mock_list_tags.assert_called_once_with(
            client, "arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo"
        )

    @patch(
        "ansible_collections.amazon.ai.plugins.module_utils.sagemaker.list_tags",
        return_value={"remove": "old"},
    )
    def test_check_mode_does_not_modify_tags(self, mock_list_tags):
        """Check mode should report tag drift without calling mutating tag APIs."""
        client = MagicMock()
        module = MagicMock()
        module.check_mode = True

        result = update_model_package_group_tags(
            client,
            module,
            "arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo",
            {"keep": "value"},
        )

        client.add_tags.assert_not_called()
        client.delete_tags.assert_not_called()
        assert result == (True, "Check mode: would have updated model package group tags.")
        mock_list_tags.assert_called_once_with(
            client, "arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo"
        )

    @patch(
        "ansible_collections.amazon.ai.plugins.module_utils.sagemaker.list_tags",
        return_value={"keep": "value", "remove": "old"},
    )
    def test_purge_tags_false_keeps_unmentioned_keys(self, mock_list_tags):
        """When purge_tags is false, extra tags should stay untouched."""
        client = MagicMock()
        module = MagicMock()
        module.check_mode = False

        result = update_model_package_group_tags(
            client,
            module,
            "arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo",
            {"keep": "new"},
            purge_tags=False,
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

        result = update_model_package_group_tags(
            client,
            module,
            "arn:aws:sagemaker:us-east-1:123456789012:model-package-group/demo",
            {"keep": "new"},
            purge_tags=True,
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

    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_group_info.list_tags")
    @patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_group_info.describe_model_package_group"
    )
    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_group_info.list_model_package_groups")
    def test_list_tag_filter_excludes_mismatched_values(
        self, mock_list_model_package_groups, mock_describe_model_package_group, mock_list_tags
    ):
        """A desired tag value must match the group's actual tag value."""
        client = MagicMock()
        module = MagicMock()
        module.params = {
            "model_package_group_name": None,
            "tags": {"project": "demo"},
        }
        mock_list_model_package_groups.return_value = [{"ModelPackageGroupName": "group-a"}]
        mock_describe_model_package_group.return_value = {
            "ModelPackageGroupName": "group-a",
            "ModelPackageGroupArn": "arn:a",
        }
        mock_list_tags.return_value = {"project": "other"}

        assert find_model_package_groups(client, module) == []

    @patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_group_info.describe_model_package_group"
    )
    def test_missing_named_group_returns_empty_list(self, mock_describe_model_package_group):
        """An exact-name lookup miss should be non-fatal and return no results."""
        client = MagicMock()
        module = MagicMock()
        module.params = {"model_package_group_name": "missing-group"}
        mock_describe_model_package_group.return_value = None

        result = find_model_package_groups(client, module)

        assert result == []
        mock_describe_model_package_group.assert_called_once_with(client, "missing-group")

    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_group_info.list_tags")
    @patch(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_group_info.describe_model_package_group"
    )
    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_group_info.list_model_package_groups")
    def test_list_filters_sorts_limits_skips_missing_summaries_and_filters_tags(
        self, mock_list_model_package_groups, mock_describe_model_package_group, mock_list_tags
    ):
        """List lookups should forward filters, skip vanished summaries, and apply tag filtering."""
        client = MagicMock()
        module = MagicMock()
        module.params = {
            "model_package_group_name": None,
            "name_contains": "demo",
            "creation_time_after": "2026-01-01T00:00:00Z",
            "creation_time_before": "2027-01-01T00:00:00Z",
            "sort_by": "Name",
            "sort_order": "Ascending",
            "max_items": 3,
            "tags": {"project": "demo"},
        }
        mock_list_model_package_groups.return_value = [
            {"ModelPackageGroupName": "group-a"},
            {"ModelPackageGroupName": "missing-group"},
            {"ModelPackageGroupName": "group-b"},
        ]
        mock_describe_model_package_group.side_effect = [
            {"ModelPackageGroupName": "group-a", "ModelPackageGroupArn": "arn:a"},
            None,
            {"ModelPackageGroupName": "group-b", "ModelPackageGroupArn": "arn:b"},
        ]
        mock_list_tags.side_effect = [
            {"project": "other"},
            {"project": "demo", "owner": "platform"},
        ]

        result = find_model_package_groups(client, module)

        mock_list_model_package_groups.assert_called_once_with(
            client,
            max_items=3,
            NameContains="demo",
            CreationTimeAfter="2026-01-01T00:00:00Z",
            CreationTimeBefore="2027-01-01T00:00:00Z",
            SortBy="Name",
            SortOrder="Ascending",
        )
        assert mock_describe_model_package_group.call_count == 3
        assert mock_list_tags.call_count == 2
        assert result == [
            {
                "model_package_group_name": "group-b",
                "model_package_group_arn": "arn:b",
                "tags": {"project": "demo", "owner": "platform"},
            }
        ]


class TestFindModelPackages:
    """Test cases for the model package info module finder."""

    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info.list_tags")
    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info.describe_model_package")
    def test_named_lookup_forwards_included_data_without_fetching_tags(
        self, mock_describe_model_package, mock_list_tags
    ):
        """Exact-name lookups should pass IncludedData and omit unrequested tag reads."""
        client = MagicMock()
        module = MagicMock()
        module.params = {
            "model_package_name": "demo-package",
            "included_data": "MetadataOnly",
            "tags": None,
        }
        mock_describe_model_package.return_value = {
            "ModelPackageName": "demo-package",
            "ModelPackageArn": "arn:package",
        }
        mock_list_tags.return_value = {"project": "demo"}

        result = find_model_packages(client, module)

        mock_describe_model_package.assert_called_once_with(client, "demo-package", IncludedData="MetadataOnly")
        mock_list_tags.assert_not_called()
        assert result == [
            {
                "model_package_name": "demo-package",
                "model_package_arn": "arn:package",
            }
        ]

    def test_model_package_name_and_tags_are_mutually_exclusive(self):
        with patch(
            "ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info.AnsibleAWSModule",
            side_effect=RuntimeError("argument validation"),
        ) as ansible_module:
            with pytest.raises(RuntimeError, match="argument validation"):
                model_package_info_main()

        assert ansible_module.call_args.kwargs["mutually_exclusive"] == [("model_package_name", "tags")]

    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info.list_tags")
    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info.describe_model_package")
    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info.list_model_packages")
    def test_list_forwards_model_package_type_and_included_data(
        self, mock_list_model_packages, mock_describe_model_package, mock_list_tags
    ):
        """List lookups should forward ModelPackageType and describe IncludedData."""
        client = MagicMock()
        module = MagicMock()
        module.params = {
            "model_package_name": None,
            "model_package_group_name": "demo-group",
            "model_approval_status": "Approved",
            "model_package_type": "Versioned",
            "included_data": "AllData",
            "name_contains": "demo",
            "creation_time_after": "2026-01-01T00:00:00Z",
            "creation_time_before": "2027-01-01T00:00:00Z",
            "sort_by": "Name",
            "sort_order": "Ascending",
            "max_results": 3,
            "tags": {"project": "demo"},
        }
        mock_list_model_packages.return_value = [{"ModelPackageName": "package-a", "ModelPackageArn": "arn:package-a"}]
        mock_describe_model_package.return_value = {
            "ModelPackageName": "package-a",
            "ModelPackageArn": "arn:package-a",
        }
        mock_list_tags.return_value = {"project": "demo"}

        result = find_model_packages(client, module)

        mock_list_model_packages.assert_called_once_with(
            client,
            ModelPackageGroupName="demo-group",
            ModelApprovalStatus="Approved",
            ModelPackageType="Versioned",
            NameContains="demo",
            CreationTimeAfter="2026-01-01T00:00:00Z",
            CreationTimeBefore="2027-01-01T00:00:00Z",
            SortBy="Name",
            SortOrder="Ascending",
            MaxResults=3,
        )
        mock_describe_model_package.assert_called_once_with(client, "package-a", IncludedData="AllData")
        mock_list_tags.assert_called_once_with(client, "arn:package-a")
        assert result == [
            {
                "model_package_name": "package-a",
                "model_package_arn": "arn:package-a",
                "tags": {"project": "demo"},
            }
        ]

    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info.list_tags")
    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info.describe_model_package")
    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info.list_model_packages")
    def test_list_describes_arn_when_summary_omits_name(
        self, mock_list_model_packages, mock_describe_model_package, mock_list_tags
    ):
        """Versioned package summaries may need to be described by ARN."""
        client = MagicMock()
        module = MagicMock()
        module.params = {
            "model_package_name": None,
            "model_package_group_name": "demo-group",
            "model_approval_status": None,
            "model_package_type": "Versioned",
            "included_data": None,
            "name_contains": None,
            "creation_time_after": None,
            "creation_time_before": None,
            "sort_by": None,
            "sort_order": None,
            "max_results": None,
            "tags": None,
        }
        mock_list_model_packages.return_value = [
            {"ModelPackageArn": "arn:aws:sagemaker:us-east-1:123456789012:model-package/demo-group/1"}
        ]
        mock_describe_model_package.return_value = {
            "ModelPackageArn": "arn:aws:sagemaker:us-east-1:123456789012:model-package/demo-group/1",
            "ModelPackageGroupName": "demo-group",
        }

        result = find_model_packages(client, module)

        mock_describe_model_package.assert_called_once_with(
            client,
            "arn:aws:sagemaker:us-east-1:123456789012:model-package/demo-group/1",
        )
        mock_list_tags.assert_not_called()
        assert result == [
            {
                "model_package_arn": "arn:aws:sagemaker:us-east-1:123456789012:model-package/demo-group/1",
                "model_package_group_name": "demo-group",
            }
        ]

    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info.list_tags")
    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info.describe_model_package")
    @patch("ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_info.list_model_packages")
    def test_list_filters_tags_before_describe_and_reads_each_tag_owner_once(
        self, mock_list_model_packages, mock_describe_model_package, mock_list_tags
    ):
        """Versioned packages share group tags: read them once per group and skip describing non-matches."""
        client = MagicMock()
        module = MagicMock()
        module.params = {
            "model_package_name": None,
            "included_data": None,
            "tags": {"project": "demo"},
        }
        arn_prefix = "arn:aws:sagemaker:us-east-1:123456789012"
        mock_list_model_packages.return_value = [
            {"ModelPackageArn": f"{arn_prefix}:model-package/group-a/1"},
            {"ModelPackageArn": f"{arn_prefix}:model-package/group-a/2"},
            {"ModelPackageArn": f"{arn_prefix}:model-package/group-b/1"},
        ]
        mock_list_tags.side_effect = lambda _client, arn: (
            {"project": "demo"} if arn.endswith("group-a") else {"project": "other"}
        )
        mock_describe_model_package.side_effect = lambda _client, identifier: {"ModelPackageArn": identifier}

        result = find_model_packages(client, module)

        assert mock_list_tags.call_args_list == [
            ((client, f"{arn_prefix}:model-package-group/group-a"),),
            ((client, f"{arn_prefix}:model-package-group/group-b"),),
        ]
        assert [call.args[1] for call in mock_describe_model_package.call_args_list] == [
            f"{arn_prefix}:model-package/group-a/1",
            f"{arn_prefix}:model-package/group-a/2",
        ]
        assert [package["model_package_arn"] for package in result] == [
            f"{arn_prefix}:model-package/group-a/1",
            f"{arn_prefix}:model-package/group-a/2",
        ]
        assert all(package["tags"] == {"project": "demo"} for package in result)


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
