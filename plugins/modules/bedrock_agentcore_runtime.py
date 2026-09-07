#!/usr/bin/python

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: bedrock_agentcore_runtime
short_description: Manage Amazon Bedrock AgentCore runtimes
version_added: "2.0.0"
author:
    - Domen Dobnikar (@domendobnikar)
description:
    - Creates, updates, and deletes Amazon Bedrock AgentCore runtimes.
    - AgentCore runtime tags are applied only when a runtime is created.
options:
    state:
        description:
            - The desired state of the AgentCore runtime.
        type: str
        choices: ['present', 'absent']
        default: present
    agent_runtime_name:
        description:
            - The name of the AgentCore runtime.
            - The name is immutable because AgentCore does not provide a rename operation.
        type: str
        required: true
        aliases: ["name"]
    agent_runtime_version:
        description:
            - The version of the AgentCore runtime.
            - Can be used with O(state=absent) to specify the version of the runtime to delete.
        type: str
    container_configuration:
        description:
            - Configuration for a container-based runtime.
            - Required when O(state=present) unless O(code_configuration) is specified.
        type: dict
        suboptions:
            container_uri:
                description:
                    - The URI of the container image for the runtime.
                type: str
                required: true
    code_configuration:
        description:
            - Configuration for a code-based runtime.
            - Required when O(state=present) unless O(container_configuration) is specified.
        type: dict
        suboptions:
            s3_bucket:
                description:
                    - The S3 bucket containing the runtime code.
                type: str
                required: true
            s3_prefix:
                description:
                    - The S3 prefix containing the runtime code.
                type: str
                required: true
            s3_version_id:
                description:
                    - The S3 object version identifier for the runtime code.
                type: str
            runtime:
                description:
                    - The language runtime for the code configuration.
                type: str
                required: true
                choices: ['PYTHON_3_10', 'PYTHON_3_11', 'PYTHON_3_12', 'PYTHON_3_13', 'PYTHON_3_14', 'NODE_22']
            entry_point:
                description:
                    - The entry point for the runtime code.
                type: list
                elements: str
                required: true
    role_arn:
        description:
            - The ARN of the IAM role assumed by AgentCore to run the runtime.
            - Required when O(state=present).
        type: str
    network_mode:
        description:
            - The network mode for the runtime.
        type: str
        choices: ['PUBLIC', 'VPC']
    network_security_groups:
        description:
            - The security groups for a VPC runtime.
        type: list
        elements: str
    network_subnets:
        description:
            - The subnets for a VPC runtime.
        type: list
        elements: str
    description:
        description:
            - A description of the runtime.
        type: str
    protocol:
        description:
            - The server protocol used by the runtime.
        type: str
        choices: ['MCP', 'HTTP', 'A2A', 'AGUI']
    idle_runtime_session_timeout:
        description:
            - The idle runtime session timeout in seconds.
            - Default is 900 seconds (15 minutes) set by AWS.
        type: int
    max_lifetime:
        description:
            - The maximum runtime lifetime in seconds.
            - Default is 28800 seconds (8 hours) set by AWS.
        type: int
    environment_variables:
        description:
            - Environment variables supplied to the runtime.
        type: dict
    authorizer_discovery_url:
        description:
            - The discovery URL for the custom JWT authorizer.
        type: str
    authorizer_allowed_audience:
        description:
            - Audience values accepted by the custom JWT authorizer.
        type: list
        elements: str
    authorizer_allowed_clients:
        description:
            - Client values accepted by the custom JWT authorizer.
        type: list
        elements: str
    authorizer_allowed_scopes:
        description:
            - Scope values accepted by the custom JWT authorizer.
        type: list
        elements: str
    capacity_provider_arn:
        description:
            - The ARN of the capacity provider for the runtime.
            - Run the AgentCore Runtime on the Instances compute type.
            - Provisions Amazon Web Services managed compute in your account.
        type: str
    session_storage:
        description:
            - Configuration for session storage.
            - Persistent storage that is preserved across AgentCore Runtime session.
            - Cannot be set if O(s3_files_access_point), O(efs_access_point) or O(capacity_provider_volume) is specified.
        type: dict
        suboptions:
            mount_path:
                description:
                    - The mount path for the session storage filesystem inside the AgentCore Runtime.
                    - Must be under /mnt with exactly one subdirectory level (for example, /mnt/data).
                type: str
                required: true
    s3_files_access_point:
        description:
            - Configuration for an Amazon S3 Files access point to mount into the AgentCore Runtime.
            - Cannot be set if O(session_storage), O(efs_access_point) or O(capacity_provider_volume) is specified.
        type: dict
        suboptions:
            access_point_arn:
                description:
                    - The ARN of the S3 Files access point.
                type: str
                required: true
            mount_path:
                description:
                    - The mount path for the S3 Files access point inside the AgentCore Runtime.
                    - Must be under /mnt with exactly one subdirectory level (for example, /mnt/data).
                type: str
                required: true
    efs_access_point:
        description:
            - Configuration for an Amazon EFS access point to mount into the AgentCore Runtime.
            - Cannot be set if O(session_storage), O(s3_files_access_point) or O(capacity_provider_volume) is specified.
        type: dict
        suboptions:
            access_point_arn:
                description:
                    - The ARN of the EFS access point.
                type: str
                required: true
            mount_path:
                description:
                    - The mount path for the EFS access point inside the AgentCore Runtime.
                    - Must be under /mnt with exactly one subdirectory level (for example, /mnt/data).
                type: str
                required: true
    capacity_provider_volume:
        description:
            - Configuration for a capacity provider volume to mount into the AgentCore Runtime.
            - Cannot be set if O(session_storage), O(s3_files_access_point), or O(efs_access_point) is specified.
        type: dict
        suboptions:
            volume_name:
                description:
                    - The name of the capacity provider volume.
                type: str
                required: true
            mount_path:
                description:
                    - The mount path for the capacity provider volume inside the AgentCore Runtime.
                    - Must be under /mnt with exactly one subdirectory level (for example, /mnt/data).
                type: str
                required: true
    tags:
        description:
            - Tags attached to the runtime when it is created.
            - Tags cannot be modified after creation by this module.
        type: dict
        aliases: ["resource_tags"]
    wait:
        description:
            - Whether to wait for the requested operation to reach a terminal state.
        type: bool
        default: true
    wait_timeout:
        description:
            - The maximum time in seconds to wait for an operation to complete.
        type: int
        default: 600
