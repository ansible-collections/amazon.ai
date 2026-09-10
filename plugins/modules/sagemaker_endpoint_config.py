#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_endpoint_config
short_description: Manage Amazon SageMaker endpoint configurations
version_added: "2.0.0"
author:
    - Jan Likar (@JanLikar)
description:
    - Create and delete Amazon SageMaker endpoint configurations.
    - Endpoint configurations are immutable; changing a configuration property requires a replacement.
options:
    state:
        description: The desired state of the endpoint configuration.
        type: str
        choices: [present, absent]
        default: present
    endpoint_config_name:
        description: The name of the endpoint configuration.
        type: str
        required: true
        aliases: [name]
    production_variants:
        description: Production variants for the endpoint configuration. Required when O(state=present).
        type: list
        elements: dict
        suboptions:
            variant_name:
                description: The name of the production variant.
                type: str
                required: true
            model_name:
                description: The name of the SageMaker model.
                type: str
                required: true
            initial_instance_count:
                description: The initial number of instances.
                type: int
            instance_type:
                description: The ML compute instance type.
                type: str
            initial_variant_weight:
                description: The initial traffic weight for the variant.
                type: float
            serverless_config:
                description: Serverless inference configuration.
                type: dict
                suboptions:
                    memory_size_in_m_b:
                        description: The memory size in MB for each inference instance.
                        type: int
                        aliases: [memory_size_in_mb]
                    max_concurrency:
                        description: The maximum number of concurrent invocations.
                        type: int
                    provisioned_concurrency:
                        description: The provisioned concurrency.
                        type: int
            routing_config:
                description: Request routing configuration.
                type: dict
                suboptions:
                    routing_strategy:
                        description: The request routing strategy.
                        type: str
                    prefix_aware_routing_config:
                        description: Prefix-aware routing configuration.
                        type: dict
                        suboptions:
                            prefix_length:
                                description: The prefix length used for routing.
                                type: int
                            concurrency_threshold:
                                description: The concurrency threshold for prefix-aware routing.
                                type: int
    async_inference_config:
        description: Async inference configuration.
        type: dict
    data_capture_config:
        description: Data capture configuration.
        type: dict
    enable_network_isolation:
        description: Whether to enable network isolation.
        type: bool
    execution_role_arn:
        description: The IAM execution role ARN.
        type: str
    explainer_config:
        description: Clarify explainer configuration.
        type: dict
    kms_key_id:
        description: The KMS key identifier.
        type: str
    metrics_config:
        description: Metrics configuration.
        type: dict
    shadow_production_variants:
        description: Shadow production variants.
        type: list
        elements: dict
        suboptions:
            variant_name:
                description: The name of the shadow production variant.
                type: str
                required: true
            model_name:
                description: The name of the SageMaker model.
                type: str
                required: true
            initial_instance_count:
                description: The initial number of instances.
                type: int
            instance_type:
                description: The ML compute instance type.
                type: str
            initial_variant_weight:
                description: The initial traffic weight for the variant.
                type: float
            serverless_config:
                description: Serverless inference configuration.
                type: dict
                suboptions:
                    memory_size_in_m_b:
                        description: The memory size in MB for each inference instance.
                        type: int
                        aliases: [memory_size_in_mb]
                    max_concurrency:
                        description: The maximum number of concurrent invocations.
                        type: int
                    provisioned_concurrency:
                        description: The provisioned concurrency.
                        type: int
            routing_config:
                description: Request routing configuration.
                type: dict
                suboptions:
                    routing_strategy:
                        description: The request routing strategy.
                        type: str
                    prefix_aware_routing_config:
                        description: Prefix-aware routing configuration.
                        type: dict
                        suboptions:
                            prefix_length:
                                description: The prefix length used for routing.
                                type: int
                            concurrency_threshold:
                                description: The concurrency threshold for prefix-aware routing.
                                type: int
    vpc_config:
        description: VPC configuration.
        type: dict
    tags:
        description: Tags to associate with the endpoint configuration.
        type: dict
        aliases: [resource_tags]
    purge_tags:
        description: Whether to remove tags not specified in tags.
        type: bool
        default: true
notes:
    - Required IAM actions include sagemaker:CreateEndpointConfig, sagemaker:DescribeEndpointConfig,
      sagemaker:DeleteEndpointConfig, sagemaker:AddTags, sagemaker:ListTags, sagemaker:DeleteTags, and
      iam:PassRole when an execution role is supplied.
attributes:
    check_mode:
        description: Can run in check mode and report what would change without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_endpoint_config_info
      description: Gather information about SageMaker endpoint configurations.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Create an endpoint configuration
  amazon.ai.sagemaker_endpoint_config:
    endpoint_config_name: my-endpoint-config
    production_variants:
      - variant_name: AllTraffic
        model_name: my-model
        initial_instance_count: 1
        instance_type: ml.m5.large

- name: Delete an endpoint configuration
  amazon.ai.sagemaker_endpoint_config:
    state: absent
    endpoint_config_name: my-endpoint-config
