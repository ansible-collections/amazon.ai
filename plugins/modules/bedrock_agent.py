#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
            - Specifies a new name for the agent.
        type: str
        required: true
    new_agent_name:
        description:
            - The new name to assign to the agent.
        type: str
    orchestration_type:
        description:
            - Specifies the type of orchestration strategy for the agent.
        type: str
        choices: ['DEFAULT', 'CUSTOM_ORCHESTRATION']
        default: "DEFAULT"
    foundation_model:
        description:
            - ARN or name of a Bedrock model.
            - Required when O(state=present).
        type: str
    instruction:
        description:
            - The instructions for the agent.
            - Required when O(state=present).
        type: str
    agent_resource_role_arn:
        description:
            - The ARN of the IAM role for the agent.
            - Required when O(state=present).
        type: str
    agent_collaboration:
        description:
            - The agent's collaboration role.
        type: str
        choices: ['SUPERVISOR', 'SUPERVISOR_ROUTER', 'DISABLED']
    prompt_override_configuration:
        description:
            - A dictionary to define custom prompt configurations for the agent.
            - Supports fields to customize prompts at various stages of the agent's processing.
        type: dict
        suboptions:
            prompt_configurations:
                description:
                    - A list of prompt configuration dictionaries.
                type: list
                elements: dict
                suboptions:
                    prompt_type:
                        description:
                            - Step in the agent sequence that this prompt configuration applies to.
                        type: str
                    base_prompt_template:
                        description:
                            - The prompt template to replace the default prompt template.
                        type: str
                    inference_configuration:
                        description:
                            - Inference parameters to use when invoking a foundation model.
                        type: dict
                        suboptions:
                            maximum_length:
                                description: Maximum number of tokens to generate.
                                type: int
                            temperature:
                                description: Sampling temperature for generation.
                                type: float
                            top_k:
                                description: Top-K sampling parameter.
                                type: int
                            top_p:
                                description: Top-P (nucleus) sampling parameter.
                                type: float
                            stop_sequences:
                                description: List of strings that signal the end of generation.
                                type: list
                                elements: str
                    parser_mode:
                        description:
                            - Specifies whether to override the default parser.
                        type: str
                    prompt_creation_mode:
                        description:
                            - Specifies whether to override the default prompt template.
                        type: str
                    prompt_state:
                        description:
                            - Specifies whether to allow the agent to carry out the step specified in the prompt type.
                        type: str
            override_lambda:
                description:
                    - ARN of a Lambda function to override the prompt orchestration for the agent.
                type: str
    tags:
        description:
            - Any tags that you want to attach to the agent.
            - Tags cannot be modified. They are only applied when a new Amazon Bedrock Agent is created.
        type: dict
        aliases: ["resource_tags"]
    wait_timeout:
        description:
            - Specifies the maximum amount of time, in seconds, that the module should wait
              for the requested operation on the Bedrock Agent to complete before timing out.
            - This applies to operations that may take time to reach a stable state, such as
              creating, or updating an agent.
            - During this period, the module will poll the agent's status at regular intervals
              to detect when the operation has completed.
            - If the agent does not reach the desired state within this timeout, the module
              will fail.
            - Increasing this value may be useful for slower or heavily loaded environments,
              while decreasing it can make the module fail faster when quick feedback is desired.
        default: 600
        type: int
