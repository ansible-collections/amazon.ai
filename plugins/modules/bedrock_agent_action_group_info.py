#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: bedrock_agent_action_group_info
short_description: Gather information about a Bedrock Agent's Action Groups
version_added: "1.0.0"
author:
    - Alina Buzachis (@alinabuzachis)
description:
    - This module can retrieve details for a specific action group by ID or name, or list all action groups for a given agent.
options:
    agent_name:
        description:
            - The name of the agent.
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

- name: List all action groups with full details
  amazon.ai.bedrock_agent_action_group_info:
    agent_name: "my_test_agent"
"""


RETURN = r"""
action_groups:
    description: A dictionary containing the detailed configuration of an action group.
    type: dict
    returned: always, on success
    contains:
        action_group_id:
            description: The unique identifier of the action group.
            type: str
            sample: "9IXXEEO8FR"
        action_group_name:
            description: The name of the action group.
            type: str
            sample: "get-weather-info-test"
        action_group_state:
            description: The state of the action group.
            type: str
            sample: "ENABLED"
        agent_id:
            description: The unique identifier of the agent this action group belongs to.
            type: str
            sample: "RNKFFDOKFN"
        agent_version:
            description: The version of the agent this action group is associated with.
            type: str
            sample: "DRAFT"
        action_group_executor:
            description: Details about the action group's executor.
            type: dict
            contains:
                lambda:
                    description: The ARN of the Lambda function that executes the action group.
                    type: str
                    sample: "arn:aws:lambda:us-east-1:123456789012:function:test-bedrock-lambda-test:12"
        api_schema:
            description: The OpenAPI 3.0 schema that defines the action group's API.
            type: dict
            contains:
                payload:
                    description: The raw YAML/JSON content of the API schema.
                    type: str
        description:
            description: A description of the action group.
            type: str
            sample: "Gets the current date and time."
        created_at:
            description: The timestamp when the action group was created.
            type: str
            sample: "2025-10-03T14:33:09.676524+00:00"
        updated_at:
            description: The timestamp when the action group was last updated.
            type: str
            sample: "2025-10-03T14:33:09.676524+00:00"
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.bedrock import find_agent
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import get_agent_action_group
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import list_agent_action_groups

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main():
    argument_spec = dict(
        agent_name=dict(type="str", required=True),
        agent_version=dict(type="str", default="DRAFT"),
        action_group_name=dict(type="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    agent_name: str = module.params["agent_name"]
    agent_version: Optional[str] = module.params["agent_version"]
    action_group_name: Optional[str] = module.params.get("action_group_name")

    try:
        client = module.client("bedrock-agent", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    result: List[Dict[str, Any]] = []
    action_groups_details: List[Dict[str, Any]] = []

    try:
        # Find the agent ID from the provided name
        agents_list: List[Dict[str, Any]] = find_agent(client, module)
        agent: Optional[Dict[str, Any]] = agents_list[0] if agents_list else None
        if not agent:
            module.fail_json(msg=f"Agent with name '{agent_name}' not found.")
        agent_id: str = agent.get("agentId")

        if action_group_name:
            # Find a specific action group by name
            action_groups_summaries: List[Dict[str, Any]] = list_agent_action_groups(
                client, agentId=agent_id, agentVersion=agent_version
            )
            found_id: Optional[str] = None
            for summary in action_groups_summaries:
                if summary.get("actionGroupName") == action_group_name:
                    found_id = summary.get("actionGroupId")
                    break

            if found_id:
                details: Dict[str, Any] = get_agent_action_group(client, agent_id, agent_version, found_id)
                result.append(details)
        else:
            # List all action groups and get full details for each
            action_groups_summaries: List[Dict[str, Any]] = list_agent_action_groups(
                client, agentId=agent_id, agentVersion=agent_version
            )
            for summary in action_groups_summaries:
                details: Dict[str, Any] = get_agent_action_group(
                    client, agent_id, agent_version, summary.get("actionGroupId")
                )
                action_groups_details.append(details)
            result = action_groups_details

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(
        action_groups=[camel_dict_to_snake_dict(action_group, ignore_list=["tags"]) for action_group in result]
    )


if __name__ == "__main__":
    main()
