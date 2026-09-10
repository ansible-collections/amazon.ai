#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_model_info
short_description: Gather information about Amazon SageMaker Models
version_added: "2.0.0"
author:
    - Jan Likar (@janlikar)
description:
    - This module retrieves details for a single Amazon SageMaker model or lists all models.
options:
    model_name:
        description:
            - The name of the model to retrieve.
            - If not provided, the module lists all models.
        type: str
        aliases: ['name']
    tags:
        description:
            - A tag map to filter models by.
            - Only models whose tags contain all the given key/value pairs are returned.
            - Ignored when O(model_name) is provided.
        type: dict
    name_contains:
        description:
            - A string that must be contained in the model name.
            - Ignored when O(model_name) is provided.
        type: str
    creation_time_after:
        description:
            - Only include models created after this timestamp.
            - Ignored when O(model_name) is provided.
        type: str
    creation_time_before:
        description:
            - Only include models created before this timestamp.
            - Ignored when O(model_name) is provided.
        type: str
    sort_by:
        description:
            - The field to sort results by.
            - Ignored when O(model_name) is provided.
        type: str
        choices: ['Name', 'CreationTime']
    sort_order:
        description:
            - The sort order for results.
            - Ignored when O(model_name) is provided.
        type: str
        choices: ['Ascending', 'Descending']
    max_results:
        description:
            - The maximum number of models to return.
            - Ignored when O(model_name) is provided.
        type: int
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Get info about a specific model
  amazon.ai.sagemaker_model_info:
    model_name: example-model

- name: List all SageMaker models
  amazon.ai.sagemaker_model_info:

- name: List models filtered by name and tags
  amazon.ai.sagemaker_model_info:
    name_contains: example
    tags:
      project: demo
    sort_by: CreationTime
    sort_order: Descending
"""

RETURN = r"""
models:
    description: A list of dictionaries containing detailed configuration of Amazon SageMaker models.
    type: list
    elements: dict
    returned: always
    contains:
        model_name:
            description: The name of the model.
            type: str
            sample: example-model
        model_arn:
            description: The Amazon Resource Name (ARN) of the model.
            type: str
            sample: "arn:aws:sagemaker:us-east-1:123456789012:model/example-model"
        primary_container:
            description: The location of the primary docker image and container information.
            type: dict
            contains:
                image:
                    description: The path to the Docker image containing the inference code.
                    type: str
                    sample: "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest"
                model_data_url:
                    description: The S3 path where the model artifacts are stored.
                    type: str
                    sample: "s3://example-bucket/model.tar.gz"
                environment:
                    description: Environment variables set in the container.
                    type: dict
        execution_role_arn:
            description: The ARN of the IAM role that SageMaker can assume.
            type: str
            sample: "arn:aws:iam::123456789012:role/SageMakerExecutionRole"
        vpc_config:
            description: The VPC configuration for the model.
            type: dict
            contains:
                subnets:
                    description: The VPC subnet IDs.
                    type: list
                    elements: str
                security_group_ids:
                    description: The VPC security group IDs.
                    type: list
                    elements: str
        enable_network_isolation:
            description: Whether network isolation is enabled for the model.
            type: bool
        creation_time:
            description: The date and time the model was created.
            type: str
            sample: "2025-10-01T15:36:41.199376+00:00"
        tags:
            description: A dictionary containing the model tags.
            type: dict
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_model
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_models
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _normalize_model(model: Dict[str, Any], tags: Dict[str, str]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = camel_dict_to_snake_dict(model, ignore_list=["tags"])
    normalized["tags"] = tags
    return normalized


def find_models(client, module: AnsibleAWSModule) -> List[Dict[str, Any]]:
    model_name: Optional[str] = module.params.get("model_name")

    if model_name:
        model: Optional[Dict[str, Any]] = describe_model(client, model_name)
        if model is None:
            return list()
        return [_normalize_model(model, list_tags(client, model["ModelArn"]))]

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
    if module.params.get("max_results"):
        params["MaxResults"] = module.params["max_results"]

    summaries: List[Dict[str, Any]] = list_models(client, **params)
    models: List[Dict[str, Any]] = list()
    for summary in summaries:
        model = describe_model(client, summary["ModelName"])
        if model is None:
            continue
        tags: Dict[str, str] = list_tags(client, model["ModelArn"])
        models.append(_normalize_model(model, tags))

    desired_tags: Optional[Dict[str, str]] = module.params.get("tags")
    if desired_tags:
        models = [m for m in models if desired_tags.items() <= m["tags"].items()]

    return models


def main() -> None:
    argument_spec = dict(
        model_name=dict(type="str", aliases=["name"]),
        tags=dict(type="dict"),
        name_contains=dict(type="str"),
        creation_time_after=dict(type="str"),
        creation_time_before=dict(type="str"),
        sort_by=dict(type="str", choices=["Name", "CreationTime"]),
        sort_order=dict(type="str", choices=["Ascending", "Descending"]),
        max_results=dict(type="int"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    try:
        models = find_models(client, module)
        module.exit_json(changed=False, models=models)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
