#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for sagemaker module_utils."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import DomainStatus
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _build_domain_params
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _build_replacement_space_params
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _endpoint_config_properties_differ
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_domain
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_domain
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_domain
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_endpoint_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_model_package_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import domain_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import get_domain_by_name
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_domains
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_endpoint_configs
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_model_package_groups
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_models
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_spaces
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_needs_replacement
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_package_group_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_domain_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_endpoint_config_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_domain
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import space_needs_replacement
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import space_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_model_package_group_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_domain_status
from ansible_collections.amazon.ai.plugins.modules.sagemaker_model_package_group_info import find_model_package_groups
from botocore.exceptions import ClientError


def test_describe_domain_returns_none_when_missing():
    client = MagicMock()
    client.describe_domain.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFound", "Message": "Domain not found"}},
        "DescribeDomain",
    )

    assert describe_domain(client, "d-missing") is None
    client.describe_domain.assert_called_once_with(DomainId="d-missing")


def test_describe_domain_reraises_other_errors():
    client = MagicMock()
    client.describe_domain.side_effect = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "Invalid domain ID"}},
        "DescribeDomain",
    )

    with pytest.raises(ClientError):
        describe_domain(client, "invalid")


def test_describe_domain_returns_response():
    client = MagicMock()
    client.describe_domain.return_value = {"DomainId": "d-123", "Status": "InService"}

    assert describe_domain(client, "d-123") == {"DomainId": "d-123", "Status": "InService"}
    client.describe_domain.assert_called_once_with(DomainId="d-123")


def test_list_domains_without_max_results_lists_all_pages():
    client = MagicMock()
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value.build_full_result.return_value = {
        "Domains": [{"DomainName": "domain-a"}, {"DomainName": "domain-b"}]
    }

    assert list_domains(client) == [{"DomainName": "domain-a"}, {"DomainName": "domain-b"}]
    paginator.paginate.assert_called_once_with()


def test_list_domains_caps_total_results_using_pagination_config():
    client = MagicMock()
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value.build_full_result.return_value = {"Domains": [{"DomainName": "domain-a"}]}

    assert list_domains(client, MaxResults=1) == [{"DomainName": "domain-a"}]
    client.get_paginator.assert_called_once_with("list_domains")
    paginator.paginate.assert_called_once_with(PaginationConfig={"MaxItems": 1})


def test_get_domain_by_name_matches_exactly_after_listing_all_pages():
    client = MagicMock()
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value.build_full_result.return_value = {
        "Domains": [{"DomainName": "matching-domain-suffix"}, {"DomainName": "matching-domain"}]
    }

    assert get_domain_by_name(client, "matching-domain") == {"DomainName": "matching-domain"}
    paginator.paginate.assert_called_once_with()


def test_get_domain_by_name_returns_none_when_no_exact_match_exists():
    client = MagicMock()
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value.build_full_result.return_value = {
        "Domains": [{"DomainName": "matching-domain-suffix"}]
    }

    assert get_domain_by_name(client, "matching-domain") is None


def test_build_domain_params_converts_options_and_tags():
    module = MagicMock()
    module.params = {
        "domain_name": "test-domain",
        "auth_mode": "IAM",
        "default_user_settings": {"execution_role": "arn:aws:iam::123456789012:role/test"},
        "app_network_access_type": None,
        "vpc_id": None,
        "subnet_ids": None,
        "home_efs_file_system_creation": None,
        "kms_key_id": None,
        "tag_propagation": "ENABLED",
        "tags": {"Environment": "test"},
    }

    assert _build_domain_params(module) == {
        "DomainName": "test-domain",
        "AuthMode": "IAM",
        "DefaultUserSettings": {"ExecutionRole": "arn:aws:iam::123456789012:role/test"},
        "TagPropagation": "ENABLED",
        "Tags": [{"Key": "Environment", "Value": "test"}],
    }


