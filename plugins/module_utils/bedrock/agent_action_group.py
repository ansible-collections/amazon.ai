# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass

from typing import Any
from typing import Dict
from typing import List
from typing import Optional


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
