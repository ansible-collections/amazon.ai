#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_notebook_instance_lifecycle_config_info
short_description: Gather information about Amazon SageMaker notebook instance lifecycle configurations
version_added: "2.0.0"
author:
    - Domen Dobnikar (@domendobnikar)
description:
    - Retrieve a notebook instance lifecycle configuration by name or list matching configurations.
    - This module does not mutate AWS state.
options:
    notebook_instance_lifecycle_config_name:
        description:
            - The name of the lifecycle configuration to retrieve.
            - If omitted, the module lists matching lifecycle configurations.
        type: str
        aliases: [name]
    name_contains:
        description:
            - A substring that must appear in the lifecycle configuration name.
        type: str
    sort_by:
        description:
            - The field used to sort the returned lifecycle configurations.
        type: str
        choices: [Name, CreationTime, LastModifiedTime]
    sort_order:
        description:
            - The sort order for the returned lifecycle configurations.
        type: str
        choices: [Ascending, Descending]
    creation_time_after:
        description:
            - Only include lifecycle configurations created after this time.
            - Must be an ISO 8601 timestamp, for example C(2026-01-01T00:00:00Z).
        type: str
    creation_time_before:
        description:
            - Only include lifecycle configurations created before this time.
            - Must be an ISO 8601 timestamp, for example C(2026-01-01T00:00:00Z).
        type: str
    last_modified_time_after:
        description:
            - Only include lifecycle configurations last modified after this time.
            - Must be an ISO 8601 timestamp, for example C(2026-01-01T00:00:00Z).
        type: str
    last_modified_time_before:
        description:
            - Only include lifecycle configurations last modified before this time.
            - Must be an ISO 8601 timestamp, for example C(2026-01-01T00:00:00Z).
        type: str
    tags:
        description:
            - A tag map used to filter lifecycle configurations by exact key/value matches.
            - When listing, tags are fetched for each candidate, which adds one API call per candidate.
            - When retrieving by name, the matched resource always includes its tags, whether or not this option is set.
        type: dict
    max_items:
        description:
            - The maximum number of lifecycle configurations to return. Must be at least V(1).
            - When O(tags) is set, the limit applies to the configurations that match the tags. The module
              stops fetching tags once the limit is reached.
            - Mutually exclusive with O(notebook_instance_lifecycle_config_name).
        type: int
notes:
    - 'Requires the following IAM permissions:'
    - sagemaker:DescribeNotebookInstanceLifecycleConfig
    - sagemaker:ListNotebookInstanceLifecycleConfigs
    - sagemaker:ListTags
seealso:
    - module: amazon.ai.sagemaker_notebook_instance_lifecycle_config
      description: Manage Amazon SageMaker notebook instance lifecycle configurations.
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
- name: Retrieve a lifecycle configuration by name
  amazon.ai.sagemaker_notebook_instance_lifecycle_config_info:
    notebook_instance_lifecycle_config_name: example-lifecycle-config

- name: List lifecycle configurations for a project
  amazon.ai.sagemaker_notebook_instance_lifecycle_config_info:
    name_contains: example
    sort_by: CreationTime
    sort_order: Descending

- name: Retrieve the five most recently modified lifecycle configurations
  amazon.ai.sagemaker_notebook_instance_lifecycle_config_info:
    sort_by: LastModifiedTime
    sort_order: Descending
    max_items: 5

- name: Filter lifecycle configurations by tags
  amazon.ai.sagemaker_notebook_instance_lifecycle_config_info:
    tags:
      project: demo
"""

RETURN = r"""
notebook_instance_lifecycle_configs:
    description:
        - Matching lifecycle configurations.
        - When retrieving by name, the list holds at most one item and also includes I(on_create), I(on_start) and I(tags).
    type: list
    elements: dict
    returned: always, on success
    contains:
        notebook_instance_lifecycle_config_name:
            description: The lifecycle configuration name.
            type: str
            sample: "example-lifecycle-config"
        notebook_instance_lifecycle_config_arn:
            description: The ARN of the lifecycle configuration.
            type: str
            sample: "arn:aws:sagemaker:us-east-1:123456789012:notebook-instance-lifecycle-config/example-lifecycle-config"
        creation_time:
            description: The time the lifecycle configuration was created.
            type: str
            sample: "2026-01-01T00:00:00+00:00"
        last_modified_time:
            description: The time the lifecycle configuration was last modified.
            type: str
            sample: "2026-01-01T00:00:00+00:00"
        on_create:
            description: The decoded shell script run when a notebook instance is created, or null when unset.
            type: str
            returned: when retrieving by name
            sample: "#!/bin/bash\necho 'Preparing notebook'"
        on_start:
            description: The decoded shell script run when a notebook instance starts, or null when unset.
            type: str
            returned: when retrieving by name
            sample: "#!/bin/bash\necho 'Starting notebook'"
        tags:
            description: The tags assigned to the lifecycle configuration.
            type: dict
            returned: when retrieving by name, or when I(tags) is set
            sample:
                project: demo
