#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for sagemaker module_utils."""

from copy import deepcopy
from unittest.mock import MagicMock
from unittest.mock import patch

import botocore.session
import pytest
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import USER_SETTINGS_OPTIONS
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import USER_SETTINGS_REQUEST_RENAMES
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import USER_SETTINGS_RESPONSE_RENAMES
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _endpoint_config_properties_differ
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import build_user_settings
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_endpoint_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_model_package_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_user_profile
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import format_user_profile
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_endpoint_configs
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_model_package_groups
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_models
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_user_profiles
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_needs_replacement
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_package_group_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_endpoint_config_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_model_package_group_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import user_settings_to_update
from ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_group_info import find_model_package_groups
from ansible_collections.amazon.ai.plugins.modules.sagemaker_user_profile import _user_settings_options
from botocore.exceptions import ClientError

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict


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


# --------------------------------------------------------------------------------------
# User profiles — parameter mapping, describe and list
# --------------------------------------------------------------------------------------
_DEFAULT_RESOURCE_SPEC = {
    "sage_maker_image_arn": "arn:aws:sagemaker:us-east-1:123456789012:image/img",
    "sage_maker_image_version_alias": "1.0",
    "instance_type": "ml.t3.medium",
    "lifecycle_config_arn": "arn:aws:sagemaker:us-east-1:123456789012:studio-lifecycle-config/lc",
    "training_plan_arn": "arn:aws:sagemaker:us-east-1:123456789012:training-plan/tp",
}
_APP_LIFECYCLE_MANAGEMENT = {
    "idle_settings": {
        "lifecycle_management": "ENABLED",
        "idle_timeout_in_minutes": 120,
        "min_idle_timeout_in_minutes": 60,
        "max_idle_timeout_in_minutes": 240,
    }
}
_CUSTOM_IMAGES = [{"image_name": "img", "image_version_number": 1, "app_image_config_name": "cfg"}]