def test_domain_status_values():
    assert {status.value for status in DomainStatus} == {
        "Deleting",
        "Failed",
        "InService",
        "Pending",
        "Updating",
        "Update_Failed",
        "Delete_Failed",
        "Deleted",
    }


SAGEMAKER_UTILS = "ansible_collections.amazon.ai.plugins.module_utils.sagemaker"
DOMAIN_ROLE = "arn:aws:iam::123456789012:role/test"
DOMAIN_ARN = "arn:aws:sagemaker:us-east-1:123456789012:domain/d-123"


class ModuleFailure(Exception):
    pass


def _client_error(code, operation):
    return ClientError({"Error": {"Code": code, "Message": f"{code} error"}}, operation)


def _domain_module(check_mode=False, **overrides):
    module = MagicMock()
    module.check_mode = check_mode
    module.params = {
        "domain_name": "example-domain",
        "auth_mode": "IAM",
        "default_user_settings": {"execution_role": DOMAIN_ROLE, "security_groups": None},
        "app_network_access_type": None,
        "vpc_id": None,
        "subnet_ids": None,
        "home_efs_file_system_creation": None,
        "kms_key_id": None,
        "tag_propagation": None,
        "tags": None,
        "purge_tags": True,
        "retention_policy": None,
        "wait": False,
        "wait_timeout": 600,
    }
    module.params.update(overrides)
    module.fail_json.side_effect = ModuleFailure
    return module


def _existing_domain(**overrides):
    domain = {
        "DomainId": "d-123",
        "DomainName": "example-domain",
        "DomainArn": DOMAIN_ARN,
        "Status": "InService",
        "AuthMode": "IAM",
        "DefaultUserSettings": {"ExecutionRole": DOMAIN_ROLE, "SecurityGroups": ["sg-1", "sg-2"]},
        "AppNetworkAccessType": "VpcOnly",
        "VpcId": "vpc-1",
        "SubnetIds": ["subnet-1", "subnet-2"],
        "HomeEfsFileSystemCreation": "Enabled",
        "KmsKeyId": "kms-1",
        "TagPropagation": "DISABLED",
    }
    domain.update(overrides)
    return domain


def _fail_msg(module):
    return module.fail_json.call_args.kwargs["msg"]


@pytest.fixture(name="mock_wait_for_domain_status")
def fixture_mock_wait_for_domain_status():
    with patch(f"{SAGEMAKER_UTILS}.wait_for_domain_status") as mock:
        yield mock


class TestDomainNeedsUpdate:
    def test_matching_settings_need_no_update(self):
        module = _domain_module(
            default_user_settings={"execution_role": DOMAIN_ROLE, "security_groups": ["sg-2", "sg-1"]},
            app_network_access_type="VpcOnly",
            vpc_id="vpc-1",
            subnet_ids=["subnet-2", "subnet-1"],
            home_efs_file_system_creation="Enabled",
            kms_key_id="kms-1",
            tag_propagation="DISABLED",
        )

        assert domain_needs_update(_existing_domain(), module) is False
        module.fail_json.assert_not_called()

    def test_unset_options_are_ignored(self):
        module = _domain_module(auth_mode=None, default_user_settings=None)

        assert domain_needs_update(_existing_domain(), module) is False

    def test_empty_security_groups_match_missing_existing_value(self):
        module = _domain_module(default_user_settings={"execution_role": DOMAIN_ROLE, "security_groups": []})
        existing = _existing_domain(DefaultUserSettings={"ExecutionRole": DOMAIN_ROLE})

        assert domain_needs_update(existing, module) is False

    @pytest.mark.parametrize(
        "option, value",
        [("auth_mode", "SSO"), ("kms_key_id", "kms-2"), ("vpc_id", "vpc-2")],
    )
    def test_immutable_option_change_fails(self, option, value):
        module = _domain_module(**{option: value})

        with pytest.raises(ModuleFailure):
            domain_needs_update(_existing_domain(), module)
        assert _fail_msg(module).startswith(f"Cannot change {option} for an existing SageMaker Domain.")

    @pytest.mark.parametrize(
        "overrides",
        [
            {"default_user_settings": {"execution_role": f"{DOMAIN_ROLE}-new", "security_groups": None}},
            {"default_user_settings": {"execution_role": DOMAIN_ROLE, "security_groups": ["sg-3"]}},
            {"app_network_access_type": "PublicInternetOnly"},
            {"home_efs_file_system_creation": "Disabled"},
            {"tag_propagation": "ENABLED"},
            {"subnet_ids": ["subnet-1", "subnet-3"]},
        ],
        ids=[
            "execution_role",
            "security_groups",
            "app_network_access_type",
            "home_efs_file_system_creation",
            "tag_propagation",
            "subnet_ids",
        ],
    )
    def test_mutable_option_drift_needs_update(self, overrides):
        module = _domain_module(**overrides)

        assert domain_needs_update(_existing_domain(), module) is True
        module.fail_json.assert_not_called()

    def test_security_groups_added_to_domain_without_any(self):
        module = _domain_module(default_user_settings={"execution_role": DOMAIN_ROLE, "security_groups": ["sg-1"]})
        existing = _existing_domain(DefaultUserSettings={"ExecutionRole": DOMAIN_ROLE})

        assert domain_needs_update(existing, module) is True


