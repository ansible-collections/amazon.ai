#!/usr/bin/python
# -*- coding: utf-8 -*-


DOCUMENTATION = r"""
---
module: bedrock_agent_alias
short_description: Manage Amazon Bedrock Agent Aliases
version_added: "1.0.0"
author:
    - Alina Buzachis (@alinabuzachis)
description:
    - This module creates and deletes an alias for a Bedrock Agent.
options:
    state:
        description:
            - The state of the agent alias.
        type: str
        choices: ['present', 'absent']
        default: 'present'
    agent_id:
        description:
            - The ID of the Bedrock Agent.
        type: str
        required: true
    alias_name:
        description:
            - The name of the alias.
        type: str
        required: true
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""


EXAMPLES = r"""
- name: Create an alias for the agent
  amazon.ai.bedrock_agent_alias:
    state: present
    agent_id: "{{ agent_id }}"
    alias_name: "test_alias"
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.bedrock import _list_agent_aliases 


def _find_alias(client, agent_id, alias_name):
    """
    Finds an existing alias for a given agent.
    """
    aliases = _list_agent_aliases(client, agentId=agent_id)
    for alias in aliases:
        if alias.get('agentAliasName') == alias_name:
            return alias
    return None


def _create_alias(client, agent_id, alias_name):
    """
    Creates a new agent alias.
    """
    response = client.create_agent_alias(
        agentAliasName=alias_name,
        agentId=agent_id
    )
    alias_info = response.get('agentAlias')
    return True, alias_info


def _delete_alias(client, agent_id, alias_id):
    """
    Deletes an existing agent alias.
    """
    client.delete_agent_alias(
        agentId=agent_id,
        agentAliasId=alias_id
    )
    return True
 

def main():
    argument_spec=dict(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        agent_id=dict(type='str', required=True),
        alias_name=dict(type='str', required=True),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params['state']
    agent_id = module.params['agent_id']
    alias_name = module.params['alias_name']

    try:
        client = module.client('bedrock-agent', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    changed = False
    alias_info = None
    result = {"alias": {}}

    try:
        found_alias = _find_alias(client, agent_id, alias_name)
        if state == 'present':
            if not found_alias:
                if not module.check_mode:
                    changed, alias_info = _create_alias(client, agent_id, alias_name)

                changed = True
                if not alias_info:
                    alias_info = _find_alias(client, agent_id, alias_name)
            else:
                alias_info = found_alias
                changed = False
        
        elif state == 'absent':
            if found_alias:
                if not module.check_mode:
                    changed = _delete_alias(client, agent_id, found_alias.get('agentAliasId'))
                changed = True
            else:
                changed = False
        
        result['alias'] = camel_dict_to_snake_dict(alias_info)
        module.exit_json(changed=changed, **result)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == '__main__':
    main()
