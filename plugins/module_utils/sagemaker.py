# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import time
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

from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_message
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags
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


@AWSRetry.jittered_backoff(retries=10)
def describe_model_package(client, model_package_name: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
    """Retrieve details for a specific SageMaker model package."""
    try:
        request_kwargs: Dict[str, Any] = {"ModelPackageName": model_package_name}
        request_kwargs.update(kwargs)
        return client.describe_model_package(**request_kwargs)
    except (
        is_boto3_error_code("ResourceNotFound"),
        is_boto3_error_message("does not exist"),
        is_boto3_error_message("not found"),
    ):
        return None


@AWSRetry.jittered_backoff(retries=10)
def list_model_packages(client, **params: Any) -> List[Dict[str, Any]]:
    """Retrieve a list of SageMaker model packages."""
    paginate_params: Dict[str, Any] = dict(params)
    max_results = paginate_params.pop("MaxResults", None)
    paginator = client.get_paginator("list_model_packages")
    if max_results is not None:
        return paginator.paginate(**paginate_params, PaginationConfig={"MaxItems": max_results}).build_full_result()[
            "ModelPackageSummaryList"
        ]
    return paginator.paginate(**paginate_params).build_full_result()["ModelPackageSummaryList"]


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


def _fix_model_package_api_key_names(value: Any) -> Any:
    """Normalize AWS API key names for model package dictionaries."""
    if isinstance(value, dict):
        fixed: Dict[str, Any] = {}
        for key, nested_value in value.items():
            normalized_key = key
            # snake_dict_to_camel_dict cannot reproduce the API's MIME acronym from supported_response_mime_types.
            if key == "SupportedResponseMimeTypes":
                normalized_key = "SupportedResponseMIMETypes"
            fixed[normalized_key] = _fix_model_package_api_key_names(nested_value)
        return fixed
    if isinstance(value, list):
        return [_fix_model_package_api_key_names(item) for item in value]
    return value


def _preserve_custom_metadata_keys(value: Any) -> Any:
    """Preserve caller-defined customer metadata keys when converting AWS API payloads."""
    if isinstance(value, dict):
        return {key: _preserve_custom_metadata_keys(nested_value) for key, nested_value in value.items()}
    if isinstance(value, list):
        return [_preserve_custom_metadata_keys(item) for item in value]
    return value


def _model_package_values_match(actual: Any, desired: Any) -> bool:
    """Compare model package values after normalizing AWS key casing and ignoring AWS-only extras."""
    if actual is None and desired is None:
        return True
    if actual is None or desired is None:
        return False

    actual = _normalize_model_package_compare_value(actual)
    desired = _normalize_model_package_compare_value(desired)

    if isinstance(desired, dict):
        if not isinstance(actual, dict):
            return False
        for key, desired_value in desired.items():
            if key not in actual:
                return False
            if not _model_package_values_match(actual[key], desired_value):
                return False
        return True

    if isinstance(desired, list):
        if not isinstance(actual, list):
            return False
        if desired and all(isinstance(item, dict) for item in desired):
            if len(actual) != len(desired):
                return False
            matched_ids = set()
            for desired_item in desired:
                matched = False
                for index, actual_item in enumerate(actual):
                    if index in matched_ids:
                        continue
                    if _model_package_values_match(actual_item, desired_item):
                        matched_ids.add(index)
                        matched = True
                        break
                if not matched:
                    return False
            return True

        def key_func(item) -> str:
            return json.dumps(item, sort_keys=True, separators=(",", ":"))

        return sorted(actual, key=key_func) == sorted(desired, key=key_func)

    return actual == desired


def _normalize_model_package_compare_value(value: Any) -> Any:
    """Normalize user-supplied model package values to the AWS API shape for comparisons."""
    if value is None:
        return None
    if isinstance(value, dict):
        if "CustomerMetadataProperties" in value:
            preserved = _preserve_custom_metadata_keys(value["CustomerMetadataProperties"])
            return {"CustomerMetadataProperties": preserved}
        if "customer_metadata_properties" in value:
            preserved = _preserve_custom_metadata_keys(value["customer_metadata_properties"])
            return {"CustomerMetadataProperties": preserved}

        normalized = snake_dict_to_camel_dict(scrub_none_parameters(value), capitalize_first=True)
        return _fix_model_package_api_key_names(normalized)
    if isinstance(value, list):
        return [_normalize_model_package_compare_value(item) for item in value]
    return value


def get_model_package_tag_arn(package: Dict[str, Any], client: Optional[Any] = None) -> Optional[str]:
    """Return the ARN that owns package tags. SageMaker tags package versions only through the parent group."""
    if package.get("ModelPackageGroupArn"):
        return package["ModelPackageGroupArn"]
    group_name = package.get("ModelPackageGroupName")
    if client and group_name:
        group = describe_model_package_group(client, group_name)
        if group and group.get("ModelPackageGroupArn"):
            return group["ModelPackageGroupArn"]
    package_arn = package.get("ModelPackageArn")
    if package_arn and ":model-package/" in package_arn:
        arn_prefix, package_path = package_arn.split(":model-package/", 1)
        package_path_parts = package_path.split("/")
        if len(package_path_parts) == 2:
            return f"{arn_prefix}:model-package-group/{package_path_parts[0]}"
    return package_arn


def _build_model_package_params(module) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        field: module.params.get(field)
        for field in (
            "model_package_name",
            "model_package_group_name",
            "model_package_description",
            "model_package_registration_type",
            "inference_specification",
            "validation_specification",
            "source_algorithm_specification",
            "certify_for_marketplace",
            "additional_inference_specifications",
            "model_card",
            "model_metrics",
            "domain",
            "task",
            "sample_payload_url",
            "skip_model_validation",
            "drift_check_baselines",
            "security_config",
            "source_uri",
            "customer_metadata_properties",
            "metadata_properties",
            "model_approval_status",
            "approval_description",
            "model_life_cycle",
            "tags",
        )
    }
    tags: Optional[Dict[str, str]] = params.pop("tags", None)
    if tags is not None:
        params["tags"] = [{"Key": key, "Value": value} for key, value in tags.items()]
    customer_metadata_properties = params.pop("customer_metadata_properties", None)
    normalized = snake_dict_to_camel_dict(scrub_none_parameters(params), capitalize_first=True)
    if customer_metadata_properties is not None:
        normalized["CustomerMetadataProperties"] = _preserve_custom_metadata_keys(customer_metadata_properties)
    return _fix_model_package_api_key_names(normalized)


