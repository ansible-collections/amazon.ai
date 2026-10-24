# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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

from ansible_collections.amazon.ai.plugins.module_utils.utils import parse_json
from ansible_collections.amazon.ai.plugins.module_utils.waiters import wait_for_image_version_deletion
from ansible_collections.amazon.ai.plugins.module_utils.waiters import wait_for_model_package_group_deletion

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_message
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters

try:
    import botocore
except ImportError:
    pass


@AWSRetry.jittered_backoff(retries=10)
def list_tags(client, resource_arn: str) -> Dict[str, str]:
    paginator = client.get_paginator("list_tags")
    tags = paginator.paginate(ResourceArn=resource_arn).build_full_result()["Tags"]
    return {t["Key"]: t["Value"] for t in tags}


def reconcile_sagemaker_tags(client, module, resource_arn: str) -> bool:
    """Reconcile SageMaker resource tags using the shared ResourceArn tagging API."""
    desired_tags = module.params.get("tags")
    if desired_tags is None:
        return False

    current_tags = list_tags(client, resource_arn)
    tags_to_add, tags_to_remove = compare_aws_tags(
        current_tags,
        desired_tags,
        purge_tags=module.params.get("purge_tags", True),
    )
    if not tags_to_add and not tags_to_remove:
        return False

    if module.check_mode:
        return True

    if tags_to_add:
        client.add_tags(
            ResourceArn=resource_arn,
            Tags=ansible_dict_to_boto3_tag_list(tags_to_add),
        )
    if tags_to_remove:
        client.delete_tags(
            ResourceArn=resource_arn,
            TagKeys=tags_to_remove,
        )

    return True


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

    wait_timeout: int = module.params.get("wait_timeout")
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


def _ensure_image_version_updatable(existing: Dict[str, Any], module) -> None:
    """Fail when the status of an existing image version rules out an update."""
    image_name = module.params["image_name"]
    version = module.params["version"]
    status = existing.get("ImageVersionStatus")
    reason = existing.get("FailureReason")
    detail = f" Reason: {reason}" if reason else ""
    if status == "DELETING":
        message = "is currently being deleted. Wait for deletion to complete before using state=present."
    elif status == "CREATE_FAILED":
        message = f"failed to be created.{detail} Delete it with state=absent and create a new version."
    elif status == "DELETE_FAILED":
        message = f"could not be deleted.{detail} Retry the deletion with state=absent."
    else:
        return
    module.fail_json(
        msg=f"SageMaker image version {image_name}:{version} {message}",
        image_version=camel_dict_to_snake_dict(existing),
    )


def _ensure_base_image_unchanged(existing: Dict[str, Any], module) -> None:
    """Fail when base_image, which is create-only, differs from the one of an existing image version."""
    base_image = module.params.get("base_image")
    if base_image is not None and base_image != existing.get("BaseImage"):
        module.fail_json(
            msg=(
                f"SageMaker image version {module.params['image_name']}:{module.params['version']} has the base_image "
                f"{existing.get('BaseImage')}. base_image cannot be changed after the version is created. "
                "Omit version to create a new version with a different base_image."
            )
        )