extends_documentation_fragment:
- amazon.aws.common.modules
- amazon.aws.region.modules
- amazon.aws.boto3
"""


RETURN = r"""
agent:
    description: A dictionary containing the detailed configuration of the managed Bedrock agent.
    type: complex
    returned: always, on success
    contains:
        agent_id:
            description: The unique identifier of the agent.
            type: str
            sample: "RNKFFDOKFN"
        agent_name:
            description: The name of the agent.
            type: str
            sample: "test-bedrock-agent-test"
        agent_version:
            description: "Version of the agent."
            type: str
            sample: "DRAFT"
        agent_arn:
            description: The Amazon Resource Name (ARN) of the agent.
            type: str
            sample: "arn:aws:bedrock:us-east-1:123456789901:agent/RNKFFDOKFN"
        agent_collaboration:
            description:
                - The agent's collaboration role.
            type: str
            sample: "DISABLE"
        agent_resource_role_arn:
            description: The ARN of the IAM role with permissions to invoke the agent.
            type: str
            sample: "arn:aws:iam::123456789901:role/test-bedrock-agent-role-7a58c95cf105"
        agent_status:
            description: The current status of the agent.
            type: str
            sample: "PREPARED"
        foundation_model:
            description: The foundation model used for orchestration by the agent.
            type: str
            sample: "amazon.nova-micro-v1:0"
        instruction:
            description: The instructions that tell the agent what it should do.
            type: str
            sample: "You are a friendly chat bot that provides helpful information and assistance to users."
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
            sample: "2025-10-01T15:36:41.199376+00:00"
        updated_at:
            description: The timestamp when the agent was last updated.
            type: str
            sample: "2025-10-01T15:36:42.201271+00:00"
        prepared_at:
            description: The timestamp when the agent was last prepared.
            type: str
            sample: "2025-10-01T15:36:47.859575+00:00"
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
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: "Agent 'test-bedrock-agent-7a58c95cf105' created successfully."
"""


EXAMPLES = r"""
- name: Create a Bedrock Agent
  amazon.ai.bedrock_agent:
    state: present
    agent_name: "test-agent"
    foundation_model: "anthropic.claude-v2"
    instruction: "You are a friendly chat bot that helps with tasks."
    agent_resource_role_arn: "arn:aws:iam::123456789012:role/BedrockAgentRole"

- name: Delete a Bedrock Agent
  amazon.ai.bedrock_agent:
    state: absent
    agent_name: "my-first-agent"
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.bedrock import create_agent
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import delete_agent
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import find_agent
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import get_agent
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import update_agent

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main():
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        agent_name=dict(type="str", required=True),
        new_agent_name=dict(type="str"),
        foundation_model=dict(type="str"),
        instruction=dict(type="str"),
        agent_resource_role_arn=dict(type="str"),
        orchestration_type=dict(type="str", default="DEFAULT", choices=["DEFAULT", "CUSTOM_ORCHESTRATION"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        agent_collaboration=dict(type="str", choices=["SUPERVISOR", "SUPERVISOR_ROUTER", "DISABLED"]),
        wait_timeout=dict(type="int", default=600, required=False),
        prompt_override_configuration=dict(
            type="dict",
            options=dict(
                prompt_configurations=dict(
                    type="list",
                    elements="dict",
                    options=dict(
                        prompt_type=dict(type="str"),
                        base_prompt_template=dict(type="str"),
                        inference_configuration=dict(
                            type="dict",
                            options=dict(
                                maximum_length=dict(type="int"),
                                temperature=dict(type="float"),
                                top_k=dict(type="int"),
                                top_p=dict(type="float"),
                                stop_sequences=dict(type="list", elements="str"),
                            ),
                        ),
                        parser_mode=dict(type="str"),
                        prompt_creation_mode=dict(type="str"),
                        prompt_state=dict(type="str"),
                    ),
                ),
                override_lambda=dict(type="str"),
            ),
        ),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[("state", "present", ["foundation_model", "instruction", "agent_resource_role_arn"])],
    )

    state: str = module.params["state"]

    try:
        client = module.client("bedrock-agent", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    changed: bool = False
    result: Dict[str, Any] = dict(agent={})
    agents: List[Dict[str, Any]] = find_agent(client, module)
    existing_agent: Optional[Dict[str, Any]] = agents[0] if agents else None

    try:
        if state == "present":
            if existing_agent:
                # Update existing agent
                changed, agent_id, msg = update_agent(module, client, existing_agent)
                result["agent"] = get_agent(client, agent_id)
                result["msg"] = msg
            else:
                # Create a new agent
                changed, agent_id, msg = create_agent(module, client)
                result["agent"] = get_agent(client, agent_id) if agent_id else {}
                result["msg"] = msg

        elif state == "absent":
            if existing_agent:
                # Delete existing agent
                changed, msg = delete_agent(module, client, existing_agent)
                result["msg"] = msg
            else:
                result["msg"] = "Agent does not exist."

        module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
