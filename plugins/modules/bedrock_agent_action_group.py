#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
---
module: bedrock_agent_action_group
short_description: Manage Amazon Bedrock Agent Action Groups
version_added: "1.0.0"
author:
    - Alina Buzachis (@alinabuzachis)
description:
    - This module creates, updates, and deletes an action group for a Bedrock Agent.
options:
    state:
        description:
            - The state of the action group.
        type: str
        choices: ['present', 'absent']
        default: 'present'
    agent_id:
        description:
            - The ID of the Bedrock Agent.
        type: str
        required: true
    action_group_name:
        description:
            - The name of the action group.
        type: str
        required: true
    description:
        description:
            - A description of the action group.
        type: str
    lambda_arn:
        description:
            - The ARN of the Lambda function for the action group.
        type: str
        required: true
    api_schema_path:
        description:
            - The local path to the OpenAPI schema file (YAML or JSON).
        type: str
        required: true
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Create an action group for the agent
  amazon.ai.bedrock_agent_action_group:
    state: present
    agent_id: "{{ agent_id }}"
    action_group_name: "get_current_date_time"
    description: "Gets the current date and time."
    lambda_arn: "arn:aws:lambda:us-east-1:123456789012:function:MyBedrockFunction"
    api_schema_path: "scenario_resources/api_schema.yaml"
"""


import json
import yaml
import time

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.bedrock import _list_agent_action_groups
from ansible_collections.amazon.aws.plugins.module_utils.bedrock import _prepare_agent
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict


def _find_action_group(client, agent_id, action_group_name):
    """Finds an existing action group by name and returns its details."""
    action_groups = _list_agent_action_groups(client, agentId=agent_id, agentVersion='DRAFT')
    for group in action_groups:
        if group['actionGroupName'] == action_group_name:
            return client.get_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                actionGroupId=group['actionGroupId']
            )['actionGroup']
    return None


def _create_action_group(client, agent_id, action_group_name, description, lambda_arn, api_schema):
    """Creates a new action group."""
    response = client.create_agent_action_group(
        agentId=agent_id,
        agentVersion='DRAFT',
        actionGroupName=action_group_name,
        description=description,
        actionGroupExecutor={'lambda': lambda_arn},
        apiSchema={'payload': api_schema}
    )
    return True, response.get('agentActionGroup')


def _update_action_group(client, agent_id, action_group_id, action_group_name, description, lambda_arn, api_schema):
    """Updates an existing action group."""
    response = client.update_agent_action_group(
        agentId=agent_id,
        agentVersion='DRAFT',
        actionGroupId=action_group_id,
        actionGroupName=action_group_name,
        description=description,
        actionGroupExecutor={'lambda': lambda_arn},
        apiSchema={'payload': api_schema}
    )
    return True, response.get('agentActionGroup')
 

def _delete_action_group(client, agent_id, action_group_id):
    """Deletes an existing action group."""
    client.delete_agent_action_group(
        agentId=agent_id,
        agentVersion='DRAFT',
        actionGroupId=action_group_id
    )
    return True


def main():
    argument_spec=dict(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        agent_id=dict(type='str', required=True),
        action_group_name=dict(type='str', required=True),
        description=dict(type='str'),
        lambda_arn=dict(type='str', required=True),
        api_schema_path=dict(type='str', required=True),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    state = module.params['state']
    agent_id = module.params['agent_id']
    action_group_name = module.params['action_group_name']
    description = module.params.get('description')
    lambda_arn = module.params['lambda_arn']
    api_schema_path = module.params['api_schema_path']

    changed = False
    action_group_info = None
    result = {"action_group": {}}

    try:
        client = module.client('bedrock-agent', retry_decorator=AWSRetry.jittered_backoff())
        found_action_group = _find_action_group(client, agent_id, action_group_name)

        if state == 'present':
            api_schema = None
            try:
                with open(api_schema_path, 'r') as file:
                    api_schema = json.dumps(yaml.safe_load(file))
            except (IOError, yaml.YAMLError) as e:
                module.fail_json(msg="Failed to read API schema file: %s" % str(e))

            if found_action_group:
                current_api_schema = json.dumps(found_action_group['apiSchema']['payload'])
                
                if current_api_schema != api_schema or found_action_group.get('description') != description:
                    if not module.check_mode:
                        changed, action_group_info = _update_action_group(
                            client, agent_id, found_action_group['actionGroupId'], action_group_name, description, lambda_arn, api_schema
                        )
                    else:
                        changed = True
                else:
                    action_group_info = found_action_group

            else:
                if not module.check_mode:
                    changed, action_group_info = _create_action_group(client, agent_id, action_group_name, description, lambda_arn, api_schema)
                else:
                    changed = True

        elif state == 'absent':
            if found_action_group:
                if not module.check_mode:
                    changed = _delete_action_group(client, agent_id, found_action_group['actionGroupId'])
                else:
                    changed = True

        # Conditionally prepare the agent after a change
        if changed and not module.check_mode:
            _prepare_agent(client, agent_id)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)
    
    result = dict(changed=changed)
    if action_group_info:
        result['action_group'] = camel_dict_to_snake_dict(action_group_info)
    
    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