def update_image_version(client, module, existing: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Update the properties and aliases of an existing SageMaker image version.

    The status is checked first and the differences are computed from the version as it is. A version
    still in CREATING is waited on (when wait is enabled) only to confirm it is ready when nothing
    differs, or before the update when an update is needed. With wait disabled the update is sent
    right away, which the service accepts for a version that is still being created.

    Returns:
        A tuple (changed, message, image_version) with the image version as it is after the call.
    """
    image_name = module.params["image_name"]
    version = module.params["version"]
    wait = module.params.get("wait", True)

    _ensure_image_version_updatable(existing, module)
    _ensure_base_image_unchanged(existing, module)
    creating = existing.get("ImageVersionStatus") == "CREATING"

    properties_to_update, aliases_to_add, aliases_to_delete = image_version_needs_update(existing, module)
    if not (properties_to_update or aliases_to_add or aliases_to_delete):
        if creating and wait and not module.check_mode:
            wait_for_image_version_created(client, module, image_name, version)
            existing = get_image_version(client, image_name, version) or existing
        return False, f"SageMaker image version {image_name}:{version} already matches the desired state.", existing

    if module.check_mode:
        return True, f"Check mode: would have updated SageMaker image version {image_name}:{version}.", existing

    if creating and wait:
        wait_for_image_version_created(client, module, image_name, version)

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
    # UpdateImageVersion resets Horovod to false whenever the call omits it, so keep the current value.
    if "Horovod" not in params and existing.get("Horovod") is not None:
        params["Horovod"] = existing["Horovod"]
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

    if existing.get("ImageVersionStatus") == "DELETING":
        if not module.check_mode:
            wait_for_image_version_deletion(client, module)
        return False, f"SageMaker image version {image_name}:{version} is already being deleted."

    if existing.get("ImageVersionStatus") == "CREATING":
        # DeleteImageVersion rejects a version that is still being created with ResourceInUse.
        if not module.params.get("wait", True):
            module.fail_json(
                msg=(
                    f"SageMaker image version {image_name}:{version} is still being created and cannot be deleted "
                    "until creation finishes. Retry later, or use wait=true to wait for the creation first."
                )
            )
        if not module.check_mode:
            wait_for_image_version_created(client, module, image_name, version)

    if module.check_mode:
        return True, f"Check mode: would have deleted SageMaker image version {image_name}:{version}."

    if existing.get("ImageVersionStatus") == "DELETE_FAILED":
        module.warn(
            f"A previous deletion of SageMaker image version {image_name}:{version} failed "
            f"({existing.get('FailureReason', 'no reason reported')}). Retrying the deletion."
        )

    try:
        client.delete_image_version(ImageName=image_name, Version=version, aws_retry=True)
    except is_boto3_error_code("ResourceNotFound"):
        # Deleted by someone else between the describe and this call.
        return False, f"SageMaker image version {image_name}:{version} does not exist."
    wait_for_image_version_deletion(client, module)
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


def update_model_package_group_tags(client, module, model_package_group_arn: str) -> Tuple[bool, str]:
    """Reconcile SageMaker model package group tags in place."""
    changed = reconcile_sagemaker_tags(client, module, model_package_group_arn)
    if not changed:
        return False, "No updates needed."
    if module.check_mode:
        return True, "Check mode: would have updated model package group tags."

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
        if variant_name not in existing_by_name or _endpoint_config_mapping_differs(
            desired_variant, existing_by_name[variant_name]
        ):
            return True
    return False


def _endpoint_config_mapping_differs(desired: Dict[str, Any], existing: Dict[str, Any]) -> bool:
    for key, desired_value in desired.items():
        existing_value = existing.get(key)
        if isinstance(desired_value, dict):
            if not isinstance(existing_value, dict) or _endpoint_config_mapping_differs(desired_value, existing_value):
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
        return not isinstance(existing_value, dict) or _endpoint_config_mapping_differs(desired_value, existing_value)
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
    return reconcile_sagemaker_tags(client, module, existing["EndpointConfigArn"])


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
    return reconcile_sagemaker_tags(client, module, existing["EndpointArn"])


@AWSRetry.jittered_backoff(retries=10)
def describe_pipeline(
    client, pipeline_name: str, pipeline_version_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Retrieve a SageMaker pipeline definition, returning None when it does not exist."""
    params = dict(PipelineName=pipeline_name)
    if pipeline_version_id is not None:
        params["PipelineVersionId"] = pipeline_version_id
    try:
        return client.describe_pipeline(**params)
    except is_boto3_error_code("ResourceNotFound"):
        return None


@AWSRetry.jittered_backoff(retries=10)
def list_pipelines(client, max_items: Optional[int] = None, **params: Any) -> List[Dict[str, Any]]:
    """Retrieve pipeline definition summaries using the SageMaker paginator."""
    paginator = client.get_paginator("list_pipelines")
    if max_items is not None:
        return paginator.paginate(**params, PaginationConfig={"MaxItems": max_items}).build_full_result()[
            "PipelineSummaries"
        ]
    return paginator.paginate(**params).build_full_result()["PipelineSummaries"]


def get_pipeline_definition_from_s3(client, location: Dict[str, Any], module) -> Any:
    """Read and parse the JSON definition object referenced by a pipeline S3 location."""
    params = dict(Bucket=location["Bucket"], Key=location["ObjectKey"])
    if location.get("VersionId") is not None:
        params["VersionId"] = location["VersionId"]
    try:
        response = client.get_object(**params)
        body = response["Body"]
        try:
            content = body.read()
        finally:
            body.close()
    except is_boto3_error_code("NoSuchKey") as e:
        module.fail_json_aws(e, msg="The S3 pipeline definition object does not exist.")
    except is_boto3_error_code("InvalidObjectState") as e:
        module.fail_json_aws(e, msg="The S3 pipeline definition object must be restored before it can be read.")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to read the S3 pipeline definition object.")
    if isinstance(content, bytes):
        try:
            content = content.decode("utf-8")
        except UnicodeDecodeError as e:
            module.fail_json(msg=f"The S3 pipeline definition object is not valid UTF-8: {e}")
    return parse_json(content, module, "S3 pipeline definition")


def _pipeline_properties_to_wait_for(module, s3_client=None) -> Dict[str, Any]:
    param_names = (
        "pipeline_definition",
        "pipeline_definition_s3_location",
        "role_arn",
        "pipeline_display_name",
        "pipeline_description",
        "parallelism_configuration",
    )
    desired = {key: module.params.get(key) for key in param_names if module.params.get(key) is not None}
    params = snake_dict_to_camel_dict(scrub_none_parameters(desired), capitalize_first=True)
    if "PipelineDefinition" in params:
        params["PipelineDefinition"] = parse_json(params["PipelineDefinition"], module, "pipeline_definition")
    if "PipelineDefinitionS3Location" in params:
        location = params.pop("PipelineDefinitionS3Location")
        params["PipelineDefinition"] = get_pipeline_definition_from_s3(s3_client, location, module)
    return params


def pipeline_properties_to_update(existing: Dict[str, Any], module, s3_client=None) -> Dict[str, Any]:
    desired = {
        field: module.params.get(field)
        for field in (
            "pipeline_definition",
            "pipeline_definition_s3_location",
            "role_arn",
            "pipeline_display_name",
            "pipeline_description",
            "parallelism_configuration",
        )
    }
    desired = scrub_none_parameters(desired)
    params = snake_dict_to_camel_dict(desired, capitalize_first=True)

    properties_to_update: Dict[str, Any] = dict()
    for field, value in params.items():
        if field == "PipelineDefinition":
            desired_definition = parse_json(value, module, "pipeline_definition")
            current_definition = parse_json(existing.get(field), module, "existing pipeline definition")
            if desired_definition != current_definition:
                properties_to_update[field] = value
        elif field == "PipelineDefinitionS3Location":
            desired_definition = get_pipeline_definition_from_s3(s3_client, value, module)
            current_definition = existing.get("PipelineDefinition")
            if current_definition is None or desired_definition != parse_json(
                current_definition, module, "existing pipeline definition"
            ):
                properties_to_update[field] = value
        elif existing.get(field) != value:
            properties_to_update[field] = value
    return properties_to_update


def create_pipeline(client, module, s3_client=None) -> Tuple[bool, str]:
    """Create a SageMaker pipeline definition."""
    pipeline_name = module.params["pipeline_name"]
    if module.check_mode:
        return True, f"Check mode: would have created pipeline {pipeline_name}."

    params = {
        field: module.params.get(field)
        for field in (
            "pipeline_name",
            "pipeline_definition",
            "pipeline_definition_s3_location",
            "role_arn",
            "pipeline_display_name",
            "pipeline_description",
            "parallelism_configuration",
        )
    }
    params["tags"] = module.params.get("tags")
    params = snake_dict_to_camel_dict(scrub_none_parameters(params), capitalize_first=True)
    if "Tags" in params:
        params["Tags"] = ansible_dict_to_boto3_tag_list(module.params["tags"])
    expected_properties = None
    if module.params.get("wait", True):
        expected_properties = _pipeline_properties_to_wait_for(module, s3_client=s3_client)
    client.create_pipeline(**params)
    if module.params.get("wait", True):
        wait_for_pipeline_status(
            client,
            module,
            pipeline_name,
            expected_properties=expected_properties,
        )
    return True, f"Pipeline {pipeline_name} created successfully."


@AWSRetry.jittered_backoff(retries=10)
def update_pipeline(
    client, module, properties_to_update: Dict[str, Any], existing: Dict[str, Any], s3_client=None
) -> Tuple[bool, str, Optional[int]]:
    """Update mutable properties of an existing SageMaker pipeline."""
    pipeline_name = module.params["pipeline_name"]
    if not properties_to_update:
        return False, f"No updates needed for pipeline {pipeline_name}.", None
    if module.check_mode:
        return True, f"Check mode: would have updated pipeline {pipeline_name}.", None

    params = dict(properties_to_update)
    if set(params) == {"ParallelismConfiguration"}:
        # Updating parallelism by itself does not work; include the existing RoleArn.
        params["RoleArn"] = existing["RoleArn"]
    params["PipelineName"] = pipeline_name
    expected_properties = None
    if module.params.get("wait", True):
        expected_properties = _pipeline_properties_to_wait_for(module, s3_client=s3_client)
    response = client.update_pipeline(**params)
    if module.params.get("wait", True):
        pipeline_version_id = response.get("PipelineVersionId")
        wait_for_pipeline_status(
            client,
            module,
            pipeline_name,
            expected_properties=expected_properties,
            pipeline_version_id=pipeline_version_id,
        )
    return True, f"Pipeline {pipeline_name} updated successfully.", response.get("PipelineVersionId")


@AWSRetry.jittered_backoff(retries=10)
def reconcile_pipeline_tags(client, module, pipeline: Dict[str, Any]) -> Tuple[bool, str]:
    """Reconcile pipeline tags when the caller explicitly supplies a tag map."""
    desired_tags: Optional[Dict[str, str]] = module.params.get("tags")
    if desired_tags is None:
        return False, ""
    current_tags = list_tags(client, pipeline["PipelineArn"])
    tags_to_add, tags_to_remove = compare_aws_tags(
        current_tags,
        desired_tags,
        module.params["purge_tags"],
    )
    if not tags_to_add and not tags_to_remove:
        return False, f"No updates needed for pipeline {module.params['pipeline_name']} tags."
    if module.check_mode:
        return True, f"Check mode: would have updated tags for pipeline {module.params['pipeline_name']}."
    if tags_to_add:
        client.add_tags(ResourceArn=pipeline["PipelineArn"], Tags=ansible_dict_to_boto3_tag_list(tags_to_add))
    if tags_to_remove:
        client.delete_tags(ResourceArn=pipeline["PipelineArn"], TagKeys=tags_to_remove)
    return True, f"Tags for pipeline {module.params['pipeline_name']} updated successfully."


@AWSRetry.jittered_backoff(retries=10)
def delete_pipeline(client, module) -> Tuple[bool, str]:
    """Delete a SageMaker pipeline definition and optionally wait for its removal."""
    pipeline_name = module.params["pipeline_name"]
    if module.check_mode:
        return True, f"Check mode: would have deleted pipeline {pipeline_name}."
    client.delete_pipeline(PipelineName=pipeline_name)
    if module.params.get("wait", True):
        wait_for_pipeline_status(client, module, pipeline_name, deleted=True)
    return True, f"Pipeline {pipeline_name} deleted successfully."


def wait_for_pipeline_status(
    client,
    module,
    pipeline_name: str,
    deleted: bool = False,
    expected_properties: Optional[Dict[str, Any]] = None,
    pipeline_version_id: Optional[int] = None,
) -> None:
    """Wait for a SageMaker pipeline to become active or be deleted."""
    wait_timeout = module.params.get("wait_timeout", 600)
    deadline = time.monotonic() + wait_timeout
    while True:
        pipeline = describe_pipeline(client, pipeline_name, pipeline_version_id)

        if deleted and pipeline is None:
            return
        if (
            not deleted
            and pipeline is not None
            and pipeline.get("PipelineStatus") == "Active"
            and _pipeline_properties_match(pipeline, expected_properties or {}, module, pipeline_name)
        ):
            return

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            desired_state = "deletion" if deleted else "Active status with requested properties"
            module.fail_json(msg=f"Timed out waiting for pipeline {pipeline_name} to reach {desired_state}.")
        time.sleep(min(5, remaining))


def _pipeline_properties_match(
    pipeline: Dict[str, Any], expected_properties: Dict[str, Any], module, pipeline_name: str
) -> bool:
    for name, expected in expected_properties.items():
        actual = pipeline.get(name)
        if name == "PipelineDefinition":
            actual = parse_json(actual, module, f"pipeline {pipeline_name} definition returned while waiting")
        if actual != expected:
            return False
    return True


def describe_training_job(client, training_job_name: str) -> Optional[Dict[str, Any]]:
    """Retrieve details for a SageMaker training job, or None when it does not exist."""
    try:
        return client.describe_training_job(TrainingJobName=training_job_name)
    except is_boto3_error_code("ResourceNotFound"):
        return None
    except is_boto3_error_code("ValidationException") as e:
        if e.response["Error"].get("Message") == "Requested resource not found.":
            return None
        raise


@AWSRetry.jittered_backoff(retries=10)
def list_training_jobs(client, **params: Any) -> List[Dict[str, Any]]:
    """Retrieve all matching SageMaker training job summaries."""
    paginator = client.get_paginator("list_training_jobs")
    return paginator.paginate(**params).build_full_result()["TrainingJobSummaries"]


def normalize_training_job(training_job: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a SageMaker training job response while preserving arbitrary map keys."""
    normalized = camel_dict_to_snake_dict(
        training_job,
        ignore_list=["Tags", "HyperParameters", "Environment", "ProfilingParameters", "RuleParameters"],
    )
    for aws_key, option_key in (("HyperParameters", "hyper_parameters"), ("Environment", "environment")):
        if aws_key in training_job:
            normalized[option_key] = dict(training_job[aws_key])

    profiler_config = training_job.get("ProfilerConfig")
    if profiler_config and "ProfilingParameters" in profiler_config:
        normalized["profiler_config"]["profiling_parameters"] = dict(profiler_config["ProfilingParameters"])

    for aws_rule, normalized_rule in zip(
        training_job.get("ProfilerRuleConfigurations") or [], normalized.get("profiler_rule_configurations") or []
    ):
        if "RuleParameters" in aws_rule:
            normalized_rule["rule_parameters"] = dict(aws_rule["RuleParameters"])

    normalized["tags"] = training_job.get("Tags", {})
    return normalized


def _camelize_training_job_params(values: Dict[str, Any]) -> Dict[str, Any]:
    params = snake_dict_to_camel_dict(scrub_none_parameters(values), capitalize_first=True)
    resource_config = params.get("ResourceConfig")
    if resource_config and "VolumeSizeInGb" in resource_config:
        resource_config["VolumeSizeInGB"] = resource_config.pop("VolumeSizeInGb")

    for field in ("hyper_parameters", "environment"):
        if values.get(field) is not None:
            api_field = next(iter(snake_dict_to_camel_dict({field: None}, capitalize_first=True)))
            params[api_field] = dict(values[field])

    profiler_config = values.get("profiler_config")
    if profiler_config and profiler_config.get("profiling_parameters") is not None:
        params["ProfilerConfig"]["ProfilingParameters"] = dict(profiler_config["profiling_parameters"])

    profiler_rules = values.get("profiler_rule_configurations")
    if profiler_rules is not None:
        for rule, converted_rule in zip(profiler_rules, params["ProfilerRuleConfigurations"]):
            if "VolumeSizeInGb" in converted_rule:
                converted_rule["VolumeSizeInGB"] = converted_rule.pop("VolumeSizeInGb")
            if rule.get("rule_parameters") is not None:
                converted_rule["RuleParameters"] = dict(rule["rule_parameters"])
    return params


def training_job_params(module) -> Dict[str, Any]:
    """Build CreateTrainingJob parameters from the module's snake_case options."""
    fields = (
        "training_job_name",
        "role_arn",
        "algorithm_specification",
        "input_data_config",
        "output_data_config",
        "resource_config",
        "stopping_condition",
        "vpc_config",
        "hyper_parameters",
        "environment",
        "enable_network_isolation",
        "enable_inter_container_traffic_encryption",
        "enable_managed_spot_training",
        "checkpoint_config",
        "retry_strategy",
        "profiler_config",
        "profiler_rule_configurations",
        "remote_debug_config",
        "tags",
    )
    values = {field: module.params.get(field) for field in fields}
    params = _camelize_training_job_params(values)
    if module.params.get("tags") is not None:
        params["Tags"] = ansible_dict_to_boto3_tag_list(module.params["tags"])
    return params


def _training_job_mapping_differs(desired: Any, existing: Any, _depth: int = 0) -> bool:
    if _depth > 100:
        raise ValueError("Maximum recursion depth exceeded in _training_job_mapping_differs")
    if isinstance(desired, dict):
        existing = existing if isinstance(existing, dict) else {}
        return any(
            _training_job_mapping_differs(value, existing.get(key), _depth + 1) for key, value in desired.items()
        )
    if isinstance(desired, list):
        existing = existing if isinstance(existing, list) else []
        return len(desired) != len(existing) or any(
            _training_job_mapping_differs(value, existing_value, _depth + 1)
            for value, existing_value in zip(desired, existing)
        )
    if desired is False and existing is None:
        return False
    return desired != existing


def training_job_needs_replacement(existing: Dict[str, Any], module) -> List[str]:
    """Return the requested create-only properties that differ from an existing job."""
    desired = training_job_params(module)
    differences = []
    for key, value in desired.items():
        if key in ("TrainingJobName", "Tags", "ProfilerConfig", "ProfilerRuleConfigurations", "RemoteDebugConfig"):
            continue
        if key == "ResourceConfig":
            desired_resource_config = {
                field: item for field, item in value.items() if field != "KeepAlivePeriodInSeconds"
            }
            if desired_resource_config and _training_job_mapping_differs(
                desired_resource_config, existing.get("ResourceConfig", {})
            ):
                differences.append("resource_config")
            continue
        if _training_job_mapping_differs(value, existing.get(key)):
            differences.append(next(iter(camel_dict_to_snake_dict({key: None}))))
    return differences


def _training_job_update_params(existing: Dict[str, Any], module) -> Dict[str, Any]:
    params: Dict[str, Any] = {"TrainingJobName": module.params["training_job_name"]}
    values = {}
    for field in ("profiler_config", "profiler_rule_configurations", "remote_debug_config"):
        desired = module.params.get(field)
        if desired is not None:
            converted = _camelize_training_job_params({field: desired})
            if not converted:
                continue
            aws_field, aws_value = next(iter(converted.items()))
            if _training_job_mapping_differs(aws_value, existing.get(aws_field)):
                values[field] = desired

    resource_config = module.params.get("resource_config")
    if resource_config and resource_config.get("keep_alive_period_in_seconds") is not None:
        desired_retention = resource_config["keep_alive_period_in_seconds"]
        current_retention = existing.get("ResourceConfig", {}).get("KeepAlivePeriodInSeconds")
        if desired_retention != current_retention:
            warm_pool_status = existing.get("WarmPoolStatus", {}).get("Status")
            if desired_retention and warm_pool_status != "Available":
                module.fail_json(
                    msg=(
                        f"Cannot update keep_alive_period_in_seconds for training job "
                        f"{module.params['training_job_name']} unless its warm pool is Available."
                    )
                )
            values["resource_config"] = {"keep_alive_period_in_seconds": desired_retention}

    if "remote_debug_config" in values and existing.get("SecondaryStatus") not in ("Downloading", "Training"):
        module.fail_json(
            msg=(
                f"Cannot update remote_debug_config for training job {module.params['training_job_name']} "
                f"while its secondary status is {existing.get('SecondaryStatus')}."
            )
        )

    params.update(_camelize_training_job_params(values))
    return params


def update_training_job(client, module, existing: Dict[str, Any]) -> bool:
    """Apply supported in-place training job updates when their values differ."""
    params = _training_job_update_params(existing, module)
    if len(params) == 1:
        return False
    if module.check_mode:
        return True
    client.update_training_job(**params)
    if params.get("ResourceConfig", {}).get("KeepAlivePeriodInSeconds") == 0 and module.params["wait"]:
        _wait_for_warm_pool_termination(client, module, module.params["training_job_name"])
    return True


def stop_training_job(client, training_job_name: str) -> None:
    """Stop a running SageMaker training job."""
    try:
        client.stop_training_job(TrainingJobName=training_job_name)
    except is_boto3_error_code("ResourceNotFound"):
        return


@AWSRetry.jittered_backoff(retries=10)
def _set_training_job_warm_pool_retention(client, training_job_name: str, retention_seconds: int) -> None:
    client.update_training_job(
        TrainingJobName=training_job_name,
        ResourceConfig={"KeepAlivePeriodInSeconds": retention_seconds},
    )


@AWSRetry.jittered_backoff(retries=10)
def delete_training_job(client, module, training_job_name: str) -> None:
    """Delete a terminal SageMaker training job."""
    if not module.botocore_at_least("1.40.61"):
        module.fail_json(
            msg=(
                f"Cannot delete training job {training_job_name}: deleting SageMaker training jobs "
                "requires botocore >= 1.40.61."
            )
        )
    try:
        client.delete_training_job(TrainingJobName=training_job_name)
    except is_boto3_error_code("ResourceInUse") as e:
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        module.fail_json(
            msg=(
                f"Cannot delete training job {training_job_name}; it must be Completed, Failed, or Stopped "
                "and must not have an Available warm pool. "
                f"AWS returned: {error_msg}"
            )
        )
    except is_boto3_error_code("ResourceNotFound"):
        return


def reconcile_training_job_tags(client, module, existing: Dict[str, Any]) -> bool:
    """Reconcile training job tags when the caller explicitly supplies tags."""
    return reconcile_sagemaker_tags(client, module, existing["TrainingJobArn"])


def wait_for_training_job(
    client, module, training_job_name: str, allow_failed: bool = False
) -> Optional[Dict[str, Any]]:
    """Wait for a training job to complete or stop using SageMaker's botocore waiter."""
    wait_timeout = module.params["wait_timeout"]
    delay = min(120, max(1, wait_timeout))
    max_attempts = max(1, wait_timeout // delay + 1)
    waiter = client.get_waiter("training_job_completed_or_stopped")
    try:
        waiter.wait(
            TrainingJobName=training_job_name,
            WaiterConfig={"Delay": delay, "MaxAttempts": max_attempts},
        )
    except WaiterError as e:
        last_response = e.last_response
        if not isinstance(last_response, dict):
            last_response = {}
        if allow_failed and last_response.get("TrainingJobStatus") == "Failed":
            return describe_training_job(client, training_job_name)
        error_response = last_response.get("Error")
        if isinstance(error_response, dict):
            error_code = error_response.get("Code")
            if error_code == "ResourceNotFound":
                return None
            if error_code == "ValidationException":
                module.fail_json(
                    msg=f"Error waiting for training job {training_job_name}: {error_response.get('Message') or e}"
                )
        existing = describe_training_job(client, training_job_name)
        reason = existing.get("FailureReason", "") if existing else ""
        module.fail_json(msg=f"Error waiting for training job {training_job_name} to complete or stop: {reason or e}")
    return describe_training_job(client, training_job_name)


def wait_for_training_job_deletion(client, module, training_job_name: str) -> None:
    """Wait until DescribeTrainingJob reports that the training job no longer exists."""
    deadline = time.monotonic() + module.params["wait_timeout"]
    while True:
        if describe_training_job(client, training_job_name) is None:
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            module.fail_json(
                msg=(
                    f"Timed out waiting for training job {training_job_name} to be deleted "
                    f"after {module.params['wait_timeout']} seconds."
                )
            )
        time.sleep(min(15, remaining))


def _wait_for_warm_pool_termination(client, module, training_job_name: str) -> Optional[Dict[str, Any]]:
    deadline = time.monotonic() + module.params["wait_timeout"]
    while True:
        existing = describe_training_job(client, training_job_name)
        if existing is None or existing.get("WarmPoolStatus", {}).get("Status") != "Available":
            return existing
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            module.fail_json(
                msg=(
                    f"Timed out waiting for the warm pool of training job {training_job_name} "
                    "to stop being Available."
                )
            )
        time.sleep(min(15, remaining))


def _validate_training_job_create_params(module) -> None:
    required = ("role_arn", "algorithm_specification", "output_data_config", "resource_config")
    missing = [field for field in required if module.params.get(field) is None]
    if missing:
        module.fail_json(msg=f"These options are required when creating a training job: {', '.join(missing)}.")
    resource_config = module.params["resource_config"]
    missing_resource_fields = [
        field
        for field in ("instance_type", "instance_count", "volume_size_in_gb")
        if resource_config.get(field) is None
    ]
    if missing_resource_fields:
        module.fail_json(
            msg=(
                "These resource_config options are required when creating a training job: "
                f"{', '.join(missing_resource_fields)}."
            )
        )


def _fresh_training_job(client, module) -> Optional[Dict[str, Any]]:
    name = module.params["training_job_name"]
    if module.params["wait"]:
        return wait_for_training_job(client, module, name)
    return describe_training_job(client, name)


def _stop_training_job_before_deletion(
    client, module, existing: Dict[str, Any], purpose: str
) -> Tuple[Dict[str, Any], bool, Optional[str]]:
    name = module.params["training_job_name"]
    status = existing.get("TrainingJobStatus")
    if status not in ("InProgress", "Stopping"):
        return existing, False, None

    changed = status == "InProgress"
    if status == "InProgress":
        stop_training_job(client, name)
    if module.params["wait"]:
        existing = wait_for_training_job(client, module, name, allow_failed=True)
        return existing, changed, None
    latest = describe_training_job(client, name) or existing
    if changed:
        return latest, changed, f"Training job {name} is stopping before {purpose}."
    return latest, changed, f"Training job {name} is already stopping before {purpose}."


def _prepare_training_job_deletion(
    client, module, existing: Dict[str, Any], operation: str
) -> Tuple[Optional[Dict[str, Any]], bool, Optional[str]]:
    name = module.params["training_job_name"]
    purpose = "replacement" if operation == "replace" else "deletion"
    existing, changed, msg = _stop_training_job_before_deletion(client, module, existing, purpose)
    if msg is not None:
        return existing, changed, msg

    existing = describe_training_job(client, name)
    if existing is None:
        return None, changed, f"Training job {name} no longer exists before {purpose}."

    status = existing.get("TrainingJobStatus")
    if status not in ("Completed", "Failed", "Stopped"):
        module.fail_json(msg=f"Cannot {operation} training job {name} while it is in state {status}.")

    if existing.get("WarmPoolStatus", {}).get("Status") == "Available":
        _set_training_job_warm_pool_retention(client, name, 0)
        changed = True
        if not module.params["wait"]:
            return (
                describe_training_job(client, name) or existing,
                changed,
                f"Training job {name} warm pool is terminating before {purpose}.",
            )
        existing = _wait_for_warm_pool_termination(client, module, name) or existing

    existing = describe_training_job(client, name)
    if existing is None:
        return None, changed, f"Training job {name} no longer exists before {purpose}."
    status = existing.get("TrainingJobStatus")
    if status not in ("Completed", "Failed", "Stopped"):
        module.fail_json(msg=f"Cannot {operation} training job {name} while it is in state {status}.")
    return existing, changed, None


def _replace_training_job(client, module, existing: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], bool, str]:
    name = module.params["training_job_name"]
    existing, changed, msg = _prepare_training_job_deletion(client, module, existing, "replace")
    if msg is not None:
        return existing, changed, msg
    delete_training_job(client, module, name)
    changed = True
    if not module.params["wait"]:
        return (
            describe_training_job(client, name) or existing,
            changed,
            f"Training job {name} deletion was initiated before replacement.",
        )
    wait_for_training_job_deletion(client, module, name)

    client.create_training_job(**training_job_params(module))
    final_job = _fresh_training_job(client, module)
    return final_job, changed, f"Training job {name} replaced with a new execution."


def _replace_training_job_if_allowed(
    client, module, existing: Dict[str, Any]
) -> Tuple[Optional[Dict[str, Any]], bool, str]:
    _validate_training_job_create_params(module)
    if module.check_mode:
        return existing, True, f"Check mode: would have replaced training job {module.params['training_job_name']}."
    return _replace_training_job(client, module, existing)


def _reconcile_training_job(client, module, existing: Dict[str, Any]) -> Tuple[Dict[str, Any], bool, str]:
    name = module.params["training_job_name"]
    updated = update_training_job(client, module, existing)
    tags_changed = reconcile_training_job_tags(client, module, existing)
    changed = updated or tags_changed
    if module.check_mode:
        if changed:
            return existing, True, f"Check mode: would have updated training job {name}."
        return existing, False, f"Training job {name} is already up to date."

    final_job = describe_training_job(client, name) or existing
    if changed:
        return final_job, True, f"Training job {name} updated successfully."
    return final_job, False, f"Training job {name} is already up to date."


def _manage_training_job_present(
    client, module, existing: Optional[Dict[str, Any]]
) -> Tuple[Optional[Dict[str, Any]], bool, str]:
    name = module.params["training_job_name"]
    if existing is None:
        _validate_training_job_create_params(module)
        if module.check_mode:
            return None, True, f"Check mode: would have created training job {name}."
        client.create_training_job(**training_job_params(module))
        job = _fresh_training_job(client, module)
        return job, True, f"Training job {name} created successfully."

    status = existing.get("TrainingJobStatus")
    if status in ("Completed", "Failed", "Stopped"):
        if module.params["force"]:
            return _replace_training_job_if_allowed(client, module, existing)
    elif status == "Deleting":
        module.fail_json(msg=f"Cannot manage training job {name} while it is being deleted.")
    elif status != "InProgress":
        module.fail_json(msg=f"Cannot manage training job {name} while it is in state {status}.")

    replacement_fields = training_job_needs_replacement(existing, module)
    if replacement_fields and not module.params["force"]:
        module.fail_json(
            msg=(
                f"Training job {name} differs in create-only options: {', '.join(replacement_fields)}. "
                "Set force: true to delete it and create a new execution."
            )
        )
    if replacement_fields and module.params["force"]:
        return _replace_training_job_if_allowed(client, module, existing)
    return _reconcile_training_job(client, module, existing)


def _manage_training_job_stopped(
    client, module, existing: Optional[Dict[str, Any]]
) -> Tuple[Optional[Dict[str, Any]], bool, str]:
    name = module.params["training_job_name"]
    if existing is None:
        return None, False, f"Training job {name} does not exist."

    status = existing.get("TrainingJobStatus")
    if status in ("Completed", "Failed", "Stopped"):
        return existing, False, f"Training job {name} is already in terminal state {status}."
    if status == "Deleting":
        module.fail_json(msg=f"Cannot stop training job {name} while it is being deleted.")
    if status == "InProgress":
        if module.check_mode:
            return existing, True, f"Check mode: would have stopped training job {name}."
        stop_training_job(client, name)
        if not module.params["wait"]:
            return describe_training_job(client, name) or existing, True, f"Training job {name} is stopping."
    elif status == "Stopping":
        if not module.params["wait"]:
            return existing, False, f"Training job {name} is already stopping."
    else:
        module.fail_json(msg=f"Cannot stop training job {name} while it is in state {status}.")

    final_job = wait_for_training_job(client, module, name, allow_failed=True)
    if final_job and final_job.get("TrainingJobStatus") == "Stopped":
        return final_job, status == "InProgress", f"Training job {name} stopped successfully."
    if final_job:
        return (
            final_job,
            status == "InProgress",
            (f"Training job {name} reached terminal state {final_job.get('TrainingJobStatus')} before it stopped."),
        )
    return None, status == "InProgress", f"Training job {name} is no longer available."


def _manage_training_job_absent(
    client, module, existing: Optional[Dict[str, Any]]
) -> Tuple[Optional[Dict[str, Any]], bool, str]:
    name = module.params["training_job_name"]
    if existing is None:
        return None, False, f"Training job {name} does not exist."
    if existing.get("TrainingJobStatus") == "Deleting":
        if module.check_mode:
            return existing, False, f"Training job {name} is already being deleted."
        if module.params["wait"]:
            wait_for_training_job_deletion(client, module, name)
        return existing, False, f"Training job {name} is already being deleted."
    if module.check_mode:
        return existing, True, f"Check mode: would have deleted training job {name}."

    existing, changed, msg = _prepare_training_job_deletion(client, module, existing, "delete")
    if msg is not None:
        return existing, changed, msg
    delete_training_job(client, module, name)
    changed = True
    if module.params["wait"]:
        wait_for_training_job_deletion(client, module, name)
        return existing, changed, f"Training job {name} deleted successfully."
    return describe_training_job(client, name) or existing, changed, f"Training job {name} deletion was initiated."


def manage_training_job(
    client, module, existing: Optional[Dict[str, Any]]
) -> Tuple[Optional[Dict[str, Any]], bool, str]:
    """Reconcile a SageMaker training job to the requested state."""
    state = module.params["state"]
    if state == "present":
        return _manage_training_job_present(client, module, existing)
    if state == "stopped":
        job, changed, msg = _manage_training_job_stopped(client, module, existing)
        tags_changed = bool(job and reconcile_training_job_tags(client, module, job))
        if tags_changed:
            previously_changed = changed
            changed = True
            if module.check_mode:
                if previously_changed:
                    msg += " Tags would also be updated."
                else:
                    msg = f"Check mode: would have updated training job {module.params['training_job_name']} tags."
            elif not previously_changed:
                msg = f"Training job {module.params['training_job_name']} tags updated successfully."
        return job, changed, msg
    return _manage_training_job_absent(client, module, existing)
