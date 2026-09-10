# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


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
