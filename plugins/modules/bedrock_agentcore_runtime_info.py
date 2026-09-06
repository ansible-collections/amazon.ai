#!/usr/bin/python

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: bedrock_agentcore_runtime_info
short_description: Gather information about Bedrock AgentCore runtimes
version_added: "2.0.0"
author:
    - Domen Dobnikar (@domendobnikar)
description:
    - Gets details for a single Bedrock AgentCore runtime or lists all runtimes.
options:
    agent_runtime_name:
        description:
            - The name of the AgentCore runtime to retrieve. If not provided, the module will list all runtimes.
        type: str
        aliases: ["name"]
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""


EXAMPLES = r"""
- name: Get info about a specific agent runtime
  amazon.ai.bedrock_agentcore_runtime_info:
    agent_runtime_name: "my-runtime"

- name: List all Bedrock AgentCore runtimes
  amazon.ai.bedrock_agentcore_runtime_info:
"""


RETURN = r"""
agent_runtimes:
    description: A list of dictionaries, where each dictionary contains detailed configuration of the managed Bedrock AgentCore runtime.
    type: complex
    returned: always, on success
    contains:
        agent_runtime_arn:
            description: The Amazon Resource Name (ARN) of the runtime.
            type: str
            sample: "arn:aws:bedrock:us-east-1:123456789901:agent-runtime/RNKFFDOKFN"
        agent_runtime_id:
            description: The unique identifier of the runtime.
            type: str
            sample: "RNKFFDOKFN"
        agent_runtime_name:
            description: The name of the runtime.
            type: str
            sample: "test-agentcore-runtime"
        agent_runtime_version:
            description: The version of the runtime.
            type: str
            sample: "1"
        status:
            description: The current status of the runtime.
            type: str
            sample: "READY"
        role_arn:
            description: The ARN of the IAM role assumed by the runtime.
            type: str
            sample: "arn:aws:iam::123456789901:role/test-agentcore-runtime-role"
        agent_runtime_artifact:
            description: The runtime artifact configuration.
            type: dict
            contains:
                container_configuration:
                    description: Container-based runtime configuration.
                    type: dict
                    contains:
                        container_uri:
                            description: The URI of the container image.
                            type: str
                code_configuration:
                    description: Code-based runtime configuration.
                    type: dict
                    contains:
                        s3_bucket:
                            description: The S3 bucket containing the runtime code.
                            type: str
                        s3_prefix:
                            description: The S3 prefix containing the runtime code.
                            type: str
                        s3_version_id:
                            description: The S3 object version identifier.
                            type: str
                        runtime:
                            description: The language runtime.
                            type: str
                        entry_point:
                            description: The entry point for the runtime code.
                            type: list
                            elements: str
        network_configuration:
            description: The network configuration for the runtime.
            type: dict
            contains:
                network_mode:
                    description: The network mode (PUBLIC or VPC).
                    type: str
                network_mode_config:
                    description: VPC configuration.
                    type: dict
                    contains:
                        security_groups:
                            description: Security group IDs for VPC mode.
                            type: list
                            elements: str
                        subnets:
                            description: Subnet IDs for VPC mode.
                            type: list
                            elements: str
        description:
            description: The description of the runtime.
            type: str
        protocol_configuration:
            description: The protocol configuration for the runtime.
            type: dict
            contains:
                server_protocol:
                    description: The server protocol used (MCP, HTTP, A2A, or AGUI).
                    type: str
        lifecycle_configuration:
            description: The lifecycle configuration for the runtime.
            type: dict
            contains:
                idle_runtime_session_timeout:
                    description: The idle session timeout in seconds.
                    type: int
                max_lifetime:
                    description: The maximum lifetime in seconds.
                    type: int
        environment_variables:
            description: Environment variables for the runtime.
            type: dict
        authorizer_configuration:
            description: The authorizer configuration for the runtime.
            type: dict
            contains:
                custom_jwt_authorizer:
                    description: Custom JWT authorizer configuration.
                    type: dict
                    contains:
                        discovery_url:
                            description: The JWT discovery URL.
                            type: str
                        allowed_audience:
                            description: Allowed audience values.
                            type: list
                            elements: str
                        allowed_clients:
                            description: Allowed client IDs.
                            type: list
                            elements: str
                        allowed_scopes:
                            description: Allowed OAuth scopes.
                            type: list
                            elements: str
        filesystem_configurations:
            description: The filesystem configurations for the runtime.
            type: list
            elements: dict
            contains:
                session_storage:
                    description: The session storage configuration for the filesystem.
                    type: dict
                    contains:
                        access_point_arn:
                            description: The ARN of the session storage access point.
                            type: str
                        mount_path:
                            description: The mount path for the session storage.
                            type: str
                s3_files_access_point:
                    description: The S3 Files Access Point configuration for the filesystem.
                    type: dict
                    contains:
                        access_point_arn:
                            description: The ARN of the S3 Files Access Point.
                            type: str
                        mount_path:
                            description: The mount path for the S3 Files Access Point.
                            type: str
                efs_access_point:
                    description: The EFS Access Point configuration for the filesystem.
                    type: dict
                    contains:
                        access_point_arn:
                            description: The ARN of the EFS Access Point.
                            type: str
                        mount_path:
                            description: The mount path for the EFS Access Point.
                            type: str
                capacity_provider_volume:
                    description: The capacity provider volume configuration for the filesystem.
                    type: dict
                    contains:
                        volume_name:
                            description: The name of the capacity provider volume.
                            type: str
                        mount_path:
                            description: The mount path for the capacity provider volume.
                            type: str
        capacity_provider_configuration:
            description: The capacity provider configuration for the runtime.
            type: dict
            contains:
                capacity_provider_arn:
                    description: The ARN of the capacity provider.
                    type: str
        created_at:
            description: The timestamp when the runtime was created.
            type: str
            sample: "2025-10-01T15:36:41.199376+00:00"
        last_updated_at:
            description: The timestamp when the runtime was last updated.
            type: str
            sample: "2025-10-01T15:36:42.201271+00:00"
        failure_reason:
            description: The reason for a failed runtime (if applicable).
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

from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import get_agent_runtime_by_id
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import get_agent_runtime_by_name
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import list_agent_runtimes

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main():
    argument_spec = dict(
        agent_runtime_name=dict(type="str", aliases=["name"]),
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
        agent_runtime_name: Optional[str] = module.params.get("agent_runtime_name")
        result: List[Dict[str, Any]] = list()

        if agent_runtime_name:
            existing_runtime: Optional[Dict[str, Any]] = get_agent_runtime_by_name(client, agent_runtime_name)
            if existing_runtime:
                result.append(existing_runtime)
        else:
            runtime_summaries: List[Dict[str, Any]] = list_agent_runtimes(client)
            for runtime_summary in runtime_summaries:
                agent_runtime_id: str = runtime_summary.get("agent_runtime_id")
                runtime_detail: Optional[Dict[str, Any]] = get_agent_runtime_by_id(client, agent_runtime_id)
                if runtime_detail:
                    result.append(runtime_detail)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(agent_runtimes=[camel_dict_to_snake_dict(runtime, ignore_list=["tags"]) for runtime in result])


if __name__ == "__main__":
    main()