class TestCreateDomain:
    def test_check_mode_does_not_create(self, mock_wait_for_domain_status):
        client = MagicMock()
        module = _domain_module(check_mode=True, wait=True)

        assert create_domain(client, module) == (True, "Check mode: would have created Domain example-domain.")
        client.create_domain.assert_not_called()
        mock_wait_for_domain_status.assert_not_called()

    def test_creates_domain_with_converted_params(self, mock_wait_for_domain_status):
        client = MagicMock()
        client.create_domain.return_value = {"DomainArn": DOMAIN_ARN, "DomainId": "d-123"}
        module = _domain_module(tag_propagation="ENABLED", tags={"Environment": "test"})

        assert create_domain(client, module) == (True, "Domain example-domain created successfully.")
        client.create_domain.assert_called_once_with(
            DomainName="example-domain",
            AuthMode="IAM",
            DefaultUserSettings={"ExecutionRole": DOMAIN_ROLE},
            TagPropagation="ENABLED",
            Tags=[{"Key": "Environment", "Value": "test"}],
        )
        mock_wait_for_domain_status.assert_not_called()

    def test_waits_for_in_service_when_wait_enabled(self, mock_wait_for_domain_status):
        client = MagicMock()
        client.create_domain.return_value = {"DomainId": "d-123"}
        module = _domain_module(wait=True)

        create_domain(client, module)

        mock_wait_for_domain_status.assert_called_once_with(client, module, "d-123", DomainStatus.IN_SERVICE)

    def test_fails_when_no_domain_id_returned(self, mock_wait_for_domain_status):
        client = MagicMock()
        client.create_domain.return_value = {}
        module = _domain_module(wait=True)

        with pytest.raises(ModuleFailure):
            create_domain(client, module)
        assert _fail_msg(module) == "CreateDomain did not return a DomainId for Domain example-domain."
        mock_wait_for_domain_status.assert_not_called()

    def test_resource_in_use_fails_with_guidance(self):
        client = MagicMock()
        client.create_domain.side_effect = _client_error("ResourceInUse", "CreateDomain")
        module = _domain_module()

        with pytest.raises(ModuleFailure):
            create_domain(client, module)
        assert "conflicting resource operation is in progress" in _fail_msg(module)

    def test_other_errors_propagate(self):
        client = MagicMock()
        client.create_domain.side_effect = _client_error("ValidationException", "CreateDomain")

        with pytest.raises(ClientError):
            create_domain(client, _domain_module())


