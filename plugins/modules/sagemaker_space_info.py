#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_space_info
short_description: Gather information about SageMaker AI Spaces
version_added: "2.0.0"
description:
    - Retrieve a SageMaker Space by Domain ID and exact name.
    - List SageMaker Spaces with optional Domain and name filters.
options:
    domain_id:
        description:
            - The ID of the Domain to retrieve Spaces from.
        type: str
    space_name:
        description:
            - The exact name of the Space to retrieve.
            - Requires O(domain_id).
        type: str
        aliases: [name]
    space_name_contains:
        description:
            - Return Spaces whose names contain this string.
            - Mutually exclusive with O(space_name).
        type: str
    max_items:
        description:
            - The maximum total number of Spaces to return.
            - By default, all matching Spaces are returned.
        type: int
        version_added: "2.0.0"
    sort_by:
        description:
            - The field to sort Spaces by.
        type: str
        choices: [CreationTime, LastModifiedTime]
    sort_order:
        description:
            - The order in which to sort Spaces.
        type: str
        choices: [Ascending, Descending]
notes:
    - Required IAM actions include sagemaker:DescribeSpace and sagemaker:ListSpaces.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
attributes:
    check_mode:
        description: Can run in check mode without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_space
      description: Manage SageMaker Spaces.
author:
    - Jan Likar (@JanLikar)
"""

EXAMPLES = r"""
- name: Get a Space by Domain ID and exact name
  amazon.ai.sagemaker_space_info:
    domain_id: "d-0123456789ab"
    space_name: "ml-engineering"

- name: List Spaces in a Domain
  amazon.ai.sagemaker_space_info:
    domain_id: "d-0123456789ab"
    sort_by: "CreationTime"
    sort_order: "Descending"
    max_items: 20

- name: Search Spaces by name
  amazon.ai.sagemaker_space_info:
    space_name_contains: "engineering"
"""

RETURN = r"""
spaces:
    description: Matching SageMaker Spaces, each containing the complete DescribeSpace response.
    returned: always
    type: list
    elements: dict
    sample:
        - domain_id: "d-0123456789ab"
          space_name: "ml-engineering"
          space_arn: "arn:aws:sagemaker:us-east-1:123456789012:space/d-0123456789ab/ml-engineering"
          status: "InService"
    contains:
        domain_id:
            description: The ID of the Domain that contains the Space.
            type: str
            sample: "d-0123456789ab"
        space_arn:
            description: The Amazon Resource Name of the Space.
            type: str
            sample: "arn:aws:sagemaker:us-east-1:123456789012:space/d-0123456789ab/ml-engineering"
        space_name:
            description: The name of the Space.
            type: str
            sample: "ml-engineering"
        space_display_name:
            description: The display name of the Space.
            type: str
            sample: "ML Engineering"
        home_efs_file_system_uid:
            description: The user ID used for the Space's home file system.
            type: str
            sample: "1001"
        ownership_settings:
            description: The ownership settings for the Space.
            type: dict
            sample:
                owner_user_profile_name: "ml-engineer"
            contains:
                owner_user_profile_name:
                    description: The user profile that owns the Space.
                    type: str
                    sample: "ml-engineer"
        space_settings:
            description: The settings of the Space.
            type: dict
            sample:
                app_type: "JupyterLab"
                space_storage_settings:
                    ebs_storage_settings:
                        ebs_volume_size_in_gb: 16
            contains:
                app_type:
                    description: The application type for the Space.
                    type: str
                    sample: "JupyterLab"
                code_editor_app_settings:
                    description: Code Editor application settings.
                    type: dict
                    sample: {}
                custom_file_systems:
                    description: Custom file systems attached to the Space.
                    type: list
                    elements: dict
                    sample:
                        - efs_file_system:
                              file_system_id: "fs-12345678"
                jupyter_lab_app_settings:
                    description: JupyterLab application settings.
                    type: dict
                    sample: {}
                jupyter_server_app_settings:
                    description: JupyterServer application settings.
                    type: dict
                    sample: {}
                kernel_gateway_app_settings:
                    description: KernelGateway application settings.
                    type: dict
                    sample: {}
                remote_access:
                    description: Remote access settings.
                    type: str
                    sample: "ENABLED"
                space_managed_resources:
                    description: Resources managed by SageMaker for the Space.
                    type: str
                    sample: "ENABLED"
                space_storage_settings:
                    description: Storage settings for the Space.
                    type: dict
                    sample:
                        ebs_storage_settings:
                            ebs_volume_size_in_gb: 16
        space_sharing_settings:
            description: The sharing settings for the Space.
            type: dict
            sample:
                sharing_type: "Private"
            contains:
                sharing_type:
                    description: Whether the Space is private or shared.
                    type: str
                    sample: "Private"
        creation_time:
            description: The time when the Space was created.
            type: str
            sample: "2025-01-01T12:00:00Z"
        last_modified_time:
            description: The time when the Space was last modified.
            type: str
            sample: "2025-01-01T12:00:00Z"
        status:
            description: The current status of the Space.
            type: str
            sample: "InService"
        failure_reason:
            description: The reason the Space entered a failed status.
            type: str
            sample: "The requested operation could not be completed."
        url:
            description: The URL of the Space.
            type: str
            sample: "https://example.aws"
msg:
    description: Informative message about the query.
    returned: always
    type: str
    sample: "Retrieved 1 SageMaker Space."
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_space
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_spaces

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


def _space_info_params(module: AnsibleAWSModule) -> Dict[str, Any]:
    params = {
        "domain_id_equals": module.params.get("domain_id"),
        "space_name_contains": module.params.get("space_name_contains"),
        "sort_by": module.params.get("sort_by"),
        "sort_order": module.params.get("sort_order"),
    }
    return snake_dict_to_camel_dict(scrub_none_parameters(params), capitalize_first=True)


def _spaces_for_list(client, module: AnsibleAWSModule) -> List[Dict[str, Any]]:
    summaries = list_spaces(client, max_items=module.params.get("max_items"), **_space_info_params(module))
    spaces = []
    for summary in summaries:
        space = describe_space(client, summary["DomainId"], summary["SpaceName"])
        if space is not None:
            spaces.append(space)
    return spaces


def main() -> None:
    module = AnsibleAWSModule(
        argument_spec=dict(
            domain_id=dict(type="str"),
            space_name=dict(type="str", aliases=["name"]),
            space_name_contains=dict(type="str"),
            max_items=dict(type="int"),
            sort_by=dict(type="str", choices=["CreationTime", "LastModifiedTime"]),
            sort_order=dict(type="str", choices=["Ascending", "Descending"]),
        ),
        mutually_exclusive=[("space_name", "space_name_contains")],
        required_by=dict(space_name=["domain_id"]),
        supports_check_mode=True,
    )
    if module.params["max_items"] is not None and module.params["max_items"] < 1:
        module.fail_json(msg="max_items must be greater than zero.")

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        if module.params.get("space_name"):
            found = describe_space(client, module.params["domain_id"], module.params["space_name"])
            spaces = [found] if found else []
        else:
            spaces = _spaces_for_list(client, module)

        converted_spaces = [camel_dict_to_snake_dict(space, ignore_list=["tags", "Tags"]) for space in spaces]
        module.exit_json(
            changed=False,
            msg=f"Retrieved {len(converted_spaces)} SageMaker Space(s).",
            spaces=converted_spaces,
        )
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