"""

try:
    import botocore
except ImportError:
    pass

from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import decode_lifecycle_script
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_notebook_instance_lifecycle_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_notebook_instance_lifecycle_configs
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


def _normalize_lifecycle_config(
    summary: Dict[str, Any], *, include_scripts: bool = False, tags: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    normalized = camel_dict_to_snake_dict(summary, ignore_list=["tags", "Tags"])
    if include_scripts:
        normalized["on_create"] = decode_lifecycle_script(summary.get("OnCreate"))
        normalized["on_start"] = decode_lifecycle_script(summary.get("OnStart"))
    if tags is not None:
        normalized["tags"] = tags
    return normalized


TIME_FILTERS = (
    "creation_time_after",
    "creation_time_before",
    "last_modified_time_after",
    "last_modified_time_before",
)


def _parse_iso_datetime(module: AnsibleAWSModule, option: str, value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        module.fail_json(
            msg=f"Invalid value for {option}: '{value}'. Expected an ISO 8601 timestamp, "
            "for example '2026-01-01T00:00:00Z'."
        )


def _parse_time_filters(module: AnsibleAWSModule) -> Dict[str, datetime]:
    return {
        option: _parse_iso_datetime(module, option, module.params[option])
        for option in TIME_FILTERS
        if module.params.get(option) is not None
    }


def find_notebook_instance_lifecycle_configs(client, module: AnsibleAWSModule) -> List[Dict[str, Any]]:
    name = module.params.get("notebook_instance_lifecycle_config_name")
    if name:
        config = describe_notebook_instance_lifecycle_config(client, name)
        if config is None:
            return []
        tags = list_tags(client, config["NotebookInstanceLifecycleConfigArn"])
        named_tags: Optional[Dict[str, str]] = module.params.get("tags")
        if named_tags is not None and not named_tags.items() <= tags.items():
            return []
        return [
            _normalize_lifecycle_config(
                config,
                include_scripts=True,
                tags=tags,
            )
        ]

    raw: Dict[str, Any] = {field: module.params.get(field) for field in ("name_contains", "sort_by", "sort_order")}
    raw.update(_parse_time_filters(module))
    params = snake_dict_to_camel_dict(scrub_none_parameters(raw), capitalize_first=True)

    desired_tags: Optional[Dict[str, str]] = module.params.get("tags")
    max_items: Optional[int] = module.params.get("max_items")
    # Tag filtering is client-side, so the cap must apply to matches rather than to the API listing.
    api_max_items = max_items if desired_tags is None else None

    summaries = list_notebook_instance_lifecycle_configs(client, max_items=api_max_items, **params)
    matches: List[Dict[str, Any]] = []

    for summary in summaries:
        if max_items is not None and len(matches) >= max_items:
            break
        tags = None
        if desired_tags is not None:
            tags = list_tags(client, summary["NotebookInstanceLifecycleConfigArn"])
            if not desired_tags.items() <= tags.items():
                continue
        matches.append(_normalize_lifecycle_config(summary, tags=tags))

    return matches


def main() -> None:
    argument_spec = dict(
        notebook_instance_lifecycle_config_name=dict(type="str", aliases=["name"]),
        name_contains=dict(type="str"),
        sort_by=dict(type="str", choices=["Name", "CreationTime", "LastModifiedTime"]),
        sort_order=dict(type="str", choices=["Ascending", "Descending"]),
        creation_time_after=dict(type="str"),
        creation_time_before=dict(type="str"),
        last_modified_time_after=dict(type="str"),
        last_modified_time_before=dict(type="str"),
        tags=dict(type="dict"),
        max_items=dict(type="int"),
    )
    list_filters = ("name_contains", "sort_by", "sort_order", "max_items") + TIME_FILTERS
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[("notebook_instance_lifecycle_config_name", filter_name) for filter_name in list_filters],
    )

    if module.params.get("max_items") is not None and module.params["max_items"] < 1:
        module.fail_json(msg="max_items must be a positive integer.")

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        configs = find_notebook_instance_lifecycle_configs(client, module)
        module.exit_json(changed=False, notebook_instance_lifecycle_configs=configs)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
