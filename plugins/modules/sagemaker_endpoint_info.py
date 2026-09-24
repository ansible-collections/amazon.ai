#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_endpoint_info
short_description: Gather information about SageMaker endpoints
version_added: "2.0.0"
author:
    - Jan Likar (@JanLikar)
description:
    - Retrieve one endpoint by name or list endpoints with filters.
options:
    endpoint_name:
        description: The endpoint name to retrieve.
        type: str
        aliases: [name]
    creation_time_after:
        description: Only include endpoints created after this time.
        type: str
    creation_time_before:
        description: Only include endpoints created before this time.
        type: str
    last_modified_time_after:
        description: Only include endpoints last modified after this time.
        type: str
    last_modified_time_before:
        description: Only include endpoints last modified before this time.
        type: str
    max_results:
        description: Maximum number of endpoints to return.
        type: int
    name_contains:
        description: A substring in the endpoint name.
        type: str
    status_equals:
        description: Only include endpoints with this status.
        type: str
        choices:
            - OutOfService
            - Creating
            - Updating
            - SystemUpdating
            - RollingBack
            - InService
            - Deleting
            - Failed
            - UpdateRollbackFailed
    sort_by:
        description: The field to sort by.
        type: str
        choices: [Name, CreationTime, Status]
    sort_order:
        description: The sort order.
        type: str
        choices: [Ascending, Descending]
notes:
    - Required IAM actions include sagemaker:DescribeEndpoint and sagemaker:ListEndpoints.
attributes:
    check_mode:
        description: Can run in check mode without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_endpoint
      description: Manage SageMaker endpoints.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Get an endpoint
  amazon.ai.sagemaker_endpoint_info:
    endpoint_name: my-endpoint

- name: List in-service endpoints
  amazon.ai.sagemaker_endpoint_info:
    status_equals: InService
    sort_by: CreationTime
    sort_order: Descending
"""

RETURN = r"""
endpoints:
    description: Matching endpoints.
    type: list
    elements: dict
    contains:
        endpoint_name:
            description: The name of the endpoint.
            type: str
        endpoint_arn:
            description: The Amazon Resource Name (ARN) of the endpoint.
            type: str
        endpoint_config_name:
            description: The name of the endpoint configuration.
            type: str
        endpoint_status:
            description: The status of the endpoint.
            type: str
        failure_reason:
            description: If the endpoint failed, the reason for failure.
            type: str
        production_variants:
            description: A list of production variants for the endpoint.
            type: list
            elements: dict
        creation_time:
            description: The date and time that the endpoint was created.
            type: str
        last_modified_time:
            description: The date and time that the endpoint was last modified.
            type: str
    returned: always
    sample:
        - endpoint_name: my-endpoint
          endpoint_arn: arn:aws:sagemaker:us-east-1:123456789012:endpoint/my-endpoint
          endpoint_config_name: my-endpoint-config
          endpoint_status: InService
"""

try:
    import botocore
except ImportError:
    pass

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_endpoints

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


def main() -> None:
    argument_spec = dict(
        endpoint_name=dict(type="str", aliases=["name"]),
        creation_time_after=dict(type="str"),
        creation_time_before=dict(type="str"),
        last_modified_time_after=dict(type="str"),
        last_modified_time_before=dict(type="str"),
        max_results=dict(type="int"),
        name_contains=dict(type="str"),
        status_equals=dict(
            type="str",
            choices=[
                "OutOfService",
                "Creating",
                "Updating",
                "SystemUpdating",
                "RollingBack",
                "InService",
                "Deleting",
                "Failed",
                "UpdateRollbackFailed",
            ],
        ),
        sort_by=dict(type="str", choices=["Name", "CreationTime", "Status"]),
        sort_order=dict(type="str", choices=["Ascending", "Descending"]),
    )
    list_filters = (
        "creation_time_after",
        "creation_time_before",
        "last_modified_time_after",
        "last_modified_time_before",
        "max_results",
        "name_contains",
        "status_equals",
        "sort_by",
        "sort_order",
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[("endpoint_name", filter_name) for filter_name in list_filters],
    )
    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        if module.params.get("endpoint_name"):
            found = describe_endpoint(client, module.params["endpoint_name"])
            endpoints = [found] if found else []
        else:
            raw = {key: module.params.get(key) for key in list_filters}
            summaries = list_endpoints(
                client,
                **snake_dict_to_camel_dict(scrub_none_parameters(raw), capitalize_first=True),
            )
            endpoints = [
                endpoint
                for summary in summaries
                if (endpoint := describe_endpoint(client, summary["EndpointName"])) is not None
            ]
        module.exit_json(endpoints=[camel_dict_to_snake_dict(endpoint) for endpoint in endpoints])
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
