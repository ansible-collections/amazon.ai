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
    agent_version:
        description:
            - The version of the agent.
        type: str
        default: 'DRAFT'
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
    returned: always, on success
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
            sample: "Gets the current date and time."
        created_at:
            description: The timestamp when the action group was created.
            type: str
            sample: "2025-10-03T14:33:09.676524+00:00"
        updated_at:
            description: The timestamp when the action group was last updated.
            type: str
            sample: "2025-10-03T14:33:09.676524+00:00"
msg:
    description: Informative message about the action.
    returned: always
    type: str
    sample: "Action group 'get_weather_info_8e57bb73f58e' created successfully."
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
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import _prepare_agent
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import find_agent

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _find_action_group(client, agent_id: str, action_group_name: str, agent_version: str) -> Optional[Dict[str, Any]]:
    """
    Find an existing action group by name.

    Args:
        client: The boto3 Bedrock Agent client.
        agent_id: The unique ID of the agent.
        action_group_name: The name of the action group to look for.
        agent_version: The version of the agent (e.g., "DRAFT").

    Returns:
        The action group details as a dictionary if found, otherwise None.
    """
    action_groups = _list_agent_action_groups(client, agentId=agent_id, agentVersion=agent_version)
    for group in action_groups:
        group_info = _get_agent_action_group(client, agent_id, agent_version, group["actionGroupId"])
        if group["actionGroupName"] == action_group_name:
            return group_info
    return None


def _create_action_group(client, module: AnsibleAWSModule, agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Create a new action group.

    Args:
        client: The boto3 Bedrock Agent client.
        module: The AnsibleAWSModule instance with user parameters.
        agent_id: The unique ID of the agent.

    Returns:
        A tuple of:
            - The created action group dictionary (or empty dict in check mode).
            - A human-readable message about the operation.
    """
    if module.check_mode:
        return {}, f"Check mode: would have created action group {module.params['action_group_name']}."

    params: Dict[str, Any] = {
        "agentId": agent_id,
        "agentVersion": module.params["agent_version"],
        "actionGroupName": module.params["action_group_name"],
        "actionGroupExecutor": {"lambda": module.params["lambda_arn"]},
        "apiSchema": {"payload": module.params["api_schema"]},
        "actionGroupState": module.params["action_group_state"],
    }

    if module.params.get("description"):
        params["description"] = module.params["description"]

    response = client.create_agent_action_group(**params)
    result = response.get("agentActionGroup", {})
    return result, f"Action group '{module.params['action_group_name']}' created successfully."


def _update_action_group(
    client, module: AnsibleAWSModule, existing_action_group: Dict[str, Any], agent_id: str
) -> Tuple[bool, Dict[str, Any]]:
    """
    Update an existing action group if any differences are found.

    Args:
        client: The boto3 Bedrock Agent client.
        module: The AnsibleAWSModule instance with user parameters.
        existing_action_group: The current action group configuration from AWS.
        agent_id: The unique ID of the agent.

    Returns:
        A tuple of:
            - changed (bool): Whether any changes would be applied.
            - response (dict): The updated action group (or original if unchanged).
            - msg (str): Human-readable message about the operation.
    """
    response = existing_action_group
    api_schema: str = module.params["api_schema"]
    action_group_state: str = module.params["action_group_state"]
    description: Optional[str] = module.params.get("description")
    agent_version: Optional[str] = module.params.get("agent_version")

    current_api_schema_obj: Dict[str, Any] = yaml.safe_load(existing_action_group["apiSchema"]["payload"])
    api_schema_obj: Dict[str, Any] = yaml.safe_load(api_schema)

    new_action_group_name: Optional[str] = module.params.get("new_action_group_name")

    update_obj: Dict[str, Any] = {}
    changed: bool = False

    if current_api_schema_obj != api_schema_obj:
        update_obj["apiSchema"] = {"payload": api_schema}

    if action_group_state != existing_action_group.get("actionGroupState"):
        update_obj["actionGroupState"] = action_group_state

    if agent_version != existing_action_group.get("agentVersion"):
        update_obj["agentVersion"] = agent_version

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
                "actionGroupId": existing_action_group["actionGroupId"],
            }
        )
        if update_obj.get("apiSchema") is None:
            update_obj["apiSchema"] = existing_action_group["apiSchema"]

        if update_obj.get("actionGroupName") is None:
            update_obj["actionGroupName"] = existing_action_group["actionGroupName"]

        if update_obj.get("actionGroupExecutor") is None:
            update_obj["actionGroupExecutor"] = existing_action_group["actionGroupExecutor"]

        if update_obj.get("agentVersion") is None:
            update_obj["agentVersion"] = existing_action_group["agentVersion"]

        changed = True
        if module.check_mode:
            return True, {}, f"Check mode: would have updated action group {existing_action_group['actionGroupName']}."
        else:
            result = client.update_agent_action_group(**update_obj)
            response = result.get("agentActionGroup", {})
    else:
        return changed, existing_action_group, "No updates needed."

    return changed, response, f"Action group '{response.get('actionGroupName')}' updated successfully."


def _delete_action_group(client, module, agent_id: str, existing: dict) -> None:
    """
    Delete an existing action group.

    Args:
        client: The boto3 Bedrock Agent client.
        module: The AnsibleAWSModule instance.
        agent_id: The unique ID of the agent.
        existing: The existing action group dictionary to delete.

    Returns:
        A message describing the outcome of the operation.
    """
    if module.check_mode:
        return f"Check mode: would have deleted action group {existing['actionGroupName']}."

    client.delete_agent_action_group(
        agentId=agent_id, agentVersion=existing["agentVersion"], actionGroupId=existing["actionGroupId"]
    )
    return f"Action group {existing['actionGroupName']} deleted successfully."


def main():
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        agent_name=dict(type="str", required=True),
        action_group_name=dict(type="str", required=True),
        agent_version=dict(type="str", default="DRAFT"),
        new_action_group_name=dict(type="str"),
        action_group_state=dict(type="str", choices=["ENABLED", "DISABLED"], default="ENABLED"),
        description=dict(type="str"),
        lambda_arn=dict(type="str"),
        api_schema=dict(type="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[("state", "present", ["lambda_arn", "api_schema"])],
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
    agent_version: Optional[str] = module.params["agent_version"]

    changed: bool = False
    action_group_info: Optional[Dict[str, Any]] = None
    result: Dict[str, Any] = {"action_group": {}}

    try:
        found_action_group: Optional[Dict[str, Any]] = _find_action_group(
            client, agent_id, action_group_name, agent_version
        )

        if state == "present":
            if found_action_group:
                changed, action_group_info, msg = _update_action_group(client, module, found_action_group, agent_id)
                result["msg"] = msg
            else:
                action_group_info, msg = _create_action_group(client, module, agent_id)
                result["msg"] = msg
                changed = True

        elif state == "absent":
            if found_action_group:
                msg = _delete_action_group(client, module, agent_id, found_action_group)
                result["msg"] = msg
                changed = True
            else:
                result["msg"] = "Action group does not exist."

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    # Conditionally prepare the agent after a change
    if changed and not module.check_mode:
        _prepare_agent(client, agent_id)

    result["changed"] = changed
    if action_group_info:
        action_group = _get_agent_action_group(
            client, agent_id, action_group_info["agentVersion"], action_group_info["actionGroupId"]
        )
        result["action_group"] = camel_dict_to_snake_dict(action_group)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
