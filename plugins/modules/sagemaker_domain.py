#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_domain
short_description: Manage Amazon SageMaker AI Domains
version_added: "2.0.0"
description:
    - Create, update, and delete Amazon SageMaker AI Domains.
    - Domain user profiles, spaces, and applications are managed separately.
options:
    state:
        description:
            - The desired state of the Domain.
        type: str
        choices: [present, absent]
        default: present
    domain_name:
        description:
            - The name of the Domain to manage.
        type: str
        required: true
        aliases: [name]
    auth_mode:
        description:
            - The authentication mode for the Domain.
            - Required when O(state=present).
            - This setting cannot be changed after the Domain is created.
        type: str
        choices: [IAM, SSO]
    default_user_settings:
        description:
            - The default user settings for the Domain.
            - Required when O(state=present).
            - Only the execution role and security groups are managed.
        type: dict
        suboptions:
            execution_role:
                description:
                    - The IAM execution role ARN for the Domain's default user profile.
                type: str
                required: true
            security_groups:
                description:
                    - The VPC security groups for the Domain's default user settings.
                    - Required when O(app_network_access_type=VpcOnly).
                type: list
                elements: str
    app_network_access_type:
        description:
            - The network access type for applications in the Domain.
        type: str
        choices: [PublicInternetOnly, VpcOnly]
    vpc_id:
        description:
            - The VPC ID for the Domain.
            - This setting cannot be changed on an existing Domain.
            - AWS SageMaker only supports the use of a VPC with 'Default' instance tenancy.
        type: str
    subnet_ids:
        description:
            - The subnet IDs for the Domain.
            - Required with O(vpc_id), and required when O(app_network_access_type=VpcOnly).
        type: list
        elements: str
    home_efs_file_system_creation:
        description:
            - Whether to create a home Amazon EFS file system for the Domain.
            - AWS does not support changing V(Enabled) to V(Disabled).
        type: str
        choices: [Enabled, Disabled]
    kms_key_id:
        description:
            - The AWS KMS key ID used to encrypt the Domain's home file system.
            - This setting cannot be changed after the Domain is created.
        type: str
    tag_propagation:
        description:
            - Whether tags on the Domain are propagated to its associated resources.
        type: str
        choices: [ENABLED, DISABLED]
    tags:
        description:
            - Tags to associate with the Domain.
        type: dict
        aliases: [resource_tags]
    purge_tags:
        description:
            - Whether to remove tags not specified in O(tags).
        type: bool
        default: true
    retention_policy:
        description:
            - The retention policy to apply when deleting the Domain.
            - Only usable when O(state=absent)
            - The default is to retain the home file system.
        type: str
        choices: [Retain, Delete]
    wait:
        description:
            - Whether to wait for the create, update, or delete operation to complete.
        type: bool
        default: true
    wait_timeout:
        description:
            - How long, in seconds, to wait for a Domain lifecycle operation to complete.
        type: int
        default: 600
notes:
    - Required IAM actions include sagemaker:CreateDomain, sagemaker:DescribeDomain,
      sagemaker:UpdateDomain, sagemaker:DeleteDomain, sagemaker:ListDomains,
      sagemaker:ListTags, sagemaker:AddTags, sagemaker:DeleteTags, and iam:PassRole.
    - Constrain iam:PassRole to the sagemaker.amazonaws.com service where applicable.
    - Domain creation, updates, and deletion always wait for the operation to complete.
    - Domain deletion does not remove dependent user profiles, spaces, or applications.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
attributes:
    check_mode:
        description: Can run in check mode and report what would change without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_domain_info
      description: Gather information about SageMaker AI Domains.
author:
    - Domen Dobnikar (@domendobnikar)
"""

EXAMPLES = r"""
- name: Create a SageMaker AI Domain
  amazon.ai.sagemaker_domain:
    domain_name: example-domain
    auth_mode: IAM
    default_user_settings:
      execution_role: arn:aws:iam::123456789012:role/SageMakerExecutionRole

