#!/usr/bin/python
# -*- coding: utf-8 -*-


DOCUMENTATION = r"""
---
module: bedrock_agent
short_description: Manage Amazon Bedrock Agents
version_added: "1.0.0"
author:
    - Alina Buzachis (@alinabuzachis)
description:
    - This module creates, updates, and deletes Amazon Bedrock Agents.
options:
    state:
        description:
            - The state of the agent.
        type: str
        choices: ['present', 'absent']
        default: 'present'
    agent_name:
        description:
            - The name of the agent.
        type: str
        required: true
    foundation_model:
        description:
            - The foundation model to be used by the agent.
        type: str
        required: true
    instruction:
        description:
            - The instructions for the agent.
        type: str
        required: true
    role_arn:
        description:
            - The ARN of the IAM role for the agent.
        type: str
        required: true
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Create a Bedrock Agent
  amazon.ai.bedrock_agent:
    state: present
    agent_name: "test-agent"
    foundation_model: "anthropic.claude-v2"
    instruction: "You are a friendly chat bot that helps with tasks."
    role_arn: "arn:aws:iam::123456789012:role/BedrockAgentRole"
    region: "us-east-1"

- name: Delete a Bedrock Agent
  amazon.ai.bedrock_agent:
    state: absent
    agent_name: "my-first-agent"
    region: "us-east-1"
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

from ansible_collections.amazon.ai.plugins.module_utils.bedrock import wait_for_status
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import find_agent
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import _get_agent, _prepare_agent


def _create_agent(module, client):
    """Creates a new agent."""
    agent_name = module.params['agent_name']
    foundation_model = module.params['foundation_model']
    instruction = module.params['instruction']
    role_arn = module.params['role_arn']

    new_agent = client.create_agent(
        agentName=agent_name,
        foundationModel=foundation_model,
        instruction=instruction,
        agentResourceRoleArn=role_arn
    )
    agent_id = new_agent['agent']['agentId']
    wait_for_status(client, agent_id, 'NOT_PREPARED')
    
    _prepare_agent(client, agent_id)

    return agent_id


def _update_agent(module, client, existing_agent):
    """Updates an existing agent if necessary."""

    agent_name = module.params['agent_name']
    foundation_model = module.params['foundation_model']
    instruction = module.params['instruction']
    role_arn = module.params['role_arn']
    existing_agent_id = existing_agent['agentId']

    needs_update = (
        existing_agent['agentName'] != agent_name or
        existing_agent['foundationModel'] != foundation_model or
        existing_agent['instruction'] != instruction or
        existing_agent['agentResourceRoleArn'] != role_arn
    )

    if needs_update and not module.check_mode:
        client.update_agent(
            agentId=existing_agent_id,
            agentName=agent_name,
            foundationModel=foundation_model,
            instruction=instruction,
            agentResourceRoleArn=role_arn
        )
        
        wait_for_status(client,existing_agent_id, 'UPDATING')
        
        _prepare_agent(client, existing_agent_id)
    
    return needs_update, existing_agent_id


def _delete_agent(module, client, existing_agent):
    """Deletes an existing agent."""
    if not module.check_mode:
        client.delete_agent(agentId=existing_agent['agentId'])
    return True


def main():
    argument_spec=dict(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        agent_name=dict(type='str', required=True),
        foundation_model=dict(type='str', required=True),
        instruction=dict(type='str', required=True),
        role_arn=dict(type='str', required=True),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    state = module.params['state']

    try:
        client = module.client('bedrock-agent', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    changed = False
    result = dict(agent={})
    existing_agent = find_agent(client)

    try:
        if state == 'present':
            if existing_agent:
                # Update existing agent
                changed, agent_id = _update_agent(module, client, existing_agent)
                result['agent'] = _get_agent(client, agent_id)
            else:
                # Create a new agent
                if not module.check_mode:
                    agent_id = _create_agent(module, client)
                    result['agent'] = _get_agent(client, agent_id)
                changed = True
        
        elif state == 'absent':
            if existing_agent:
                # Delete existing agent
                changed = _delete_agent(module, client, existing_agent)
                module.exit_json(changed=changed, **result)
    
        module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))
    
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

if __name__ == '__main__':
    main()
