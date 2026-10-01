#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_model_package
short_description: Manage Amazon SageMaker model packages
version_added: "2.0.0"
author:
    - Jan Likar (@JanLikar)
description:
    - Create, update, and delete Amazon SageMaker model packages.
    - Reconcile tags on an existing model package.
options:
    state:
        description:
            - The desired state of the model package.
        type: str
        choices: [present, absent]
        default: present
    model_package_name:
        description:
            - The name of the model package to manage.
            - Required for updates and deletes, and for standalone package creation.
            - Omit this option when creating a package inside an existing model package group.
        type: str
        aliases: ['name']
    model_package_group_name:
        description:
            - The name of the model package group in which the package should be created.
            - Mutually exclusive with O(model_package_name).
        type: str
    model_package_description:
        description:
            - The description of the model package.
        type: str
    model_package_registration_type:
        description:
            - The registration type for the model package.
        type: str
        choices: [Logged, Registered]
    model_approval_status:
        description:
            - The approval status that should be applied to the package.
        type: str
        choices: [Approved, Rejected, PendingManualApproval]
    approval_description:
        description:
            - Additional approval notes for the model package.
        type: str
    model_life_cycle:
        description:
            - The lifecycle stage of the model package.
        type: dict
    inference_specification:
        description:
            - The inference specification used for the package.
        type: dict
    validation_specification:
        description:
            - Validation configuration for the package.
        type: dict
    source_algorithm_specification:
        description:
            - Source algorithm specification for model package creation.
        type: dict
    certify_for_marketplace:
        description:
            - Whether the model is certified for the AWS Marketplace.
        type: bool
    additional_inference_specifications:
        description:
            - Additional inference specifications to add when creating the package.
        type: list
        elements: dict
    model_card:
        description:
            - Model card information for the package.
        type: dict
    model_metrics:
        description:
            - Model metrics for the package.
        type: dict
    domain:
        description:
            - The machine learning domain for the package.
        type: str
    task:
        description:
            - The machine learning task for the package.
        type: str
    sample_payload_url:
        description:
            - The S3 URI of a sample payload for the package.
        type: str
    skip_model_validation:
        description:
            - Whether to skip model validation.
        type: bool
    drift_check_baselines:
        description:
            - Drift check baseline configuration for the package.
        type: dict
    security_config:
        description:
            - Security configuration for the package.
        type: dict
    source_uri:
        description:
            - The source URI for the package.
        type: str
    metadata_properties:
        description:
            - Metadata properties for the package.
        type: dict
    customer_metadata_properties:
        description:
            - Customer metadata to attach to the package.
        type: dict
    customer_metadata_properties_to_remove:
        description:
            - Metadata keys to remove from the package.
        type: list
        elements: str
    additional_inference_specifications_to_add:
        description:
            - Additional inference specifications used to update the package.
        type: list
        elements: dict
    tags:
        description:
            - Tags to apply to a standalone model package.
            - Cannot be used with O(model_package_group_name) because SageMaker versioned packages
              inherit tags from their model package group.
        type: dict
        aliases: ['resource_tags']
    purge_tags:
        description:
            - Whether tags omitted from O(tags) should be removed.
        type: bool
        default: true
    wait:
        description:
            - Whether to wait until the model package reaches a terminal status.
        type: bool
        default: true
    wait_timeout:
        description:
            - Maximum time to wait for a model package to reach a terminal state.
        type: int
        default: 600
notes:
    - 'Requires the following IAM permissions:'
    - sagemaker:CreateModelPackage
    - sagemaker:DescribeModelPackage
    - sagemaker:UpdateModelPackage
    - sagemaker:DeleteModelPackage
    - sagemaker:AddTags
    - sagemaker:ListTags
    - sagemaker:DeleteTags
seealso:
    - module: amazon.ai.sagemaker_model_package_info
      description: Retrieve details for a single model package or list matching packages.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
attributes:
    check_mode:
        description:
            - Supports running in check mode and reporting what would change.
        support: full
"""

EXAMPLES = r"""
- name: Create a SageMaker model package in a model package group
  amazon.ai.sagemaker_model_package:
    state: present
    model_package_group_name: example-model-package-group
    model_package_description: Demo model package
    model_approval_status: PendingManualApproval

- name: Update approval status on an existing model package
  amazon.ai.sagemaker_model_package:
    state: present
    model_package_name: example-model-package
    model_approval_status: Approved
    approval_description: Approved after validation.

- name: Delete a model package
  amazon.ai.sagemaker_model_package:
    state: absent
    model_package_name: example-model-package
