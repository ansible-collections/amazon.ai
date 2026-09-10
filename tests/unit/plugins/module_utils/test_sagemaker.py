#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for sagemaker module_utils."""

from unittest.mock import MagicMock

import pytest
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _endpoint_config_properties_differ
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_endpoint_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_endpoint_configs
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_models
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_needs_replacement
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_endpoint_config_tags
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
