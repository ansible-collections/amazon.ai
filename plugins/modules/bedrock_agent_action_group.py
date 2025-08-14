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


from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


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


    try:
        client = module.client('bedrock-agent', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    try:
        # Load API schema from file
        with open(api_schema_path, 'r') as file:
            api_schema = json.dumps(yaml.safe_load(file))

        existing_action_groups = client.list_agent_action_groups(agentId=agent_id, agentVersion='DRAFT')
        found_action_group = None
        for group in existing_action_groups.get('actionGroupSummaries', []):
            if group['actionGroupName'] == action_group_name:
                found_action_group = client.get_agent_action_group(
                    agentId=agent_id,
                    agentVersion='DRAFT',
                    actionGroupId=group['actionGroupId']
                )['actionGroup']
                break

        changed = False
        
        if state == 'present':
            if found_action_group:
                # Compare and update if necessary. Update logic can be more complex based on specific fields.
                # For this example, we'll assume a change in schema or description requires an update.
                current_api_schema = json.dumps(client.get_agent_action_group(
                    agentId=agent_id,
                    agentVersion='DRAFT',
                    actionGroupId=found_action_group['actionGroupId']
                )['actionGroup']['apiSchema']['payload'])
                
                if current_api_schema != api_schema or found_action_group.get('description') != description:
                    if not module.check_mode:
                        client.update_agent_action_group(
                            agentId=agent_id,
                            agentVersion='DRAFT',
                            actionGroupId=found_action_group['actionGroupId'],
                            actionGroupName=action_group_name,
                            description=description,
                            actionGroupExecutor={'lambda': lambda_arn},
                            apiSchema={'payload': api_schema}
                        )
                    changed = True
            else:
                if not module.check_mode:
                    client.create_agent_action_group(
                        agentId=agent_id,
                        agentVersion='DRAFT',
                        actionGroupName=action_group_name,
                        description=description,
                        actionGroupExecutor={'lambda': lambda_arn},
                        apiSchema={'payload': api_schema}
                    )
                changed = True

        elif state == 'absent':
            if found_action_group:
                if not module.check_mode:
                    client.delete_agent_action_group(
                        agentId=agent_id,
                        agentVersion='DRAFT',
                        actionGroupId=found_action_group['actionGroupId']
                    )
                changed = True

        # Always prepare the agent after any changes to an action group
        if changed and not module.check_mode:
            client.prepare_agent(agentId=agent_id)
            while client.get_agent(agentId=agent_id)['agent']['agentStatus'] != 'PREPARED':
                time.sleep(5)
        
        module.exit_json(changed=changed)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

if __name__ == '__main__':
    main()
