#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_model
short_description: Manage Amazon SageMaker Models
version_added: "2.0.0"
author:
    - Jan Likar (@janlikar)
description:
    - This module creates and deletes Amazon SageMaker models.
options:
    state:
        description:
            - The desired state of the model.
        type: str
        choices: ['present', 'absent']
        default: present
    model_name:
        description:
            - The name of the model to manage.
        type: str
        required: true
        aliases: ['name']
    primary_container:
        description:
            - Configuration for the model's primary container.
            - Required when O(state=present).
        type: dict
        suboptions:
            image:
                description:
                    - The path to the Docker image containing the inference code.
                type: str
                required: true
            model_data_url:
                description:
                    - The S3 path where the model artifacts are stored.
                    - Mutually exclusive with O(primary_container.model_data_source).
                type: str
            model_data_source:
                description:
                    - The location of the model artifacts.
                    - Mutually exclusive with O(primary_container.model_data_url).
                type: dict
                suboptions:
                    s3_data_source:
                        description:
                            - Specifies the S3 location of the model artifacts.
                        type: dict
                        required: true
                        suboptions:
                            s3_uri:
                                description:
                                    - The S3 URI of the model artifacts.
                                type: str
                                required: true
                            s3_data_type:
                                description:
                                    - The type of the S3 data source.
                                    - Use V(S3Object) when O(primary_container.model_data_source.s3_data_source.s3_uri)
                                      points to a single object.
                                    - Use V(S3Prefix) when it points to a key name prefix; the URI must end with a
                                      forward slash.
                                type: str
                                required: true
                                choices: ['S3Prefix', 'S3Object']
                            compression_type:
                                description:
                                    - How the model artifacts are stored.
                                    - Use V(None) for uncompressed artifacts (works with both V(S3Object) and V(S3Prefix)).
                                    - Use V(Gzip) for a gzip-compressed TAR archive; only valid with V(S3Object).
                                type: str
                                required: true
                                choices: ['None', 'Gzip']
                            model_access_config:
                                description:
                                    - Specifies the access configuration for the model artifacts.
                                type: dict
                                suboptions:
                                    accept_eula:
                                        description:
                                            - Whether to accept the end-user license agreement for the model artifacts.
                                        type: bool
                            hub_access_config:
                                description:
                                    - Configuration for access to a hub for the model artifacts.
                                type: dict
                                suboptions:
                                    hub_content_arn:
                                        description:
                                            - The ARN of the hub content for the model.
                                        type: str
                            manifest_s3_uri:
                                description:
                                    - The S3 URI of the manifest file for the model artifacts.
                                type: str
                            etag:
                                description:
                                    - The ETag of the S3 object referenced by O(primary_container.model_data_source.s3_data_source.s3_uri).
                                type: str
                            manifest_etag:
                                description:
                                    - The ETag of the S3 object referenced by
                                      O(primary_container.model_data_source.s3_data_source.manifest_s3_uri).
                                type: str
            environment:
                description:
                    - Environment variables to set in the container.
                type: dict
                default: {}
    execution_role_arn:
        description:
            - The ARN of the IAM role that SageMaker can assume.
            - Required when O(state=present).
        type: str
    vpc_config:
        description:
            - The VPC configuration for the model.
        type: dict
        suboptions:
            subnets:
                description:
                    - The VPC subnet IDs.
                type: list
                elements: str
            security_group_ids:
                description:
                    - The VPC security group IDs.
                type: list
                elements: str
    tags:
        description:
            - Tags to apply to the model.
        type: dict
        aliases: [resource_tags]
    purge_tags:
        description:
            - Whether tags omitted from O(tags) should be removed.
        type: bool
        default: true
    enable_network_isolation:
        description:
            - Whether network isolation is enabled for the model.
        type: bool
    force:
        description:
            - Whether to delete and recreate the model when O(primary_container), O(execution_role_arn),
              O(vpc_config), or O(enable_network_isolation) drift from the existing model.
            - Amazon SageMaker models cannot be updated in place for these fields; without this option
              the module fails instead of replacing the model.
        type: bool
        default: false
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Create a SageMaker model
  amazon.ai.sagemaker_model:
    state: present
    model_name: example-model
    execution_role_arn: arn:aws:iam::123456789012:role/SageMakerExecutionRole
    primary_container:
      image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest
      model_data_url: s3://example-bucket/model.tar.gz

- name: Delete a SageMaker model
  amazon.ai.sagemaker_model:
    state: absent
    model_name: example-model

- name: Force replacement of a SageMaker model when its container image changes
  amazon.ai.sagemaker_model:
    state: present
    model_name: example-model
    execution_role_arn: arn:aws:iam::123456789012:role/SageMakerExecutionRole
    primary_container:
      image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/example:v2
      model_data_url: s3://example-bucket/model.tar.gz
    force: true
