#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: bedrock_agent_action_group
short_description: Manage Amazon Bedrock Agent Action Groups
version_added: "1.0.0"
author:
    - Alina Buzachis (@alinabuzachis)
description:
    - This module creates, updates, and deletes an action group for a Bedrock Agent.
options:
    state:
        description:
            - The state of the action group.
            - To delete an action group, ensure that the O(action_group_state=DISABLED).
        type: str
        choices: ['present', 'absent']
        default: 'present'
    agent_name:
        description:
            - The name of the Bedrock Agent.
        type: str
        required: true
    action_group_name:
        description:
            - The name of the action group.
        type: str
        required: true
    new_action_group_name:
        description:
            - Specifies a new name for the action group.
        type: str
    action_group_state:
        description:
            - Specifies whether the action group is available for the agent to invoke
              or not when sending an InvokeAgent request.
        type: str
        choices: ['ENABLED','DISABLED']
        default: "ENABLED"
    description:
        description:
            - A description of the action group.
        type: str
    lambda_arn:
        description:
            - The ARN of the Lambda function for the action group.
            - Required when O(state=present).
        type: str
    api_schema:
        description:
            - The OpenAPI schema.
            - Required when O(state=present).
        type: str
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""


RETURN = r"""
action_group:
    description: A dictionary containing the detailed configuration of an action group.
    type: dict
    returned: when a single action group is requested
    contains:
        action_group_id:
            description: The unique identifier of the action group.
            type: str
            sample: "9IXXEEO8FR"
        action_group_name:
            description: The name of the action group.
            type: str
            sample: "get-weather-info-test"
        action_group_state:
            description: The state of the action group.
            type: str
            sample: "ENABLED"
        agent_id:
            description: The unique identifier of the agent this action group belongs to.
            type: str
            sample: "RNKFFDOKFN"
        agent_version:
            description: The version of the agent this action group is associated with.
            type: str
            sample: "DRAFT"
        action_group_executor:
            description: Details about the action group's executor.
            type: dict
            contains:
                lambda:
                    description: The ARN of the Lambda function that executes the action group.
                    type: str
                    sample: "arn:aws:lambda:us-east-1:123456789012:function:test-bedrock-lambda-test:12"
        api_schema:
            description: The OpenAPI 3.0 schema that defines the action group's API.
            type: dict
            contains:
                payload:
                    description: The raw YAML/JSON content of the API schema.
                    type: str
        description:
            description: A description of the action group.
            type: str
            sample: Gets the current date and time.
        created_at:
            description: The timestamp when the action group was created.
            type: str
        updated_at:
            description: The timestamp when the action group was last updated.
            type: str
"""


EXAMPLES = r"""
- name: Create an action group for the agent
  amazon.ai.bedrock_agent_action_group:
    state: present
    agent_name: "{{ agent_name }}"
    action_group_name: "get_current_date_time"
    description: "Gets the current date and time."
    lambda_arn: "arn:aws:lambda:us-east-1:123456789012:function:MyBedrockFunction"
    api_schema: "{{ lookup('file', 'files/api_schema.yaml') }}"

- name: Delete Agent action group
  amazon.ai.bedrock_agent_action_group:
    agent_name: "{{ agent_name }}"
    action_group_name: "{{ action_group_name }}"
    state: absent
"""


try:
    import yaml
except ImportError:
    # Handled in module setup
    pass

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from ansible_collections.amazon.ai.plugins.module_utils.bedrock import _get_agent_action_group
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import _list_agent_action_groups
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import find_agent

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _find_action_group(client, agent_id: str, action_group_name: str) -> Optional[Dict[str, Any]]:
    """Finds an existing action group by name and returns its details."""
    action_groups = _list_agent_action_groups(client, agentId=agent_id, agentVersion="DRAFT")
    for group in action_groups:
        group_info = _get_agent_action_group(client, agent_id, "DRAFT", group["actionGroupId"])
        if group["actionGroupName"] == action_group_name:
            return group_info
    return None


def _create_action_group(client, module: AnsibleAWSModule, agent_id: str) -> Optional[Dict[str, Any]]:
    """Creates a new action group."""
    params: Dict[str, Any] = {
        "agentId": agent_id,
        "agentVersion": "DRAFT",
        "actionGroupName": module.params["action_group_name"],
        "actionGroupExecutor": {"lambda": module.params["lambda_arn"]},
        "apiSchema": {"payload": module.params["api_schema"]},
    }

    if module.params.get("description"):
        params["description"] = module.params["description"]

    response = client.create_agent_action_group(**params)
    return response.get("agentActionGroup")