"""

RETURN = r"""
model_package:
    description: A dictionary containing the managed model package.
    type: dict
    returned: on success when O(state=present)
    sample:
        model_package_name: example-model-package
        model_package_arn: arn:aws:sagemaker:us-east-1:123456789012:model-package/example-model-package
        model_package_description: Demo model package
        model_approval_status: PendingManualApproval
        creation_time: '2025-01-01T00:00:00+00:00'
        tags:
            project: demo
    contains:
        model_package_name:
            description: The name of the model package.
            type: str
            sample: example-model-package
        model_package_arn:
            description: The ARN of the model package.
            type: str
            sample: arn:aws:sagemaker:us-east-1:123456789012:model-package/example-model-package
        model_package_description:
            description: The description of the model package.
            type: str
            sample: Demo model package
        model_approval_status:
            description: The approval status of the package.
            type: str
            sample: PendingManualApproval
        creation_time:
            description: The creation time of the package.
            type: str
            sample: '2025-01-01T00:00:00+00:00'
        tags:
            description: The tags assigned to the model package, returned when O(tags) is specified.
            type: dict
            returned: when O(tags) is specified
            sample:
                project: demo
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: Model package example-model-package created successfully.
tags:
    description: The current tags assigned to the standalone model package or inherited from its model package group.
    type: dict
    returned: on success when O(state=present) and O(tags) is specified
    sample:
        project: demo