"""

RETURN = r"""
model:
    description: A dictionary containing the detailed configuration of the managed model.
    type: dict
    returned: when O(state=present)
    contains:
        model_name:
            description: The name of the model.
            type: str
            sample: example-model
        model_arn:
            description: The Amazon Resource Name (ARN) of the model.
            type: str
            sample: "arn:aws:sagemaker:us-east-1:123456789012:model/example-model"
        primary_container:
            description: The location of the primary docker image and container configuration.
            type: dict
            contains:
                image:
                    description: The path to the Docker image containing the inference code.
                    type: str
                    sample: "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest"
                model_data_url:
                    description: The S3 path where the model artifacts, including model weights and bias, are stored.
                    type: str
                    sample: "s3://example-bucket/model.tar.gz"
                environment:
                    description: Environment variables to set in the container.
                    type: dict
        execution_role_arn:
            description: The ARN of the IAM role that SageMaker can assume to access model artifacts and docker image.
            type: str
            sample: "arn:aws:iam::123456789012:role/SageMakerExecutionRole"
        vpc_config:
            description: The VPC configuration for the model.
            type: dict
            contains:
                subnets:
                    description: The VPC subnet IDs.
                    type: list
                    elements: str
                security_group_ids:
                    description: The VPC security group IDs.
                    type: list
                    elements: str
        enable_network_isolation:
            description: Whether network isolation is enabled for the model.
            type: bool
        creation_time:
            description: The date and time the model was created.
            type: str
            sample: "2025-10-01T15:36:41.199376+00:00"
tags:
    description: A dictionary containing the model tags.
    type: dict
    returned: when O(state=present)
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: Model example-model created successfully.
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_model
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_model
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_model
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_needs_replacement
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_model_tags

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _normalize_model(model: Dict[str, Any]) -> Dict[str, Any]:
    return camel_dict_to_snake_dict(model, ignore_list=["tags"])


def _ensure_present(client, module, existing: Optional[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    result: Dict[str, Any] = dict(msg="", model={}, tags={})
    if existing is None:
        changed, result["msg"] = create_model(client, module)
        if not module.check_mode:
            existing = describe_model(client, module.params["model_name"])
            if existing is not None:
                result["model"] = _normalize_model(existing)
                result["tags"] = list_tags(client, existing["ModelArn"])
        return changed, result

    if model_needs_replacement(existing, module):
        if not module.params["force"]:
            module.fail_json(
                msg=(
                    "SageMaker model requires replacement when primary_container, execution_role_arn,"
                    " vpc_config, or enable_network_isolation changes. Set force=true to delete and"
                    " recreate the model."
                )
            )

        _deleted, delete_msg = delete_model(client, module)
        changed, create_msg = create_model(client, module)
        result["msg"] = f"{delete_msg} {create_msg}"
        if not module.check_mode:
            existing = describe_model(client, module.params["model_name"])
            if existing is not None:
                result["model"] = _normalize_model(existing)
                result["tags"] = list_tags(client, existing["ModelArn"])
        return changed, result

    changed: bool = False
    if module.params.get("tags") is not None:
        changed, result["msg"] = update_model_tags(
            client,
            module,
            existing["ModelArn"],
            module.params.get("tags"),
            purge_tags=module.params["purge_tags"],
        )
    result["model"] = _normalize_model(existing)
    result["tags"] = list_tags(client, existing["ModelArn"])
    return changed, result


def _ensure_absent(client, module, existing: Optional[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    if existing is None:
        return False, dict(msg="Model does not exist.")

    changed, msg = delete_model(client, module)
    return changed, dict(msg=msg)


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        model_name=dict(type="str", required=True, aliases=["name"]),
        primary_container=dict(
            type="dict",
            options=dict(
                image=dict(type="str", required=True),
                model_data_url=dict(type="str"),
                model_data_source=dict(
                    type="dict",
                    options=dict(
                        s3_data_source=dict(
                            type="dict",
                            required=True,
                            options=dict(
                                s3_uri=dict(type="str", required=True),
                                s3_data_type=dict(type="str", required=True, choices=["S3Prefix", "S3Object"]),
                                compression_type=dict(type="str", required=True, choices=["None", "Gzip"]),
                                model_access_config=dict(
                                    type="dict",
                                    options=dict(
                                        accept_eula=dict(type="bool"),
                                    ),
                                ),
                                hub_access_config=dict(
                                    type="dict",
                                    options=dict(
                                        hub_content_arn=dict(type="str"),
                                    ),
                                ),
                                manifest_s3_uri=dict(type="str"),
                                etag=dict(type="str"),
                                manifest_etag=dict(type="str"),
                            ),
                        ),
                    ),
                ),
                environment=dict(type="dict", default={}),
            ),
            mutually_exclusive=[["model_data_url", "model_data_source"]],
        ),
        execution_role_arn=dict(type="str"),
        vpc_config=dict(
            type="dict",
            options=dict(
                subnets=dict(type="list", elements="str"),
                security_group_ids=dict(type="list", elements="str"),
            ),
        ),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        enable_network_isolation=dict(type="bool"),
        force=dict(type="bool", default=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[("state", "present", ["primary_container", "execution_role_arn"])],
    )

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing: Optional[Dict[str, Any]] = describe_model(client, module.params["model_name"])
        if module.params["state"] == "present":
            changed, result = _ensure_present(client, module, existing)
        else:
            changed, result = _ensure_absent(client, module, existing)

        module.exit_json(changed=changed, **result)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