def _build_model_package_update_params(module, model_package_arn: str) -> Dict[str, Any]:
    params: Dict[str, Any] = {"ModelPackageArn": model_package_arn}
    update_fields: Dict[str, Any] = {}
    for field in (
        "model_approval_status",
        "approval_description",
        "customer_metadata_properties",
        "customer_metadata_properties_to_remove",
        "model_life_cycle",
        "additional_inference_specifications_to_add",
    ):
        value = module.params.get(field)
        if value is not None:
            update_fields[field] = value
    customer_metadata_properties = update_fields.pop("customer_metadata_properties", None)
    params.update(snake_dict_to_camel_dict(scrub_none_parameters(update_fields), capitalize_first=True))
    if customer_metadata_properties is not None:
        params["CustomerMetadataProperties"] = _preserve_custom_metadata_keys(customer_metadata_properties)
    return scrub_none_parameters(params)


@AWSRetry.jittered_backoff(retries=10)
def create_model_package(client, module) -> Tuple[bool, str, Optional[str]]:
    """Create a SageMaker model package."""
    name = module.params.get("model_package_name")
    group_name = module.params.get("model_package_group_name")
    if module.check_mode:
        if name:
            return True, f"Check mode: would have created model package {name}.", None
        return True, f"Check mode: would have created model package in group {group_name}.", None

    response = client.create_model_package(**_build_model_package_params(module))
    if name:
        return True, f"Model package {name} created successfully.", response.get("ModelPackageArn")
    return True, f"Model package in group {group_name} created successfully.", response.get("ModelPackageArn")