"""

RETURN = r"""
endpoint_config:
    description: The endpoint configuration after the operation.
    type: dict
    contains:
        endpoint_config_name:
            description: The endpoint configuration name.
            type: str
        endpoint_config_arn:
            description: The endpoint configuration ARN.
            type: str
    returned: on success when state is present
    sample:
        endpoint_config_name: my-endpoint-config
        endpoint_config_arn: arn:aws:sagemaker:us-east-1:123456789012:endpoint-config/my-endpoint-config
tags:
    description: A dictionary containing the endpoint configuration tags.
    type: dict
    returned: on success when state is present
    sample: {}
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: Endpoint configuration my-endpoint-config created successfully.
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _endpoint_config_properties_differ
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_endpoint_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_endpoint_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_endpoint_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import endpoint_config_params
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_endpoint_config_tags

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _endpoint_config_tags_message(name, changed, check_mode) -> str:
    if not changed:
        return f"Endpoint configuration {name} is already up to date."
    if check_mode:
        return f"Check mode: would have updated endpoint configuration {name} tags."
    return f"Endpoint configuration {name} tags updated successfully."


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        endpoint_config_name=dict(type="str", required=True, aliases=["name"]),
        production_variants=dict(
            type="list",
            elements="dict",
            options=dict(
                variant_name=dict(type="str", required=True),
                model_name=dict(type="str", required=True),
                initial_instance_count=dict(type="int"),
                instance_type=dict(type="str"),
                initial_variant_weight=dict(type="float"),
                serverless_config=dict(
                    type="dict",
                    options=dict(
                        memory_size_in_m_b=dict(type="int", aliases=["memory_size_in_mb"]),
                        max_concurrency=dict(type="int"),
                        provisioned_concurrency=dict(type="int"),
                    ),
                ),
                routing_config=dict(
                    type="dict",
                    options=dict(
                        routing_strategy=dict(type="str"),
                        prefix_aware_routing_config=dict(
                            type="dict",
                            options=dict(
                                prefix_length=dict(type="int"),
                                concurrency_threshold=dict(type="int"),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        async_inference_config=dict(type="dict"),
        data_capture_config=dict(type="dict"),
        enable_network_isolation=dict(type="bool"),
        execution_role_arn=dict(type="str"),
        explainer_config=dict(type="dict"),
        kms_key_id=dict(type="str"),
        metrics_config=dict(type="dict"),
        shadow_production_variants=dict(
            type="list",
            elements="dict",
            options=dict(
                variant_name=dict(type="str", required=True),
                model_name=dict(type="str", required=True),
                initial_instance_count=dict(type="int"),
                instance_type=dict(type="str"),
                initial_variant_weight=dict(type="float"),
                serverless_config=dict(
                    type="dict",
                    options=dict(
                        memory_size_in_m_b=dict(type="int", aliases=["memory_size_in_mb"]),
                        max_concurrency=dict(type="int"),
                        provisioned_concurrency=dict(type="int"),
                    ),
                ),
                routing_config=dict(
                    type="dict",
                    options=dict(
                        routing_strategy=dict(type="str"),
                        prefix_aware_routing_config=dict(
                            type="dict",
                            options=dict(
                                prefix_length=dict(type="int"),
                                concurrency_threshold=dict(type="int"),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        vpc_config=dict(type="dict"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[("state", "present", ["production_variants"])],
    )
    name = module.params["endpoint_config_name"]
    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing = describe_endpoint_config(client, name)
        if module.params["state"] == "absent":
            if not existing:
                module.exit_json(changed=False, msg=f"Endpoint configuration {name} does not exist.")
            if module.check_mode:
                module.exit_json(changed=True, msg=f"Check mode: would have deleted endpoint configuration {name}.")
            delete_endpoint_config(client, name)
            module.exit_json(changed=True, msg=f"Endpoint configuration {name} deleted successfully.")

        if existing:
            desired = endpoint_config_params(module)
            if _endpoint_config_properties_differ(desired, existing):
                module.fail_json(
                    msg=f"Endpoint configuration {name} requires replacement because immutable properties differ."
                )
            changed = reconcile_endpoint_config_tags(client, module, existing)
            result = camel_dict_to_snake_dict(describe_endpoint_config(client, name), ignore_list=["tags"])
            module.exit_json(
                changed=changed,
                endpoint_config=result,
                tags=list_tags(client, existing["EndpointConfigArn"]),
                msg=_endpoint_config_tags_message(name, changed, module.check_mode),
            )

        if module.check_mode:
            module.exit_json(changed=True, msg=f"Check mode: would have created endpoint configuration {name}.")
        create_endpoint_config(client, module)
        created = describe_endpoint_config(client, name)
        result = camel_dict_to_snake_dict(created, ignore_list=["tags"])
        module.exit_json(
            changed=True,
            endpoint_config=result,
            tags=list_tags(client, created["EndpointConfigArn"]),
            msg=f"Endpoint configuration {name} created successfully.",
        )
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