- name: Create a VPC-only SageMaker AI Domain
  amazon.ai.sagemaker_domain:
    domain_name: example-vpc-domain
    auth_mode: IAM
    app_network_access_type: VpcOnly
    vpc_id: vpc-0123456789abcdef0
    subnet_ids:
      - subnet-0123456789abcdef0
    default_user_settings:
      execution_role: arn:aws:iam::123456789012:role/SageMakerExecutionRole
      security_groups:
        - sg-0123456789abcdef0

- name: Update Domain tags
  amazon.ai.sagemaker_domain:
    domain_name: example-domain
    auth_mode: IAM
    default_user_settings:
      execution_role: arn:aws:iam::123456789012:role/SageMakerExecutionRole
    tags:
      environment: production
      owner: ml-team

- name: Delete a SageMaker AI Domain and its home file system
  amazon.ai.sagemaker_domain:
    state: absent
    domain_name: example-domain
    retention_policy: Delete
"""

RETURN = r"""
domain:
    description: The complete SageMaker Domain returned by the API after a create or update.
    type: dict
    returned: always, on success
    contains:
        domain_id:
            description: The unique identifier of the Domain.
            type: str
            sample: d-1234567890
        domain_arn:
            description: The Amazon Resource Name of the Domain.
            type: str
            sample: arn:aws:sagemaker:us-east-1:123456789012:domain/d-1234567890
        domain_name:
            description: The name of the Domain.
            type: str
            sample: example-domain
        status:
            description: The current status of the Domain.
            type: str
            sample: InService
        home_efs_file_system_id:
            description: The ID of the Domain's home Amazon EFS file system.
            type: str
        single_sign_on_managed_application_instance_id:
            description: The ID of the AWS IAM Identity Center managed application instance.
            type: str
        single_sign_on_application_arn:
            description: The ARN of the AWS IAM Identity Center application.
            type: str
        creation_time:
            description: The time when the Domain was created.
            type: str
        last_modified_time:
            description: The time when the Domain was last modified.
            type: str
        failure_reason:
            description: The reason the Domain entered a failed status.
            type: str
        security_group_id_for_domain_boundary:
            description: The security group used for the Domain boundary.
            type: str
        auth_mode:
            description: The authentication mode used by the Domain.
            type: str
        default_user_settings:
            description:
                - Default user profile settings.
                - Including execution role, security groups.
            type: dict
            contains:
                execution_role:
                    description: The execution role ARN for user profiles.
                    type: str
                security_groups:
                    description: The security groups assigned to user profiles.
                    type: list
                    elements: str
                sharing_settings:
                    description: notebook_output_option, s3_output_path, and s3_kms_key_id.
                    type: dict
                jupyter_server_app_settings:
                    description: Jupyter server app settings.
                    type: dict
                kernel_gateway_app_settings:
                    description: Kernel gateway app settings.
                    type: dict
                tensor_board_app_settings:
                    description: TensorBoard app settings.
                    type: dict
                r_studio_server_pro_app_settings:
                    description: access_status and user_group.
                    type: dict
                r_session_app_settings:
                    description: R session app settings.
                    type: dict
                canvas_app_settings:
                    description: Canvas app settings.
                    type: dict
                code_editor_app_settings:
                    description: Code editor app settings.
                    type: dict
                jupyter_lab_app_settings:
                    description: Jupyter Lab app settings.
                    type: dict
                space_storage_settings:
                    description: Space storage settings.
                    type: dict
                default_landing_uri:
                    description: The default landing URI for user profiles.
                    type: str
                studio_web_portal:
                    description: Whether the Studio web portal is enabled for user profiles.
                    type: str
                custom_posix_user_config:
                    description: Custom POSIX user configuration containing uid and gid.
                    type: dict
                custom_file_system_configs:
                    description: Custom file system configurations.
                    type: list
                    elements: dict
                studio_web_portal_settings:
                    description: Studio web portal settings.
                    type: dict
                auto_mount_home_efs:
                    description: Whether the home EFS file system is mounted automatically.
                    type: str
        domain_settings:
            description: Domain-wide settings for the SageMaker domain.
            type: dict
            contains:
                security_group_ids:
                    description: Security groups assigned to the Domain.
                    type: list
                    elements: str
                r_studio_server_pro_domain_settings:
                    type: dict
                    description: RStudio server pro domain settings.
                execution_role_identity_config:
                    description: The Domain execution role identity configuration.
                    type: str
                trusted_identity_propagation_settings:
                    description: Trusted identity propagation status.
                    type: dict
                docker_settings:
                    description: enable_docker_access, vpc_only_trusted_accounts, and rootless_docker.
                    type: dict
                amazon_q_settings:
                    description: Amazon Q status and q_profile_arn.
                    type: dict
                unified_studio_settings:
                    description: Unified Studio settings.
                    type: dict
                ip_address_type:
                    description: The IP address type used by the Domain.
                    type: str
        app_network_access_type:
            description: The network access type for applications in the Domain.
            type: str
        home_efs_file_system_kms_key_id:
            description: The KMS key ID used to encrypt the Domain's home EFS file system.
            type: str
        subnet_ids:
            description: The subnet IDs associated with the Domain.
            type: list
            elements: str
        url:
            description: The URL of the Domain.
            type: str
        vpc_id:
            description: The ID of the VPC associated with the Domain.
            type: str
        kms_key_id:
            description: The KMS key ID used to encrypt the Domain's data.
            type: str
        app_security_group_management:
            description: Whether SageMaker or the customer manages application security groups.
            type: str
        home_efs_file_system_creation:
            description: Whether a home EFS file system is created for the Domain.
            type: str
        tag_propagation:
            description: Whether Domain tags are propagated to associated resources.
            type: str
        default_space_settings:
            type: dict
            description: Default space settings for the SageMaker domain.
            contains:
                execution_role:
                    description: The execution role ARN for spaces.
                    type: str
                security_groups:
                    description: The security groups assigned to spaces.
                    type: list
                    elements: str
                jupyter_server_app_settings:
                    description: Jupyter server app settings for the space.
                    type: dict
                kernel_gateway_app_settings:
                    description: Kernel gateway app settings for the space.
                    type: dict
                jupyter_lab_app_settings:
                    description: Jupyter lab app settings for the space.
                    type: dict
                space_storage_settings:
                    description: Space storage settings for the space.
                    type: dict
                custom_posix_user_config:
                    description: Custom POSIX user configuration containing uid and gid.
                    type: dict
                custom_file_system_configs:
                    description: Custom file system configurations for the space.
                    type: list
                    elements: dict
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: Domain example-domain created successfully.
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import DomainStatus
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_domain
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_domain
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_domain
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import get_domain_by_name
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_domain_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_domain
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_domain_status

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _domain_status_check(client, module: AnsibleAWSModule, domain: Optional[Dict[str, Any]]) -> None:
    if domain:
        domain_id = domain["DomainId"]
        domain_name = domain["DomainName"]
        status = domain.get("Status")
        is_present = module.params["state"] == "present"

        if status in (
            DomainStatus.IN_SERVICE,
            DomainStatus.FAILED,
            DomainStatus.UPDATE_FAILED,
            DomainStatus.DELETE_FAILED,
        ):
            # Domain can be managed even if in FAILED state as long as the failure reason is fixed
            return

        if module.check_mode:
            module.exit_json(
                changed=False,
                msg=f"Domain {domain_name} is currently in {status} state (check mode).",
            )

        if not module.params["wait"]:
            module.exit_json(
                changed=False,
                msg=f"Domain {domain_name} is currently in {status} state (not waiting).",
            )

        if status == DomainStatus.DELETING:
            wait_for_domain_status(client, module, domain_id, DomainStatus.DELETED)
            if not is_present:
                module.exit_json(changed=False, msg=f"Domain {domain_name} is deleted.")
        elif status in (DomainStatus.PENDING, DomainStatus.UPDATING):
            wait_for_domain_status(client, module, domain_id, DomainStatus.IN_SERVICE)

        # Refresh the domain information after waiting for the status change
        domain = describe_domain(client, domain_id)


