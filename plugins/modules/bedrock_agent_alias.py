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

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


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
    region = module.params['region']

    try:
        client = module.client('bedrock-agent', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    try:
        existing_aliases = client.list_agent_aliases(agentId=agent_id)
        found_alias = None
        for alias in existing_aliases.get('agentAliasSummaries', []):
            if alias['agentAliasName'] == alias_name:
                found_alias = alias
                break

        changed = False

        if state == 'present':
            if not found_alias:
                if not module.check_mode:
                    client.create_agent_alias(
                        agentAliasName=alias_name,
                        agentId=agent_id
                    )
                changed = True
        
        elif state == 'absent':
            if found_alias:
                if not module.check_mode:
                    client.delete_agent_alias(
                        agentId=agent_id,
                        agentAliasId=found_alias['agentAliasId']
                    )
                changed = True
        
        module.exit_json(changed=changed)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == '__main__':
    main()
