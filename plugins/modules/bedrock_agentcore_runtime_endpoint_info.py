#!/usr/bin/python

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: bedrock_agentcore_runtime_endpoint_info
short_description: Gather information about Bedrock AgentCore runtime endpoints
version_added: "2.0.0"
author:
    - Domen Dobnikar (@domendobnikar)
description:
    - Gets details for a single Bedrock AgentCore runtime endpoint or lists all endpoints for a given runtime.
options:
    agent_runtime_name:
        description:
            - The name of the parent AgentCore runtime.
            - Required to identify which runtime's endpoints to query.
        type: str
        required: true
        aliases: ["name"]
    endpoint_name:
        description:
            - The name of the specific endpoint to retrieve.
            - If not provided, the module will list all endpoints for the runtime.
        type: str
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Get info about a specific endpoint
  amazon.ai.bedrock_agentcore_runtime_endpoint_info:
    agent_runtime_name: "my-runtime"
    endpoint_name: "my-endpoint"

- name: List all endpoints for a runtime
  amazon.ai.bedrock_agentcore_runtime_endpoint_info:
    agent_runtime_name: "my-runtime"
"""

RETURN = r"""
agent_runtime_endpoints:
    description:
        - A list of dictionaries, where each dictionary contains detailed configuration of a Bedrock AgentCore runtime endpoint.
        - When a specific endpoint is requested, returns a single-element list.
    type: complex
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
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import get_agent_runtime_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import get_agent_runtime_quick_summary_by_name
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import list_agent_runtime_endpoints

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main() -> None:
    argument_spec = dict(
        agent_runtime_name=dict(type="str", required=True, aliases=["name"]),
        endpoint_name=dict(type="str"),
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
        agent_runtime_name: str = module.params["agent_runtime_name"]
        endpoint_name: Optional[str] = module.params.get("endpoint_name")
        result: List[Dict[str, Any]] = list()

        runtime_summary = get_agent_runtime_quick_summary_by_name(client, agent_runtime_name)
        if not runtime_summary:
            module.exit_json(agent_runtime_endpoints=list())

        agent_runtime_id: str = runtime_summary.get("agent_runtime_id")

        if endpoint_name:
            endpoint = get_agent_runtime_endpoint(client, agent_runtime_id, endpoint_name)
            if endpoint:
                result.append(endpoint)
        else:
            endpoints = list_agent_runtime_endpoints(client, agent_runtime_id)
            for endpoint in endpoints:
                endpoint_details = get_agent_runtime_endpoint(client, agent_runtime_id, endpoint.get("name"))
                if endpoint_details:
                    result.append(endpoint_details)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(
        agent_runtime_endpoints=[camel_dict_to_snake_dict(endpoint, ignore_list=["tags"]) for endpoint in result]
    )


if __name__ == "__main__":
    main()