"""

try:
    import botocore
except ImportError:
    pass

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _model_package_values_match
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _normalize_model_package_compare_value
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _preserve_custom_metadata_keys
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_model_package
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_model_package
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_model_package
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import get_model_package_tag_arn
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_package_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_model_package
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_model_package_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_model_package_status

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _normalize_model_package(package: Dict[str, Any], tags: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    normalized: Dict[str, Any] = camel_dict_to_snake_dict(package, ignore_list=["tags"])
    if "CustomerMetadataProperties" in package:
        normalized["customer_metadata_properties"] = _preserve_custom_metadata_keys(
            package["CustomerMetadataProperties"]
        )
    if tags is not None:
        normalized["tags"] = tags
    return normalized


def _wait_for_model_package_status(client, module, model_package_name: Optional[str]) -> None:
    try:
        wait_for_model_package_status(client, model_package_name, wait_timeout=module.params["wait_timeout"])
    except (RuntimeError, TimeoutError) as e:
        module.fail_json(msg=str(e))


def _validate_model_package_create_params(module) -> None:
    if not (module.params.get("model_package_name") or module.params.get("model_package_group_name")):
        module.fail_json(msg="One of model_package_name or model_package_group_name must be provided.")

    if not (module.params.get("inference_specification") or module.params.get("source_algorithm_specification")):
        module.fail_json(
            msg="One of inference_specification or source_algorithm_specification is required when creating a model package."
        )

    update_only_fields = [
        "additional_inference_specifications_to_add",
        "customer_metadata_properties_to_remove",
    ]
    for field in update_only_fields:
        if module.params.get(field) is not None:
            module.fail_json(msg=f"{field} can only be used when updating an existing model package.")


def _ensure_present(client, module, existing: Optional[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    if module.params.get("model_package_name") and module.params.get("model_package_group_name"):
        module.fail_json(
            msg="Specify only one of model_package_name or model_package_group_name when creating or updating a model package."
        )

    if existing is not None and existing.get("ModelPackageStatus") == "Deleting":
        module.fail_json(
            msg=(
                f"Model package {existing.get('ModelPackageName', module.params.get('model_package_name'))} is currently "
                "being deleted. Wait for deletion to complete before recreating or updating it."
            )
        )

    desired_tags: Optional[Dict[str, str]] = module.params.get("tags")
    result: Dict[str, Any] = {"msg": "", "model_package": {}}
    if existing is None:
        _validate_model_package_create_params(module)
        if desired_tags is not None and module.params.get("model_package_group_name"):
            module.fail_json(
                msg=(
                    "Tags cannot be specified when creating a model package in a model package group. "
                    "Manage inherited tags on the model package group instead."
                )
            )
        changed, result["msg"], created_package_arn = create_model_package(client, module)
        if not module.check_mode:
            package_identifier = created_package_arn or module.params.get("model_package_name")
            if module.params.get("wait") and package_identifier is not None:
                _wait_for_model_package_status(client, module, package_identifier)
            if package_identifier is not None:
                existing = describe_model_package(client, package_identifier)
            if existing is not None:
                if module.params.get("tags") is not None:
                    tag_arn = get_model_package_tag_arn(existing, client)
                    tags = list_tags(client, tag_arn or existing["ModelPackageArn"])
                    result["model_package"] = _normalize_model_package(existing, tags)
                    result["tags"] = tags
                else:
                    result["model_package"] = _normalize_model_package(existing)
        return changed, result

    create_only_fields = (
        "model_package_group_name",
        "model_package_description",
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
        "metadata_properties",
        "model_package_registration_type",
    )
    for param_name in create_only_fields:
        desired_value = _normalize_model_package_compare_value(module.params.get(param_name))
        api_name = next(iter(snake_dict_to_camel_dict({param_name: None}, capitalize_first=True)))
        if desired_value is not None and not _model_package_values_match(existing.get(api_name), desired_value):
            module.fail_json(
                msg=(
                    f"SageMaker model package field {param_name} is create-only and cannot be changed in place. "
                    "Delete and recreate the package to change it."
                )
            )

    messages: List[str] = []
    changed = False
    tag_target_arn = get_model_package_tag_arn(existing, client)
    if desired_tags is not None:
        if existing.get("ModelPackageGroupName") or existing.get("ModelPackageGroupArn"):
            module.fail_json(
                msg=(
                    "Tags cannot be reconciled on model packages in a model package group. "
                    "Manage inherited tags on the model package group instead."
                )
            )
        tag_changed, tag_msg = update_model_package_tags(
            client,
            module,
            tag_target_arn,
            desired_tags,
            purge_tags=module.params["purge_tags"],
        )
        changed = changed or tag_changed
        if tag_msg != "No updates needed.":
            messages.append(tag_msg)

    package_name = module.params.get("model_package_name") or existing.get("ModelPackageName")
    if model_package_needs_update(existing, module):
        package_changed, package_msg = update_model_package(client, module, existing["ModelPackageArn"])
        changed = changed or package_changed
        if package_msg != "No updates needed.":
            messages.append(package_msg)
        if module.params.get("wait") and not module.check_mode:
            _wait_for_model_package_status(client, module, package_name)

    if changed or desired_tags is not None:
        existing = describe_model_package(client, package_name)

    tags = None
    if module.params.get("tags") is not None:
        effective_tag_arn = get_model_package_tag_arn(existing) or existing["ModelPackageArn"]
        tags = list_tags(client, effective_tag_arn)
    result["model_package"] = _normalize_model_package(existing, tags)
    if tags is not None:
        result["tags"] = tags
    result["msg"] = " ".join(messages) if messages else "No updates needed."
    return changed, result


def _ensure_absent(client, module, existing: Optional[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    if existing is None:
        return False, {"msg": "Model package does not exist."}

    if existing.get("ModelPackageStatus") == "Deleting":
        if module.params.get("wait") and not module.check_mode:
            _wait_for_model_package_status(client, module, module.params.get("model_package_name"))
        return False, {"msg": "Model package is already being deleted."}

    changed, msg = delete_model_package(client, module)
    if module.params.get("wait") and not module.check_mode:
        _wait_for_model_package_status(client, module, module.params.get("model_package_name"))
    return changed, {"msg": msg}


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        model_package_name=dict(type="str", aliases=["name"]),
        model_package_group_name=dict(type="str"),
        model_package_description=dict(type="str"),
        model_package_registration_type=dict(type="str", choices=["Logged", "Registered"]),
        model_approval_status=dict(type="str", choices=["Approved", "Rejected", "PendingManualApproval"]),
        approval_description=dict(type="str"),
        model_life_cycle=dict(type="dict"),
        inference_specification=dict(type="dict"),
        validation_specification=dict(type="dict"),
        source_algorithm_specification=dict(type="dict"),
        certify_for_marketplace=dict(type="bool"),
        additional_inference_specifications=dict(type="list", elements="dict"),
        model_card=dict(type="dict"),
        model_metrics=dict(type="dict"),
        domain=dict(type="str"),
        task=dict(type="str"),
        sample_payload_url=dict(type="str"),
        skip_model_validation=dict(type="bool"),
        drift_check_baselines=dict(type="dict"),
        security_config=dict(type="dict"),
        source_uri=dict(type="str"),
        metadata_properties=dict(type="dict"),
        customer_metadata_properties=dict(type="dict"),
        customer_metadata_properties_to_remove=dict(type="list", elements="str"),
        additional_inference_specifications_to_add=dict(type="list", elements="dict"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[("state", "absent", ["model_package_name"])],
        mutually_exclusive=[("model_package_name", "model_package_group_name")],
    )

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing: Optional[Dict[str, Any]] = None
        if module.params.get("model_package_name"):
            existing = describe_model_package(client, module.params["model_package_name"])
        if module.params["state"] == "present":
            changed, result = _ensure_present(client, module, existing)
        else:
            changed, result = _ensure_absent(client, module, existing)

        module.exit_json(changed=changed, **result)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
