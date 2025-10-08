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
