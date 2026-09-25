#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for sagemaker module_utils."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _endpoint_config_properties_differ
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_endpoint_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_model_package_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_endpoint_configs
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_model_package_groups
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_models
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_needs_replacement
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_package_group_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_endpoint_config_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_model_package_group_tags
from ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_group_info import find_model_package_groups
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
