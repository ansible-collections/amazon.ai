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
            - The name of the agent.
        type: str
    orchestration_type:
        description:
            - Specifies the type of orchestration strategy for the agent.
        type: str
        choices: ['DEFAULT','CUSTOM_ORCHESTRATION']
        default: "DEFAULT"
    foundation_model:
        description:
            - The foundation model to be used by the agent.
            - Required when O(state=present).
        type: str
    instruction:
        description:
            - The instructions for the agent.
            - Required when O(state=present).
        type: str
    role_arn:
        description:
            - The ARN of the IAM role for the agent.
            - Required when O(state=present).
        type: str
    agent_collaboration:
        description:
            - The agent's collaboration role.
        type: str
        choices: ['SUPERVISOR', 'SUPERVISOR_ROUTER', 'DISABLED']
    tags:
        description:
            - Any tags that you want to attach to the agent.
            - Tags cannot be modified. They are only applied when a new Amazon Bedrock Agent is created.
        type: dict
        aliases: ["resource_tags"]
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""


RETURN = r"""
agent:
    description: A dictionary containing the detailed configuration of the managed Bedrock agent.
    type: dict
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


EXAMPLES = r"""
- name: Create a Bedrock Agent
  amazon.ai.bedrock_agent:
    state: present
    agent_name: "test-agent"
    foundation_model: "anthropic.claude-v2"
    instruction: "You are a friendly chat bot that helps with tasks."
    role_arn: "arn:aws:iam::123456789012:role/BedrockAgentRole"

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
from typing import Tuple

from ansible_collections.amazon.ai.plugins.module_utils.bedrock import _get_agent
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import _prepare_agent
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import find_agent
from ansible_collections.amazon.ai.plugins.module_utils.bedrock import wait_for_status

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _create_agent(module: AnsibleAWSModule, client) -> str:
    """Creates a new agent."""
    params: Dict[str, Any] = {
        "agentName": module.params["agent_name"],
        "foundationModel": module.params["foundation_model"],
        "instruction": module.params["instruction"],
        "agentResourceRoleArn": module.params["role_arn"],
        "orchestrationType": module.params["orchestration_type"],
    }

    if module.params.get("tags"):
        params["tags"] = module.params["tags"]

    if module.params.get("agent_collaboration"):
        params["agentCollaboration"] = module.params["agent_collaboration"]

    new_agent = client.create_agent(**params)
    agent_id: str = new_agent["agent"]["agentId"]
    wait_for_status(client, agent_id, "NOT_PREPARED")
    _prepare_agent(client, agent_id)

    return agent_id


def _update_agent(module: AnsibleAWSModule, client, existing_agent: Dict[str, Any]) -> Tuple[bool, str]:
    """Updates an existing agent if necessary."""
    existing_agent_id: str = existing_agent["agentId"]
    needs_update: Dict[str, Any] = {}
    changed: bool = False

    if module.params.get("new_agent_name") and existing_agent["agentName"] != module.params["new_agent_name"]:
        needs_update["agentName"] = module.params["new_agent_name"]

    if existing_agent["foundationModel"] != module.params["foundation_model"]:
        needs_update["foundationModel"] = module.params["foundation_model"]

    if existing_agent["instruction"] != module.params["instruction"]:
        needs_update["instruction"] = module.params["instruction"]

    if existing_agent["agentResourceRoleArn"] != module.params["role_arn"]:
        needs_update["agentResourceRoleArn"] = module.params["role_arn"]

    if (
        module.params.get("orchestration_type")
        and existing_agent["orchestrationType"] != module.params["orchestration_type"]
    ):
        needs_update["orchestrationType"] = module.params["orchestration_type"]

    if (
        module.params.get("agent_collaboration")
        and existing_agent["agentCollaboration"] != module.params["agent_collaboration"]
    ):
        needs_update["agentCollaboration"] = module.params["agent_collaboration"]

    if needs_update:
        changed = True
        if not module.check_mode:
            needs_update["agentId"] = existing_agent_id
            client.update_agent(**needs_update)
            wait_for_status(client, existing_agent_id, "UPDATING")
            _prepare_agent(client, existing_agent_id)

    return changed, existing_agent_id


def _delete_agent(module: AnsibleAWSModule, client, existing_agent: Dict[str, Any]) -> None:
    """Deletes an existing agent."""
    if not module.check_mode:
        client.delete_agent(agentId=existing_agent["agentId"])


def main():
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        agent_name=dict(type="str", required=True),
        new_agent_name=dict(type="str"),
        foundation_model=dict(type="str"),
        instruction=dict(type="str"),
        role_arn=dict(type="str"),
        orchestration_type=dict(type="str", default="DEFAULT", choices=["DEFAULT", "CUSTOM_ORCHESTRATION"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        agent_collaboration=dict(type="str", choices=["SUPERVISOR", "SUPERVISOR_ROUTER", "DISABLED"]),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[("state", "present", ("foundation_model", "instruction", "role_arn"))],
    )

    state: str = module.params["state"]

    try:
        client = module.client("bedrock-agent", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    changed: bool = False
    result: Dict[str, Any] = dict(agent={})
    existing_agent: Dict[str, Any] = find_agent(client, module)

    try:
        if state == "present":
            if existing_agent:
                # Update existing agent
                changed, agent_id = _update_agent(module, client, existing_agent)
                result["agent"] = _get_agent(client, agent_id)
            else:
                # Create a new agent
                if not module.check_mode:
                    agent_id = _create_agent(module, client)
                    result["agent"] = _get_agent(client, agent_id)
                changed = True

        elif state == "absent":
            if existing_agent:
                # Delete existing agent
                _delete_agent(module, client, existing_agent)
                module.exit_json(changed=True, **result)

        module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
