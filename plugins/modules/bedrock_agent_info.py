#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: bedrock_agent_info
short_description: Gathers information about Bedrock Agents
version_added: "1.0.0"
author:
    - Alina Buzachis (@alinabuzachis)
description:
    - This module gets details for a single Bedrock Agent or lists all agents.
options:
    agent_name:
        description:
            - The unique identifier of the agent to retrieve. If not provided, the module will list all agents.
        type: str
    list_action_groups:
        description:
            - If V(true), lists all action groups for the specified agent.
        type: bool
        default: false
    list_aliases:
        description:
            - If V(true), lists all aliases for the specified agent.
        type: bool
        default: false
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""


EXAMPLES = r"""
- name: Get info about a specific agent
  amazon.ai.bedrock_agent_info:
    agent_id: "ABCDEFGHIJKLMNOP"
  register: agent_details

- name: Get info about a specific agent, its action groups and aliases
  amazon.ai.bedrock_agent_info:
    agent_id: "ABCDEFGHIJKLMNOP"
    list_action_groups: true
    list_aliases: true
  register: agent_details

- name: List all Bedrock agents
  amazon.ai.bedrock_agent_info:
  register: all_agents
"""


RETURN = r"""
agent:
    description: A dictionary or list of dictionaries containing the details of the agent.
    type: complex
    returned: always
    contains:
        agent_id:
            description: The unique identifier of the agent.
            type: str
            sample: "RNKFFDOKFN"
        agent_name:
            description: The name of the agent.
            type: str
            sample: "test-bedrock-agent-test"
        agent_arn:
            description: The Amazon Resource Name (ARN) of the agent.
            type: str
            sample: "arn:aws:bedrock:us-east-1:123456789901:agent/RNKFFDOKFN"
        agent_resource_role_arn:
            description: The ARN of the IAM role with permissions to invoke the agent.
            type: str
        agent_status:
            description: The current status of the agent.
            type: str
            sample: PREPARED
        foundation_model:
            description: The foundation model used for orchestration by the agent.
            type: str
            sample: amazon.nova-micro-v1:0
        instruction:
            description: The instructions that tell the agent what it should do.
            type: str
        orchestration_type:
            description: The orchestration strategy for the agent.
            type: str
            sample: "DEFAULT"
        idle_session_ttl_in_seconds:
            description: The number of seconds for which the agent keeps conversation information.
            type: int
            sample: 600
        created_at:
            description: The timestamp when the agent was created.
            type: str
        updated_at:
            description: The timestamp when the agent was last updated.
            type: str
        prepared_at:
            description: The timestamp when the agent was last prepared.
            type: str
        prompt_override_configuration:
            description: Contains configurations to override prompt templates in different parts of an agent sequence.
            type: dict
            contains:
                prompt_configurations:
                    description: A list of prompt configuration dictionaries.
                    type: list
                    elements: dict
                    contains:
                        prompt_type:
                            description: The step in the agent sequence that this prompt configuration applies to.
                            type: str
                        base_prompt_template:
                            description: The prompt template to replace the default prompt template.
                            type: str
                        inference_configuration:
                            description: Inference parameters to use when the agent invokes a foundation model.
                            type: dict
                        parser_mode:
                            description: Specifies whether to override the default parser Lambda function.
                            type: str
                        prompt_creation_mode:
                            description: Specifies whether to override the default prompt template for this prompt type.
                            type: str
                        prompt_state:
                            description: Specifies whether to allow the agent to carry out the step specified in the prompt type.
                            type: str
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.bedrock import _list_agent_action_groups
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import _list_agent_aliases
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import find_agent

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _add_related_info(client, module: AnsibleAWSModule, agent_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to add action groups and aliases to an agent's info.

    Args:
        client: The Boto3 client.
        module: The Ansible module object.
        agent_info: A dictionary containing the agent's summary or details.

    Returns:
        The updated agent_info dictionary.
    """
    list_action_groups: Optional[bool] = module.params.get("list_action_groups")
    list_aliases: Optional[bool] = module.params.get("list_aliases")

    agent_id: Optional[str] = agent_info.get("agentId")

    if list_action_groups:
        agent_info["actionGroups"] = _list_agent_action_groups(client, agentId=agent_id, agentVersion="DRAFT")

    if list_aliases:
        agent_info["aliases"] = _list_agent_aliases(client, agentId=agent_id)

    return agent_info


def main():
    argument_spec = dict(
        agent_name=dict(type="str"),
        list_action_groups=dict(type="bool", default=False),
        list_aliases=dict(type="bool", default=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    agent_name: Optional[str] = module.params.get("agent_name")

    try:
        client = module.client("bedrock-agent", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    result: Dict[str, Any] = {}

    try:
        if agent_name:
            # Find a single agent by name
            agent_details: Optional[Dict[str, Any]] = find_agent(client, module)
            if agent_details:
                result["agent"] = _add_related_info(client, module, agent_details)
            else:
                result["agent"] = {}  # Agent not found
        else:
            # List all agents
            agents_list: List[Dict[str, Any]] = find_agent(client, module)

            # Conditionally fetch and add related info for each agent
            updated_agents_list = []
            for agent_summary in agents_list:
                updated_agents_list.append(_add_related_info(client, module, agent_summary))

            result["agent"] = updated_agents_list

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(**camel_dict_to_snake_dict(result))


if __name__ == "__main__":
    main()