# Every UserSettings member (a top-level module option), with every nested structure and all three acronym keys.
USER_SETTINGS_FIXTURE = {
    "execution_role": "arn:aws:iam::123456789012:role/exec",
    "security_groups": ["sg-1", "sg-2"],
    "sharing_settings": {
        "notebook_output_option": "Allowed",
        "s3_output_path": "s3://bucket/out",
        "s3_kms_key_id": "kms-key",
    },
    "jupyter_server_app_settings": {
        "default_resource_spec": _DEFAULT_RESOURCE_SPEC,
        "lifecycle_config_arns": ["arn:lc1"],
        "code_repositories": [{"repository_url": "https://example.com/repo.git"}],
    },
    "kernel_gateway_app_settings": {
        "default_resource_spec": _DEFAULT_RESOURCE_SPEC,
        "custom_images": _CUSTOM_IMAGES,
        "lifecycle_config_arns": ["arn:lc1"],
    },
    "tensor_board_app_settings": {"default_resource_spec": {"instance_type": "system"}},
    "r_studio_server_pro_app_settings": {"access_status": "ENABLED", "user_group": "R_STUDIO_USER"},
    "r_session_app_settings": {
        "default_resource_spec": {"sage_maker_image_version_arn": "arn:imgver"},
        "custom_images": _CUSTOM_IMAGES,
    },
    "canvas_app_settings": {
        "time_series_forecasting_settings": {
            "status": "ENABLED",
            "amazon_forecast_role_arn": "arn:aws:iam::123456789012:role/forecast",
        },
        "model_register_settings": {
            "status": "DISABLED",
            "cross_account_model_register_role_arn": "arn:aws:iam::123456789012:role/register",
        },
        "workspace_settings": {"s3_artifact_path": "s3://bucket/canvas", "s3_kms_key_id": "kms-key"},
        "identity_provider_o_auth_settings": [
            {"data_source_name": "Snowflake", "status": "ENABLED", "secret_arn": "arn:secret"},
        ],
        "direct_deploy_settings": {"status": "ENABLED"},
        "kendra_settings": {"status": "DISABLED"},
        "generative_ai_settings": {"amazon_bedrock_role_arn": "arn:aws:iam::123456789012:role/bedrock"},
        "emr_serverless_settings": {
            "execution_role_arn": "arn:aws:iam::123456789012:role/emr",
            "status": "ENABLED",
        },
    },
    "code_editor_app_settings": {
        "default_resource_spec": _DEFAULT_RESOURCE_SPEC,
        "custom_images": _CUSTOM_IMAGES,
        "lifecycle_config_arns": ["arn:lc1"],
        "app_lifecycle_management": _APP_LIFECYCLE_MANAGEMENT,
        "built_in_lifecycle_config_arn": "arn:builtin",
    },
    "jupyter_lab_app_settings": {
        "default_resource_spec": _DEFAULT_RESOURCE_SPEC,
        "custom_images": _CUSTOM_IMAGES,
        "lifecycle_config_arns": ["arn:lc1"],
        "code_repositories": [{"repository_url": "https://example.com/repo.git"}],
        "app_lifecycle_management": _APP_LIFECYCLE_MANAGEMENT,
        "emr_settings": {
            "assumable_role_arns": ["arn:aws:iam::123456789012:role/assume"],
            "execution_role_arns": ["arn:aws:iam::123456789012:role/run"],
        },
        "built_in_lifecycle_config_arn": "arn:builtin",
    },
    "space_storage_settings": {
        "default_ebs_storage_settings": {"default_ebs_volume_size_in_gb": 5, "maximum_ebs_volume_size_in_gb": 100}
    },
    "default_landing_uri": "studio::",
    "studio_web_portal": "ENABLED",
    "custom_posix_user_config": {"uid": 10000, "gid": 1001},
    "custom_file_system_configs": [
        {"efs_file_system_config": {"file_system_id": "fs-0123456789abcdef0", "file_system_path": "/home"}},
        {"fsx_lustre_file_system_config": {"file_system_id": "fs-0fedcba9876543210", "file_system_path": "/lustre"}},
        {"s3_file_system_config": {"s3_uri": "s3://bucket/data", "mount_path": "/mnt/s3"}},
    ],
    "studio_web_portal_settings": {
        "hidden_ml_tools": ["Comet"],
        "hidden_app_types": ["JupyterServer"],
        "hidden_instance_types": ["ml.p4d.24xlarge"],
        "hidden_sage_maker_image_version_aliases": [
            {"sage_maker_image_name": "sagemaker_distribution", "version_aliases": ["1.0"]},
        ],
        "execution_role_session_name_mode": "USER_IDENTITY",
    },
    "auto_mount_home_efs": "DefaultAsDomain",
}


def test_user_settings_options_are_every_user_settings_member():
    """Every UserSettings member is a top-level option, and the fixture sets all of them."""
    model = botocore.session.get_session().get_service_model("sagemaker")
    members = model.shape_for("UserSettings").members

    assert len(USER_SETTINGS_OPTIONS) == len(members)
    assert set(USER_SETTINGS_OPTIONS) == set(USER_SETTINGS_FIXTURE)
    assert set(build_user_settings(USER_SETTINGS_FIXTURE)) == set(members)


def test_module_argument_spec_exposes_user_settings_options_at_top_level():
    assert set(_user_settings_options()) == set(USER_SETTINGS_OPTIONS)


@pytest.mark.parametrize(
    "aws_key, produced",
    [
        ("AutoMountHomeEFS", "auto_mount_home_efs"),
        ("EFSFileSystemConfig", "efs_file_system_config"),
        ("FSxLustreFileSystemConfig", "f_sx_lustre_file_system_config"),
    ],
)
def test_camel_dict_to_snake_dict_spelling_of_acronym_keys(aws_key, produced):
    """Pins what the implicit conversion produces, which the response renames depend on."""
    assert list(camel_dict_to_snake_dict({aws_key: "x"})) == [produced]


def test_user_settings_renames_restore_the_acronym_keys():
    assert set(USER_SETTINGS_REQUEST_RENAMES.values()) == {
        "AutoMountHomeEFS",
        "EFSFileSystemConfig",
        "FSxLustreFileSystemConfig",
    }
    assert USER_SETTINGS_RESPONSE_RENAMES == {"f_sx_lustre_file_system_config": "fsx_lustre_file_system_config"}


