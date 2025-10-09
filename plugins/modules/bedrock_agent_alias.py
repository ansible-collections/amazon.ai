#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
    agent_name:
        description:
            - The name of the Bedrock Agent.
        type: str
        required: true
    alias_name:
        description:
            - The name of the alias.
        type: str
        required: true
    description:
        description:
            - A description of the alias of the agent.
        type: str
    routing_configuration:
        description:
            - Contains details about the routing configuration of the alias.
        type: dict
        suboptions:
            agent_version:
                description:
                    - The version of the agent with which the alias is associated.
                type: str
            provisioned_throughput:
                description:
                    - Information on the Provisioned Throughput assigned to an agent alias.
                type: str
    tags:
        description:
            - Any tags that you want to attach to the alias.
        type: dict
        aliases: ["resource_tags"]
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""


RETURN = r"""
agent_alias:
    description: A dictionary containing the detailed configuration of an agent alias.
    type: dict
    returned: always
    contains:
        agent_alias_id:
            description: The unique identifier of the alias.
            type: str
            sample: "Q8U5JCV5WI"
        agent_alias_name:
            description: The name of the alias.
            type: str
            sample: "test-alias"
        agent_alias_arn:
            description: The Amazon Resource Name (ARN) of the alias.
            type: str
            sample: "arn:aws:bedrock:us-east-1:123456789012:agent-alias/FFMGQXTAZM/Q8U5JCV5WI"
        agent_id:
            description: The unique identifier of the agent this alias is for.
            type: str
            sample: "FFMGQXTAZM"
        agent_alias_status:
            description: The status of the alias.
            type: str
            sample: "PREPARED"
        alias_invocation_state:
            description: The invocation state for the agent alias.
            type: str
            sample: "ACCEPT_INVOCATIONS"
        routing_configuration:
            description: Details about the version of the agent with which the alias is associated.
            type: list
            elements: dict
            contains:
                agent_version:
                    description: The version of the agent the alias points to.
                    type: str
            sample: [
                {
                    "agent_version": "1"
                }
            ]
        agent_alias_history_events:
            description: Contains details about the history of the alias.
            type: list
            elements: dict
            contains:
                start_date:
                    description: The date that the alias began being associated with the version.
                    type: str
                end_date:
                    description: The date that the alias stopped being associated with the version.
                    type: str
                routing_configuration:
                    description: The routing configuration at a specific point in time.
                    type: list
            sample: [
                {
                    "end_date": "2025-10-06T10:15:05.278613+00:00",
                    "routing_configuration": [
                        {}
                    ],
                    "start_date": "2025-10-06T10:15:01.909990+00:00"
                },
                {
                    "routing_configuration": [
                        {
                            "agent_version": "1"
                        }
                    ],
                    "start_date": "2025-10-06T10:15:05.278613+00:00"
                }
            ]
        description:
            description: The description of the alias.
            type: str
            sample: "Test Alias for Agent."
        created_at:
            description: The timestamp when the alias was created.
            type: str
            sample: "2025-10-06T10:15:01.909990+00:00"
        updated_at:
            description: The timestamp when the alias was last updated.
            type: str
            sample: "2025-10-06T10:15:01.909990+00:00"
msg:
    description: Informative message about the action.
    returned: always
    type: str
    sample: "Agent alias 'test-bedrock-agent--alias- 7a58c95cf105' created successfully."
"""


EXAMPLES = r"""
- name: Create an alias for the agent
  amazon.ai.bedrock_agent_alias:
    state: present
    agent_name: "{{ agent_name }}"
    alias_name: "{{ alias_name }}"

- name: Delete an alias for the agent
  amazon.ai.bedrock_agent_alias:
    state: absent
    agent_name: "{{ agent_name }}"
    alias_name: "{{ alias_name }}"
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.bedrock import create_alias
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import delete_alias
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import find_agent
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import find_alias
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import get_agent_alias

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main():
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        agent_name=dict(type="str", required=True),
        alias_name=dict(type="str", required=True),
        tags=dict(type="dict", aliases=["resource_tags"]),
        description=dict(type="str"),
        routing_configuration=dict(
            type="dict",
            options=dict(
                agent_version=dict(type="str"),
                provisioned_throughput=dict(type="str"),
            ),
        ),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state: str = module.params["state"]
    agent_name: str = module.params["agent_name"]
    alias_name: str = module.params["alias_name"]

    try:
        client = module.client("bedrock-agent", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    changed: bool = False
    result: Dict[str, Any] = {"agent_alias": {}}

    try:
        # Get the agent ID from the provided name
        agents_list: List[Dict[str, Any]] = find_agent(client, module)
        agent: Optional[Dict[str, Any]] = agents_list[0] if agents_list else None
        if not agent:
            module.fail_json(msg=f"Agent with name '{agent_name}' not found.")
        agent_id: str = agent.get("agentId")

        found_alias: Optional[Dict[str, Any]] = find_alias(client, agent_id, alias_name)

        if state == "present":
            if found_alias is None:
                changed, alias_id, msg = create_alias(client, module, agent_id)
                result["agent_alias"] = get_agent_alias(client, agent_id, alias_id) if alias_id else {}
                result["msg"] = msg
                changed = True

            else:
                result[
                    "msg"
                ] = f"An agent alias with name {found_alias['agentAliasName']} exists and can not be updated."
                result["agent_alias"] = get_agent_alias(client, agent_id, found_alias["agentAliasId"])

        elif state == "absent":
            if found_alias is not None:
                changed, agent_id, msg = delete_alias(client, module, agent_id, found_alias)
                result["msg"] = msg
            else:
                result["msg"] = "Agent alias does not exist."

        module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
