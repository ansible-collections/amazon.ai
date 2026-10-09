# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

try:
    from botocore.exceptions import WaiterError
except ImportError:
    pass

from ansible_collections.amazon.ai.plugins.module_utils.waiters import wait_for_image_version_deletion
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
def describe_image_version(
    client, image_name: str, version: Optional[int] = None, alias: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve details for a SageMaker Image Version.

    Args:
        client: The boto3 SageMaker client.
        image_name: The name of the parent SageMaker Image.
        version: The version number. Without version or alias the latest version is described.
        alias: An alias of the version.

    Returns:
        A dictionary with the image version details if found, otherwise None.
    """
    params = scrub_none_parameters({"ImageName": image_name, "Version": version, "Alias": alias})
    try:
        return client.describe_image_version(**params)
    except is_boto3_error_code("ResourceNotFound"):
        return None


@AWSRetry.jittered_backoff(retries=10)
def list_image_versions(client, image_name: str, **params: Any) -> List[Dict[str, Any]]:
    """
    Retrieve the versions of a SageMaker Image using pagination.

    Returns:
        A list of image version summary dictionaries, empty when the image does not exist.
    """
    paginator = client.get_paginator("list_image_versions")
    try:
        return paginator.paginate(ImageName=image_name, **params).build_full_result()["ImageVersions"]
    except is_boto3_error_code("ResourceNotFound"):
        return []


@AWSRetry.jittered_backoff(retries=10)
def list_image_version_aliases(client, image_name: str, version: Optional[int] = None) -> List[str]:
    """
    Retrieve the aliases of a SageMaker Image Version, or of all its versions when version is None.

    Returns:
        A list of aliases, empty when the image does not exist.
    """
    params = scrub_none_parameters({"ImageName": image_name, "Version": version})
    paginator = client.get_paginator("list_aliases")
    try:
        return paginator.paginate(**params).build_full_result()["SageMakerImageVersionAliases"]
    except is_boto3_error_code("ResourceNotFound"):
        return []


def _attach_image_version_aliases(client, image_name: str, image_version: Dict[str, Any]) -> Dict[str, Any]:
    """Add the 'Aliases' key to a describe_image_version response."""
    image_version["Aliases"] = list_image_version_aliases(client, image_name, version=image_version["Version"])
    return image_version


def get_image_version(client, image_name: str, version: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a SageMaker Image Version together with its aliases.

    Returns:
        The describe response with an added 'Aliases' key, or None if the version does not exist.
    """
    image_version = describe_image_version(client, image_name, version=version)
    if image_version is None:
        return None
    return _attach_image_version_aliases(client, image_name, image_version)


def find_image_versions(
    client, image_name: str, version: Optional[int] = None, alias: Optional[str] = None, **list_params: Any
) -> List[Dict[str, Any]]:
    """
    Find the versions of a SageMaker Image, each together with its aliases.

    Args:
        client: The boto3 SageMaker client.
        image_name: The name of the parent SageMaker Image.
        version: Return only this version.
        alias: Return only the version carrying this alias.
        **list_params: Extra ListImageVersions parameters (PascalCase), used when neither
            version nor alias is given.

    Returns:
        A list of describe responses, empty when nothing matched.
    """
    if version is not None or alias is not None:
        image_version = describe_image_version(client, image_name, version=version, alias=alias)
        if image_version is None:
            return []
        return [_attach_image_version_aliases(client, image_name, image_version)]

    image_versions = (
        get_image_version(client, image_name, summary["Version"])
        for summary in list_image_versions(client, image_name, **list_params)
    )
    return [image_version for image_version in image_versions if image_version is not None]


IMAGE_VERSION_PROPERTIES = (
    "horovod",
    "job_type",
    "ml_framework",
    "processor",
    "programming_lang",
    "release_notes",
    "vendor_guidance",
)


def _image_version_params(module, **extra: Any) -> Dict[str, Any]:
    """
    Convert the image version option values, plus extra snake_case keys, to API parameters.

    Keys whose value is None are dropped.
    """
    values = {name: module.params.get(name) for name in IMAGE_VERSION_PROPERTIES}
    params = snake_dict_to_camel_dict(scrub_none_parameters(dict(values, **extra)), capitalize_first=True)
    # The generic conversion spells the key "MlFramework"; the API expects "MLFramework".
    if "MlFramework" in params:
        params["MLFramework"] = params.pop("MlFramework")
    return params


def wait_for_image_version_created(client, module, image_name: str, version: int) -> None:
    """Wait for a SageMaker image version to reach CREATED using the botocore waiter."""
    if not module.params.get("wait", True):
        return

    wait_timeout: int = module.params.get("wait_timeout", 600)
    delay = max(1, min(60, wait_timeout))
    waiter = client.get_waiter("image_version_created")
    try:
        waiter.wait(
            ImageName=image_name,
            Version=version,
            WaiterConfig=dict(Delay=delay, MaxAttempts=max(1, wait_timeout // delay)),
        )
    except WaiterError as e:
        image_version = describe_image_version(client, image_name, version=version) or {}
        reason = image_version.get("FailureReason", "")
        module.fail_json(
            msg=f"Error waiting for SageMaker image version {image_name}:{version} to be created: {reason or e}"
        )


def create_image_version(client, module) -> Tuple[bool, str, Optional[int]]:
    """
    Create a SageMaker image version and wait for it to be created.

    Returns:
        A tuple (changed, message, version) where version is the number assigned by the service,
        or None in check mode.
    """
    image_name = module.params["image_name"]
    if module.check_mode:
        return True, f"Check mode: would have created a version of SageMaker image {image_name}.", None

    params = _image_version_params(
        module,
        image_name=image_name,
        base_image=module.params["base_image"],
        aliases=module.params.get("aliases"),
    )
    response = client.create_image_version(aws_retry=True, **params)
    # ImageVersionArn ends in "image-version/<name>/<version>"
    version = int(response["ImageVersionArn"].rsplit("/", 1)[-1])
    wait_for_image_version_created(client, module, image_name, version)
    return True, f"SageMaker image version {image_name}:{version} created successfully.", version


def image_version_needs_update(existing: Dict[str, Any], module) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """
    Compare the supplied options with an existing image version.

    Returns:
        A tuple (properties_to_update, aliases_to_add, aliases_to_delete).
    """
    base_image = module.params.get("base_image")
    if base_image is not None and base_image != existing.get("BaseImage"):
        module.fail_json(
            msg=(
                "base_image cannot be changed on an existing image version. "
                f"Current: {existing.get('BaseImage')}. Create a new version instead."
            )
        )

    desired = _image_version_params(module)
    properties_to_update = {key: value for key, value in desired.items() if existing.get(key) != value}

    aliases_to_add: List[str] = []
    aliases_to_delete: List[str] = []
    if module.params.get("aliases") is not None:
        desired_aliases = set(module.params["aliases"])
        existing_aliases = set(existing.get("Aliases", []))
        aliases_to_add = sorted(desired_aliases - existing_aliases)
        aliases_to_delete = sorted(existing_aliases - desired_aliases)

    return properties_to_update, aliases_to_add, aliases_to_delete


def update_image_version(client, module, existing: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Update the properties and aliases of an existing SageMaker image version.

    A version still in CREATING is first waited on (when wait is enabled).

    Returns:
        A tuple (changed, message, image_version) with the image version as it is after the call.
    """
    image_name = module.params["image_name"]
    version = module.params["version"]

    if existing.get("ImageVersionStatus") == "CREATING" and module.params.get("wait", True):
        wait_for_image_version_created(client, module, image_name, version)
        existing = get_image_version(client, image_name, version) or existing

    properties_to_update, aliases_to_add, aliases_to_delete = image_version_needs_update(existing, module)
    if not (properties_to_update or aliases_to_add or aliases_to_delete):
        return False, f"SageMaker image version {image_name}:{version} already matches the desired state.", existing

    if module.check_mode:
        return True, f"Check mode: would have updated SageMaker image version {image_name}:{version}.", existing

    params = snake_dict_to_camel_dict(
        scrub_none_parameters(
            dict(
                image_name=image_name,
                version=version,
                aliases_to_add=aliases_to_add or None,
                aliases_to_delete=aliases_to_delete or None,
            )
        ),
        capitalize_first=True,
    )
    params.update(properties_to_update)
    client.update_image_version(aws_retry=True, **params)
    updated = get_image_version(client, image_name, version) or existing
    return True, f"SageMaker image version {image_name}:{version} updated successfully.", updated


def delete_image_version(client, module, existing: Optional[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Delete a SageMaker image version and wait until it is gone.

    Args:
        existing: The described image version, or None when it does not exist.
    """
    image_name = module.params["image_name"]
    version = module.params["version"]
    if existing is None:
        return False, f"SageMaker image version {image_name}:{version} does not exist."

    wait_timeout: int = module.params.get("wait_timeout", 600)
    if existing.get("ImageVersionStatus") == "DELETING":
        wait_for_image_version_deletion(client, module, image_name, version, wait_timeout=wait_timeout)
        return False, f"SageMaker image version {image_name}:{version} is already being deleted."

    if module.check_mode:
        return True, f"Check mode: would have deleted SageMaker image version {image_name}:{version}."

    client.delete_image_version(ImageName=image_name, Version=version, aws_retry=True)
    wait_for_image_version_deletion(client, module, image_name, version, wait_timeout=wait_timeout)
    return True, f"SageMaker image version {image_name}:{version} deleted successfully."


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
    delay = max(1, min(30, wait_timeout))
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