def test_build_user_settings_converts_and_renames():
    user_settings = build_user_settings(USER_SETTINGS_FIXTURE)

    assert user_settings["AutoMountHomeEFS"] == "DefaultAsDomain"
    assert user_settings["CustomFileSystemConfigs"] == [
        {"EFSFileSystemConfig": {"FileSystemId": "fs-0123456789abcdef0", "FileSystemPath": "/home"}},
        {"FSxLustreFileSystemConfig": {"FileSystemId": "fs-0fedcba9876543210", "FileSystemPath": "/lustre"}},
        {"S3FileSystemConfig": {"S3Uri": "s3://bucket/data", "MountPath": "/mnt/s3"}},
    ]
    jupyter_lab = user_settings["JupyterLabAppSettings"]
    assert jupyter_lab["DefaultResourceSpec"]["SageMakerImageArn"] == _DEFAULT_RESOURCE_SPEC["sage_maker_image_arn"]
    assert jupyter_lab["DefaultResourceSpec"]["InstanceType"] == "ml.t3.medium"
    assert jupyter_lab["AppLifecycleManagement"]["IdleSettings"] == {
        "LifecycleManagement": "ENABLED",
        "IdleTimeoutInMinutes": 120,
        "MinIdleTimeoutInMinutes": 60,
        "MaxIdleTimeoutInMinutes": 240,
    }
    assert jupyter_lab["EmrSettings"] == {
        "AssumableRoleArns": ["arn:aws:iam::123456789012:role/assume"],
        "ExecutionRoleArns": ["arn:aws:iam::123456789012:role/run"],
    }
    assert user_settings["SpaceStorageSettings"] == {
        "DefaultEbsStorageSettings": {"DefaultEbsVolumeSizeInGb": 5, "MaximumEbsVolumeSizeInGb": 100}
    }
    assert user_settings["CanvasAppSettings"] == {
        "TimeSeriesForecastingSettings": {
            "Status": "ENABLED",
            "AmazonForecastRoleArn": "arn:aws:iam::123456789012:role/forecast",
        },
        "ModelRegisterSettings": {
            "Status": "DISABLED",
            "CrossAccountModelRegisterRoleArn": "arn:aws:iam::123456789012:role/register",
        },
        "WorkspaceSettings": {"S3ArtifactPath": "s3://bucket/canvas", "S3KmsKeyId": "kms-key"},
        "IdentityProviderOAuthSettings": [
            {"DataSourceName": "Snowflake", "Status": "ENABLED", "SecretArn": "arn:secret"}
        ],
        "DirectDeploySettings": {"Status": "ENABLED"},
        "KendraSettings": {"Status": "DISABLED"},
        "GenerativeAiSettings": {"AmazonBedrockRoleArn": "arn:aws:iam::123456789012:role/bedrock"},
        "EmrServerlessSettings": {"ExecutionRoleArn": "arn:aws:iam::123456789012:role/emr", "Status": "ENABLED"},
    }
    assert user_settings["RStudioServerProAppSettings"] == {"AccessStatus": "ENABLED", "UserGroup": "R_STUDIO_USER"}
    assert user_settings["StudioWebPortalSettings"]["HiddenSageMakerImageVersionAliases"] == [
        {"SageMakerImageName": "sagemaker_distribution", "VersionAliases": ["1.0"]}
    ]


def test_build_user_settings_drops_none_and_unrelated_options():
    params = {
        "domain_id": "d-abc123",
        "user_profile_name": "user",
        "tags": {"k": "v"},
        "wait": True,
        "execution_role": "arn:aws:iam::123456789012:role/exec",
        "security_groups": None,
        "jupyter_lab_app_settings": {
            "default_resource_spec": {"instance_type": "ml.t3.medium", "sage_maker_image_arn": None},
            "app_lifecycle_management": None,
        },
    }

    assert build_user_settings(params) == {
        "ExecutionRole": "arn:aws:iam::123456789012:role/exec",
        "JupyterLabAppSettings": {"DefaultResourceSpec": {"InstanceType": "ml.t3.medium"}},
    }


def test_build_user_settings_returns_empty_dict_without_settings():
    assert build_user_settings({"domain_id": "d-abc123", "user_profile_name": "user", "tags": None}) == {}


