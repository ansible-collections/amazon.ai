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

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters

# Bedrock Foundation Model Utilities


def get_model_details(client, model_id: str) -> Dict[str, Any]:
    """
    Retrieves detailed information about a specific foundation model using the
    Bedrock `get_foundation_model` API.

    Args:
        client (boto3.client): A Boto3 Bedrock client.
        model_id (str): The identifier of the foundation model to retrieve.

    Returns:
        Dict[str, Any]: A dictionary containing the model details, with keys converted
                        to snake_case. Returns an empty dictionary if no details are found.
    """
    response = client.get_foundation_model(modelIdentifier=model_id)
    return camel_dict_to_snake_dict(response.get("modelDetails", {}))


def list_models_with_filters(module: AnsibleAWSModule, client) -> List[Dict[str, Any]]:
    """
    Retrieves a list of foundation models using the Bedrock `list_foundation_models` API,
    optionally filtering by provider, customization type, output modality, or inference type.

    Args:
        module (AnsibleAWSModule): The Ansible AWS module instance containing user parameters.
        client (boto3.client): A Boto3 Bedrock client.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing model summaries,
                              with keys converted to snake_case. Returns an empty list if no models are found.
    """
    params: Dict[str, Any] = {}

    if module.params.get("by_provider"):
        params["byProvider"] = module.params["by_provider"]

    if module.params.get("by_customization_type"):
        params["byCustomizationType"] = module.params["by_customization_type"]

    if module.params.get("by_output_modality"):
        params["byOutputModality"] = module.params["by_output_modality"]

    if module.params.get("by_inference_type"):
        params["byInferenceType"] = module.params["by_inference_type"]

    response = client.list_foundation_models(**params)
    return [camel_dict_to_snake_dict(model) for model in response.get("modelSummaries", [])]


