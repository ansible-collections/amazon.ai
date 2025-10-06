#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: bedrock_agent_alias_info
short_description: Gathers information about a Bedrock Agent's Aliases
version_added: "1.0.0"
author:
    - Alina Buzachis (@alinabuzachis)
description:
    - This module can retrieve details for a specific alias or lists all aliases for a given Bedrock Agent, identified by its name.
options:
    agent_name:
        description:
            - The name of the agent.
        type: str
        required: true
    alias_name:
        description:
            - The name of the agent alias.
        type: str
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: List all aliases for an agent by name
  amazon.ai.bedrock_agent_alias_info:
    agent_name: "my-test-agent"

- name: List information about a specific agent alias
  amazon.ai.bedrock_agent_alias_info:
    agent_name: "my-test-agent"
    alias_name: "my-test-agent-alias"
"""

<<<<<<< HEAD

=======
>>>>>>> 4e6c0fa (Add bedrock_agent_alias and bedrock_agent_alias_info modules)
RETURN = r"""
agent_aliases:
    description: A list of dictionaries, where each dictionary contains the detailed configuration of an agent alias.
    type: complex
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
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import get_agent_alias
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import list_agent_aliases

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main():
    argument_spec = dict(
        agent_name=dict(type="str", required=True),
        alias_name=dict(type="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    agent_name: str = module.params["agent_name"]

    try:
        client = module.client("bedrock-agent", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    result: List[Dict[str, Any]] = []

    try:
        # Get the agent ID from the provided name
        agents_list: List[Dict[str, Any]] = find_agent(client, module)
        agent: Optional[Dict[str, Any]] = agents_list[0] if agents_list else None
        if not agent:
            module.fail_json(msg=f"Agent with name '{agent_name}' not found.")

        agent_id: str = agent.get("agentId")

        # List aliases using the found agent ID
        aliases_summary: List[Dict[str, Any]] = list_agent_aliases(client, agentId=agent_id)

        if module.params.get("alias_name"):
            found_alias = next(
                (alias for alias in aliases_summary if alias["agentAliasName"] == module.params["alias_name"]), None
            )
            if found_alias:
                result.append(get_agent_alias(client, agent_id, found_alias.get("agentAliasId")))
        else:
            for alias in aliases_summary:
                result.append(get_agent_alias(client, agent_id, alias.get("agentAliasId")))

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(agent_aliases=[camel_dict_to_snake_dict(alias, ignore_list=["tags"]) for alias in result])


if __name__ == "__main__":
    main()
