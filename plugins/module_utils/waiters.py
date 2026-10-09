# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import Any

try:
    import botocore.waiter as core_waiter
    from botocore.exceptions import WaiterError
except ImportError:
    pass

try:
    from ansible_collections.amazon.aws.plugins.module_utils.retries import RetryingBotoClientWrapper
except ImportError:
    try:
        from ansible_collections.amazon.aws.plugins.module_utils.modules import (
            _RetryingBotoClientWrapper as RetryingBotoClientWrapper,
        )
    except ImportError:
        RetryingBotoClientWrapper = None


model_package_group_data = {
    "version": 2,
    "waiters": {
        "ModelPackageGroupDeleted": {
            "description": "Wait until a SageMaker model package group is deleted",
            "delay": 15,
            "maxAttempts": 40,
            "operation": "DescribeModelPackageGroup",
            "acceptors": [
                {
                    "matcher": "error",
                    "expected": "ValidationException",
                    "state": "success",
                }
            ],
        }
    },
}

# botocore ships an ImageVersionDeleted waiter, but its success acceptor expects the error code
# ResourceNotFoundException, while DescribeImageVersion raises ResourceNotFound. The native waiter
# therefore reports a completed delete as a WaiterError, so this copy fixes the error code.
image_version_data = {
    "version": 2,
    "waiters": {
        "ImageVersionDeleted": {
            "description": "Wait until a SageMaker image version is deleted",
            "delay": 15,
            "maxAttempts": 40,
            "operation": "DescribeImageVersion",
            "acceptors": [
                {
                    "matcher": "error",
                    "expected": "ResourceNotFound",
                    "state": "success",
                },
                {
                    "matcher": "path",
                    "argument": "ImageVersionStatus",
                    "expected": "DELETE_FAILED",
                    "state": "failure",
                },
            ],
        }
    },
}


def model_package_group_model(name: str) -> Any:
    return core_waiter.WaiterModel(waiter_config=model_package_group_data).get_waiter(name)


def image_version_model(name: str) -> Any:
    return core_waiter.WaiterModel(waiter_config=image_version_data).get_waiter(name)


waiters_by_name = {
    (
        "SageMaker",
        "model_package_group_deleted",
    ): lambda sagemaker: core_waiter.Waiter(
        "model_package_group_deleted",
        model_package_group_model("ModelPackageGroupDeleted"),
        core_waiter.NormalizedOperationMethod(sagemaker.describe_model_package_group),
    ),
    (
        "SageMaker",
        "image_version_deleted",
    ): lambda sagemaker: core_waiter.Waiter(
        "image_version_deleted",
        image_version_model("ImageVersionDeleted"),
        core_waiter.NormalizedOperationMethod(sagemaker.describe_image_version),
    ),
}


def get_waiter(client, waiter_name: str) -> Any:
    if RetryingBotoClientWrapper is not None and isinstance(client, RetryingBotoClientWrapper):
        return get_waiter(client.client, waiter_name)
    try:
        return waiters_by_name[(client.__class__.__name__, waiter_name)](client)
    except KeyError:
        raise NotImplementedError(
            "Waiter {0} could not be found for client {1}. Available waiters: {2}".format(
                waiter_name,
                type(client),
                ", ".join(repr(key) for key in waiters_by_name.keys()),
            )
        )


def wait_for_model_package_group_deletion(
    client, module, model_package_group_name: str, wait_timeout: int = 600
) -> None:
    """Wait until a SageMaker model package group is actually gone."""
    if not module.params.get("wait", True):
        return

    delay = 15
    max_attempts = max(1, wait_timeout // delay)
    waiter = get_waiter(client, "model_package_group_deleted")
    try:
        waiter.wait(
            ModelPackageGroupName=model_package_group_name,
            WaiterConfig={"Delay": delay, "MaxAttempts": max_attempts},
        )
    except WaiterError:
        module.fail_json(
            msg=(
                f"Timeout waiting for model package group {model_package_group_name} to be deleted. "
                "The resource still exists after the configured wait timeout."
            )
        )


def wait_for_image_version_deletion(client, module, image_name: str, version: int, wait_timeout: int = 600) -> None:
    """Wait until a SageMaker image version is actually gone."""
    if not module.params.get("wait", True):
        return

    delay = 15
    max_attempts = max(1, wait_timeout // delay)
    waiter = get_waiter(client, "image_version_deleted")
    try:
        waiter.wait(
            ImageName=image_name,
            Version=version,
            WaiterConfig={"Delay": delay, "MaxAttempts": max_attempts},
        )
    except WaiterError as e:
        last_response = e.last_response or {}
        if last_response.get("ImageVersionStatus") == "DELETE_FAILED":
            module.fail_json(
                msg=(
                    f"SageMaker image version {image_name}:{version} entered DELETE_FAILED state: "
                    f"{last_response.get('FailureReason', 'no reason reported')}"
                )
            )
        module.fail_json(msg=f"Error waiting for SageMaker image version {image_name}:{version} to be deleted: {e}")