# Bedrock Agent Utilities


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
def list_agents(client, **params: Any) -> List[Dict[str, Any]]:
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
        - Uses `list_agents()` to enumerate all agents.
        - If `agent_name` is provided in module params, returns a list
          containing only the matching agent (if found), or an empty list.
        - If no name is given, returns detailed info for all agents.
    """
    agent_name: Optional[str] = module.params.get("agent_name")

    agents_list: List[Dict[str, Any]] = list_agents(client)
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


# Bedrock Agent Alias


def wait_for_alias_status(
    client, module, agent_id: str, alias_id: str, status: str, sleep_time: Optional[int] = 5
) -> None:
    """
    Wait for an Amazon Bedrock Agent alias to reach a specific status.

    This function polls a Bedrock Agent alias at fixed intervals until it
    reaches the desired `status` or the timeout expires.

    Behavior:
        - Uses `client.get_agent_alias()` to check the alias's current status.
        - Waits `sleep_time` seconds between polling attempts.
        - Stops early if the alias reaches the target status or if it's deleted
          while waiting for the "DELETED" state.
        - Raises a TimeoutError if the desired status is not reached before
          the timeout expires.

    Args:
        client: A boto3 Bedrock Agent client instance.
        agent_id (str): The ID of the parent Bedrock Agent.
        alias_id (str): The unique identifier of the alias to monitor.
        status (str): The target alias status to wait for
                      (e.g., "PREPARED", "DELETED").
        sleep_time (int, optional): Number of seconds to sleep between polling
                                    attempts. Defaults to 5 seconds.

    Raises:
        ClientError: If AWS returns an unexpected error during polling.
        TimeoutError: If the alias does not reach the target status within
                      the timeout duration.
    """
    wait_timeout = module.params.get("wait_timeout", 600)
    max_attempts = max(1, wait_timeout // sleep_time)

    for attempt in range(max_attempts):
        try:
            alias_info = client.get_agent_alias(agentId=agent_id, agentAliasId=alias_id)
            current_status = alias_info["agentAlias"]["agentAliasStatus"]

            if current_status == status:
                return

            time.sleep(sleep_time)

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                if status == "DELETED":
                    return
                raise
            raise

    raise TimeoutError(
        f"Timeout waiting for alias {alias_id} (agent {agent_id}) to reach "
        f"status '{status}'. Last known status: '{current_status}'."
    )


@AWSRetry.jittered_backoff(retries=10)
def get_agent_alias(client, agent_id: str, alias_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve details for a specific alias of a Bedrock Agent.

    Args:
        client: The boto3 Bedrock Agent client.
        agent_id: The unique identifier of the Bedrock Agent.
        alias_id: The unique identifier of the alias.

    Returns:
        A dictionary containing the alias details if it exists, otherwise None.

    Raises:
        ClientError: If AWS returns an unexpected error other than 'ResourceNotFoundException'.

    Behavior:
        - Uses the `get_agent_alias()` API to fetch alias metadata.
        - Retries up to 10 times with exponential backoff using the `@AWSRetry.jittered_backoff` decorator.
        - Returns None if the alias does not exist (i.e., has been deleted or never created).
    """
    try:
        return client.get_agent_alias(agentId=agent_id, agentAliasId=alias_id)["agentAlias"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return None


@AWSRetry.jittered_backoff(retries=10)
def list_agent_aliases(client, **params: Any) -> List[Dict[str, Any]]:
    """
    Retrieve all aliases for a given Bedrock Agent.

    Args:
        client: The boto3 Bedrock Agent client.
        **params: Additional parameters (e.g., `agentId`) for the paginator.

    Returns:
        A list of alias summary dictionaries.
    """
    paginator = client.get_paginator("list_agent_aliases")
    return paginator.paginate(**params).build_full_result()["agentAliasSummaries"]


def find_alias(client, agent_id: str, alias_name: str) -> Optional[Dict[str, Any]]:
    """
    Find an existing alias for a given Bedrock agent.

    Args:
        client: The boto3 Bedrock Agent client.
        agent_id: The unique identifier of the agent.
        alias_name: The name of the alias to search for.

    Returns:
        The alias dictionary if found, otherwise None.
    """
    aliases: List[Dict[str, Any]] = list_agent_aliases(client, agentId=agent_id)
    for alias in aliases:
        if alias.get("agentAliasName") == alias_name:
            return alias
    return None


def create_alias(client, module: AnsibleAWSModule, agent_id: str) -> Tuple[bool, Optional[str], str]:
    """
    Create a new alias for a Bedrock agent.

    Args:
        client: The boto3 Bedrock Agent client.
        module: The AnsibleAWSModule instance containing user parameters.
        agent_id: The unique identifier of the Bedrock agent.

    Returns:
        Tuple containing:
            - changed (bool): Whether the alias was created or would be created.
            - alias_id (Optional[str]): The ID of the created alias (None in check mode).
            - msg (str): Human-readable message about the operation.
    """
    changed: bool = True

    if module.check_mode:
        return changed, None, f"Check mode: would have created agent alias {module.params['alias_name']}."

    params: Dict[str, Any] = {
        "agentAliasName": module.params["alias_name"],
        "agentId": agent_id,
    }
    if module.params.get("description"):
        params["description"] = module.params["description"]

    if module.params.get("tags"):
        params["tags"] = module.params["tags"]

    if module.params.get("routing_configuration"):
        params["routingConfiguration"] = snake_dict_to_camel_dict(module.params["routing_configuration"])

    response = client.create_agent_alias(**params)
    alias_info: Dict[str, Any] = response.get("agentAlias")
    alias_id = alias_info["agentAliasId"]

    # Wait until alias reaches PREPARED state
    wait_for_alias_status(client, module, agent_id, alias_id, "PREPARED")

    return changed, alias_id, f"Agent alias {module.params['alias_name']} created successfully."


def delete_alias(
    client, module: AnsibleAWSModule, agent_id: str, existing_alias: Dict[str, Any]
) -> Tuple[bool, Optional[str], str]:
    """
    Delete an existing alias for a Bedrock agent.

    Args:
        client: The boto3 Bedrock Agent client.
        module: The AnsibleAWSModule instance containing user parameters.
        agent_id: The ID of the Bedrock Agent.
        existing_alias: The alias dictionary returned by AWS to delete.

    Returns:
        Tuple containing:
            - changed (bool): Whether the alias was deleted or would be deleted.
            - alias_id (Optional[str]): The deleted alias ID (None in check mode).
            - msg (str): Human-readable message about the operation.
    """
    if module.check_mode:
        return True, None, f"Check mode: would have deleted agent alias '{existing_alias['agentAliasName']}'."

    client.delete_agent_alias(agentId=agent_id, agentAliasId=existing_alias["agentAliasId"])

    return True, None, f"Agent alias {existing_alias['agentAliasName']} deleted successfully."


# Bedrock Agent Action Group Utilities


@AWSRetry.jittered_backoff(retries=10)
def get_agent_action_group(client, agent_id: str, agent_version: str, action_group_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve details for a specific action group associated with a Bedrock Agent.

    Args:
        client: The boto3 Bedrock Agent client.
        agent_id: The unique identifier of the Bedrock Agent.
        agent_version: The version identifier of the agent.
        action_group_id: The unique identifier of the action group.

    Returns:
        The action group details as a dictionary if found, otherwise None.
    """
    try:
        return client.get_agent_action_group(
            agentId=agent_id, agentVersion=agent_version, actionGroupId=action_group_id
        )["agentActionGroup"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return None


@AWSRetry.jittered_backoff(retries=10)
def list_agent_action_groups(client, **params: Any) -> List[Dict[str, Any]]:
    """
    Retrieve all action groups for a given Bedrock Agent.

    Args:
        client: The boto3 Bedrock Agent client.
        **params: Additional parameters (e.g., `agentId`, `agentVersion`) for the paginator.

    Returns:
        A list of action group summary dictionaries.
    """
    paginator = client.get_paginator("list_agent_action_groups")
    return paginator.paginate(**params).build_full_result()["actionGroupSummaries"]
