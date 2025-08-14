import time
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass


def _wait_for_status(client, agent_id, status):
    """Waits for an agent to reach a specific status."""
    while client.get_agent(agentId=agent_id)['agent']['agentStatus'] != status:
        time.sleep(5)


@AWSRetry.jittered_backoff(retries=10)
def _list_agents(client, **params):
    paginator = client.get_paginator("list_agents")
    return paginator.paginate(**params).build_full_result()["agentSummaries"]


def _get_agent(client, agent_id):
    try:
        return client.get_agent(agentId=agent_id)['agent']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return None


def _find_agent(client, module):
    """Finds an agent by name and returns its details or None."""
    params = dict()
    agent_name = module.params['agent_name']
    
    response = _list_agents(client, **params)
    if response:
        for agent in response.get('agentSummaries', []):
            if agent['agentName'] == agent_name:
                return _get_agent(client, agent['agentId'])

    return None