seealso:
    - module: amazon.ai.bedrock_agentcore_runtime_info
notes:
    - Verify the required IAM actions against the AWS Service Authorization Reference before relying on them in a policy.
    - The IAM actions are bedrock-agentcore:CreateAgentRuntime, bedrock-agentcore:GetAgentRuntime,
      bedrock-agentcore:UpdateAgentRuntime, bedrock-agentcore:DeleteAgentRuntime, and
      bedrock-agentcore:ListAgentRuntimes, plus iam:PassRole when a role is supplied.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Create a container-based AgentCore runtime
  amazon.ai.bedrock_agentcore_runtime:
    state: present
    agent_runtime_name: weather_runtime
    container_configuration:
      container_uri: 123456789012.dkr.ecr.us-east-1.amazonaws.com/weather:latest
    role_arn: arn:aws:iam::123456789012:role/AgentCoreRuntimeRole

- name: Delete an AgentCore runtime
  amazon.ai.bedrock_agentcore_runtime:
    state: absent
    agent_runtime_name: weather_runtime
"""

RETURN = r"""
agent_runtime:
    description: Details about the AgentCore runtime after the module operation.
    returned: always, on success
    type: dict
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
msg:
    description: Informative message about the action.
    returned: always
    type: str
    sample: Agent runtime weather_runtime created successfully.
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


