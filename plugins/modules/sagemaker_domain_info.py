#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_domain_info
short_description: Gather information about SageMaker AI Domains
version_added: "2.0.0"
description:
    - Retrieve a SageMaker AI Domain by ID or exact name.
    - List SageMaker AI Domains when no selector is provided.
options:
    domain_id:
        description:
            - The ID of the Domain to retrieve.
        type: str
    domain_name:
        description:
            - The exact name of the Domain to retrieve.
        type: str
        aliases: [name]
    max_results:
        description:
            - The maximum number of Domains to return when listing Domains.
        type: int
notes:
    - Required IAM actions include sagemaker:DescribeDomain and sagemaker:ListDomains.
attributes:
    check_mode:
        description: Can run in check mode without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_domain
      description: Manage SageMaker AI Domains.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
author:
    - Domen Dobnikar (@domendobnikar)
"""

EXAMPLES = r"""
- name: Get a Domain by ID
  amazon.ai.sagemaker_domain_info:
    domain_id: d-0123456789ab

- name: Get a Domain by exact name
  amazon.ai.sagemaker_domain_info:
    domain_name: example-domain

- name: List up to ten Domains
  amazon.ai.sagemaker_domain_info:
    max_results: 10
"""

RETURN = r"""
domains:
    description: Matching SageMaker AI Domains.
    type: list
    elements: dict
    contains:
        domain_id:
            description: The unique identifier of the Domain.
            type: str
        domain_arn:
            description: The Amazon Resource Name (ARN) of the Domain.
            type: str
        domain_name:
            description: The name of the Domain.
            type: str
        status:
            description: The current status of the Domain.
            type: str
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
            description: Default user profile settings for the SageMaker domain.
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
                    description: Jupyter server app settings for the user profile.
                    type: dict
                kernel_gateway_app_settings:
                    description: Kernel gateway app settings for the user profile.
                    type: dict
                tensor_board_app_settings:
                    description: TensorBoard app settings for the user profile.
                    type: dict
                r_studio_server_pro_app_settings:
                    description: RStudio server pro app settings for the user profile.
                    type: dict
                r_session_app_settings:
                    description: R session app settings for the user profile.
                    type: dict
                canvas_app_settings:
                    description: Canvas app settings for the user profile.
                    type: dict
                code_editor_app_settings:
                    description: Code editor app settings for the user profile.
                    type: dict
                jupyter_lab_app_settings:
                    description: Jupyter lab app settings for the user profile.
                    type: dict
                space_storage_settings:
                    description: Space storage settings for the user profile.
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
                    description: Custom file system configurations for the user profile.
                    type: list
                    elements: dict
                studio_web_portal_settings:
                    description: Studio web portal settings for the user profile.
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
                    description: R studio server pro domain settings.
                    type: dict
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
                    description: Unified Studio settings for the SageMaker domain.
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
            description: Default space settings for the SageMaker domain.
            type: dict
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
        tags:
            description: Tags associated with the Domain.
            type: list
            elements: dict
    returned: always, on success
"""

try:
    import botocore
except ImportError:
    pass

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_domain
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import get_domain_by_name
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_domains

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


def _add_tags(client, domains):
    for domain in domains:
        if domain and "DomainArn" in domain:
            domain_arn = domain["DomainArn"]
            tags = client.list_tags(ResourceArn=domain_arn)
            domain["Tags"] = tags["Tags"] if tags and "Tags" in tags else []


def main() -> None:
    module = AnsibleAWSModule(
        argument_spec=dict(
            domain_id=dict(type="str"),
            domain_name=dict(type="str", aliases=["name"]),
            max_results=dict(type="int"),
        ),
        mutually_exclusive=[("domain_id", "domain_name")],
        supports_check_mode=True,
    )
    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        if module.params.get("domain_id"):
            found = describe_domain(client, module.params["domain_id"])
            domains = [found] if found else []
        elif module.params.get("domain_name"):
            found = get_domain_by_name(client, module.params["domain_name"])
            if found:
                found = describe_domain(client, found["DomainId"])
            domains = [found] if found else []
        else:
            params = snake_dict_to_camel_dict(
                scrub_none_parameters({"max_results": module.params.get("max_results")}),
                capitalize_first=True,
            )
            found_domains = list_domains(client, **params)
            domains = []
            for domain in found_domains:
                if domain:
                    domains.append(describe_domain(client, domain["DomainId"]))

        _add_tags(client, domains)

        module.exit_json(
            changed=False,
            domains=[camel_dict_to_snake_dict(domain, ignore_list=["tags", "Tags"]) for domain in domains],
        )
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