def test_user_settings_to_update_returns_only_differing_members_merged_over_current():
    current = deepcopy(USER_SETTINGS_FIXTURE)
    module = MagicMock()
    module.params = {
        "domain_id": "d-abc123",
        "user_profile_name": "user",
        "execution_role": current["execution_role"],
        "security_groups": list(reversed(current["security_groups"])),
        "jupyter_lab_app_settings": {
            "default_resource_spec": {"instance_type": "ml.m5.large", "sage_maker_image_arn": None},
            "app_lifecycle_management": None,
        },
        "studio_web_portal": None,
    }

    result = user_settings_to_update(module, {"user_settings": current})

    expected_jupyter_lab = deepcopy(current["jupyter_lab_app_settings"])
    expected_jupyter_lab["default_resource_spec"]["instance_type"] = "ml.m5.large"
    assert result == {"jupyter_lab_app_settings": expected_jupyter_lab}


def test_user_settings_to_update_is_empty_when_nothing_differs():
    module = MagicMock()
    module.params = {"domain_id": "d-abc123", "user_profile_name": "user", **deepcopy(USER_SETTINGS_FIXTURE)}

    assert user_settings_to_update(module, {"user_settings": deepcopy(USER_SETTINGS_FIXTURE)}) == {}


def test_user_settings_to_update_without_user_settings():
    module = MagicMock()
    module.params = {"domain_id": "d-abc123", "user_profile_name": "user", **dict.fromkeys(USER_SETTINGS_OPTIONS)}

    assert user_settings_to_update(module, {"user_settings": deepcopy(USER_SETTINGS_FIXTURE)}) == {}


def test_user_settings_round_trip_through_format_user_profile():
    profile = {
        "DomainId": "d-abc123",
        "UserProfileArn": "arn:aws:sagemaker:us-east-1:123456789012:user-profile/d-abc123/user",
        "UserProfileName": "user",
        "HomeEfsFileSystemUid": "200001",
        "Status": "InService",
        "UserSettings": build_user_settings(USER_SETTINGS_FIXTURE),
        "ResponseMetadata": {"RequestId": "abc"},
    }

    result = format_user_profile(profile)

    assert result["user_settings"] == USER_SETTINGS_FIXTURE
    assert result["domain_id"] == "d-abc123"
    assert result["user_profile_arn"] == profile["UserProfileArn"]
    assert result["home_efs_file_system_uid"] == "200001"
    assert result["status"] == "InService"
    assert "response_metadata" not in result
    assert "tags" not in result


def test_format_user_profile_attaches_tags_unchanged():
    tags = {"CamelKey": "v", "snake_key": "w"}

    result = format_user_profile({"DomainId": "d-abc123", "UserProfileName": "user"}, tags=tags)

    assert result["tags"] == tags
    assert "user_settings" not in result


def test_describe_user_profile_returns_none_when_missing():
    client = MagicMock()
    client.describe_user_profile.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFound", "Message": "User profile does not exist."}},
        "DescribeUserProfile",
    )

    assert describe_user_profile(client, "d-abc123", "missing") is None
    client.describe_user_profile.assert_called_once_with(DomainId="d-abc123", UserProfileName="missing")


def test_describe_user_profile_reraises_other_errors():
    client = MagicMock()
    client.describe_user_profile.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
        "DescribeUserProfile",
    )

    with pytest.raises(ClientError):
        describe_user_profile(client, "d-abc123", "user")


def test_list_user_profiles_maps_filters_and_paginates():
    client = MagicMock()
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value.build_full_result.return_value = {
        "UserProfiles": [{"DomainId": "d-abc123", "UserProfileName": "user"}]
    }

    result = list_user_profiles(
        client, domain_id="d-abc123", user_profile_name_contains="us", sort_by="CreationTime", sort_order="Descending"
    )

    assert result == [{"DomainId": "d-abc123", "UserProfileName": "user"}]
    client.get_paginator.assert_called_once_with("list_user_profiles")
    paginator.paginate.assert_called_once_with(
        DomainIdEquals="d-abc123", UserProfileNameContains="us", SortBy="CreationTime", SortOrder="Descending"
    )


def test_list_user_profiles_omits_unset_filters():
    client = MagicMock()
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value.build_full_result.return_value = {"UserProfiles": []}

    assert list_user_profiles(client) == []
    paginator.paginate.assert_called_once_with()