def _domain_by_name(client, domain_name: str) -> Optional[Dict[str, Any]]:
    summary = get_domain_by_name(client, domain_name)
    if summary is None:
        return None
    return describe_domain(client, summary["DomainId"])


def _present(client, module: AnsibleAWSModule, domain_name: str, existing: Optional[Dict[str, Any]]) -> None:
    if existing is None:
        changed, msg = create_domain(client, module)
        if module.check_mode:
            module.exit_json(changed=changed, msg=msg)
        existing = _domain_by_name(client, domain_name)
        if existing is None:
            module.fail_json(msg=f"Domain {domain_name} was not found after it was created.")
        module.exit_json(
            changed=changed,
            domain=camel_dict_to_snake_dict(existing, ignore_list=["tags", "Tags"]),
            msg=msg,
        )
    else:
        domain_id = existing["DomainId"]
        update_changed, msg = update_domain(client, module, existing)
        tags_changed = reconcile_domain_tags(client, module, existing)
        changed = update_changed or tags_changed
        if tags_changed and not update_changed:
            msg = f"Domain {domain_name} tags updated successfully."

        if module.check_mode:
            module.exit_json(changed=changed, msg=msg)

        else:
            if changed:
                existing = describe_domain(client, domain_id)
                if existing is None:
                    module.fail_json(msg=f"Domain {domain_name} was not found after it was updated.")
                module.exit_json(
                    changed=changed,
                    domain=camel_dict_to_snake_dict(existing, ignore_list=["tags", "Tags"]),
                    msg=msg,
                )
            module.exit_json(changed=changed, msg=msg)


