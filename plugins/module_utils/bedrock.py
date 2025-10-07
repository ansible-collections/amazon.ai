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

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


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


def wait_for_agent_status(client, module, agent_id: str, status: str) -> None:
    """
    Poll the Bedrock Agent until it reaches the specified status or timeout expires.

    Behavior:
        - Repeatedly checks the agent's current status using `client.get_agent()`.
        - Sleeps for 5 seconds between polling attempts.
        - Stops polling once the agent reaches the desired status.
        - Gracefully handles cases where the agent is deleted while waiting:
          exits silently if the desired status is "DELETED".
        - Raises a TimeoutError if the desired status is not reached within wait_timeout.

    Args:
        client: boto3 Bedrock Agent client.
        agent_id: Agent ID to poll.
        status: Target agent status to wait for.
        wait_timeout: Max seconds to wait before timing out (default: 600).

    Raises:
        TimeoutError: If timeout expires before reaching target status.
        ClientError: If AWS returns unexpected error.
    """
    start_time = time.time()
    wait_timeout = module.params["wait_timeout"]

    while True:
        try:
            current_status = client.get_agent(agentId=agent_id)["agent"]["agentStatus"]

            if current_status == status:
                break

            if time.time() - start_time > wait_timeout:
                module.fail_json(
                    msg=f"Timeout waiting for agent {agent_id} to reach status '{status}'. "
                    f"Last known status: '{current_status}'."
                )

            time.sleep(5)

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                if status == "DELETED":
                    break
                raise
            raise


@AWSRetry.jittered_backoff(retries=10)
def _prepare_agent(client, module, agent_id: str) -> bool:
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
def _get_agent(client, agent_id: str) -> Optional[Dict[str, Any]]:
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


@AWSRetry.jittered_backoff(retries=10)
def _get_agent_action_group(
    client, agent_id: str, agent_version: str, action_group_id: str
) -> Optional[Dict[str, Any]]:
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
def _list_agent_action_groups(client, **params: Any) -> List[Dict[str, Any]]:
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


@AWSRetry.jittered_backoff(retries=10)
def _list_agent_aliases(client, **params: Any) -> List[Dict[str, Any]]:
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
                return [_get_agent(client, agent_summary["agentId"])]
        return []  # Empty list if no match found
    else:
        # Return a list of all agents with their detailed information
        return [_get_agent(client, agent["agentId"]) for agent in agents_list]