class TestUpdateDomain:
    def test_up_to_date_domain_is_not_updated(self, mock_wait_for_domain_status):
        client = MagicMock()
        module = _domain_module(wait=True)

        assert update_domain(client, module, _existing_domain()) == (
            False,
            "Domain example-domain is already up to date.",
        )
        client.update_domain.assert_not_called()
        mock_wait_for_domain_status.assert_not_called()

    def test_check_mode_does_not_update(self, mock_wait_for_domain_status):
        client = MagicMock()
        module = _domain_module(check_mode=True, tag_propagation="ENABLED")

        assert update_domain(client, module, _existing_domain()) == (
            True,
            "Check mode: would have updated Domain example-domain.",
        )
        client.update_domain.assert_not_called()

    def test_sends_only_mutable_fields(self, mock_wait_for_domain_status):
        client = MagicMock()
        module = _domain_module(
            default_user_settings={"execution_role": DOMAIN_ROLE, "security_groups": ["sg-3"]},
            app_network_access_type="VpcOnly",
            vpc_id="vpc-1",
            subnet_ids=["subnet-1"],
            home_efs_file_system_creation="Enabled",
            kms_key_id="kms-1",
            tag_propagation="ENABLED",
            tags={"Environment": "test"},
        )

        assert update_domain(client, module, _existing_domain()) == (
            True,
            "Domain example-domain updated successfully.",
        )
        client.update_domain.assert_called_once_with(
            DomainId="d-123",
            DefaultUserSettings={"ExecutionRole": DOMAIN_ROLE, "SecurityGroups": ["sg-3"]},
            AppNetworkAccessType="VpcOnly",
            SubnetIds=["subnet-1"],
            HomeEfsFileSystemCreation="Enabled",
            TagPropagation="ENABLED",
        )
        mock_wait_for_domain_status.assert_not_called()

    def test_waits_for_in_service_when_wait_enabled(self, mock_wait_for_domain_status):
        client = MagicMock()
        module = _domain_module(wait=True, tag_propagation="ENABLED")

        update_domain(client, module, _existing_domain())

        mock_wait_for_domain_status.assert_called_once_with(client, module, "d-123", DomainStatus.IN_SERVICE)

    def test_resource_in_use_fails_with_guidance(self):
        client = MagicMock()
        client.update_domain.side_effect = _client_error("ResourceInUse", "UpdateDomain")
        module = _domain_module(tag_propagation="ENABLED")

        with pytest.raises(ModuleFailure):
            update_domain(client, module, _existing_domain())
        assert "while dependent apps are active" in _fail_msg(module)


class TestDeleteDomain:
    def test_check_mode_does_not_delete(self, mock_wait_for_domain_status):
        client = MagicMock()
        module = _domain_module(check_mode=True, wait=True)

        assert delete_domain(client, module, "d-123") == (True, "Check mode: would have deleted Domain d-123.")
        client.delete_domain.assert_not_called()
        mock_wait_for_domain_status.assert_not_called()

    def test_deletes_without_retention_policy(self, mock_wait_for_domain_status):
        client = MagicMock()
        module = _domain_module()

        assert delete_domain(client, module, "d-123") == (True, "Domain d-123 deleted successfully.")
        client.delete_domain.assert_called_once_with(DomainId="d-123")
        mock_wait_for_domain_status.assert_not_called()

    @pytest.mark.parametrize("retention_policy", ["Retain", "Delete"])
    def test_deletes_with_retention_policy(self, retention_policy, mock_wait_for_domain_status):
        client = MagicMock()
        module = _domain_module(retention_policy=retention_policy)

        delete_domain(client, module, "d-123")

        client.delete_domain.assert_called_once_with(
            DomainId="d-123", RetentionPolicy={"HomeEfsFileSystem": retention_policy}
        )

    def test_waits_for_deletion_when_wait_enabled(self, mock_wait_for_domain_status):
        client = MagicMock()
        module = _domain_module(wait=True)

        delete_domain(client, module, "d-123")

        mock_wait_for_domain_status.assert_called_once_with(client, module, "d-123", DomainStatus.DELETED)

    def test_already_deleted_domain_is_tolerated(self, mock_wait_for_domain_status):
        client = MagicMock()
        client.delete_domain.side_effect = _client_error("ResourceNotFound", "DeleteDomain")
        module = _domain_module()

        delete_domain(client, module, "d-123")

        module.fail_json.assert_not_called()

    def test_resource_in_use_fails_with_guidance(self):
        client = MagicMock()
        client.delete_domain.side_effect = _client_error("ResourceInUse", "DeleteDomain")
        module = _domain_module()

        with pytest.raises(ModuleFailure):
            delete_domain(client, module, "d-123")
        assert "while child resources such as apps or user profiles remain" in _fail_msg(module)


