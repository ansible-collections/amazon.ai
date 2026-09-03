#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_endpoint_config
short_description: Manage Amazon SageMaker endpoint configurations
version_added: "1.1.0"
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
    async_inference_config:
        description: Async inference configuration.
        type: dict
    data_capture_config:
        description: Data capture configuration.
        type: dict
    enable_network_isolation:
        description: Whether to enable network isolation.
        type: bool
        default: false
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
    wait:
        description: Retained for consistency; endpoint configurations have no waiter.
        type: bool
        default: true
    wait_timeout:
        description: Retained for consistency; endpoint configurations have no waiter.
        type: int
        default: 600
notes:
    - Required IAM actions include sagemaker:CreateEndpointConfig, sagemaker:DescribeEndpointConfig,
      sagemaker:DeleteEndpointConfig, sagemaker:AddTags, sagemaker:ListTags, sagemaker:DeleteTags, and
      iam:PassRole when an execution role is supplied.
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
    returned: on success when state is present
    sample:
        endpoint_config_name: my-endpoint-config
        endpoint_config_arn: arn:aws:sagemaker:us-east-1:123456789012:endpoint-config/my-endpoint-config
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: Endpoint configuration my-endpoint-config created successfully.
"""

try:
    import botocore
except ImportError:
    pass

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


def _variants_differ(desired_variants, existing_variants) -> bool:
    if not isinstance(existing_variants, list) or len(desired_variants) != len(existing_variants):
        return True
    return any(
        existing_variant.get(field) != value
        for desired_variant, existing_variant in zip(desired_variants, existing_variants)
        for field, value in desired_variant.items()
    )


def _endpoint_config_property_differs(key, desired_value, existing) -> bool:
    existing_value = existing.get(key)
    if key in ("ProductionVariants", "ShadowProductionVariants"):
        return _variants_differ(desired_value, existing_value)
    return desired_value != existing_value


def _endpoint_config_properties_differ(desired, existing) -> bool:
    return any(
        _endpoint_config_property_differs(key, desired_value, existing)
        for key, desired_value in desired.items()
        if key not in ("EndpointConfigName", "Tags")
    )


def _endpoint_config_tags_message(name, changed, check_mode) -> str:
    if not changed:
        return f"Endpoint configuration {name} is already up to date."
    if check_mode:
        return f"Check mode: would have updated endpoint configuration {name} tags."
    return f"Endpoint configuration {name} tags updated successfully."


def main():
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        endpoint_config_name=dict(type="str", required=True, aliases=["name"]),
        production_variants=dict(type="list", elements="dict"),
        async_inference_config=dict(type="dict"),
        data_capture_config=dict(type="dict"),
        enable_network_isolation=dict(type="bool", default=False),
        execution_role_arn=dict(type="str"),
        explainer_config=dict(type="dict"),
        kms_key_id=dict(type="str"),
        metrics_config=dict(type="dict"),
        shadow_production_variants=dict(type="list", elements="dict"),
        vpc_config=dict(type="dict"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[("state", "present", ["production_variants"])],
    )
    name = module.params["endpoint_config_name"]
    try:
        client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    try:
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
            if module.params.get("tags") is not None:
                result["tags"] = list_tags(client, existing["EndpointConfigArn"])
            module.exit_json(
                changed=changed,
                endpoint_config=result,
                msg=_endpoint_config_tags_message(name, changed, module.check_mode),
            )

        if module.check_mode:
            module.exit_json(changed=True, msg=f"Check mode: would have created endpoint configuration {name}.")
        create_endpoint_config(client, module)
        created = describe_endpoint_config(client, name)
        result = camel_dict_to_snake_dict(created, ignore_list=["tags"])
        if module.params.get("tags") is not None:
            result["tags"] = list_tags(client, created["EndpointConfigArn"])
        module.exit_json(
            changed=True,
            endpoint_config=result,
            msg=f"Endpoint configuration {name} created successfully.",
        )
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e)


if __name__ == "__main__":
    main()