@AWSRetry.jittered_backoff(retries=10)
def update_model_package(client, module, model_package_arn: str) -> Tuple[bool, str]:
    """Update a SageMaker model package in place."""
    name = module.params.get("model_package_name")
    if name is None:
        raise ValueError("model_package_name is required for model package updates.")
    if module.check_mode:
        return True, f"Check mode: would have updated model package {name}."

    client.update_model_package(**_build_model_package_update_params(module, model_package_arn))
    return True, f"Model package {name} updated successfully."


def model_package_needs_update(existing: Dict[str, Any], module) -> bool:
    """Determine whether a model package requires an in-place update."""
    desired = _build_model_package_update_params(module, existing.get("ModelPackageArn", ""))
    for key in (
        "ModelApprovalStatus",
        "ApprovalDescription",
        "CustomerMetadataProperties",
        "ModelLifeCycle",
    ):
        desire_value = desired.get(key)
        if desire_value is None:
            continue
        if not _model_package_values_match(existing.get(key), desire_value):
            return True

    properties_to_remove = module.params.get("customer_metadata_properties_to_remove")
    existing_properties = existing.get("CustomerMetadataProperties", {})
    if properties_to_remove and any(key in existing_properties for key in properties_to_remove):
        return True

    specifications_to_add = module.params.get("additional_inference_specifications_to_add")
    existing_specifications = existing.get("AdditionalInferenceSpecifications", [])
    if specifications_to_add and any(
        not any(_model_package_values_match(actual, desired) for actual in existing_specifications)
        for desired in specifications_to_add
    ):
        return True

    return False


@AWSRetry.jittered_backoff(retries=10)
def delete_model_package(client, module) -> Tuple[bool, str]:
    """Delete a SageMaker model package."""
    name = module.params.get("model_package_name")
    if name is None:
        raise ValueError("model_package_name is required for model package deletion.")
    if module.check_mode:
        return True, f"Check mode: would have deleted model package {name}."

    client.delete_model_package(ModelPackageName=name)
    return True, f"Model package {name} deleted successfully."


@AWSRetry.jittered_backoff(retries=10)
def wait_for_model_package_status(client, model_package_name: Optional[str], wait_timeout: int = 600) -> None:
    """Wait until the model package reaches a terminal status."""
    if model_package_name is None:
        return

    deadline = time.time() + wait_timeout
    while time.time() < deadline:
        try:
            package = client.describe_model_package(ModelPackageName=model_package_name)
        except (
            is_boto3_error_code("ResourceNotFound"),
            is_boto3_error_message("does not exist"),
            is_boto3_error_message("not found"),
        ):
            return

        status = package.get("ModelPackageStatus")
        if status in ("Completed", "Failed"):
            if status == "Failed":
                raise RuntimeError(f"SageMaker model package {model_package_name} entered a failed state.")
            return
        if status == "Deleting":
            time.sleep(5)
            continue
        time.sleep(5)

    raise TimeoutError(f"Timed out waiting for model package {model_package_name} to reach a terminal status.")


@AWSRetry.jittered_backoff(retries=10)
def update_model_package_tags(
    client, module, model_package_arn: str, desired_tags: Dict[str, str], purge_tags: bool = True
) -> Tuple[bool, str]:
    """Reconcile SageMaker model package tags in place."""
    current_tags: Dict[str, str] = list_tags(client, model_package_arn)

    tags_to_add: Dict[str, str] = {key: value for key, value in desired_tags.items() if current_tags.get(key) != value}
    tags_to_remove: List[str] = [key for key in current_tags if key not in desired_tags] if purge_tags else []

    if not tags_to_add and not tags_to_remove:
        return False, "No updates needed."

    if module.check_mode:
        return True, "Check mode: would have updated model package tags."

    if tags_to_add:
        client.add_tags(
            ResourceArn=model_package_arn,
            Tags=[{"Key": key, "Value": value} for key, value in tags_to_add.items()],
        )
    if tags_to_remove:
        client.delete_tags(ResourceArn=model_package_arn, TagKeys=tags_to_remove)

    return True, "Model package tags updated successfully."


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
