#!/usr/bin/python
# -*- coding: utf-8 -*-


DOCUMENTATION = r"""
---
module: bedrock_agent_info
short_description: Gathers information about Bedrock Agents
version_added: "1.0.0"
author:
    - Alina Buzachis (@alinabuzachis)
description:
    - This module gets details for a single Bedrock Agent or lists all agents.
options:
    agent_id:
        description:
            - The unique identifier of the agent to retrieve. If not provided, the module will list all agents.
        type: str
    list_action_groups:
        description:
            - If true, lists all action groups for the specified agent.
        type: bool
        default: false
    list_aliases:
        description:
            - If true, lists all aliases for the specified agent.
        type: bool
        default: false
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""


EXAMPLES = r"""
- name: Get info about a specific agent
  amazon.ai.bedrock_agent_info:
    agent_id: "ABCDEFGHIJKLMNOP"
  register: agent_details

- name: Get info about a specific agent, its action groups and aliases
  amazon.ai.bedrock_agent_info:
    agent_id: "ABCDEFGHIJKLMNOP"
    list_action_groups: true
    list_aliases: true
  register: agent_details

- name: List all Bedrock agents
  amazon.ai.bedrock_agent_info:
  register: all_agents
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main():
    argument_spec=dict(
        agent_id=dict(type='str'),
        list_action_groups=dict(type='bool', default=False),
        list_aliases=dict(type='bool', default=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    agent_id = module.params.get('agent_id')
    list_action_groups = module.params.get('list_action_groups')
    list_aliases = module.params.get('list_aliases')
    
    try:
        client = module.client('bedrock-agent', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    result = dict(changed=False)
    
    try:
        if agent_id:
            # Get a single agent's info
            try:
                response = client.get_agent(agentId=agent_id)
                result['agent'] = response.get('agent')
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    result['agent'] = None
                else:
                    raise
            # Conditionally list action groups
            if list_action_groups and result.get('agent'):
                response = client.list_agent_action_groups(agentId=agent_id, agentVersion='DRAFT')
                result['agent']['actionGroups'] = response.get('actionGroupSummaries')

            # Conditionally list aliases
            if list_aliases and result.get('agent'):
                response = client.list_agent_aliases(agentId=agent_id)
                result['agent']['aliases'] = response.get('agentAliasSummaries')
        else:
            # List all agents
            response = client.list_agents()
            agents_list = response.get('agentSummaries', [])

            # Conditionally fetch and add action groups/aliases for each agent
            if list_action_groups or list_aliases:
                for agent_summary in agents_list:
                    current_agent_id = agent_summary['agentId']
                    
                    if list_action_groups:
                        response_ag = client.list_agent_action_groups(agentId=current_agent_id, agentVersion='DRAFT')
                        agent_summary['actionGroups'] = response_ag.get('actionGroupSummaries')
                    
                    if list_aliases:
                        response_al = client.list_agent_aliases(agentId=current_agent_id)
                        agent_summary['aliases'] = response_al.get('agentAliasSummaries')

            result['agents'] = agents_list
            
    except ClientError as e:
        module.fail_json(msg=f"AWS ClientError: {e.response['Error']['Message']}")
    except Exception as e:
        module.fail_json(msg=str(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