def _update_action_group(
    client, module: AnsibleAWSModule, existing_action_group: Dict[str, Any], agent_id: str
) -> Tuple[bool, Dict[str, Any]]:
    """Updates an existing action group."""
    response = existing_action_group
    api_schema: str = module.params["api_schema"]
    action_group_state: str = module.params["action_group_state"]
    description: Optional[str] = module.params.get("description")

    current_api_schema_obj: Dict[str, Any] = yaml.safe_load(existing_action_group["apiSchema"]["payload"])
    api_schema_obj: Dict[str, Any] = yaml.safe_load(api_schema)

    new_action_group_name: Optional[str] = module.params.get("new_action_group_name")

    update_obj: Dict[str, Any] = {}
    changed: bool = False

    if current_api_schema_obj != api_schema_obj:
        update_obj["apiSchema"] = {"payload": api_schema}

    if action_group_state != existing_action_group.get("actionGroupState"):
        update_obj["actionGroupState"] = action_group_state

    if description and existing_action_group.get("description") != description:
        update_obj["description"] = description

    if new_action_group_name and existing_action_group["actionGroupName"] != new_action_group_name:
        update_obj["actionGroupName"] = new_action_group_name

    if (
        existing_action_group.get("actionGroupExecutor", {}).get("lambda")
        and existing_action_group.get("actionGroupExecutor", {}).get("lambda") != module.params["lambda_arn"]
    ):
        update_obj["actionGroupExecutor"] = {"lambda": module.params["lambda_arn"]}

    if update_obj:
        update_obj.update(
            {
                "agentId": agent_id,
                "agentVersion": "DRAFT",
                "actionGroupId": existing_action_group["actionGroupId"],
            }
        )
        if update_obj.get("apiSchema") is None:
            update_obj["apiSchema"] = existing_action_group["apiSchema"]

        changed = True
        if not module.check_mode:
            result = client.update_agent_action_group(**update_obj)
            response = result.get("agentActionGroup")
    return changed, response


def _delete_action_group(client, agent_id: str, action_group_id: str) -> None:
    """Deletes an existing action group."""
    client.delete_agent_action_group(agentId=agent_id, agentVersion="DRAFT", actionGroupId=action_group_id)


def main():
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        agent_name=dict(type="str", required=True),
        action_group_name=dict(type="str", required=True),
        new_action_group_name=dict(type="str"),
        action_group_state=dict(type="str", choices=["ENABLED", "DISABLED"], default="ENABLED"),
        description=dict(type="str"),
        lambda_arn=dict(type="str"),
        api_schema=dict(type="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[("state", "present", ("lambda_arn", "api_schema"))],
    )

    agent_name: str = module.params["agent_name"]

    try:
        client = module.client("bedrock-agent", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    # Get the agent ID from the provided name
    agent: Optional[Dict[str, Any]] = find_agent(client, module)
    if not agent:
        module.fail_json(msg=f"Agent with name '{agent_name}' not found.")
    agent_id: str = agent.get("agentId")

    state: str = module.params["state"]
    action_group_name: str = module.params["action_group_name"]

    changed: bool = False
    action_group_info: Optional[Dict[str, Any]] = None
    result: Dict[str, Any] = {"action_group": {}}

    try:
        found_action_group: Optional[Dict[str, Any]] = _find_action_group(client, agent_id, action_group_name)

        if state == "present":
            if found_action_group:
                changed, action_group_info = _update_action_group(client, module, found_action_group, agent_id)
            else:
                if not module.check_mode:
                    action_group_info = _create_action_group(client, module, agent_id)
                changed = True

        elif state == "absent":
            if found_action_group:
                if not module.check_mode:
                    _delete_action_group(client, agent_id, found_action_group["actionGroupId"])
                changed = True

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    result["changed"] = changed
    if action_group_info:
        action_group = _get_agent_action_group(
            client, agent_id, action_group_info["agentVersion"], action_group_info["actionGroupId"]
        )
        result["action_group"] = camel_dict_to_snake_dict(action_group)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
