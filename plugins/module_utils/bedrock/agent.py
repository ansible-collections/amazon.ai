# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import time

from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


def wait_for_agent_status(client, module, agent_id: str, status: str, sleep_time: Optional[int] = 5) -> None:
    """
    Wait for an Amazon Bedrock Agent to reach a specific status.

    This function polls the Bedrock Agent at fixed intervals until it either
    reaches the desired `status` or the configured timeout expires.

    Behavior:
        - Uses `client.get_agent()` to retrieve the agent's current status.
        - Waits `sleep_time` seconds between each polling attempt.
        - Stops early if the agent reaches the desired status or is deleted
          while waiting for the "DELETED" state.
        - Fails the Ansible module gracefully if the timeout expires.

    Args:
        client: A boto3 Bedrock Agent client instance.
        module: The current Ansible module object, used for error reporting
                and accessing parameters (specifically `wait_timeout`).
        agent_id (str): The unique identifier of the Bedrock Agent to monitor.
        status (str): The target agent status to wait for
                      (e.g., "PREPARED", "DELETED").
        sleep_time (int, optional): Number of seconds to sleep between polling
                                    attempts. Defaults to 5 seconds.

    Raises:
        ClientError: If AWS returns an unexpected error during polling.
        TimeoutError: If the agent does not reach the target status before
                      the timeout expires.
    """
    wait_timeout = module.params.get("wait_timeout", 600)
    max_attempts = max(1, wait_timeout // sleep_time)

    for attempt in range(max_attempts):
        try:
            current_status = client.get_agent(agentId=agent_id)["agent"]["agentStatus"]

            if current_status == status:
                return

            time.sleep(sleep_time)

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                if status == "DELETED":
                    return
                raise
            raise

    # If we exit the loop without returning, timeout expired
    module.fail_json(
        msg=f"Timeout waiting for agent {agent_id} to reach status '{status}'. "
        f"Last known status: '{current_status}'."
    )


@AWSRetry.jittered_backoff(retries=10)
def prepare_agent(client, module, agent_id: str) -> bool:
    """
    Prepare a Bedrock Agent and wait until it reaches the 'PREPARED' state.

    Args:
        client: The boto3 Bedrock Agent client.
        agent_id: The unique identifier of the Bedrock Agent.

    Returns:
        True once the agent successfully reaches the 'PREPARED' state.

    Behavior:
        - Calls the `prepare_agent()` API operation.
        - Waits using `wait_for_agent_status()` until the agent reports status 'PREPARED'.
        - Retries automatically using the AWS jittered backoff decorator.
    """
    client.prepare_agent(agentId=agent_id)
    wait_for_agent_status(client, module, agent_id, "PREPARED")

    return True


@AWSRetry.jittered_backoff(retries=10)
def _list_agents(client, **params: Any) -> List[Dict[str, Any]]:
    """
    Retrieve a list of Bedrock Agents using pagination.

    Args:
        client: The boto3 Bedrock Agent client.
        **params: Additional filter parameters accepted by the `list_agents` API.

    Returns:
        A list of agent summary dictionaries.
    """
    paginator = client.get_paginator("list_agents")
    return paginator.paginate(**params).build_full_result()["agentSummaries"]


@AWSRetry.jittered_backoff(retries=10)
def get_agent(client, agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve details for a specific Bedrock Agent.

    Args:
        client: The boto3 Bedrock Agent client.
        agent_id: The unique identifier of the Bedrock Agent.

    Returns:
        A dictionary with detailed agent information if found, otherwise None.

    Raises:
        ClientError: If AWS returns an error other than 'ResourceNotFoundException'.
    """
    try:
        return client.get_agent(agentId=agent_id)["agent"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return None


def find_agent(client, module) -> List[Dict[str, Any]]:
    """
    Find Bedrock Agents, optionally filtering by name.

    Args:
        client: The boto3 Bedrock Agent client.
        module: The Ansible module instance containing user parameters.

    Returns:
        List of agent detail dictionaries. Empty list if none are found.

    Behavior:
        - Uses `_list_agents()` to enumerate all agents.
        - If `agent_name` is provided in module params, returns a list
          containing only the matching agent (if found), or an empty list.
        - If no name is given, returns detailed info for all agents.
    """
    agent_name: Optional[str] = module.params.get("agent_name")

    agents_list: List[Dict[str, Any]] = _list_agents(client)
    if not agents_list:
        return []

    if agent_name:
        for agent_summary in agents_list:
            if agent_summary["agentName"] == agent_name:
                return [get_agent(client, agent_summary["agentId"])]
        return []  # Empty list if no match found
    else:
        # Return a list of all agents with their detailed information
        return [get_agent(client, agent["agentId"]) for agent in agents_list]


def create_agent(module: AnsibleAWSModule, client) -> Tuple[bool, Optional[str], str]:
    """
    Creates a new agent if not in check_mode, otherwise simulates creation.

    Args:
        module: The AnsibleAWSModule instance.
        client: boto3 bedrock-agent client.

    Returns:
        (changed, agent_id, message)
    """
    changed: bool = True

    if module.check_mode:
        return changed, None, f"Check mode: would have created agent {module.params['agent_name']}."

    params: Dict[str, Any] = {
        "agent_name": module.params["agent_name"],
        "foundation_model": module.params["foundation_model"],
        "instruction": module.params["instruction"],
        "agent_resource_role_arn": module.params["agent_resource_role_arn"],
        "orchestration_type": module.params["orchestration_type"],
        "tags": module.params.get("tags"),
        "agent_collaboration": module.params.get("agent_collaboration"),
        "prompt_override_configuration": module.params.get("prompt_override_configuration"),
    }

    # Convert snake_case to camelCase for AWS API
    camel_params = snake_dict_to_camel_dict(scrub_none_parameters(params))
    new_agent = client.create_agent(**camel_params)
    agent_id: str = new_agent["agent"]["agentId"]

    wait_for_agent_status(client, module, agent_id, "NOT_PREPARED")
    prepare_agent(client, module, agent_id)

    return changed, agent_id, f"Agent {module.params['agent_name']} created successfully."


def update_agent(module: AnsibleAWSModule, client, existing_agent: Dict[str, Any]) -> Tuple[bool, Optional[str], str]:
    """
    Updates an existing agent if differences are detected.

    Args:
        module: The AnsibleAWSModule instance.
        client: boto3 bedrock-agent client.
        existing_agent: dict of existing agent details.

    Returns:
        (changed, agent_id, message)
    """
    existing_agent_id: str = existing_agent["agentId"]
    needs_update: Dict[str, Any] = {}
    changed: bool = False

    # Handle new_agent_name separately
    if module.params.get("new_agent_name") and existing_agent["agentName"] != module.params["new_agent_name"]:
        needs_update["agentName"] = module.params["new_agent_name"]

    # Generic fields to check and update
    generic_fields = [
        "foundation_model",
        "instruction",
        "agent_resource_role_arn",
        "orchestration_type",
        "agent_collaboration",
    ]

    for field in generic_fields:
        value = module.params.get(field)
        if value is not None:
            # Convert snake_case to camelCase to match existing_agent keys
            camel_key = snake_dict_to_camel_dict({field: None}).popitem()[0]
            if existing_agent.get(camel_key) != value:
                needs_update[field] = value

    if module.params.get("prompt_override_configuration"):
        dromedary_case_prompt_config = snake_dict_to_camel_dict(module.params["prompt_override_configuration"])
        if existing_agent["promptOverrideConfiguration"] != dromedary_case_prompt_config:
            needs_update["promptOverrideConfiguration"] = dromedary_case_prompt_config

    if needs_update:
        for required in ["agentName", "foundationModel", "agentResourceRoleArn"]:
            if required not in needs_update:
                # Pull from existing agent
                needs_update[required] = existing_agent[required]

        changed = True
        if module.check_mode:
            return True, existing_agent_id, f'Check mode: would have updated agent {existing_agent["agentName"]}.'

        needs_update["agentId"] = existing_agent_id
        client.update_agent(**needs_update)
        prepare_agent(client, module, existing_agent_id)
    else:
        return changed, existing_agent_id, "No updates needed."

    return changed, existing_agent_id, f"Agent {existing_agent['agentName']} updated successfully."


def delete_agent(module: AnsibleAWSModule, client, existing_agent: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Deletes an existing agent.

    Args:
        module: The AnsibleAWSModule instance.
        client: boto3 bedrock-agent client.
        existing_agent: dict of existing agent details.

    Returns:
        (changed, message)
    """
    if module.check_mode:
        return True, f"Check mode: would have deleted agent '{existing_agent['agentName']}'."

    if existing_agent["agentStatus"] == "DELETING":
        return False, f"Agent {existing_agent['agentName']} in DELETING state."

    client.delete_agent(agentId=existing_agent["agentId"])
    return True, f"Agent {existing_agent['agentName']} deleted successfully."