from typing import Any
from typing import Dict
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import create_agent_runtime
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import delete_agent_runtime
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import get_agent_runtime_by_id
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import get_agent_runtime_by_name
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import update_agent_runtime
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import AgentRuntimeStatus

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def runtime_status_check(existing_runtime: Dict[str, Any], state: str, module: AnsibleAWSModule) -> None:
    # Early exit if existing_runtime is deleting, creating or updating
    if existing_runtime:
        if existing_runtime.get("status") == AgentRuntimeStatus.DELETING:
            module.exit_json(changed=False, msg=f"Agent runtime is currently being deleted.")
        if state == "present" and existing_runtime.get("status") in {
            AgentRuntimeStatus.UPDATING,
            AgentRuntimeStatus.CREATING,
        }:
            module.exit_json(changed=False, msg=f"Agent runtime is currently in {existing_runtime.get('status')}.")


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        agent_runtime_name=dict(type="str", required=True, aliases=["name"]),
        container_configuration=dict(
            type="dict",
            options=dict(container_uri=dict(type="str", required=True)),
        ),
        code_configuration=dict(
            type="dict",
            options=dict(
                s3_bucket=dict(type="str", required=True),
                s3_prefix=dict(type="str", required=True),
                s3_version_id=dict(type="str"),
                runtime=dict(
                    type="str",
                    required=True,
                    choices=["PYTHON_3_10", "PYTHON_3_11", "PYTHON_3_12", "PYTHON_3_13", "PYTHON_3_14", "NODE_22"],
                ),
                entry_point=dict(type="list", elements="str", required=True),
            ),
        ),
        role_arn=dict(type="str"),
        network_mode=dict(type="str", choices=["PUBLIC", "VPC"]),
        network_security_groups=dict(type="list", elements="str"),
        network_subnets=dict(type="list", elements="str"),
        description=dict(type="str"),
        protocol=dict(type="str", choices=["MCP", "HTTP", "A2A", "AGUI"]),
        idle_runtime_session_timeout=dict(type="int"),
        max_lifetime=dict(type="int"),
        environment_variables=dict(type="dict"),
        authorizer_discovery_url=dict(type="str"),
        authorizer_allowed_audience=dict(type="list", elements="str"),
        authorizer_allowed_clients=dict(type="list", elements="str"),
        authorizer_allowed_scopes=dict(type="list", elements="str"),
        capacity_provider_arn=dict(type="str"),
        session_storage=dict(
            type="dict",
            options=dict(
                mount_path=dict(type="str", required=True),
            ),
        ),
        s3_files_access_point=dict(
            type="dict",
            options=dict(
                access_point_arn=dict(type="str", required=True),
                mount_path=dict(type="str", required=True),
            ),
        ),
        efs_access_point=dict(
            type="dict",
            options=dict(
                access_point_arn=dict(type="str", required=True),
                mount_path=dict(type="str", required=True),
            ),
        ),
        capacity_provider_volume=dict(
            type="dict",
            options=dict(
                volume_name=dict(type="str", required=True),
                mount_path=dict(type="str", required=True),
            ),
        ),
        tags=dict(type="dict", aliases=["resource_tags"]),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ["container_configuration", "code_configuration"],
            ["session_storage", "s3_files_access_point", "efs_access_point", "capacity_provider_volume"],
        ],
        required_together=[["network_security_groups", "network_subnets"]],
        required_if=[
            ("state", "present", ["role_arn"]),
            ("network_mode", "VPC", ["network_security_groups", "network_subnets"]),
        ],
    )

    if module.params["state"] == "present" and not (
        module.params.get("container_configuration") or module.params.get("code_configuration")
    ):
        module.fail_json(
            msg="Exactly one of container_configuration or code_configuration is required when state=present."
        )

    try:
        client = module.client("bedrock-agentcore-control", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    try:
        changed: bool = False
        result: Dict[str, Any] = dict(agent_runtime=dict())
        state: str = module.params["state"]
        msg: str = ""

        existing_runtime: Optional[Dict[str, Any]] = get_agent_runtime_by_name(
            client, module.params["agent_runtime_name"]
        )
        runtime_status_check(existing_runtime, state, module)

        if state == "present":
            if existing_runtime:
                changed, runtime_id, msg = update_agent_runtime(module, client, existing_runtime)
            else:
                changed, runtime_id, msg = create_agent_runtime(module, client)
            result["agent_runtime"] = get_agent_runtime_by_id(client, runtime_id) if runtime_id else dict()
        else:
            if existing_runtime:
                changed, msg = delete_agent_runtime(module, client, existing_runtime)
            else:
                msg = "Agent runtime does not exist."

        result["msg"] = msg
        module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