class TestWaitForDomainStatus:
    @pytest.fixture(autouse=True)
    def mock_time(self):
        with patch(f"{SAGEMAKER_UTILS}.time") as mock:
            self.time = mock
            yield mock

    @pytest.fixture
    def mock_describe_domain(self):
        with patch(f"{SAGEMAKER_UTILS}.describe_domain") as mock:
            yield mock

    @staticmethod
    def _statuses(*statuses):
        return [None if status is None else {"DomainId": "d-123", "Status": status} for status in statuses]

    def test_returns_when_status_already_reached(self, mock_describe_domain):
        client = MagicMock()
        module = _domain_module()
        mock_describe_domain.side_effect = self._statuses("InService")

        wait_for_domain_status(client, module, "d-123", DomainStatus.IN_SERVICE)

        mock_describe_domain.assert_called_once_with(client, "d-123")
        self.time.sleep.assert_not_called()
        module.fail_json.assert_not_called()

    def test_polls_until_status_reached(self, mock_describe_domain):
        module = _domain_module()
        mock_describe_domain.side_effect = self._statuses("Pending", "Updating", "InService")

        wait_for_domain_status(MagicMock(), module, "d-123", DomainStatus.IN_SERVICE, sleep_time=7)

        assert mock_describe_domain.call_count == 3
        self.time.sleep.assert_called_with(7)
        module.fail_json.assert_not_called()

    @pytest.mark.parametrize("status", ["Failed", "Update_Failed", "Delete_Failed", "Deleted"])
    def test_terminal_status_fails_early(self, status, mock_describe_domain):
        module = _domain_module()
        mock_describe_domain.side_effect = self._statuses("Pending", status, "InService")

        with pytest.raises(ModuleFailure):
            wait_for_domain_status(MagicMock(), module, "d-123", DomainStatus.IN_SERVICE)

        assert _fail_msg(module) == f"Domain d-123 entered terminal status {status} while waiting for InService."
        assert mock_describe_domain.call_count == 2

    def test_missing_domain_fails_when_waiting_for_in_service(self, mock_describe_domain):
        module = _domain_module()
        mock_describe_domain.side_effect = self._statuses("Pending", None)

        with pytest.raises(ModuleFailure):
            wait_for_domain_status(MagicMock(), module, "d-123", DomainStatus.IN_SERVICE)

        assert _fail_msg(module) == "Domain d-123 was not found while waiting for status InService."

    def test_returns_once_domain_is_gone_when_waiting_for_deletion(self, mock_describe_domain):
        module = _domain_module()
        mock_describe_domain.side_effect = self._statuses("Deleting", "Deleting", None)

        wait_for_domain_status(MagicMock(), module, "d-123", DomainStatus.DELETED)

        assert mock_describe_domain.call_count == 3
        module.fail_json.assert_not_called()

    @pytest.mark.parametrize("status", ["Delete_Failed", "Failed"])
    def test_failed_deletion_fails_early(self, status, mock_describe_domain):
        module = _domain_module()
        mock_describe_domain.side_effect = self._statuses("Deleting", status, None)

        with pytest.raises(ModuleFailure):
            wait_for_domain_status(MagicMock(), module, "d-123", DomainStatus.DELETED)

        assert _fail_msg(module) == f"Domain d-123 entered terminal status {status} while waiting for deletion."
        assert mock_describe_domain.call_count == 2

    @pytest.mark.parametrize(
        "target, status, expected",
        [
            (DomainStatus.IN_SERVICE, "Pending", "InService"),
            (DomainStatus.DELETED, "Deleting", "absence"),
        ],
    )
    def test_times_out_after_wait_timeout(self, target, status, expected, mock_describe_domain):
        module = _domain_module(wait_timeout=15)
        mock_describe_domain.return_value = {"DomainId": "d-123", "Status": status}

        with pytest.raises(ModuleFailure):
            wait_for_domain_status(MagicMock(), module, "d-123", target, sleep_time=5)

        assert mock_describe_domain.call_count == 3
        assert _fail_msg(module) == (
            f"Timeout waiting for Domain d-123 to reach {expected}. Last known status: {status}."
        )

    def test_short_wait_timeout_still_checks_once(self, mock_describe_domain):
        module = _domain_module(wait_timeout=1)
        mock_describe_domain.side_effect = self._statuses("InService")

        wait_for_domain_status(MagicMock(), module, "d-123", DomainStatus.IN_SERVICE, sleep_time=5)

        mock_describe_domain.assert_called_once()
        module.fail_json.assert_not_called()


