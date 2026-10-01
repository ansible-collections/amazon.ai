#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_model_package_info
short_description: Gather information about Amazon SageMaker Model Packages
version_added: "2.0.0"
author:
    - Jan Likar (@janlikar)
description:
    - Retrieve details for a single Amazon SageMaker model package or list matching model packages.
options:
    model_package_name:
        description:
            - The name of the model package to retrieve.
            - If not provided, the module lists model packages matching the other filters.
        type: str
        aliases: ['name']
    model_package_group_name:
        description:
            - Limit results to packages in the named model package group.
        type: str
    model_approval_status:
        description:
            - Filter by model approval status.
        type: str
        choices: ['Approved', 'Rejected', 'PendingManualApproval']
    model_package_type:
        description:
            - Filter by model package type.
        type: str
        choices: ['Versioned', 'Unversioned', 'Both']
    included_data:
        description:
            - The model package data to include when describing matching packages.
        type: str
        choices: ['AllData', 'MetadataOnly']
    tags:
        description:
            - A tag map to filter model packages by.
            - Only model packages whose tags contain all the given key/value pairs are returned.
        type: dict
        aliases: ['resource_tags']
    name_contains:
        description:
            - A string that must be contained in the model package name.
        type: str
    creation_time_after:
        description:
            - Only include model packages created after this timestamp.
        type: str
    creation_time_before:
        description:
            - Only include model packages created before this timestamp.
        type: str
    sort_by:
        description:
            - The field to sort results by.
        type: str
        choices: ['Name', 'CreationTime']
    sort_order:
        description:
            - The sort order for results.
        type: str
        choices: ['Ascending', 'Descending']
    max_results:
        description:
            - The maximum number of model packages to return.
        type: int
notes:
    - 'Requires the following IAM permissions:'
    - sagemaker:DescribeModelPackage
    - sagemaker:ListModelPackages
    - sagemaker:ListTags
seealso:
    - module: amazon.ai.sagemaker_model_package
      description: Manage a model package, reconcile tags, or update approval status.
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
- name: Get info about a specific model package
  amazon.ai.sagemaker_model_package_info:
    model_package_name: example-model-package

- name: List model packages for a group
  amazon.ai.sagemaker_model_package_info:
    model_package_group_name: example-model-group
    name_contains: demo
    sort_by: CreationTime
    sort_order: Descending
"""

RETURN = r"""
model_packages:
    description: A list of dictionaries containing detailed configuration of Amazon SageMaker model packages.
    type: list
    elements: dict
    returned: always
    sample:
        - model_package_name: example-model-package
          model_package_arn: arn:aws:sagemaker:us-east-1:123456789012:model-package/example-model-package
          model_package_description: Demo model package
          model_approval_status: PendingManualApproval
          creation_time: '2025-01-01T00:00:00+00:00'
          tags:
            project: demo
    contains:
        model_package_name:
            description: The name of the model package.
            type: str
            sample: example-model-package
        model_package_arn:
            description: The ARN of the model package.
            type: str
            sample: arn:aws:sagemaker:us-east-1:123456789012:model-package/example-model-package
        model_package_description:
            description: The description of the model package.
            type: str
            sample: Demo model package
        model_approval_status:
            description: The approval status of the package.
            type: str
            sample: PendingManualApproval
        creation_time:
            description: The creation time of the package.
            type: str
            sample: '2025-01-01T00:00:00+00:00'
        tags:
            description: A dictionary containing the model package tags.
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

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_model_package
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import get_model_package_tag_arn
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_model_packages
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


def _normalize_model_package(package: Dict[str, Any], tags: Dict[str, str]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = camel_dict_to_snake_dict(package, ignore_list=["tags"])
    normalized["tags"] = tags
    return normalized


def find_model_packages(client, module: AnsibleAWSModule) -> List[Dict[str, Any]]:
    model_package_name: Optional[str] = module.params.get("model_package_name")
    desired_tags: Optional[Dict[str, str]] = module.params.get("tags")
    describe_params: Dict[str, Any] = snake_dict_to_camel_dict(
        scrub_none_parameters({"included_data": module.params.get("included_data")}),
        capitalize_first=True,
    )

    if model_package_name:
        package: Optional[Dict[str, Any]] = describe_model_package(client, model_package_name, **describe_params)
        if package is None:
            return list()
        tags: Dict[str, str] = dict()
        if desired_tags is not None:
            tag_arn = get_model_package_tag_arn(package) or package["ModelPackageArn"]
            tags = list_tags(client, tag_arn)
        return [_normalize_model_package(package, tags)]

    params: Dict[str, Any] = snake_dict_to_camel_dict(
        scrub_none_parameters(
            {
                field: module.params.get(field)
                for field in (
                    "model_package_group_name",
                    "model_approval_status",
                    "model_package_type",
                    "name_contains",
                    "creation_time_after",
                    "creation_time_before",
                    "sort_by",
                    "sort_order",
                    "max_results",
                )
            }
        ),
        capitalize_first=True,
    )

    summaries: List[Dict[str, Any]] = list_model_packages(client, **params)
    packages: List[Dict[str, Any]] = list()
    for summary in summaries:
        model_package_identifier = summary.get("ModelPackageName") or summary.get("ModelPackageArn")
        if not model_package_identifier:
            continue
        package = describe_model_package(client, model_package_identifier, **describe_params)
        if package is None:
            continue
        tags: Dict[str, str] = dict()
        if desired_tags is not None:
            tag_arn = get_model_package_tag_arn(package) or package["ModelPackageArn"]
            tags = list_tags(client, tag_arn)
        packages.append(_normalize_model_package(package, tags))

    if desired_tags is not None:
        packages = [package for package in packages if desired_tags.items() <= package["tags"].items()]

    return packages


def main() -> None:
    argument_spec = dict(
        model_package_name=dict(type="str", aliases=["name"]),
        model_package_group_name=dict(type="str"),
        model_approval_status=dict(type="str", choices=["Approved", "Rejected", "PendingManualApproval"]),
        model_package_type=dict(type="str", choices=["Versioned", "Unversioned", "Both"]),
        included_data=dict(type="str", choices=["AllData", "MetadataOnly"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        name_contains=dict(type="str"),
        creation_time_after=dict(type="str"),
        creation_time_before=dict(type="str"),
        sort_by=dict(type="str", choices=["Name", "CreationTime"]),
        sort_order=dict(type="str", choices=["Ascending", "Descending"]),
        max_results=dict(type="int"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    try:
        client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        model_packages = find_model_packages(client, module)
        module.exit_json(changed=False, model_packages=model_packages)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
