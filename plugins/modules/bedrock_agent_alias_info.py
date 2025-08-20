#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
---
module: bedrock_agent_alias_info
short_description: Gathers information about a Bedrock Agent's Aliases
version_added: "1.0.0"
author:
    - Alina Buzachis (@alinabuzachis)
description:
    - This module lists all aliases for a given Bedrock Agent, identified by its name.
options:
    agent_name:
        description:
            - The name of the agent.
        type: str
        required: true
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: List all aliases for an agent by name
  amazon.ai.bedrock_agent_alias_info:
    agent_name: "my-test-agent"
  register: alias_list
"""

RETURN = r"""
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import _list_agent_aliases
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import find_agent


def main():
    argument_spec = dict(
        agent_name=dict(type='str', required=True),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    agent_name = module.params['agent_name']

    try:
        client = module.client('bedrock-agent', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    result = {"agent_alias": {}}
    
    try:
        # Get the agent ID from the provided name
        agent_id = find_agent(client, module)

        if not agent_id:
            module.fail_json(msg=f"Agent with name '{agent_name}' not found.")

        # List aliases using the found agent ID
        aliases_summary = _list_agent_aliases(client, agentId=agent_id)

        # Get full details for each alias
        aliases_details = []
        for alias in aliases_summary:
            response = client.get_agent_alias(
                agentId=agent_id,
                agentAliasId=alias.get('agentAliasId')
            )
            aliases_details.append(response.get('agentAlias'))
        
        result['agent_alias'] = aliases_details

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(**camel_dict_to_snake_dict(result))


if __name__ == '__main__':
    main()