class TestReconcileDomainTags:
    @staticmethod
    def _client(current_tags):
        client = MagicMock()
        client.get_paginator.return_value.paginate.return_value.build_full_result.return_value = {
            "Tags": [{"Key": key, "Value": value} for key, value in current_tags.items()]
        }
        return client

    def test_tags_unset_skips_api_calls(self):
        client = MagicMock()

        assert reconcile_domain_tags(client, _domain_module(), _existing_domain()) is False
        client.get_paginator.assert_not_called()
        client.add_tags.assert_not_called()
        client.delete_tags.assert_not_called()

    def test_matching_tags_are_not_changed(self):
        client = self._client({"Environment": "test"})
        module = _domain_module(tags={"Environment": "test"})

        assert reconcile_domain_tags(client, module, _existing_domain()) is False
        client.get_paginator.assert_called_once_with("list_tags")
        client.get_paginator.return_value.paginate.assert_called_once_with(ResourceArn=DOMAIN_ARN)
        client.add_tags.assert_not_called()
        client.delete_tags.assert_not_called()

    def test_adds_updates_and_purges_tags(self):
        client = self._client({"Environment": "dev", "Old": "value"})
        module = _domain_module(tags={"Environment": "test", "Team": "ml"})

        assert reconcile_domain_tags(client, module, _existing_domain()) is True
        client.add_tags.assert_called_once()
        assert client.add_tags.call_args.kwargs["ResourceArn"] == DOMAIN_ARN
        assert sorted(client.add_tags.call_args.kwargs["Tags"], key=lambda tag: tag["Key"]) == [
            {"Key": "Environment", "Value": "test"},
            {"Key": "Team", "Value": "ml"},
        ]
        client.delete_tags.assert_called_once_with(ResourceArn=DOMAIN_ARN, TagKeys=["Old"])

    def test_purge_false_keeps_unlisted_tags(self):
        client = self._client({"Old": "value"})
        module = _domain_module(tags={"Team": "ml"}, purge_tags=False)

        assert reconcile_domain_tags(client, module, _existing_domain()) is True
        client.add_tags.assert_called_once_with(ResourceArn=DOMAIN_ARN, Tags=[{"Key": "Team", "Value": "ml"}])
        client.delete_tags.assert_not_called()

    def test_only_removes_tags_when_nothing_to_add(self):
        client = self._client({"Environment": "test", "Old": "value"})
        module = _domain_module(tags={"Environment": "test"})

        assert reconcile_domain_tags(client, module, _existing_domain()) is True
        client.add_tags.assert_not_called()
        client.delete_tags.assert_called_once_with(ResourceArn=DOMAIN_ARN, TagKeys=["Old"])

    def test_check_mode_reports_change_without_modifying_tags(self):
        client = self._client({"Old": "value"})
        module = _domain_module(check_mode=True, tags={"Team": "ml"})

        assert reconcile_domain_tags(client, module, _existing_domain()) is True
        client.add_tags.assert_not_called()
        client.delete_tags.assert_not_called()


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


