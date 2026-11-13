#!/usr/bin/python

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_inference_component
short_description: Manage Amazon SageMaker inference components
version_added: "2.1.0"
author:
    - Peter Grlica (@petergrlica)
description:
    - Create, update, and delete Amazon SageMaker inference components.
    - An inference component deploys a model on an existing real-time endpoint with its own compute reservation and number of copies.
    - The endpoint, its configuration, the model, and the IAM role are managed separately.
options:
    state:
        description: The desired state of the inference component.
        type: str
        choices: [present, absent]
        default: present
    inference_component_name:
        description:
            - The name of the inference component.
            - It cannot be changed on an existing inference component.
        type: str
        required: true
        aliases: [name]
    endpoint_name:
        description:
            - The name of the existing endpoint that hosts the inference component.
            - Required when O(state=present).
            - It cannot be changed on an existing inference component.
        type: str
    variant_name:
        description:
            - The name of the existing production variant of the endpoint that hosts the inference component.
            - It cannot be changed on an existing inference component.
        type: str
    specification:
        description:
            - The deployment specification of the inference component.
            - Only the suboptions that are set are compared with the existing inference component.
            - When a difference is found, the suboptions that are set are sent as the new specification.
        type: dict
        suboptions:
            model_name:
                description: The name of an existing SageMaker model to deploy.
                type: str
            container:
                description: The container to deploy.
                type: dict
                suboptions:
                    image:
                        description: The Amazon ECR path of the container image.
                        type: str
                    artifact_url:
                        description: The Amazon S3 or HTTPS location of a single C(.tar.gz) model artifact.
                        type: str
                    environment:
                        description: Environment variables to set in the container.
                        type: dict
            startup_parameters:
                description: Timeouts applied while the container starts.
                type: dict
                suboptions:
                    model_data_download_timeout_in_seconds:
                        description: The timeout, in seconds, for downloading the model artifacts. Between 60 and 3600.
                        type: int
                    container_startup_health_check_timeout_in_seconds:
                        description: The timeout, in seconds, for the container health check. Between 60 and 3600.
                        type: int
            compute_resource_requirements:
                description:
                    - The compute resources to reserve for each copy of the inference component.
                    - Omit it for an adapter inference component.
                type: dict
                suboptions:
                    min_memory_required_in_mb:
                        description: The minimum memory, in MB, that each copy requires. At least 128.
                        type: int
                        required: true
                    max_memory_required_in_mb:
                        description: The maximum memory, in MB, that each copy may use. At least 128.
                        type: int
                    number_of_cpu_cores_required:
                        description: The number of CPU cores that each copy requires. At least 0.25.
                        type: float
                    number_of_accelerator_devices_required:
                        description: The number of accelerators that each copy requires. At least 1.
                        type: float
            base_inference_component_name:
                description: The name of the existing base inference component, to create an adapter inference component.
                type: str
    runtime_config:
        description: The runtime settings of the inference component.
        type: dict
        suboptions:
            copy_count:
                description: The number of copies of the model to deploy. At least 0.
                type: int
                required: true
    tags:
        description: Tags to associate with the inference component.
        type: dict
        aliases: [resource_tags]
    purge_tags:
        description: Whether to remove tags not specified in O(tags).
        type: bool
        default: true
    wait:
        description: Whether to wait for the inference component to reach V(InService), or to be deleted.
        type: bool
        default: true
    wait_timeout:
        description: How long, in seconds, to wait for the inference component to reach the desired state.
        type: int
        default: 600
notes:
    - Required IAM actions include sagemaker:CreateInferenceComponent, sagemaker:DescribeInferenceComponent,
      sagemaker:UpdateInferenceComponent, sagemaker:DeleteInferenceComponent, sagemaker:AddTags,
      sagemaker:ListTags, and sagemaker:DeleteTags.
    - An inference component in the V(Failed) status cannot be updated; delete it and create it again.
    - An inference component created with several specifications cannot be changed with O(specification); delete it and create it again.
    - With O(state=absent), an inference component that is being created or updated is waited for first when O(wait=true).
      The module fails when O(wait=false).