def _absent(client, module: AnsibleAWSModule, domain_name: str, existing: Optional[Dict[str, Any]]) -> None:
    changed = False
    msg = f"Domain {domain_name} does not exist."
    if existing:
        changed, msg = delete_domain(client, module, existing["DomainId"])
    module.exit_json(changed=changed, msg=msg)


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        domain_name=dict(type="str", required=True, aliases=["name"]),
        auth_mode=dict(type="str", choices=["IAM", "SSO"]),
        default_user_settings=dict(
            type="dict",
            options=dict(
                execution_role=dict(type="str", required=True),
                security_groups=dict(type="list", elements="str"),
            ),
        ),
        app_network_access_type=dict(type="str", choices=["PublicInternetOnly", "VpcOnly"]),
        vpc_id=dict(type="str"),
        subnet_ids=dict(type="list", elements="str"),
        home_efs_file_system_creation=dict(type="str", choices=["Enabled", "Disabled"]),
        kms_key_id=dict(type="str"),
        tag_propagation=dict(type="str", choices=["ENABLED", "DISABLED"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        retention_policy=dict(
            type="str",
            choices=["Retain", "Delete"],
        ),
        wait_timeout=dict(type="int", default=600),
        wait=dict(type="bool", default=True),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ["auth_mode", "default_user_settings"]),
            ("app_network_access_type", "VpcOnly", ["vpc_id", "subnet_ids"]),
        ],
        required_together=[("vpc_id", "subnet_ids")],
    )
    if (
        module.params["state"] == "present"
        and module.params["app_network_access_type"] == "VpcOnly"
        and not module.params["default_user_settings"].get("security_groups")
    ):
        module.fail_json(msg="default_user_settings.security_groups is required for VpcOnly access.")
    elif module.params["state"] != "absent" and module.params["retention_policy"] is not None:
        module.fail_json(msg="retention_policy can only be set when state is absent.")

    domain_name = module.params["domain_name"]
    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing = _domain_by_name(client, domain_name)
        _domain_status_check(client, module, existing)
        if module.params["state"] == "absent":
            _absent(client, module, domain_name, existing)
        else:
            _present(client, module, domain_name, existing)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
