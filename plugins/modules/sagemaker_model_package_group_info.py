#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_model_package_group_info
short_description: Gather information about Amazon SageMaker Model Package Groups
version_added: "2.0.0"
author:
    - Jan Likar (@janlikar)
description:
    - This module retrieves details for a single Amazon SageMaker model package group or lists all model package groups.
options:
    model_package_group_name:
        description:
            - The name of the model package group to retrieve.
            - If not provided, the module lists all model package groups.
        type: str
        aliases: ['name']
    tags:
        description:
            - A tag map to filter model package groups by.
            - Only model package groups whose tags contain all the given key/value pairs are returned.
            - Ignored when O(model_package_group_name) is provided.
        type: dict
    name_contains:
        description:
            - A string that must be contained in the model package group name.
            - Ignored when O(model_package_group_name) is provided.
        type: str
    creation_time_after:
        description:
            - Only include model package groups created after this timestamp.
            - Ignored when O(model_package_group_name) is provided.
        type: str
    creation_time_before:
        description:
            - Only include model package groups created before this timestamp.
            - Ignored when O(model_package_group_name) is provided.
        type: str
    sort_by:
        description:
            - The field to sort results by.
            - Ignored when O(model_package_group_name) is provided.
        type: str
        choices: ['Name', 'CreationTime']
    sort_order:
        description:
            - The sort order for results.
            - Ignored when O(model_package_group_name) is provided.
        type: str
        choices: ['Ascending', 'Descending']
    max_items:
        description:
            - The maximum number of model package groups to return.
            - When O(tags) is set, this limit is applied before tag filtering, so fewer matching groups may be returned.
            - Ignored when O(model_package_group_name) is provided.
        type: int
notes:
    - 'Requires the following IAM permissions:'
    - sagemaker:DescribeModelPackageGroup
    - sagemaker:ListModelPackageGroups
    - sagemaker:ListTags
seealso:
    - module: amazon.ai.sagemaker_model_package_group
      description: Manage a model package group, reconcile tags, or replace it when the description changes.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
attributes:
    check_mode:
        description:
            - Supports running in check mode and reporting what would change.
        support: full
"""

EXAMPLES = r"""
- name: Get info about a specific model package group
  amazon.ai.sagemaker_model_package_group_info:
    model_package_group_name: example-model-package-group

- name: List all SageMaker model package groups
  amazon.ai.sagemaker_model_package_group_info:

- name: List model package groups filtered by name and tags
  amazon.ai.sagemaker_model_package_group_info:
    name_contains: example
    tags:
      project: demo
    sort_by: CreationTime
    sort_order: Descending
"""

RETURN = r"""
model_package_groups:
    description: A list of dictionaries containing detailed configuration of Amazon SageMaker model package groups.
    type: list
    elements: dict
    returned: always
    sample:
        - model_package_group_name: example-model-package-group
          model_package_group_arn: arn:aws:sagemaker:us-east-1:123456789012:model-package-group/example-model-package-group
          model_package_group_description: Demo model group
          creation_time: '2025-01-01T00:00:00+00:00'
          model_package_group_status: Completed
          tags:
            project: demo
    contains:
        model_package_group_name:
            description: The name of the model package group.
            type: str
            sample: example-model-package-group
        model_package_group_arn:
            description: The Amazon Resource Name (ARN) of the model package group.
            type: str
            sample: arn:aws:sagemaker:us-east-1:123456789012:model-package-group/example-model-package-group
        model_package_group_description:
            description: The description of the model package group.
            type: str
            sample: Demo model group
        creation_time:
            description: The date and time the model package group was created.
            type: str
            sample: '2025-01-01T00:00:00+00:00'
        model_package_group_status:
            description: The status of the model package group.
            type: str
            sample: Completed
        tags:
            description: A dictionary containing the model package group tags.
            type: dict
            sample:
                project: demo
"""

try:
    import botocore
except ImportError:
    pass

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_model_package_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_model_package_groups
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _normalize_model_package_group(group: Dict[str, Any], tags: Dict[str, str]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = camel_dict_to_snake_dict(group, ignore_list=["tags"])
    normalized["tags"] = tags
    return normalized


def find_model_package_groups(client, module: AnsibleAWSModule) -> List[Dict[str, Any]]:
    model_package_group_name: Optional[str] = module.params.get("model_package_group_name")

    if model_package_group_name:
        group: Optional[Dict[str, Any]] = describe_model_package_group(client, model_package_group_name)
        if group is None:
            return list()
        return [_normalize_model_package_group(group, list_tags(client, group["ModelPackageGroupArn"]))]

    params: Dict[str, Any] = dict()
    if module.params.get("name_contains"):
        params["NameContains"] = module.params["name_contains"]
    if module.params.get("creation_time_after"):
        params["CreationTimeAfter"] = module.params["creation_time_after"]
    if module.params.get("creation_time_before"):
        params["CreationTimeBefore"] = module.params["creation_time_before"]
    if module.params.get("sort_by"):
        params["SortBy"] = module.params["sort_by"]
    if module.params.get("sort_order"):
        params["SortOrder"] = module.params["sort_order"]
    summaries: List[Dict[str, Any]] = list_model_package_groups(
        client,
        max_items=module.params.get("max_items"),
        **params,
    )
    groups: List[Dict[str, Any]] = []
    desired_tags: Optional[Dict[str, str]] = module.params.get("tags")

    for summary in summaries:
        tags: Dict[str, str] = list_tags(client, summary["ModelPackageGroupArn"])

        if desired_tags and not desired_tags.items() <= tags.items():
            continue

        groups.append(_normalize_model_package_group(summary, tags))

    return groups


def main() -> None:
    argument_spec = dict(
        model_package_group_name=dict(type="str", aliases=["name"]),
        tags=dict(type="dict"),
        name_contains=dict(type="str"),
        creation_time_after=dict(type="str"),
        creation_time_before=dict(type="str"),
        sort_by=dict(type="str", choices=["Name", "CreationTime"]),
        sort_order=dict(type="str", choices=["Ascending", "Descending"]),
        max_items=dict(type="int"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    try:
        client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    try:
        model_package_groups = find_model_package_groups(client, module)
        module.exit_json(changed=False, model_package_groups=model_package_groups)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
