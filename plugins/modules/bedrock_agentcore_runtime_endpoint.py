#!/usr/bin/python

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: bedrock_agentcore_runtime_endpoint
short_description: Manage Amazon Bedrock AgentCore runtime endpoints
version_added: "2.0.0"
author:
    - Domen Dobnikar (@domendobnikar)
description:
    - Creates, updates, and deletes Amazon Bedrock AgentCore runtime endpoints.
    - A runtime endpoint is a named, addressable alias pointing at a specific runtime version.
options:
    state:
        description:
            - The desired state of the AgentCore runtime endpoint.
        type: str
        choices: ['present', 'absent']
        default: present
    agent_runtime_name:
        description:
            - The name of the parent AgentCore runtime.
            - The module resolves this to the runtime ID via the list and match lookup pattern.
        type: str
        required: true
        aliases: ["name"]
    endpoint_name:
        description:
            - The name of the runtime endpoint.
            - The name is immutable because AgentCore does not provide a rename operation.
        type: str
        required: true
    agent_runtime_version:
        description:
            - The runtime version this endpoint should point to.
            - If omitted at creation, defaults to the latest version.
            - Updatable.
        type: str
    description:
        description:
            - A description of the runtime endpoint.
            - Updatable.
        type: str
    tags:
        description:
            - Tags to attach to the endpoint.
            - Tags are applied only when an endpoint is created.
        type: dict
        aliases: ["resource_tags"]
    wait:
        description:
            - Whether to wait for the endpoint to reach a terminal state.
        type: bool
        default: true
    wait_timeout:
        description:
            - How long (in seconds) to wait for the endpoint to reach a terminal state.
        type: int
        default: 600
seealso:
    - module: amazon.ai.bedrock_agentcore_runtime_endpoint_info
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Create an endpoint for an agentcore runtime
  amazon.ai.bedrock_agentcore_runtime_endpoint:
    state: present
    agent_runtime_name: "my-runtime"
    endpoint_name: "my-endpoint"
    description: "Production endpoint"

- name: Update an endpoint to point to a different runtime version
  amazon.ai.bedrock_agentcore_runtime_endpoint:
    state: present
    agent_runtime_name: "my-runtime"
    endpoint_name: "my-endpoint"
    agent_runtime_version: "2"

- name: Delete a runtime endpoint
  amazon.ai.bedrock_agentcore_runtime_endpoint:
    state: absent
    agent_runtime_name: "my-runtime"
    endpoint_name: "my-endpoint"
"""

RETURN = r"""
agent_runtime_endpoint:
    description: A dictionary containing the detailed configuration of the managed Bedrock AgentCore runtime endpoint.
    type: dict
    returned: always, on success
    contains:
        agent_runtime_endpoint_arn:
            description: The Amazon Resource Name (ARN) of the endpoint.
            type: str
            sample: "arn:aws:bedrock:us-east-1:123456789901:agent-runtime-endpoint/RNKFFDOKFN/my-endpoint"
        agent_runtime_arn:
            description: The ARN of the parent runtime.
            type: str
            sample: "arn:aws:bedrock:us-east-1:123456789901:agent-runtime/RNKFFDOKFN"
        id:
            description: The unique identifier of the endpoint.
            type: str
            sample: "EP123456"
        name:
            description: The name of the endpoint.
            type: str
            sample: "my-endpoint"
        live_version:
            description: The currently live runtime version for this endpoint.
            type: str
            sample: "1"
        target_version:
            description: The runtime version this endpoint is targeting or will target.
            type: str
            sample: "2"
        status:
            description: The current status of the endpoint.
            type: str
            sample: "READY"
        description:
            description: The description of the endpoint.
            type: str
            sample: "Production endpoint"
        created_at:
            description: The timestamp when the endpoint was created.
            type: str
            sample: "2025-10-03T14:33:09.676524+00:00"
        last_updated_at:
            description: The timestamp when the endpoint was last updated.
            type: str
            sample: "2025-10-03T14:33:09.676524+00:00"
        failure_reason:
            description: The reason for a failed endpoint operation (when applicable).
            type: str
            sample: "Runtime version not found"
msg:
    description: Informative message about the action.
    returned: always
    type: str
    sample: "Agent runtime endpoint 'my-endpoint' created successfully."
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import AgentRuntimeEndpointStatus
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import create_agent_runtime_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import delete_agent_runtime_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import get_agent_runtime_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import get_agent_runtime_quick_summary_by_name
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import update_agent_runtime_endpoint

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def runtime_endpoint_status_check(
    existing_runtime_endpoint: Optional[Dict[str, Any]], state: str, module: AnsibleAWSModule
) -> None:
    # Early exit if existing_runtime_endpoint is deleting, creating or updating
    if existing_runtime_endpoint:
        if existing_runtime_endpoint.get("status") == AgentRuntimeEndpointStatus.DELETING:
            module.exit_json(
                changed=False,
                msg=f"Agent runtime endpoint {existing_runtime_endpoint.get('endpoint_name')} is currently being deleted.",
            )
        if state == "present" and existing_runtime_endpoint.get("status") in {
            AgentRuntimeEndpointStatus.UPDATING,
            AgentRuntimeEndpointStatus.CREATING,
        }:
            module.exit_json(
                changed=False,
                msg=f"Agent runtime endpoint {existing_runtime_endpoint.get('endpoint_name')} is currently in {existing_runtime_endpoint.get('status')}.",
            )


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        agent_runtime_name=dict(type="str", required=True, aliases=["name"]),
        endpoint_name=dict(type="str", required=True),
        agent_runtime_version=dict(type="str"),
        description=dict(type="str"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        client = module.client("bedrock-agentcore-control", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    try:
        state: str = module.params["state"]
        agent_runtime_name: str = module.params["agent_runtime_name"]
        endpoint_name: str = module.params["endpoint_name"]
        changed: bool = False
        result: Dict[str, Any] = dict(agent_runtime_endpoint=dict())
        msg: str = ""

        existing_runtime: Optional[Dict[str, Any]] = get_agent_runtime_quick_summary_by_name(client, agent_runtime_name)
        if not existing_runtime:
            if state == "present":
                module.fail_json(msg=f"Agent runtime with name '{agent_runtime_name}' not found.")
            else:
                result["msg"] = "Agent runtime not found. No action taken."
                module.exit_json(changed=False, **camel_dict_to_snake_dict(result))
        else:
            agent_runtime_id = existing_runtime.get("agent_runtime_id")

            existing_endpoint: Optional[Dict[str, Any]] = get_agent_runtime_endpoint(
                client, agent_runtime_id, endpoint_name
            )
            runtime_endpoint_status_check(existing_endpoint, state, module)

            if state == "present":
                if existing_endpoint is None:
                    changed, endpoint_resp_name, msg = create_agent_runtime_endpoint(module, client, agent_runtime_id)
                else:
                    changed, endpoint_resp_name, msg = update_agent_runtime_endpoint(
                        module, client, agent_runtime_id, existing_endpoint
                    )
                endpoint = (
                    get_agent_runtime_endpoint(client, agent_runtime_id, endpoint_resp_name)
                    if endpoint_resp_name
                    else dict()
                )
                result["agent_runtime_endpoint"] = endpoint

            else:
                if existing_endpoint is not None:
                    changed, msg = delete_agent_runtime_endpoint(module, client, agent_runtime_id, existing_endpoint)
                else:
                    msg = "Endpoint does not exist."
            result["msg"] = msg

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(changed=changed, **result)


if __name__ == "__main__":
    main()
