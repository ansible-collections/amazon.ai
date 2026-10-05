# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

try:
    from botocore.exceptions import WaiterError
except ImportError:
    pass

from ansible_collections.amazon.ai.plugins.module_utils.waiters import wait_for_model_package_group_deletion

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_message
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


class NotebookInstanceStatus(str, Enum):
    DELETED = "Deleted"
    PENDING = "Pending"
    IN_SERVICE = "InService"
    STOPPING = "Stopping"
    STOPPED = "Stopped"
    FAILED = "Failed"
    DELETING = "Deleting"
    UPDATING = "Updating"
    PENDING_MAINTENANCE = "PendingMaintenance"
    IN_MAINTENANCE = "InMaintenance"


@AWSRetry.jittered_backoff(retries=10)
def list_tags(client, resource_arn: str) -> Dict[str, str]:
    paginator = client.get_paginator("list_tags")
    tags = paginator.paginate(ResourceArn=resource_arn).build_full_result()["Tags"]
    return {t["Key"]: t["Value"] for t in tags}


def _build_model_params(module) -> Dict[str, Any]:
    """
    Build the boto3 CreateModel request parameters from module params.

    Args:
        module: The Ansible module instance.

    Returns:
        A dictionary suitable for client.create_model().
    """
    params: Dict[str, Any] = {
        field: module.params.get(field)
        for field in (
            "model_name",
            "primary_container",
            "execution_role_arn",
            "vpc_config",
            "enable_network_isolation",
        )
    }
    tags: Optional[Dict[str, str]] = module.params.get("tags")
    if tags is not None:
        params["tags"] = [{"key": key, "value": value} for key, value in tags.items()]

    model_params = snake_dict_to_camel_dict(scrub_none_parameters(params), capitalize_first=True)
    return model_params