def _space_module(params):
    module = MagicMock()
    module.params = params
    return module


def test_list_spaces_applies_max_items_and_forwards_filters():
    client = MagicMock()
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value.build_full_result.return_value = {"Spaces": [{"SpaceName": "space-a"}]}

    result = list_spaces(client, max_items=1, DomainIdEquals="domain-a")

    paginator.paginate.assert_called_once_with(
        DomainIdEquals="domain-a",
        PaginationConfig={"MaxItems": 1},
    )
    assert result == [{"SpaceName": "space-a"}]


def test_space_needs_replacement_detects_ownership_settings_change():
    module = _space_module({"ownership_settings": {"owner_user_profile_name": "profile-b"}})
    existing = {"OwnershipSettings": {"OwnerUserProfileName": "profile-a"}}

    assert space_needs_replacement(existing, module)


def test_space_needs_replacement_detects_app_type_change():
    module = _space_module({"space_settings": {"app_type": "JupyterLab"}})
    existing = {"SpaceSettings": {"AppType": "CodeEditor"}}

    assert space_needs_replacement(existing, module)


def test_space_needs_replacement_ignores_omitted_immutable_settings():
    module = _space_module({})
    existing = {
        "OwnershipSettings": {"OwnerUserProfileName": "profile-a"},
        "SpaceSharingSettings": {"SharingType": "Private"},
        "SpaceSettings": {"AppType": "JupyterLab"},
    }

    assert not space_needs_replacement(existing, module)


def test_space_needs_update_detects_mutable_space_changes():
    module = _space_module(
        {
            "space_display_name": "Updated",
            "space_settings": {"remote_access": "ENABLED"},
        }
    )
    existing = {
        "SpaceDisplayName": "Existing",
        "SpaceSettings": {"AppType": "JupyterLab", "RemoteAccess": "DISABLED"},
    }

    assert space_needs_update(existing, module)


def test_space_needs_update_ignores_immutable_app_type():
    module = _space_module({"space_settings": {"app_type": "CodeEditor"}})
    existing = {"SpaceSettings": {"AppType": "JupyterLab"}}

    assert not space_needs_update(existing, module)


def test_build_replacement_space_params_preserves_unspecified_existing_settings():
    module = _space_module({"space_settings": {"app_type": "JupyterLab"}})
    existing = {
        "OwnershipSettings": {"OwnerUserProfileName": "profile-a"},
        "SpaceSharingSettings": {"SharingType": "Private"},
        "SpaceDisplayName": "Existing",
        "SpaceSettings": {
            "AppType": "CodeEditor",
            "RemoteAccess": "ENABLED",
        },
    }

    params = _build_replacement_space_params(module, existing)

    assert params["OwnershipSettings"] == {"OwnerUserProfileName": "profile-a"}
    assert params["SpaceSharingSettings"] == {"SharingType": "Private"}
    assert params["SpaceDisplayName"] == "Existing"
    assert params["SpaceSettings"] == {"AppType": "JupyterLab", "RemoteAccess": "ENABLED"}


def test_build_replacement_space_params_omits_missing_existing_settings():
    module = _space_module({"space_settings": {"app_type": "JupyterLab"}})
    existing = {"SpaceSettings": {"AppType": "CodeEditor"}}

    params = _build_replacement_space_params(module, existing)

    assert params == {"SpaceSettings": {"AppType": "JupyterLab"}}


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
