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
    - >-
      The following options are only applied when creating a package and are ignored on updates:
      O(model_package_group_name), O(model_package_description), O(model_package_registration_type),
      O(inference_specification), O(validation_specification), O(source_algorithm_specification),
      O(certify_for_marketplace), O(additional_inference_specifications), O(model_card), O(model_metrics),
      O(domain), O(task), O(sample_payload_url), O(skip_model_validation), O(drift_check_baselines),
      O(security_config), O(source_uri), and O(metadata_properties).
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
            - Lifecycle information for the model package.
            - Contains required C(stage) and C(stage_status) string fields, and optional C(stage_description).
            - See U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ModelLifeCycle.html).
        type: dict
    inference_specification:
        description:
            - The inference specification used for the package.
            - Contains required C(containers), a list of container definition dictionaries, and optional lists of
              C(supported_content_types), C(supported_realtime_inference_instance_types),
              C(supported_response_mime_types), and C(supported_transform_instance_types).
            - The two instance-type lists are required for unversioned packages and optional for versioned packages.
            - Container dictionaries follow the
              U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ModelPackageContainerDefinition.html)
              structure.
            - See U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_InferenceSpecification.html).
            - Required when creating a package unless O(source_algorithm_specification) is specified.
        type: dict
    validation_specification:
        description:
            - Validation configuration for the package.
            - Contains required C(validation_profiles), a list of validation profile dictionaries, and required
              C(validation_role).
            - Each profile contains required C(profile_name) and C(transform_job_definition). The transform job
              definition requires C(transform_input), C(transform_output), and C(transform_resources).
            - See U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ModelPackageValidationSpecification.html),
              U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ModelPackageValidationProfile.html),
              and U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_TransformJobDefinition.html).
        type: dict
    source_algorithm_specification:
        description:
            - Source algorithm specification for model package creation.
            - Contains required C(source_algorithms), a list with one algorithm dictionary. Each dictionary requires
              C(algorithm_name); C(model_data_etag), C(model_data_source), and C(model_data_url) are optional.
            - See U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_SourceAlgorithmSpecification.html)
              and U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_SourceAlgorithm.html).
            - Required when creating a package unless O(inference_specification) is specified.
        type: dict
    certify_for_marketplace:
        description:
            - Whether the model is certified for the AWS Marketplace.
        type: bool
    additional_inference_specifications:
        description:
            - Additional inference specifications to add when creating the package.
            - Each dictionary requires C(name) and C(containers), a list of container definition dictionaries.
              C(description), C(supported_content_types), C(supported_response_mime_types),
              C(supported_realtime_inference_instance_types), and C(supported_transform_instance_types) are optional.
            - Container dictionaries follow the
              U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ModelPackageContainerDefinition.html)
              structure.
            - See U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_AdditionalInferenceSpecificationDefinition.html).
        type: list
        elements: dict
    model_card:
        description:
            - Model card information for the package.
            - Contains optional C(model_card_content), a JSON string that follows the SageMaker model card schema,
              and C(model_card_status) with values V(Draft), V(PendingReview), V(Approved), or V(Archived).
            - See U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ModelPackageModelCard.html) and
              U(https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry-details.html#model-card-schema).
        type: dict
    model_metrics:
        description:
            - Model metrics for the package.
            - Supports optional C(bias), C(explainability), C(model_data_quality), and C(model_quality) dictionaries.
              Their report, constraints, and statistics fields use metric source dictionaries with required
              C(content_type) and C(s3_uri), and optional C(content_digest).
            - See U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ModelMetrics.html),
              U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_Bias.html),
              U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_Explainability.html),
              U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ModelDataQuality.html),
              U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ModelQuality.html), and
              U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_MetricsSource.html).
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
            - Which model validation checks to skip.
            - Set to V(All) to skip all checks or V(None) to run all checks.
        type: str
        choices: [All, None]
    drift_check_baselines:
        description:
            - Drift check baseline configuration for the package.
            - Supports optional C(bias), C(explainability), C(model_data_quality), and C(model_quality) dictionaries.
              Bias supports C(config_file), C(post_training_constraints), and C(pre_training_constraints);
              explainability supports C(config_file) and C(constraints); each quality dictionary supports
              C(constraints) and C(statistics).
            - C(config_file) uses a file source dictionary with required C(s3_uri) and optional C(content_digest)
              and C(content_type). Constraints and statistics use metric source dictionaries with required
              C(content_type) and C(s3_uri), and optional C(content_digest).
            - See U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DriftCheckBaselines.html),
              U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DriftCheckBias.html),
              U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DriftCheckExplainability.html),
              U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DriftCheckModelDataQuality.html),
              U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DriftCheckModelQuality.html),
              U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_FileSource.html), and
              U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_MetricsSource.html).
        type: dict
    security_config:
        description:
            - Security configuration for the package.
            - Contains required C(kms_key_id), the KMS key identifier used to encrypt the package.
            - See U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ModelPackageSecurityConfig.html).
        type: dict
    source_uri:
        description:
            - The source URI for the package.
        type: str
    metadata_properties:
        description:
            - Metadata properties for the package.
            - Supports optional string fields C(commit_id), C(generated_by), C(project_id), and C(repository).
            - See U(https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_MetadataProperties.html).
        type: dict
    customer_metadata_properties:
        description:
            - Customer metadata to attach to the package as an arbitrary string-to-string dictionary.
            - Customer-defined keys are preserved as supplied.
        type: dict
    customer_metadata_properties_to_remove:
        description:
            - Metadata keys to remove from the package.
        type: list
        elements: str
    additional_inference_specifications_to_add:
        description:
            - Additional inference specifications used to update the package.
            - Uses the same dictionary structure as O(additional_inference_specifications).
        type: list
        elements: dict
    tags:
        description:
            - Tags to apply to a standalone model package as a string-to-string dictionary.
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
    - >-
      ecr:BatchGetImage, when an O(inference_specification) or O(additional_inference_specifications) container
      references an image in Amazon ECR. SageMaker checks that the caller can pull the image when the package is created.
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
    model_package_group_name: "example-model-package-group"
    model_package_description: "Demo model package"
    model_approval_status: "PendingManualApproval"
    inference_specification:
      containers:
        - image: "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-model:latest"
          model_data_url: "s3://my-bucket/model.tar.gz"
      supported_transform_instance_types:
        - "ml.m5.large"

