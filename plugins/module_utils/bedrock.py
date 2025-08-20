import time
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass


def wait_for_status(client, agent_id, status):
    """Waits for an agent to reach a specific status."""
    while True:
        try:
            current_status = client.get_agent(agentId=agent_id)['agent']['agentStatus']
            if current_status == status:
                break
            time.sleep(5)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Handle cases where the agent might be deleted during wait
                if status == 'DELETED':
                    break
                # Or re-raise the error if it's an unexpected deletion
                raise
            else:
                raise


@AWSRetry.jittered_backoff(retries=10)
def _prepare_agent(client, agent_id):
    """
    Prepares a Bedrock Agent and waits for it to be in the 'PREPARED' state.
    """
    client.prepare_agent(agentId=agent_id)
    wait_for_status(client, agent_id, "PREPARED")

    return True


@AWSRetry.jittered_backoff(retries=10)
def _list_agents(client, **params):
    paginator = client.get_paginator("list_agents")
    return paginator.paginate(**params).build_full_result()["agentSummaries"]


@AWSRetry.jittered_backoff(retries=10)
def _get_agent(client, agent_id):
    try:
        return client.get_agent(agentId=agent_id)['agent']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return None


@AWSRetry.jittered_backoff(retries=10)
def _list_action_groups(client, **params):
    paginator = client.get_paginator("list_agent_action_groups")
    return paginator.paginate(**params).build_full_result()["actionGroupSummaries"]


@AWSRetry.jittered_backoff(retries=10)
def _list_agent_aliases(client, **params):
    paginator = client.get_paginator("list_agent_aliases")
    return paginator.paginate(**params).build_full_result()["agentAliasSummaries"]


def find_agent(client, module):
    """
    Finds a specific agent by name or retrieves details for all agents.

    Args:
        client (boto3.client): The Bedrock Agent Boto3 client.
        module (AnsibleModule): The AnsibleModule object.

    Returns:
        dict or list: The detailed information for a single agent or a list of agent details.
                      Returns None if a specific agent is not found.
    """
    agent_name = module.params.get('agent_name')

    agents_list = _list_agents(client)
    if not agents_list:
        return []

    if agent_name:
        for agent_summary in agents_list:
            if agent_summary['agentName'] == agent_name:
                return _get_agent(client, agent_summary['agentId'])
        return None  # Return None if the specific agent is not found
    else:
        # Return a list of all agents with their detailed information
        return [_get_agent(client, agent['agentId']) for agent in agents_list]