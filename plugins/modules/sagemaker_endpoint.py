#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_endpoint
short_description: Manage Amazon SageMaker endpoints
version_added: "2.0.0"
author:
    - Jan Likar (@JanLikar)
description:
    - Create, update, and delete Amazon SageMaker inference endpoints.
    - An endpoint serves real-time inference for an existing endpoint configuration.
    - The referenced endpoint configuration is managed separately with M(amazon.ai.sagemaker_endpoint_config).
options:
    state:
        description: The desired state of the endpoint.
        type: str
        choices: [present, absent]
        default: present
    endpoint_name:
        description: The name of the endpoint.
        type: str
        required: true
        aliases: [name]
    endpoint_config_name:
        description:
            - The name of the endpoint configuration the endpoint serves.
            - Required when O(state=present).
            - Changing it on an existing endpoint updates the endpoint in place.
        type: str
    tags:
        description: Tags to associate with the endpoint.
        type: dict
        aliases: [resource_tags]
    purge_tags:
        description: Whether to remove tags not specified in O(tags).
        type: bool
        default: true
    wait:
        description: Whether to wait for the endpoint to reach a terminal state.
        type: bool
        default: true
    wait_timeout:
        description: How long, in seconds, to wait for the endpoint to reach a terminal state.
        type: int
        default: 600
notes:
    - Required IAM actions include sagemaker:CreateEndpoint, sagemaker:DescribeEndpoint,
      sagemaker:UpdateEndpoint, sagemaker:DeleteEndpoint, sagemaker:ListEndpoints,
      sagemaker:AddTags, sagemaker:ListTags, and sagemaker:DeleteTags.
attributes:
    check_mode:
        description: Can run in check mode and report what would change without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_endpoint_info
      description: Gather information about SageMaker endpoints.
    - module: amazon.ai.sagemaker_endpoint_config
      description: Manage SageMaker endpoint configurations.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Create an endpoint
  amazon.ai.sagemaker_endpoint:
    endpoint_name: my-endpoint
    endpoint_config_name: my-endpoint-config

- name: Update an endpoint to a new configuration
  amazon.ai.sagemaker_endpoint:
    endpoint_name: my-endpoint
    endpoint_config_name: my-new-endpoint-config

- name: Delete an endpoint
  amazon.ai.sagemaker_endpoint:
    state: absent
    endpoint_name: my-endpoint
"""

RETURN = r"""
endpoint:
    description: The endpoint after the operation.
    type: dict
    returned: on success when O(state=present)
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
    sample:
        endpoint_name: my-endpoint
        endpoint_arn: arn:aws:sagemaker:us-east-1:123456789012:endpoint/my-endpoint
        endpoint_config_name: my-endpoint-config
        endpoint_status: InService
tags:
    description: A dictionary containing the endpoint tags.
    type: dict
    returned: on success when O(state=present)
    sample: {}
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: Endpoint my-endpoint created successfully.
"""

try:
    import botocore
except ImportError:
    pass

from typing import Any
from typing import Dict
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_endpoint_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_endpoint

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _endpoint_result(client, name) -> Dict[str, Any]:
    return camel_dict_to_snake_dict(describe_endpoint(client, name), ignore_list=["tags"])


def _tags_message(name, changed, check_mode) -> str:
    if not changed:
        return f"Endpoint {name} is already up to date."
    if check_mode:
        return f"Check mode: would have updated endpoint {name} tags."
    return f"Endpoint {name} tags updated successfully."


def _absent(module, client, name: str, existing: Optional[Dict[str, Any]]) -> None:
    if not existing:
        module.exit_json(changed=False, msg=f"Endpoint {name} does not exist.")
    if existing["EndpointStatus"] == "Deleting":
        if not module.check_mode and module.params["wait"]:
            wait_for_endpoint(client, module, deleted=True)
        module.exit_json(changed=False, msg=f"Endpoint {name} is already being deleted.")
    if module.check_mode:
        module.exit_json(changed=True, msg=f"Check mode: would have deleted endpoint {name}.")
    delete_endpoint(client, module)
    if module.params["wait"]:
        wait_for_endpoint(client, module, deleted=True)
    module.exit_json(changed=True, msg=f"Endpoint {name} deleted successfully.")


def _present(module, client, name: str, existing: Optional[Dict[str, Any]]) -> None:
    if existing:
        status = existing["EndpointStatus"]
        if status in ("Creating", "Updating", "SystemUpdating", "Deleting", "RollingBack"):
            module.fail_json(msg=f"Cannot update endpoint {name} while it is in state {status}.")

        if existing["EndpointConfigName"] != module.params["endpoint_config_name"]:
            if module.check_mode:
                module.exit_json(changed=True, msg=f"Check mode: would have updated endpoint {name}.")
            update_endpoint(client, module)
            if module.params["wait"]:
                wait_for_endpoint(client, module)
            reconcile_endpoint_tags(client, module, existing)
            endpoint = _endpoint_result(client, name)
            exit_kwargs = dict(
                changed=True,
                endpoint=endpoint,
                tags=list_tags(client, endpoint["endpoint_arn"]),
                msg=f"Endpoint {name} updated successfully.",
            )
            module.exit_json(**exit_kwargs)

        changed = reconcile_endpoint_tags(client, module, existing)
        endpoint = _endpoint_result(client, name)
        exit_kwargs = dict(
            changed=changed,
            endpoint=endpoint,
            tags=list_tags(client, endpoint["endpoint_arn"]),
            msg=_tags_message(name, changed, module.check_mode),
        )
        module.exit_json(**exit_kwargs)

    if module.check_mode:
        module.exit_json(changed=True, msg=f"Check mode: would have created endpoint {name}.")
    create_endpoint(client, module)
    if module.params["wait"]:
        wait_for_endpoint(client, module)
    endpoint = _endpoint_result(client, name)
    exit_kwargs = dict(
        changed=True,
        endpoint=endpoint,
        tags=list_tags(client, endpoint["endpoint_arn"]),
        msg=f"Endpoint {name} created successfully.",
    )
    module.exit_json(**exit_kwargs)


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        endpoint_name=dict(type="str", required=True, aliases=["name"]),
        endpoint_config_name=dict(type="str"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[("state", "present", ["endpoint_config_name"])],
    )
    name = module.params["endpoint_name"]
    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing = describe_endpoint(client, name)
        if module.params["state"] == "absent":
            _absent(module, client, name, existing)
        _present(module, client, name, existing)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