@AWSRetry.jittered_backoff(retries=10)
def describe_code_repository(client, repository_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve details for a specific SageMaker Code Repository.

    Args:
        client: The boto3 SageMaker client.
        repository_name: The name of the code repository.

    Returns:
        A dictionary with the code repository details if found, otherwise None.

    Raises:
        ClientError: If AWS returns an error other than 'ValidationException'.
    """
    try:
        return client.describe_code_repository(CodeRepositoryName=repository_name)
    except is_boto3_error_code("ValidationException"):
        return None


@AWSRetry.jittered_backoff(retries=10)
def list_code_repositories(client, **params: Any) -> List[Dict[str, Any]]:
    """
    Retrieve a list of SageMaker Code Repositories using pagination.

    Args:
        client: The boto3 SageMaker client.
        **params: Additional filter parameters for the list operation.

    Returns:
        A list of code repository summary dictionaries.
    """
    paginator = client.get_paginator("list_code_repositories")
    return paginator.paginate(**params).build_full_result()["CodeRepositorySummaryList"]


@AWSRetry.jittered_backoff(retries=10)
def describe_image(client, image_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve details for a specific SageMaker Image.

    Args:
        client: The boto3 SageMaker client.
        image_name: The name of the SageMaker Image.

    Returns:
        A dictionary with the image details if found, otherwise None.

    Raises:
        ClientError: If AWS returns an error other than 'ResourceNotFound'.
    """
    try:
        return client.describe_image(ImageName=image_name)
    except is_boto3_error_code("ResourceNotFound"):
        return None


@AWSRetry.jittered_backoff(retries=10)
def list_images(client, **params: Any) -> List[Dict[str, Any]]:
    """
    Retrieve a list of SageMaker Images using pagination.

    Args:
        client: The boto3 SageMaker client.
        **params: Additional filter parameters for the list operation.

    Returns:
        A list of image summary dictionaries.
    """
    paginator = client.get_paginator("list_images")
    return paginator.paginate(**params).build_full_result()["Images"]


@AWSRetry.jittered_backoff(retries=10)
def describe_notebook_instance(client, notebook_instance_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve details for a specific SageMaker notebook instance.
    Args:
        client: The boto3 SageMaker client.
        notebook_instance_name: The name of the SageMaker notebook instance.

    Returns:
        A dictionary with the notebook instance details if found, otherwise None.

    Raises:
        ClientError: If AWS returns an error other than 'ValidationException' or 'RecordNotFound'.
    """
    try:
        return client.describe_notebook_instance(NotebookInstanceName=notebook_instance_name)
    except is_boto3_error_code("ValidationException") as e:
        if "RecordNotFound" in e.response["Error"].get("Message", ""):
            return None
        raise


@AWSRetry.jittered_backoff(retries=10)
def list_notebook_instances(client, **params: Any) -> List[Dict[str, Any]]:
    """
    Retrieve a list of SageMaker notebook instances, limited to the name filter used by the collection.

    Args:
        client: The boto3 SageMaker client.
        **params: Additional filter parameters for the list operation.

    Returns:
        A list of notebook instance summary dictionaries.
    """
    paginator = client.get_paginator("list_notebook_instances")
    filtered_params = {key: value for key, value in params.items() if key in {"NameContains"}}
    return paginator.paginate(**filtered_params).build_full_result()["NotebookInstances"]


def notebook_instance_params(module) -> Dict[str, Any]:
    """
    Build the boto3 Create/Update NotebookInstance request parameters from module params.

    Args:
        module: The Ansible module containing the desired state.

    Returns:
        A dictionary of parameters suitable for the boto3 Create/Update NotebookInstance call.
    """
    values = {
        field: module.params.get(field)
        for field in (
            "notebook_instance_name",
            "instance_type",
            "role_arn",
            "subnet_id",
            "security_groups",
            "volume_size_in_gb",
            "direct_internet_access",
            "kms_key_id",
            "lifecycle_config_name",
            "default_code_repository",
            "additional_code_repositories",
            "root_access",
            "platform_identifier",
            "ip_address_type",
        )
    }
    params = snake_dict_to_camel_dict(scrub_none_parameters(values), capitalize_first=True)
    if "VolumeSizeInGb" in params:
        params["VolumeSizeInGB"] = params.pop("VolumeSizeInGb")
    if "SecurityGroups" in params:
        params["SecurityGroupIds"] = params.pop("SecurityGroups")
    if module.params.get("tags") is not None:
        params["Tags"] = ansible_dict_to_boto3_tag_list(module.params["tags"])
    return params


def notebook_instance_immutable_parameters_needs_replacement(existing_notebook: Dict[str, Any], module) -> bool:
    """
    Determine whether an existing notebook instance has immutable parameter drift.
    Args:
        existing_notebook: The existing notebook instance parameters.
        module: The Ansible module containing the desired state.

    Returns:
        True if there are immutable parameter drifts, False otherwise.
    """
    existing_params = camel_dict_to_snake_dict(existing_notebook)
    replacement_fields = (
        "subnet_id",
        "security_groups",
        "direct_internet_access",
        "kms_key_id",
        "root_access",
        "platform_identifier",
    )
    differing_fields = []
    for field in replacement_fields:
        desired_value = module.params.get(field)
        if desired_value is None:
            continue
        existing_value = existing_params.get(field)
        if field == "security_groups":
            if set(desired_value) != set(existing_value or []):
                differing_fields.append(field)
        elif desired_value != existing_value:
            differing_fields.append(field)
    return bool(differing_fields)


def notebook_instance_update_params(existing_notebook: Dict[str, Any], module) -> Dict[str, Any]:
    """
    Build an explicit UpdateNotebookInstance request for mutable drift.
    Args:
        existing_notebook: The existing notebook instance parameters.
        module: The Ansible module containing the desired state.

    Returns:
        A dictionary of parameters to update for the notebook instance.
    """
    existing_params = camel_dict_to_snake_dict(existing_notebook)
    existing_params["lifecycle_config_name"] = existing_params.get("notebook_instance_lifecycle_config_name")
    desired_fields = (
        "instance_type",
        "role_arn",
        "volume_size_in_gb",
        "lifecycle_config_name",
        "default_code_repository",
        "additional_code_repositories",
        "ip_address_type",
    )
    values: Dict[str, Any] = {"notebook_instance_name": module.params["notebook_instance_name"]}
    disassociation_fields = {
        "lifecycle_config_name": "disassociate_lifecycle_config",
        "default_code_repository": "disassociate_default_code_repository",
        "additional_code_repositories": "disassociate_additional_code_repositories",
    }
    for field in desired_fields:
        desired_value = module.params.get(field)
        existing_value = existing_params.get(field)
        if field == "volume_size_in_gb" and desired_value is not None and existing_value is not None:
            if desired_value < existing_value:
                module.fail_json(
                    msg=(
                        "Notebook instance volume_size_in_gb cannot be reduced in place; "
                        "create a replacement instance with the desired volume size."
                    )
                )
        if desired_value is None or desired_value == []:
            if existing_value:
                values[disassociation_fields[field]] = True
            continue
        if field == "additional_code_repositories":
            if set(desired_value) != set(existing_value or []):
                values[field] = desired_value
        elif desired_value != existing_value:
            values[field] = desired_value
    params = snake_dict_to_camel_dict(scrub_none_parameters(values), capitalize_first=True)
    if "VolumeSizeInGb" in params:
        params["VolumeSizeInGB"] = params.pop("VolumeSizeInGb")
    return params


def notebook_instance_needs_update(existing_notebook: Dict[str, Any], module) -> (bool, Dict[str, Any]):
    """
    Determine whether mutable notebook instance properties differ.

    Args:
        existing_notebook: The existing notebook instance parameters.
        module: The Ansible module object.

    Returns:
        A tuple where the first element is True if the notebook instance needs an update.
        False otherwise, and the second element is the dictionary of update parameters.
    """
    params = notebook_instance_update_params(existing_notebook, module)
    return len(params) > 1, params


def _notebook_instance_waiter_name(status: str) -> str:
    return {
        "InService": "notebook_instance_in_service",
        "Stopped": "notebook_instance_stopped",
        "Deleted": "notebook_instance_deleted",
    }[status]


def wait_for_notebook_instance_status(client, module, status: str) -> None:
    """
    Wait for a notebook instance status using SageMaker's botocore waiter.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module object.
        status: The desired notebook instance status to wait for.
    """
    if module.check_mode:
        return

    name = module.params["notebook_instance_name"]
    wait_timeout = module.params.get("wait_timeout", 600)
    delay = min(30, max(1, wait_timeout))
    waiter = client.get_waiter(_notebook_instance_waiter_name(status))
    try:
        waiter.wait(
            NotebookInstanceName=name,
            WaiterConfig=dict(Delay=delay, MaxAttempts=max(1, wait_timeout // delay)),
        )
    except WaiterError as e:
        failure_reason = ""
        if status != "Deleted":
            instance = describe_notebook_instance(client, name)
            if instance:
                failure_reason = instance.get("FailureReason", "")
        module.fail_json(msg=f"Error waiting for notebook instance {name} to reach {status}: {failure_reason or e}")


@AWSRetry.jittered_backoff(retries=10)
def _call_create_notebook_instance(client, module) -> None:
    """
    Internal helper to call the create_notebook_instance function.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module object.
    """
    client.create_notebook_instance(**notebook_instance_params(module))


def create_notebook_instance(client, module) -> None:
    """
    Create a SageMaker notebook instance.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module object.
    """
    if module.check_mode:
        return
    _call_create_notebook_instance(client, module)
    if module.params.get("wait", False):
        wait_for_notebook_instance_status(client, module, NotebookInstanceStatus.IN_SERVICE)


@AWSRetry.jittered_backoff(retries=10)
def _call_update_notebook_instance(client, params) -> None:
    """
    Internal helper to call the update_notebook_instance function.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module object.
        params: The parameters to update.
    """
    client.update_notebook_instance(**params)


def update_notebook_instance(client, module, existing: Dict[str, Any], params: Dict[str, Any]) -> None:
    """
    Update mutable notebook instance properties, stopping and restoring notebook as needed.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module object.
        existing: The existing notebook instance details.
        params: The parameters to update.
    """
    if len(params) == 1 or module.check_mode:
        return

    was_running = existing.get("NotebookInstanceStatus") == NotebookInstanceStatus.IN_SERVICE
    name = existing["NotebookInstanceName"]
    if existing.get("NotebookInstanceStatus") != NotebookInstanceStatus.STOPPED:
        # Notebook has to be in Stopped state before updating
        stop_notebook_instance(client, module)
    _call_update_notebook_instance(client, params)
    if module.params.get("wait", False):
        wait_for_notebook_instance_status(client, module, NotebookInstanceStatus.STOPPED)
    updated_existing = describe_notebook_instance(client, name)
    if was_running and updated_existing.get("NotebookInstanceStatus") == NotebookInstanceStatus.STOPPED:
        # Restore the notebook to its previous running state
        start_notebook_instance(client, module)


@AWSRetry.jittered_backoff(retries=10)
def _call_start_notebook_instance(client, module) -> None:
    """
    Internal helper to call the start_notebook_instance function.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module object.
    """
    client.start_notebook_instance(NotebookInstanceName=module.params["notebook_instance_name"])


def start_notebook_instance(client, module, wait_for_start=True) -> None:
    """
    Start a stopped SageMaker notebook instance.
    This operation will transition the notebook instance to the IN_SERVICE state.
    The wait behavior can be controlled using the `wait_for_start` parameter.
    There are instances when wait to start is required even if user chooses not to wait by default.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module object.
        wait_for_start: Whether to wait for the notebook instance to reach the IN_SERVICE state.
    """
    if module.check_mode:
        return
    _call_start_notebook_instance(client, module)
    if wait_for_start:
        wait_for_notebook_instance_status(client, module, NotebookInstanceStatus.IN_SERVICE)


@AWSRetry.jittered_backoff(retries=10)
def _call_stop_notebook_instance(client, module) -> None:
    """
    Internal helper to call the stop_notebook_instance function.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module object.
    """
    client.stop_notebook_instance(NotebookInstanceName=module.params["notebook_instance_name"])


def stop_notebook_instance(client, module, wait_for_stop=True) -> None:
    """
    Stop a running SageMaker notebook instance.
    This operation will transition the notebook instance to the STOPPED state.
    The wait behavior can be controlled using the `wait_for_stop` parameter.
    There are instances when wait to stop is required even if user chooses not to wait by default.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module object.
        wait_for_stop: Whether to wait for the notebook instance to reach the STOPPED state.
    """
    if module.check_mode:
        return
    _call_stop_notebook_instance(client, module)
    if wait_for_stop:
        wait_for_notebook_instance_status(client, module, NotebookInstanceStatus.STOPPED)


def reconcile_notebook_instance_tags(client, module, existing: Dict[str, Any]) -> bool:
    """
    Reconcile notebook instance tags, honoring purge_tags and check mode.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module object.
        existing: The existing notebook instance details.

    Returns:
        bool: True if any tags were added or removed, False otherwise.
    """
    desired_tags = module.params.get("tags")
    if desired_tags is None:
        return False
    current_tags = list_tags(client, existing["NotebookInstanceArn"])
    tags_to_add, tags_to_remove = compare_aws_tags(current_tags, desired_tags, module.params.get("purge_tags", True))
    if module.check_mode:
        return bool(tags_to_add or tags_to_remove)
    if tags_to_add:
        client.add_tags(
            ResourceArn=existing["NotebookInstanceArn"],
            Tags=ansible_dict_to_boto3_tag_list(tags_to_add),
        )
    if tags_to_remove:
        client.delete_tags(ResourceArn=existing["NotebookInstanceArn"], TagKeys=tags_to_remove)
    return bool(tags_to_add or tags_to_remove)


@AWSRetry.jittered_backoff(retries=10)
def _call_delete_notebook_instance(client, module) -> None:
    """
    Internal helper to call the delete_notebook_instance function.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module object.
    """
    client.delete_notebook_instance(NotebookInstanceName=module.params["notebook_instance_name"])


def delete_notebook_instance(client, module, existing: Dict[str, Any]) -> None:
    """
    Stop and delete a SageMaker notebook instance.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module instance.
        existing: The existing notebook instance details.
    """
    if module.check_mode:
        return
    name = module.params["notebook_instance_name"]
    status = existing.get("NotebookInstanceStatus")
    if status == NotebookInstanceStatus.DELETING:
        if module.params.get("wait", False):
            wait_for_notebook_instance_status(client, module, NotebookInstanceStatus.DELETED)
        return
    if status != NotebookInstanceStatus.STOPPED:
        # Notebook has to be in Stopped state before deletion
        stop_notebook_instance(client, module)
    _call_delete_notebook_instance(client, module)
    if module.params.get("wait", False):
        wait_for_notebook_instance_status(client, module, NotebookInstanceStatus.DELETED)


@AWSRetry.jittered_backoff(retries=10)
def describe_model(client, model_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve details for a specific SageMaker model.

    Args:
        client: The boto3 SageMaker client.
        model_name: The name of the model.

    Returns:
        A dictionary with the model details if found, otherwise None.
    """
    try:
        return client.describe_model(ModelName=model_name)
    except is_boto3_error_code("ValidationException") as e:
        # DescribeModel does not raise a dedicated not-found error; AWS returns a generic
        # ValidationException with a "Could not find model" message instead.
        if "Could not find model" in e.response["Error"].get("Message", ""):
            return None
        raise


@AWSRetry.jittered_backoff(retries=10)
def list_models(client, **params: Any) -> List[Dict[str, Any]]:
    """
    Retrieve a list of SageMaker models.

    Args:
        client: The boto3 SageMaker client.
        **params: Additional filter parameters for the list operation.

    Returns:
        A list of model summary dictionaries.
    """
    paginate_params: Dict[str, Any] = dict(params)
    max_results = paginate_params.pop("MaxResults", None)
    paginator = client.get_paginator("list_models")
    if max_results is not None:
        return paginator.paginate(**paginate_params, PaginationConfig={"MaxItems": max_results}).build_full_result()[
            "Models"
        ]
    return paginator.paginate(**paginate_params).build_full_result()["Models"]


@AWSRetry.jittered_backoff(retries=10)
def describe_model_package_group(client, model_package_group_name: str) -> Optional[Dict[str, Any]]:
    """Retrieve details for a specific SageMaker model package group."""
    try:
        return client.describe_model_package_group(ModelPackageGroupName=model_package_group_name)
    except is_boto3_error_code("ValidationException") as e:
        message = e.response["Error"].get("Message", "")
        if "does not exist" in message or "not found" in message:
            return None
        raise


@AWSRetry.jittered_backoff(retries=10)
def list_model_package_groups(client, max_items: Optional[int] = None, **params: Any) -> List[Dict[str, Any]]:
    """Retrieve a list of SageMaker model package groups."""
    paginator = client.get_paginator("list_model_package_groups")
    if max_items is not None:
        return paginator.paginate(**params, PaginationConfig={"MaxItems": max_items}).build_full_result()[
            "ModelPackageGroupSummaryList"
        ]
    return paginator.paginate(**params).build_full_result()["ModelPackageGroupSummaryList"]


def _build_model_package_group_params(module) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        field: module.params.get(field) for field in ("model_package_group_name", "model_package_group_description")
    }
    tags: Optional[Dict[str, str]] = module.params.get("tags")
    if tags is not None:
        params["tags"] = ansible_dict_to_boto3_tag_list(tags)
    return snake_dict_to_camel_dict(scrub_none_parameters(params), capitalize_first=True)


def create_model_package_group(client, module) -> Tuple[bool, str]:
    """Create a SageMaker model package group."""
    name = module.params["model_package_group_name"]
    if module.check_mode:
        return True, f"Check mode: would have created model package group {name}."

    client.create_model_package_group(**_build_model_package_group_params(module))
    return True, f"Model package group {name} created successfully."


def model_package_group_needs_update(existing: Dict[str, Any], module) -> bool:
    """Determine whether a model package group description drift requires replacement."""
    desired_description = module.params.get("model_package_group_description")
    if desired_description is not None and existing.get("ModelPackageGroupDescription") != desired_description:
        return True
    return False


def delete_model_package_group(client, module) -> Tuple[bool, str]:
    """Delete a SageMaker model package group."""
    name = module.params["model_package_group_name"]
    if module.check_mode:
        return True, f"Check mode: would have deleted model package group {name}."

    client.delete_model_package_group(ModelPackageGroupName=name)
    wait_timeout: int = module.params.get("wait_timeout", 600)
    if module.params.get("wait", True):
        wait_for_model_package_group_deletion(client, module, name, wait_timeout=wait_timeout)
    return True, f"Model package group {name} deleted successfully."


def update_model_package_group_tags(
    client, module, model_package_group_arn: str, desired_tags: Dict[str, str], purge_tags: bool = True
) -> Tuple[bool, str]:
    """Reconcile SageMaker model package group tags in place."""
    current_tags: Dict[str, str] = list_tags(client, model_package_group_arn)
    tags_to_add, tags_to_remove = compare_aws_tags(current_tags, desired_tags, purge_tags)

    if not tags_to_add and not tags_to_remove:
        return False, "No updates needed."

    if module.check_mode:
        return True, "Check mode: would have updated model package group tags."

    if tags_to_add:
        client.add_tags(
            ResourceArn=model_package_group_arn,
            Tags=ansible_dict_to_boto3_tag_list(tags_to_add),
        )
    if tags_to_remove:
        client.delete_tags(ResourceArn=model_package_group_arn, TagKeys=tags_to_remove)

    return True, "Model package group tags updated successfully."


@AWSRetry.jittered_backoff(retries=10)
def create_model(client, module) -> Tuple[bool, str]:
    """
    Create a SageMaker model.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module instance.

    Returns:
        A tuple of changed state and message.
    """
    model_name = module.params["model_name"]
    if module.check_mode:
        return True, f"Check mode: would have created model {model_name}."

    client.create_model(**_build_model_params(module))
    return True, f"Model {model_name} created successfully."


def _model_data_s3_uri(container: Dict[str, Any]) -> Optional[str]:
    model_data_url = container.get("ModelDataUrl")
    if model_data_url is not None:
        return model_data_url

    return container.get("ModelDataSource", {}).get("S3DataSource", {}).get("S3Uri")


def _vpc_config_differs(desired: Dict[str, Any], existing: Dict[str, Any]) -> bool:
    for key in ("Subnets", "SecurityGroupIds"):
        if set(desired.get(key) or []) != set(existing.get(key) or []):
            return True

    return False


def model_needs_replacement(existing: Dict[str, Any], module) -> bool:
    """
    Determine whether an existing SageMaker model differs from the desired state in a
    create-only field, and therefore requires replacement.

    Args:
        existing: The raw (camelCase) response from describe_model().
        module: The Ansible module instance.

    Returns:
        True if primary_container, execution_role_arn, vpc_config or enable_network_isolation differ.
    """
    desired: Dict[str, Any] = _build_model_params(module)

    if desired.get("ExecutionRoleArn") is not None and existing.get("ExecutionRoleArn") != desired.get(
        "ExecutionRoleArn"
    ):
        return True

    if desired.get("VpcConfig") is not None and _vpc_config_differs(
        desired["VpcConfig"], existing.get("VpcConfig", {})
    ):
        return True

    if desired.get("EnableNetworkIsolation") is not None and bool(existing.get("EnableNetworkIsolation")) != bool(
        desired.get("EnableNetworkIsolation")
    ):
        return True

    desired_container: Dict[str, Any] = desired.get("PrimaryContainer", {})
    existing_container: Dict[str, Any] = existing.get("PrimaryContainer", {})

    for key, value in desired_container.items():
        if key in ("ModelDataUrl", "ModelDataSource"):
            continue
        existing_value = existing_container.get(key)
        if value == {} and existing_value is None:
            continue
        if existing_value != value:
            return True

    desired_s3 = _model_data_s3_uri(desired_container)
    if desired_s3 is not None and desired_s3 != _model_data_s3_uri(existing_container):
        return True

    return False


@AWSRetry.jittered_backoff(retries=10)
def delete_model(client, module) -> Tuple[bool, str]:
    """
    Delete a SageMaker model.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module instance.

    Returns:
        A tuple of changed state and message.
    """
    model_name: str = module.params["model_name"]
    if module.check_mode:
        return True, f"Check mode: would have deleted model {model_name}."

    client.delete_model(ModelName=model_name)
    return True, f"Model {model_name} deleted successfully."


@AWSRetry.jittered_backoff(retries=10)
def update_model_tags(
    client, module, model_arn: str, desired_tags: Dict[str, str], purge_tags: bool = True
) -> Tuple[bool, str]:
    """
    Reconcile SageMaker model tags in place.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module instance.
        model_arn: The ARN of the model.
        desired_tags: The desired tag map.
        purge_tags: Whether tags omitted from desired_tags should be removed.

    Returns:
        A tuple of changed state and message.
    """
    current_tags: Dict[str, str] = list_tags(client, model_arn)

    tags_to_add: Dict[str, str] = {key: value for key, value in desired_tags.items() if current_tags.get(key) != value}
    tags_to_remove: List[str] = [key for key in current_tags if key not in desired_tags] if purge_tags else []

    if not tags_to_add and not tags_to_remove:
        return False, "No updates needed."

    if module.check_mode:
        return True, "Check mode: would have updated model tags."

    if tags_to_add:
        client.add_tags(
            ResourceArn=model_arn,
            Tags=[{"Key": key, "Value": value} for key, value in tags_to_add.items()],
        )
    if tags_to_remove:
        client.delete_tags(ResourceArn=model_arn, TagKeys=tags_to_remove)

    return True, "Model tags updated successfully."


@AWSRetry.jittered_backoff(retries=10)
def describe_endpoint_config(client, endpoint_config_name: str) -> Optional[Dict[str, Any]]:
    try:
        return client.describe_endpoint_config(EndpointConfigName=endpoint_config_name)
    except is_boto3_error_message("Could not find endpoint configuration"):
        # DescribeEndpointConfig has no dedicated not-found error; AWS returns a generic
        # ValidationException whose message reports the missing endpoint configuration.
        return None


@AWSRetry.jittered_backoff(retries=10)
def list_endpoint_configs(client, **params: Any) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("list_endpoint_configs")
    max_results = params.pop("MaxResults", None)
    if max_results is not None:
        params["PaginationConfig"] = dict(MaxItems=max_results)
    return paginator.paginate(**params).build_full_result()["EndpointConfigs"]


def endpoint_config_params(module) -> Dict[str, Any]:
    values = {
        field: module.params.get(field)
        for field in (
            "endpoint_config_name",
            "production_variants",
            "data_capture_config",
            "tags",
            "kms_key_id",
            "async_inference_config",
            "explainer_config",
            "shadow_production_variants",
            "execution_role_arn",
            "vpc_config",
            "enable_network_isolation",
            "metrics_config",
        )
    }
    return snake_dict_to_camel_dict(scrub_none_parameters(values), capitalize_first=True)


def _variants_differ(desired_variants: List[Dict[str, Any]], existing_variants: Any) -> bool:
    if not isinstance(existing_variants, list) or len(desired_variants) != len(existing_variants):
        return True
    existing_by_name = {variant.get("VariantName"): variant for variant in existing_variants}
    for desired_variant in desired_variants:
        variant_name = desired_variant.get("VariantName")
        if variant_name not in existing_by_name or _mapping_differs(desired_variant, existing_by_name[variant_name]):
            return True
    return False


def _mapping_differs(desired: Dict[str, Any], existing: Dict[str, Any]) -> bool:
    for key, desired_value in desired.items():
        existing_value = existing.get(key)
        if isinstance(desired_value, dict):
            if not isinstance(existing_value, dict) or _mapping_differs(desired_value, existing_value):
                return True
        elif key == "EnableNetworkIsolation" and desired_value is False and existing_value is None:
            continue
        elif desired_value != existing_value:
            return True
    return False


def _endpoint_config_property_differs(key: str, desired_value: Any, existing: Dict[str, Any]) -> bool:
    existing_value = existing.get(key)
    if key in ("ProductionVariants", "ShadowProductionVariants"):
        return _variants_differ(desired_value, existing_value)
    if isinstance(desired_value, dict):
        return not isinstance(existing_value, dict) or _mapping_differs(desired_value, existing_value)
    if key == "EnableNetworkIsolation" and desired_value is False and existing_value is None:
        return False
    return desired_value != existing_value


def _endpoint_config_properties_differ(desired: Dict[str, Any], existing: Dict[str, Any]) -> bool:
    return any(
        _endpoint_config_property_differs(key, desired_value, existing)
        for key, desired_value in desired.items()
        if key not in ("EndpointConfigName", "Tags")
    )


@AWSRetry.jittered_backoff(retries=10)
def create_endpoint_config(client, module) -> None:
    params = endpoint_config_params(module)
    if "Tags" in params:
        params["Tags"] = ansible_dict_to_boto3_tag_list(module.params["tags"])
    client.create_endpoint_config(**params)


@AWSRetry.jittered_backoff(retries=10)
def delete_endpoint_config(client, endpoint_config_name: str) -> None:
    client.delete_endpoint_config(EndpointConfigName=endpoint_config_name)


def reconcile_endpoint_config_tags(client, module, existing: Dict[str, Any]) -> bool:
    if module.params.get("tags") is None:
        return False
    current_tags = list_tags(client, existing["EndpointConfigArn"])
    tags_to_add, tags_to_remove = compare_aws_tags(
        current_tags,
        module.params["tags"],
        module.params["purge_tags"],
    )
    if module.check_mode:
        return bool(tags_to_add or tags_to_remove)
    if tags_to_add:
        client.add_tags(ResourceArn=existing["EndpointConfigArn"], Tags=ansible_dict_to_boto3_tag_list(tags_to_add))
    if tags_to_remove:
        client.delete_tags(ResourceArn=existing["EndpointConfigArn"], TagKeys=tags_to_remove)
    return bool(tags_to_add or tags_to_remove)


@AWSRetry.jittered_backoff(retries=10)
def describe_endpoint(client, endpoint_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve details for a specific SageMaker endpoint.

    Args:
        client: The boto3 SageMaker client.
        endpoint_name: The name of the endpoint.

    Returns:
        A dictionary with the endpoint details if found, otherwise None.
    """
    try:
        return client.describe_endpoint(EndpointName=endpoint_name)
    except is_boto3_error_code("ValidationException") as e:
        # DescribeEndpoint has no dedicated not-found error; AWS returns a generic
        # ValidationException whose message reports the missing endpoint.
        if "Could not find endpoint" in e.response["Error"].get("Message", ""):
            return None
        raise


@AWSRetry.jittered_backoff(retries=10)
def list_endpoints(client, **params: Any) -> List[Dict[str, Any]]:
    """
    Retrieve a list of SageMaker endpoints using pagination.

    Args:
        client: The boto3 SageMaker client.
        **params: Filter, sort and pagination parameters for the list operation.

    Returns:
        A list of endpoint summary dictionaries.
    """
    paginator = client.get_paginator("list_endpoints")
    max_results = params.pop("MaxResults", None)
    if max_results is not None:
        params["PaginationConfig"] = dict(MaxItems=max_results)
    return paginator.paginate(**params).build_full_result()["Endpoints"]


def endpoint_params(module) -> Dict[str, Any]:
    """
    Build the boto3 endpoint request parameters (EndpointName, EndpointConfigName) from module params.

    Args:
        module: The Ansible module instance.

    Returns:
        A dictionary with PascalCase keys.
    """
    values = {field: module.params.get(field) for field in ("endpoint_name", "endpoint_config_name")}
    return snake_dict_to_camel_dict(scrub_none_parameters(values), capitalize_first=True)


def wait_for_endpoint(client, module, deleted: bool = False) -> None:
    """
    Wait for a SageMaker endpoint to reach a terminal state using a botocore waiter.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module instance (provides endpoint_name and wait_timeout).
        deleted: When True, wait for the endpoint to be deleted; otherwise wait for InService.
    """
    endpoint_name = module.params["endpoint_name"]
    wait_timeout = module.params["wait_timeout"]
    delay = min(30, wait_timeout)
    waiter = client.get_waiter("endpoint_deleted" if deleted else "endpoint_in_service")
    try:
        waiter.wait(
            EndpointName=endpoint_name,
            WaiterConfig=dict(Delay=delay, MaxAttempts=max(1, wait_timeout // delay)),
        )
    except WaiterError as e:
        reason = ""
        if not deleted:
            endpoint = describe_endpoint(client, endpoint_name)
            if endpoint:
                reason = endpoint.get("FailureReason", "")
        module.fail_json(msg=f"Error waiting for endpoint {endpoint_name} to reach the desired state: {reason or e}")


@AWSRetry.jittered_backoff(retries=10)
def create_endpoint(client, module) -> None:
    """
    Create a SageMaker endpoint.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module instance.
    """
    params = endpoint_params(module)
    if module.params.get("tags") is not None:
        params["Tags"] = ansible_dict_to_boto3_tag_list(module.params["tags"])
    client.create_endpoint(**params)


@AWSRetry.jittered_backoff(retries=10)
def update_endpoint(client, module) -> None:
    """
    Update a SageMaker endpoint in place by swapping its endpoint configuration.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module instance.
    """
    client.update_endpoint(
        EndpointName=module.params["endpoint_name"],
        EndpointConfigName=module.params["endpoint_config_name"],
    )


@AWSRetry.jittered_backoff(retries=10)
def delete_endpoint(client, module) -> None:
    """
    Delete a SageMaker endpoint.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module instance.
    """
    client.delete_endpoint(EndpointName=module.params["endpoint_name"])


def reconcile_endpoint_tags(client, module, existing: Dict[str, Any]) -> bool:
    """
    Reconcile SageMaker endpoint tags in place, honouring purge_tags.

    Args:
        client: The boto3 SageMaker client.
        module: The Ansible module instance.
        existing: The raw (camelCase) response from describe_endpoint().

    Returns:
        True if tags were (or would be, in check mode) changed.
    """
    if module.params.get("tags") is None:
        return False
    current_tags = list_tags(client, existing["EndpointArn"])
    tags_to_add, tags_to_remove = compare_aws_tags(
        current_tags,
        module.params["tags"],
        module.params["purge_tags"],
    )
    if module.check_mode:
        return bool(tags_to_add or tags_to_remove)
    if tags_to_add:
        client.add_tags(ResourceArn=existing["EndpointArn"], Tags=ansible_dict_to_boto3_tag_list(tags_to_add))
    if tags_to_remove:
        client.delete_tags(ResourceArn=existing["EndpointArn"], TagKeys=tags_to_remove)
    return bool(tags_to_add or tags_to_remove)
