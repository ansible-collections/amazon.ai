#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_app_image_config_info
short_description: Gather information about Amazon SageMaker AppImageConfigs
version_added: "2.0.0"
author:
    - Matej Artač (@matejart)
description:
    - Retrieve a single Amazon SageMaker AppImageConfig by name, or list AppImageConfigs with optional filters.
    - Every returned AppImageConfig carries its configuration blocks, and its tags when O(include_tags) or O(tags) is set.
options:
    app_image_config_name:
        description:
            - The name of the AppImageConfig to retrieve.
            - When it is omitted, AppImageConfigs are listed, optionally filtered by the other options.
            - An AppImageConfig that does not exist gives an empty list.
            - Mutually exclusive with O(name_contains), O(creation_time_after), O(creation_time_before), O(modified_time_after),
              O(modified_time_before), O(sort_by), O(sort_order) and O(tags).
        type: str
        aliases: ["name"]
    name_contains:
        description:
            - A string that must be contained in the AppImageConfig name.
            - AWS rejects O(sort_by=Name) together with this option.
        type: str
    creation_time_after:
        description:
            - Only include AppImageConfigs created on or after this time, in ISO 8601 format.
        type: str
    creation_time_before:
        description:
            - Only include AppImageConfigs created on or before this time, in ISO 8601 format.
        type: str
    modified_time_after:
        description:
            - Only include AppImageConfigs last modified on or after this time, in ISO 8601 format.
        type: str
    modified_time_before:
        description:
            - Only include AppImageConfigs last modified on or before this time, in ISO 8601 format.
        type: str
    sort_by:
        description:
            - The field to sort the results by. AWS sorts by V(CreationTime) when it is omitted.
        type: str
        choices: ['CreationTime', 'LastModifiedTime', 'Name']
    sort_order:
        description:
            - The sort order of the results. AWS sorts V(Descending) when it is omitted.
        type: str
        choices: ['Ascending', 'Descending']
    tags:
        description:
            - A dictionary of tags to filter by.
            - Only AppImageConfigs whose tags contain all the given key/value pairs are returned.
            - Values that are not strings are converted to strings before comparing; booleans become V(true) or V(false).
            - The filter is applied after the list call, so it does not reduce the number of API calls.
        type: dict
    include_tags:
        description:
            - Whether to read the tags of every returned AppImageConfig and return them as RV(app_image_configs[].tags).
            - Reading the tags costs one extra API call for each AppImageConfig returned, so it is off by default.
            - The tags are always read when O(tags) is set.
        type: bool
        default: false
attributes:
    check_mode:
        support: full
        description: The module only reads, so it behaves the same in check_mode.
    diff_mode:
        support: none
        description: Will not return details on what has changed.
seealso:
    - module: amazon.ai.sagemaker_app_image_config
notes:
    - The module needs the C(sagemaker:DescribeAppImageConfig), C(sagemaker:ListAppImageConfigs) and C(sagemaker:ListTags) IAM permissions.
    - Reading the tags (O(include_tags) or O(tags)) costs one extra API call for each AppImageConfig returned.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Get a specific AppImageConfig
  amazon.ai.sagemaker_app_image_config_info:
    name: example-app-image-config

- name: List all AppImageConfigs
  amazon.ai.sagemaker_app_image_config_info:

- name: List AppImageConfigs whose name contains a string, newest modification first
  amazon.ai.sagemaker_app_image_config_info:
    name_contains: example
    sort_by: LastModifiedTime
    sort_order: Descending

- name: Get a specific AppImageConfig together with its tags
  amazon.ai.sagemaker_app_image_config_info:
    name: example-app-image-config
    include_tags: true

- name: List AppImageConfigs created after a date and carrying a tag
  amazon.ai.sagemaker_app_image_config_info:
    creation_time_after: "2025-01-01T00:00:00Z"
    tags:
      project: demo