attributes:
    check_mode:
        description: Can run in check mode and report what would change without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_endpoint
      description: Manage SageMaker endpoints.
    - module: amazon.ai.sagemaker_endpoint_config
      description: Manage SageMaker endpoint configurations.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Create an inference component
  amazon.ai.sagemaker_inference_component:
    inference_component_name: my-inference-component
    endpoint_name: my-endpoint
    variant_name: AllTraffic
    specification:
      model_name: my-model
      compute_resource_requirements:
        min_memory_required_in_mb: 1024
        number_of_cpu_cores_required: 1
    runtime_config:
      copy_count: 1
    tags:
      team: ml

- name: Scale an inference component to two copies
  amazon.ai.sagemaker_inference_component:
    inference_component_name: my-inference-component
    runtime_config:
      copy_count: 2

- name: Delete an inference component
  amazon.ai.sagemaker_inference_component:
    state: absent
    inference_component_name: my-inference-component
"""

RETURN = r"""
inference_component:
    description: The inference component after the operation. An empty dictionary when it does not exist.
    type: dict
    returned: always
    contains:
        inference_component_name:
            description: The name of the inference component.
            type: str
        inference_component_arn:
            description: The Amazon Resource Name (ARN) of the inference component.
            type: str
        endpoint_name:
            description: The name of the endpoint that hosts the inference component.
            type: str
        endpoint_arn:
            description: The ARN of the endpoint that hosts the inference component.
            type: str
        variant_name:
            description: The name of the production variant that hosts the inference component.
            type: str
        failure_reason:
            description: The reason for failure, when the inference component is in the V(Failed) status.
            type: str
        specification:
            description: The deployment specification of the inference component.
            type: dict
            contains:
                model_name:
                    description: The name of the SageMaker model.
                    type: str
                container:
                    description: The container of the inference component.
                    type: dict
                    contains:
                        deployed_image:
                            description: The image that is deployed.
                            type: dict
                            contains:
                                specified_image:
                                    description: The image path that was specified.
                                    type: str
                                resolved_image:
                                    description: The image path with its digest, as resolved by SageMaker.
                                    type: str
                                resolution_time:
                                    description: The date and time the image path was resolved.
                                    type: str
                        artifact_url:
                            description: The location of the model artifact.
                            type: str
                        container_metrics_config:
                            description: The container metrics settings.
                            type: dict
                            contains:
                                metrics_endpoints:
                                    description: The endpoints that the container publishes metrics on.
                                    type: list
                                    elements: dict
                                    contains:
                                        metric_publish_frequency_in_seconds:
                                            description: How often, in seconds, the metrics are published.
                                            type: int
                                        metrics_endpoint_path:
                                            description: The path of the metrics endpoint.
                                            type: str
                        environment:
                            description: The environment variables of the container.
                            type: dict
                startup_parameters:
                    description: Timeouts applied while the container starts.
                    type: dict
                    contains:
                        model_data_download_timeout_in_seconds:
                            description: The timeout for downloading the model artifacts.
                            type: int
                        container_startup_health_check_timeout_in_seconds:
                            description: The timeout for the container health check.
                            type: int
                compute_resource_requirements:
                    description: The compute resources reserved for each copy.
                    type: dict
                    contains:
                        min_memory_required_in_mb:
                            description: The minimum memory, in MB.
                            type: int
                        max_memory_required_in_mb:
                            description: The maximum memory, in MB.
                            type: int
                        number_of_cpu_cores_required:
                            description: The number of CPU cores.
                            type: float
                        number_of_accelerator_devices_required:
                            description: The number of accelerators.
                            type: float
                        accelerator_partition_type:
                            description: The accelerator partition type.
                            type: str
                base_inference_component_name:
                    description: The name of the base inference component of an adapter.
                    type: str
                instance_type:
                    description: The instance type that the specification applies to.
                    type: str
                data_cache_config:
                    description: The data caching settings of the inference component.
                    type: dict
                    contains:
                        enable_caching:
                            description: Whether caching is enabled.
                            type: bool
                scheduling_config:
                    description: The scheduling settings of the inference component.
                    type: dict
                    contains:
                        placement_strategy:
                            description: The placement strategy of the copies.
                            type: str
                        availability_zone_balance:
                            description: The Availability Zone balance settings.
                            type: dict
                            contains:
                                enforcement_mode:
                                    description: How strictly the balance is enforced.
                                    type: str
                                max_imbalance:
                                    description: The maximum difference in copies between Availability Zones.
                                    type: int
        specifications:
            description:
                - The specifications of the inference component, one per instance type.
                - Returned instead of RV(inference_component.specification) when the inference component was created with several specifications.
            type: list
            elements: dict
        runtime_config:
            description: The runtime settings of the inference component.
            type: dict
            contains:
                desired_copy_count:
                    description: The number of copies SageMaker is working towards.
                    type: int
                current_copy_count:
                    description: The number of copies that are currently deployed.
                    type: int
                placement_status:
                    description: The placement status of the copies, per instance type.
                    type: list
                    elements: dict
                    contains:
                        instance_type:
                            description: The instance type that hosts the copies.
                            type: str
                        current_copy_count:
                            description: The number of copies currently placed on the instance type.
                            type: int
        creation_time:
            description: The date and time that the inference component was created.
            type: str
        last_modified_time:
            description: The date and time that the inference component was last modified.
            type: str
        inference_component_status:
            description: The status of the inference component.
            type: str
        last_deployment_config:
            description: The deployment configuration of the most recent update.
            type: dict
            contains:
                rolling_update_policy:
                    description: The rolling update settings.
                    type: dict
                    contains:
                        maximum_batch_size:
                            description: The batch size of each rolling step.
                            type: dict
                            contains:
                                type:
                                    description: Whether the value is a number of copies or a percentage of capacity.
                                    type: str
                                value:
                                    description: The batch size.
                                    type: int
                        wait_interval_in_seconds:
                            description: The time, in seconds, to wait between rolling steps.
                            type: int
                        maximum_execution_timeout_in_seconds:
                            description: The maximum time, in seconds, that the deployment may run.
                            type: int
                        rollback_maximum_batch_size:
                            description: The batch size of each rollback step.
                            type: dict
                            contains:
                                type:
                                    description: Whether the value is a number of copies or a percentage of capacity.
                                    type: str
                                value:
                                    description: The batch size.
                                    type: int
                auto_rollback_configuration:
                    description: The automatic rollback settings.
                    type: dict
                    contains:
                        alarms:
                            description: The CloudWatch alarms that trigger a rollback.
                            type: list
                            elements: dict
                            contains:
                                alarm_name:
                                    description: The name of the alarm.
                                    type: str
        tags:
            description: The tags of the inference component.
            type: dict
    sample:
        inference_component_name: my-inference-component
        inference_component_arn: arn:aws:sagemaker:us-east-1:123456789012:inference-component/my-inference-component
        endpoint_name: my-endpoint
        variant_name: AllTraffic
        inference_component_status: InService
        runtime_config:
            desired_copy_count: 1
            current_copy_count: 1
        tags:
            team: ml
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: Inference component my-inference-component created successfully.
"""

try:
    import botocore
except ImportError:
    pass

from typing import Any
from typing import Dict
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_inference_component
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_inference_component
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_inference_component
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import (
    ensure_inference_component_create_only_unchanged,
)
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import ensure_inference_component_single_specification
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import inference_component_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_inference_component_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_inference_component
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_inference_component_status

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _inference_component_result(client, name: str) -> Dict[str, Any]:
    existing = describe_inference_component(client, name)
    if not existing:
        return {}
    result = camel_dict_to_snake_dict(existing, ignore_list=["Tags", "tags", "Environment"])
    result["tags"] = list_tags(client, existing["InferenceComponentArn"])
    return result


def _inference_component_status_check(
    client, existing: Optional[Dict[str, Any]], state: str, module: AnsibleAWSModule
) -> Optional[Dict[str, Any]]:
    # Early exit, or wait, depending on the transient or failed status of an existing inference component.
    if not existing:
        return existing
    name = module.params["inference_component_name"]
    status = existing["InferenceComponentStatus"]
    if state == "absent":
        if status == "Deleting":
            if not module.check_mode and module.params["wait"]:
                wait_for_inference_component_status(client, module, deleted=True)
            module.exit_json(
                changed=False,
                inference_component={},
                msg=f"Inference component {name} is already being deleted.",
            )
        if status in ("Creating", "Updating"):
            if not module.params["wait"]:
                module.fail_json(
                    msg=(
                        f"Inference component {name} is in the {status} status and cannot be deleted until it finishes. "
                        "Use wait=true to wait for it first, or retry later."
                    )
                )
            if not module.check_mode:
                return wait_for_inference_component_status(client, module, settle=True)
        return existing
    if status == "Deleting":
        module.fail_json(msg=f"Cannot update inference component {name} while it is being deleted.")
    if status == "Failed":
        module.fail_json(
            msg=(
                f"Inference component {name} is in the Failed status: {existing.get('FailureReason', 'unknown reason')}. "
                "Delete it and create it again."
            )
        )
    if status in ("Creating", "Updating"):
        if module.check_mode or not module.params["wait"]:
            module.exit_json(
                changed=False,
                inference_component=_inference_component_result(client, name),
                msg=f"Inference component {name} is currently in {status}.",
            )
        return wait_for_inference_component_status(client, module)
    return existing


def _absent(module, client, name: str, existing: Optional[Dict[str, Any]]) -> None:
    if not existing:
        module.exit_json(changed=False, inference_component={}, msg=f"Inference component {name} does not exist.")
    changed, msg = delete_inference_component(client, module)
    if changed and not module.check_mode and module.params["wait"]:
        wait_for_inference_component_status(client, module, deleted=True)
    module.exit_json(changed=changed, inference_component={}, msg=msg)


def _present(module, client, name: str, existing: Optional[Dict[str, Any]]) -> None:
    if not existing:
        changed, msg = create_inference_component(client, module)
        if module.check_mode:
            module.exit_json(changed=changed, inference_component={}, msg=msg)
        if module.params["wait"]:
            wait_for_inference_component_status(client, module)
        module.exit_json(changed=changed, inference_component=_inference_component_result(client, name), msg=msg)

    ensure_inference_component_create_only_unchanged(existing, module)
    ensure_inference_component_single_specification(existing, module)
    properties_to_update = inference_component_needs_update(existing, module)
    changed = False
    msg = f"Inference component {name} is already up to date."
    if properties_to_update:
        changed, msg = update_inference_component(client, module, properties_to_update)
        if changed and not module.check_mode and module.params["wait"]:
            wait_for_inference_component_status(client, module, previous=existing)
    if reconcile_inference_component_tags(client, module, existing) and not changed:
        changed = True
        msg = (
            f"Check mode: would have updated inference component {name} tags."
            if module.check_mode
            else f"Inference component {name} tags updated successfully."
        )
    module.exit_json(changed=changed, inference_component=_inference_component_result(client, name), msg=msg)


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        inference_component_name=dict(type="str", required=True, aliases=["name"]),
        endpoint_name=dict(type="str"),
        variant_name=dict(type="str"),
        specification=dict(
            type="dict",
            options=dict(
                model_name=dict(type="str"),
                container=dict(
                    type="dict",
                    options=dict(
                        image=dict(type="str"),
                        artifact_url=dict(type="str"),
                        environment=dict(type="dict"),
                    ),
                ),
                startup_parameters=dict(
                    type="dict",
                    options=dict(
                        model_data_download_timeout_in_seconds=dict(type="int"),
                        container_startup_health_check_timeout_in_seconds=dict(type="int"),
                    ),
                ),
                compute_resource_requirements=dict(
                    type="dict",
                    options=dict(
                        min_memory_required_in_mb=dict(type="int", required=True),
                        max_memory_required_in_mb=dict(type="int"),
                        number_of_cpu_cores_required=dict(type="float"),
                        number_of_accelerator_devices_required=dict(type="float"),
                    ),
                ),
                base_inference_component_name=dict(type="str"),
            ),
        ),
        runtime_config=dict(
            type="dict",
            options=dict(copy_count=dict(type="int", required=True)),
        ),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[("state", "present", ["endpoint_name"])],
    )
    name = module.params["inference_component_name"]
    state = module.params["state"]
    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing = describe_inference_component(client, name)
        existing = _inference_component_status_check(client, existing, state, module)
        if state == "absent":
            _absent(module, client, name, existing)
        _present(module, client, name, existing)
    # Botocore errors from the helpers are not converted to AnsibleAWSError, as in the other SageMaker modules.
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