- name: Update approval status on an existing model package
  amazon.ai.sagemaker_model_package:
    state: present
    model_package_name: "example-model-package"
    model_approval_status: "Approved"
    approval_description: "Approved after validation."

- name: Delete a model package
  amazon.ai.sagemaker_model_package:
    state: absent
    model_package_name: "example-model-package"
"""

RETURN = r"""
model_package:
    description: A dictionary containing the managed model package.
    type: dict
    returned: on success when O(state=present)
    sample:
        model_package_name: "example-model-package"
        model_package_arn: "arn:aws:sagemaker:us-east-1:123456789012:model-package/example-model-package"
        model_package_description: "Demo model package"
        model_approval_status: "PendingManualApproval"
        creation_time: "2025-01-01T00:00:00+00:00"
    contains:
        model_package_name:
            description: The name of the model package.
            type: str
            sample: "example-model-package"
        model_package_arn:
            description: The ARN of the model package.
            type: str
            sample: "arn:aws:sagemaker:us-east-1:123456789012:model-package/example-model-package"
        model_package_description:
            description: The description of the model package.
            type: str
            sample: "Demo model package"
        model_approval_status:
            description: The approval status of the package.
            type: str
            sample: "PendingManualApproval"
        creation_time:
            description: The creation time of the package.
            type: str
            sample: "2025-01-01T00:00:00+00:00"
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: "Model package example-model-package created successfully."
tags:
    description: "The current tags assigned to the standalone model package or inherited from its model package group."
    type: dict
    returned: on success when O(state=present)
    sample:
        project: "demo"
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

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