"""

RETURN = r"""
app_image_configs:
    description: A list of AppImageConfigs. The list is empty when none match.
    type: list
    elements: dict
    returned: always
    sample:
        - app_image_config_name: example-app-image-config
          app_image_config_arn: arn:aws:sagemaker:eu-north-1:123456789012:app-image-config/example-app-image-config
          creation_time: '2025-01-01T00:00:00+00:00'
          last_modified_time: '2025-01-01T00:00:00+00:00'
          jupyter_lab_app_image_config:
              container_config:
                  container_arguments: ["--debug"]
          tags:
              project: demo
    contains:
        app_image_config_name:
            description: The name of the AppImageConfig.
            type: str
            sample: example-app-image-config
        app_image_config_arn:
            description: The Amazon Resource Name (ARN) of the AppImageConfig.
            type: str
            sample: arn:aws:sagemaker:eu-north-1:123456789012:app-image-config/example-app-image-config
        creation_time:
            description: The date and time the AppImageConfig was created.
            type: str
            sample: '2025-01-01T00:00:00+00:00'
        last_modified_time:
            description: The date and time the AppImageConfig was last modified.
            type: str
            sample: '2025-01-01T00:00:00+00:00'
        kernel_gateway_image_config:
            description: The kernel gateway configuration, when the AppImageConfig has one.
            type: dict
            sample:
                kernel_specs:
                    - name: python3
        jupyter_lab_app_image_config:
            description: The JupyterLab configuration, when the AppImageConfig has one.
            type: dict
            sample:
                container_config:
                    container_arguments: ["--debug"]
        code_editor_app_image_config:
            description: The Code Editor configuration, when the AppImageConfig has one.
            type: dict
            sample:
                container_config:
                    container_arguments: ["--debug"]
        tags:
            description: The tags assigned to the AppImageConfig. Only returned when O(include_tags=true) or O(tags) is set.
            type: dict
            sample:
                project: demo
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import app_image_config_to_snake_dict
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_app_image_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_app_image_configs
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.utils import stringify_values

from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters

FILTER_OPTIONS = (
    "name_contains",
    "creation_time_after",
    "creation_time_before",
    "modified_time_after",
    "modified_time_before",
    "sort_by",
    "sort_order",
)


def _find_app_image_configs(client, module: AnsibleAWSModule) -> List[Dict[str, Any]]:
    name: Optional[str] = module.params.get("app_image_config_name")
    if name:
        config: Optional[Dict[str, Any]] = describe_app_image_config(client, name)
        return [config] if config else list()

    params: Dict[str, Any] = snake_dict_to_camel_dict(
        scrub_none_parameters({option: module.params.get(option) for option in FILTER_OPTIONS}),
        capitalize_first=True,
    )
    return list_app_image_configs(client, **params)


def _normalize(client, config: Dict[str, Any], with_tags: bool) -> Dict[str, Any]:
    normalized: Dict[str, Any] = app_image_config_to_snake_dict(config)
    if with_tags:
        normalized["tags"] = list_tags(client, config["AppImageConfigArn"])
    return normalized


def main() -> None:
    argument_spec = dict(
        app_image_config_name=dict(type="str", aliases=["name"]),
        name_contains=dict(type="str"),
        creation_time_after=dict(type="str"),
        creation_time_before=dict(type="str"),
        modified_time_after=dict(type="str"),
        modified_time_before=dict(type="str"),
        sort_by=dict(type="str", choices=["CreationTime", "LastModifiedTime", "Name"]),
        sort_order=dict(type="str", choices=["Ascending", "Descending"]),
        tags=dict(type="dict"),
        include_tags=dict(type="bool", default=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[("app_image_config_name", option) for option in (*FILTER_OPTIONS, "tags")],
    )

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        desired_tags: Optional[Dict[str, str]] = module.params.get("tags")
        with_tags: bool = module.params["include_tags"] or bool(desired_tags)
        configs: List[Dict[str, Any]] = [
            _normalize(client, c, with_tags) for c in _find_app_image_configs(client, module)
        ]

        if desired_tags:
            desired_tags = stringify_values(desired_tags)
            configs = [c for c in configs if desired_tags.items() <= c["tags"].items()]

        module.exit_json(app_image_configs=configs)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
