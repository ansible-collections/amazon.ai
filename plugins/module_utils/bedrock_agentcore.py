# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


@AWSRetry.jittered_backoff(retries=10)
def list_agent_runtimes(client) -> List[Dict[str, Any]]:
    """
    Retrieve all AgentCore runtime quick summaries using the AWS paginator.

    Args:
        client: The boto3 Bedrock Agent client.

    Returns:
        A list of agent runtimes quick (not detailed) summary dictionaries.
    """
    paginator = client.get_paginator("list_agent_runtimes")
    response = paginator.paginate().build_full_result()
    return [camel_dict_to_snake_dict(runtime) for runtime in response.get("agentRuntimes", [])]


def get_agent_runtime_quick_summary_by_name(client, agent_runtime_name: str) -> Optional[Dict[str, Any]]:
    """
    Get an AgentCore runtime's quick summary by its name.

    Args:
        client: The boto3 Bedrock Agent client.
        agent_runtime_name: The name of the AgentCore runtime.

    Returns:
        The quick summary dictionary of the AgentCore runtime if found, else None.
    """
    for runtime in list_agent_runtimes(client):
        if runtime.get("agent_runtime_name") == agent_runtime_name:
            return runtime
    return None


def get_agent_runtime_by_name(client, agent_runtime_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve detailed information for an AgentCore runtime by its name.

    Args:
        client: The boto3 Bedrock Agent client.
        agent_runtime_name: The name of the AgentCore runtime.

    Returns:
        The detailed dictionary of the AgentCore runtime if found, else None.
    """
    runtime_quick_summary: Optional[Dict[str, Any]] = get_agent_runtime_quick_summary_by_name(
        client, agent_runtime_name
    )
    existing_runtime: Optional[Dict[str, Any]] = None
    if runtime_quick_summary:
        existing_runtime = get_agent_runtime_by_id(client, runtime_quick_summary["agent_runtime_id"])
    return existing_runtime


@AWSRetry.jittered_backoff(retries=10)
def get_agent_runtime_by_id(client, agent_runtime_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve detailed information for an AgentCore runtime by its ID.

    Args:
        client: The boto3 Bedrock Agent client.
        agent_runtime_id: The ID of the AgentCore runtime.

    Returns:
        The detailed dictionary of the AgentCore runtime if found, else None.
    """
    try:
        response = client.get_agent_runtime(agentRuntimeId=agent_runtime_id)
    except is_boto3_error_code("ResourceNotFoundException"):
        return None
    return camel_dict_to_snake_dict(response)


def _runtime_artifact(module: AnsibleAWSModule, existing_runtime: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generates agent runtime artifact dictionary based on the module inputs and existing runtime.

    Args:
        module: The AnsibleAWSModule instance.
        existing_runtime: The existing runtime configuration, if any.

    Returns:
        The agent runtime artifact dictionary.
    """
    artifact = dict()
    if module.params.get("container_configuration") is not None:
        artifact["container_configuration"] = module.params["container_configuration"]
    elif module.params.get("code_configuration") is not None:
        artifact["code_configuration"] = module.params["code_configuration"]
    elif existing_runtime:
        artifact = existing_runtime.get("agent_runtime_artifact", dict())
    return artifact


def _runtime_parameters(
    module: AnsibleAWSModule,
    existing_runtime: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generates parameters for an AgentCore runtime based on the module inputs and existing runtime.

    Args:
        module: The AnsibleAWSModule instance.
        existing_runtime: The existing runtime configuration, if any.

    Returns:
        A dictionary of parameters for the AgentCore runtime.
    """
    params: Dict[str, Any] = dict(
        agent_runtime_artifact=_runtime_artifact(module, existing_runtime),
        role_arn=module.params.get("role_arn") or (existing_runtime or dict()).get("role_arn"),
    )
    if module.params.get("tags"):
        params["tags"] = module.params.get("tags")
    network_mode = module.params.get("network_mode")
    if network_mode:
        params["network_configuration"] = dict(network_mode=network_mode)
        if network_mode == "VPC":
            params["network_configuration"]["network_mode_config"] = dict(
                security_groups=module.params.get("network_security_groups"),
                subnets=module.params.get("network_subnets"),
            )

    if module.params.get("description") is not None:
        params["description"] = module.params["description"]
    if module.params.get("protocol"):
        params["protocol_configuration"] = dict(server_protocol=module.params["protocol"])
    lifecycle_configuration = scrub_none_parameters(
        dict(
            idle_runtime_session_timeout=module.params.get("idle_runtime_session_timeout"),
            max_lifetime=module.params.get("max_lifetime"),
        )
    )
    if lifecycle_configuration:
        params["lifecycle_configuration"] = lifecycle_configuration

    if module.params.get("environment_variables"):
        params["environment_variables"] = module.params["environment_variables"]
    if module.params.get("authorizer_discovery_url"):
        params["authorizer_configuration"] = dict(
            custom_jwt_authorizer=dict(
                discovery_url=module.params["authorizer_discovery_url"],
                allowed_audience=module.params.get("authorizer_allowed_audience"),
                allowed_clients=module.params.get("authorizer_allowed_clients"),
                allowed_scopes=module.params.get("authorizer_allowed_scopes"),
            )
        )
    if module.params.get("capacity_provider_arn"):
        params["capacity_provider_configuration"] = dict(capacity_provider_arn=module.params["capacity_provider_arn"])
    if module.params.get("session_storage"):
        params["filesystem_configurations"] = [dict(session_storage=module.params["session_storage"])]
    elif module.params.get("s3_files_access_point"):
        params["filesystem_configurations"] = [dict(s3_files_access_point=module.params["s3_files_access_point"])]
    elif module.params.get("efs_access_point"):
        params["filesystem_configurations"] = [dict(efs_access_point=module.params["efs_access_point"])]
    elif module.params.get("capacity_provider_volume"):
        params["filesystem_configurations"] = [
            dict(capacity_provider_volume=module.params["capacity_provider_volume"])
        ]
    return snake_dict_to_camel_dict(scrub_none_parameters(params))


def _runtime_update_needed(module: AnsibleAWSModule, existing_runtime: Dict[str, Any]) -> bool:
    """
    Determines if an update to the agent runtime is needed based on the desired and existing configurations.

    Args:
        module: The AnsibleAWSModule instance.
        existing_runtime: The existing runtime configuration.

    Returns:
        True if an update is needed, False otherwise.
    """
    desired: Dict[str, Any] = _runtime_parameters(module, existing_runtime)
    current = dict(
        agentRuntimeArtifact=existing_runtime.get("agent_runtime_artifact"),
        roleArn=existing_runtime.get("role_arn"),
        networkConfiguration=existing_runtime.get("network_configuration"),
        description=existing_runtime.get("description"),
        protocolConfiguration=existing_runtime.get("protocol_configuration"),
        lifecycleConfiguration=existing_runtime.get("lifecycle_configuration"),
        environmentVariables=existing_runtime.get("environment_variables"),
        authorizerConfiguration=existing_runtime.get("authorizer_configuration"),
        capacityProviderConfiguration=existing_runtime.get("capacity_provider_configuration"),
        filesystemConfigurations=existing_runtime.get("filesystem_configurations"),
    )
    desired_values: Dict[str, Any] = {
        key: value for key, value in desired.items() if key in current and value is not None
    }
    return any(
        camel_dict_to_snake_dict({key: value}) != camel_dict_to_snake_dict({key: current[key]})
        for key, value in desired_values.items()
    )


def wait_for_agent_runtime_status(
    client,
    module: AnsibleAWSModule,
    agent_runtime_id: str,
    status: str,
    sleep_time: int = 5,
) -> None:
    """
    Wait for an Amazon Bedrock Agent Runtime to reach a specific status.

    This function polls the Bedrock Agent Runtime at fixed intervals until it either
    reaches the desired `status` or the configured timeout expires.

    Behavior:
        - Uses `client.get_agent_runtime()` to retrieve the agent runtime's current status.
        - Waits `sleep_time` seconds between each polling attempt.
        - Stops early if the agent runtime reaches the desired status or is deleted
          while waiting for the "DELETED" state.
        - Fails the Ansible module gracefully if the timeout expires.

    Args:
        client: A boto3 Bedrock Agent client instance.
        module: The current Ansible module object, used for error reporting
                and accessing parameters (specifically `wait_timeout`).
        agent_runtime_id (str): The unique identifier of the Bedrock Agent runtime to monitor.
        status (str): The target agent status to wait for
                      (e.g., "PREPARED", "DELETED").
        sleep_time (int, optional): Number of seconds to sleep between polling
                                    attempts. Defaults to 5 seconds.

    Raises:
        ClientError: If AWS returns an unexpected error during polling.
        TimeoutError: If the agent runtime does not reach the target status before
                      the timeout expires.
    """
    wait_timeout = module.params.get("wait_timeout", 600)
    max_attempts = max(1, wait_timeout // sleep_time)
    current_status = None

    for attempt in range(max_attempts):
        runtime = get_agent_runtime_by_id(client, agent_runtime_id)
        if runtime is None:
            if status == "DELETED":
                return
            module.fail_json(msg=f"Agent runtime {agent_runtime_id} was not found while waiting for status '{status}'.")

        current_status = runtime.get("status")
        if current_status == status:
            return
        if current_status in {"CREATE_FAILED", "UPDATE_FAILED"}:
            module.fail_json(
                msg=f"Agent runtime {agent_runtime_id} failed with status '{current_status}': "
                f"{runtime.get('failure_reason', 'Unknown failure reason')}."
            )
        if attempt < max_attempts - 1:
            time.sleep(sleep_time)

    module.fail_json(
        msg=f"Timeout waiting for agent runtime {agent_runtime_id} to reach status '{status}'. "
        f"Last known status: '{current_status}'."
    )


def create_agent_runtime(module: AnsibleAWSModule, client) -> Tuple[bool, Optional[str], str]:
    """
    Creates a new agent runtime if not in check_mode, otherwise simulates creation.

    Args:
        module: The AnsibleAWSModule instance.
        client: boto3 bedrock-agent client.

    Returns:
        (changed, agent_runtime_id, message)
    """
    name: str = module.params["agent_runtime_name"]
    if module.check_mode:
        return True, None, f"Check mode: would have created agent runtime {name}."

    params: Dict[str, Any] = _runtime_parameters(module)
    params["agentRuntimeName"] = name
    response = client.create_agent_runtime(**params)
    agent_runtime_id = response.get("agentRuntimeId")
    # User has an option to wait for the runtime to be ready, default is True
    if module.params.get("wait", True):
        wait_for_agent_runtime_status(client, module, agent_runtime_id, "READY")
    return True, agent_runtime_id, f"Agent runtime {name} created successfully."


def update_agent_runtime(
    module: AnsibleAWSModule,
    client,
    existing_runtime: Dict[str, Any],
) -> Tuple[bool, Optional[str], str]:
    """
    Updates an existing agent runtime if not in check_mode, otherwise simulates the update.

    Args:
        module: The AnsibleAWSModule instance.
        client: boto3 bedrock-agent client.
        existing_runtime: The existing runtime configuration.

    Returns:
        (changed, agent_runtime_id, message)
    """
    agent_runtime_id = existing_runtime["agent_runtime_id"]
    if not _runtime_update_needed(module, existing_runtime):
        return False, agent_runtime_id, "No updates needed."
    if module.check_mode:
        return (
            True,
            agent_runtime_id,
            f"Check mode: would have updated agent runtime {existing_runtime['agent_runtime_name']}.",
        )

    params = _runtime_parameters(module, existing_runtime)
    params["agentRuntimeId"] = agent_runtime_id
    response = client.update_agent_runtime(**params)
    updated_id = response.get("agentRuntimeId", agent_runtime_id)
    # User has an option to wait for the runtime to be ready, default is True
    if module.params.get("wait", True):
        wait_for_agent_runtime_status(client, module, updated_id, "READY")
    return True, updated_id, f"Agent runtime {existing_runtime['agent_runtime_name']} updated successfully."


def delete_agent_runtime(module: AnsibleAWSModule, client, existing_runtime: Dict[str, Any]) -> Tuple[bool, str]:
    name = existing_runtime["agent_runtime_name"]
    if module.check_mode:
        return True, f"Check mode: would have deleted agent runtime '{name}'."

    client.delete_agent_runtime(agentRuntimeId=existing_runtime["agent_runtime_id"])
    # User has an option to wait for the runtime to be deleted, default is True
    if module.params.get("wait", True):
        wait_for_agent_runtime_status(client, module, existing_runtime["agent_runtime_id"], "DELETED")
    return True, f"Agent runtime {name} deleted successfully."
