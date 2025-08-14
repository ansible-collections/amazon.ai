# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
---
module: bedrock_agent_action_group_info
short_description: Gathers information about a Bedrock Agent's Action Groups
version_added: "1.0.0"
author:
    - Alina Buzachis (@alinabuzachis)
description:
    - This module can retrieve details for a specific action group by ID or name, or list all action groups for a given agent.
options:
    agent_name:
        description:
            - The Name of the agent.
        type: str
        required: true
    agent_version:
        description:
            - The version of the agent to query.
        type: str
        default: 'DRAFT'
    action_group_name:
        description:
            - The name of the action group to retrieve.
        type: str
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Find a specific action group by name
  amazon.ai.bedrock_agent_action_group_info:
    agent_name: "my_test_agent"
    action_group_name: "my_custom_group"
  register: action_group_by_name

- name: List all action groups with full details
  amazon.ai.bedrock_agent_action_group_info:
    agent_mname: "my_test_agent"
  register: all_action_groups
"""

RETURN = r"""
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
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import find_agent, _list_agent_action_groups, _get_agent_action_group

def main():
    argument_spec = dict(
        agent_name=dict(type='str', required=True),
        agent_version=dict(type='str', default='DRAFT'),
        action_group_name=dict(type='str'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    agent_name = module.params['agent_name']
    agent_version = module.params['agent_version']
    action_group_name = module.params.get('action_group_name')

    try:
        client = module.client('bedrock-agent', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    result = {}
    action_groups_details = []

    try:
        # Find the agent ID from the provided name
        agent_id = find_agent(client, module)
        if not agent_id:
            module.fail_json(msg=f"Agent with name '{agent_name}' not found.")
    
        if action_group_name:
            # Find a specific action group by name
            action_groups_summaries = _list_agent_action_groups(client, agentId=agent_id, agentVersion=agent_version)
            found_id = None
            for summary in action_groups_summaries:
                if summary.get('actionGroupName') == action_group_name:
                    found_id = summary.get('actionGroupId')
                    break
            
            if found_id:
                details = _get_agent_action_group(client, agent_id, agent_version, found_id)
                action_groups_details.append(details)

        else:
            # List all action groups and get full details for each
            action_groups_summaries = _list_agent_action_groups(client, agentId=agent_id, agentVersion=agent_version)
            for summary in action_groups_summaries:
                details = _get_agent_action_group(client, agent_id, agent_version, summary.get('actionGroupId'))
                action_groups_details.append(details)

        result['action_groups'] = action_groups_details

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(**camel_dict_to_snake_dict(result))

if __name__ == '__main__':
    main()
