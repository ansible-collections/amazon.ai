#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_endpoint_config_info
short_description: Gather information about SageMaker endpoint configurations
version_added: "1.1.0"
author:
    - Jan Likar (@JanLikar)
description:
    - Retrieve one endpoint configuration by name or list endpoint configurations with filters.
options:
    endpoint_config_name:
        description: The endpoint configuration name to retrieve.
        type: str
        aliases: [name]
    creation_time_after:
        description: Only include configurations created after this time.
        type: str
    creation_time_before:
        description: Only include configurations created before this time.
        type: str
    max_results:
        description: Maximum number of configurations to return.
        type: int
    name_contains:
        description: A substring in the endpoint configuration name.
        type: str
    sort_by:
        description: The field to sort by.
        type: str
        choices: [Name, CreationTime]
    sort_order:
        description: The sort order.
        type: str
        choices: [Ascending, Descending]
seealso:
    - module: amazon.ai.sagemaker_endpoint_config
      description: Manage SageMaker endpoint configurations.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Get an endpoint configuration
  amazon.ai.sagemaker_endpoint_config_info:
    endpoint_config_name: my-endpoint-config

- name: List endpoint configurations
  amazon.ai.sagemaker_endpoint_config_info:
    name_contains: my-project
    sort_by: CreationTime
    sort_order: Descending
"""

RETURN = r"""
endpoint_configs:
    description: Matching endpoint configurations.
    type: list
    elements: dict
    returned: always
    sample:
        - endpoint_config_name: my-endpoint-config
          endpoint_config_arn: arn:aws:sagemaker:us-east-1:123456789012:endpoint-config/my-endpoint-config
"""

try:
    import botocore
except ImportError:
    pass

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_endpoint_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_endpoint_configs

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


def main():
    argument_spec = dict(
        endpoint_config_name=dict(type="str", aliases=["name"]),
        creation_time_after=dict(type="str"),
        creation_time_before=dict(type="str"),
        max_results=dict(type="int"),
        name_contains=dict(type="str"),
        sort_by=dict(type="str", choices=["Name", "CreationTime"]),
        sort_order=dict(type="str", choices=["Ascending", "Descending"]),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ("endpoint_config_name", "creation_time_after"),
            ("endpoint_config_name", "creation_time_before"),
            ("endpoint_config_name", "max_results"),
            ("endpoint_config_name", "name_contains"),
            ("endpoint_config_name", "sort_by"),
            ("endpoint_config_name", "sort_order"),
        ],
    )
    try:
        client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    try:
        if module.params.get("endpoint_config_name"):
            found = describe_endpoint_config(client, module.params["endpoint_config_name"])
            configs = [found] if found else []
        else:
            raw = {
                key: module.params.get(key)
                for key in (
                    "creation_time_after",
                    "creation_time_before",
                    "max_results",
                    "name_contains",
                    "sort_by",
                    "sort_order",
                )
            }
            configs = list_endpoint_configs(
                client,
                **snake_dict_to_camel_dict(scrub_none_parameters(raw), capitalize_first=True),
            )
        module.exit_json(endpoint_configs=[camel_dict_to_snake_dict(config) for config in configs])
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e)


if __name__ == "__main__":
    main()