_CREATE_ONLY_FIELD_API_NAMES = {
    "model_package_group_name": "ModelPackageGroupName",
    "model_package_description": "ModelPackageDescription",
    "inference_specification": "InferenceSpecification",
    "validation_specification": "ValidationSpecification",
    "source_algorithm_specification": "SourceAlgorithmSpecification",
    "certify_for_marketplace": "CertifyForMarketplace",
    "additional_inference_specifications": "AdditionalInferenceSpecifications",
    "model_card": "ModelCard",
    "model_metrics": "ModelMetrics",
    "domain": "Domain",
    "task": "Task",
    "sample_payload_url": "SamplePayloadUrl",
    "skip_model_validation": "SkipModelValidation",
    "drift_check_baselines": "DriftCheckBaselines",
    "security_config": "SecurityConfig",
    "source_uri": "SourceUri",
    "metadata_properties": "MetadataProperties",
    "model_package_registration_type": "ModelPackageRegistrationType",
}


def _normalize_model_package(package: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = camel_dict_to_snake_dict(package, ignore_list=["tags"])
    if "CustomerMetadataProperties" in package:
        normalized["customer_metadata_properties"] = package["CustomerMetadataProperties"]
    return normalized


def _wait_for_model_package_status(client, module, model_package_name: Optional[str]) -> None:
    try:
        wait_for_model_package_status(client, model_package_name, wait_timeout=module.params["wait_timeout"])
    except (RuntimeError, TimeoutError) as e:
        module.fail_json(msg=str(e))


def _validate_model_package_create_params(module) -> None:
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


def _ensure_created(client, module) -> Tuple[bool, Dict[str, Any]]:
    result: Dict[str, Any] = {"msg": "", "model_package": {}, "tags": {}}
    _validate_model_package_create_params(module)
    if module.params.get("tags") is not None and module.params.get("model_package_group_name"):
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
        else:
            existing = None
        if existing is not None:
            tag_arn = get_model_package_tag_arn(existing, client)
            result["tags"] = list_tags(client, tag_arn or existing["ModelPackageArn"])
            result["model_package"] = _normalize_model_package(existing)
    return changed, result


def _ensure_updated(client, module, existing: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    desired_tags: Optional[Dict[str, str]] = module.params.get("tags")
    result: Dict[str, Any] = {"msg": "", "model_package": {}, "tags": {}}
    for param_name, api_name in _CREATE_ONLY_FIELD_API_NAMES.items():
        desired_value = _normalize_model_package_compare_value(module.params.get(param_name))
        if desired_value is not None and not _model_package_values_match(existing.get(api_name), desired_value):
            module.warn(
                f"SageMaker model package field {param_name} is create-only and cannot be changed in place; "
                "ignoring the requested value."
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

    package_identifier = (
        module.params.get("model_package_name") or existing.get("ModelPackageName") or existing.get("ModelPackageArn")
    )
    if model_package_needs_update(existing, module):
        package_changed, package_msg = update_model_package(client, module, existing["ModelPackageArn"])
        changed = changed or package_changed
        if package_msg != "No updates needed.":
            messages.append(package_msg)
        if module.params.get("wait") and not module.check_mode:
            _wait_for_model_package_status(client, module, package_identifier)

    if changed or desired_tags is not None:
        existing = describe_model_package(client, package_identifier)

    effective_tag_arn = get_model_package_tag_arn(existing) or existing["ModelPackageArn"]
    result["tags"] = list_tags(client, effective_tag_arn)
    result["model_package"] = _normalize_model_package(existing)
    result["msg"] = " ".join(messages) if messages else "No updates needed."
    return changed, result


def _ensure_present(client, module, existing: Optional[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    if existing is not None and existing.get("ModelPackageStatus") == "Deleting":
        module.fail_json(
            msg=(
                f"Model package {existing.get('ModelPackageName', module.params.get('model_package_name'))} is currently "
                "being deleted. Wait for deletion to complete before recreating or updating it."
            )
        )

    if existing is None:
        return _ensure_created(client, module)
    return _ensure_updated(client, module, existing)


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
        skip_model_validation=dict(type="str", choices=["All", "None"]),
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
        required_one_of=[("model_package_name", "model_package_group_name")],
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
