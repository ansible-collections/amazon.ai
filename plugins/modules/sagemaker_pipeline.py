#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_pipeline
short_description: Manage Amazon SageMaker Pipelines
version_added: "2.0.0"
author:
    - Jan Likar (@janlikar)
description:
    - Create, update, and delete Amazon SageMaker Pipeline definitions.
    - This module does not manage pipeline executions.
attributes:
    check_mode:
        description: Can run in check mode without changing the target.
        support: full
    diff_mode:
        description: Does not support diff mode.
        support: none
options:
    state:
        description:
            - The desired state of the pipeline.
        type: str
        choices: ['present', 'absent']
        default: present
    pipeline_name:
        description:
            - The name of the pipeline to manage.
        type: str
        required: true
        aliases: ['name']
    pipeline_definition:
        description:
            - The JSON pipeline definition as a string.
            - Required when O(state=present) unless O(pipeline_definition_s3_location) is supplied.
            - Mutually exclusive with O(pipeline_definition_s3_location).
        type: str
    pipeline_definition_s3_location:
        description:
            - The S3 object containing the JSON pipeline definition.
            - Required when O(state=present) unless O(pipeline_definition) is supplied.
            - Mutually exclusive with O(pipeline_definition).
        type: dict
        suboptions:
            bucket:
                description:
                    - The S3 bucket containing the pipeline definition.
                type: str
                required: true
            object_key:
                description:
                    - The S3 key of the pipeline definition object.
                type: str
                required: true
            version_id:
                description:
                    - The S3 object version to use.
                    - When omitted, S3's current object version is used for definition comparison.
                type: str
    role_arn:
        description:
            - The ARN of the IAM role that SageMaker uses to access AWS resources.
            - Required when creating a pipeline.
        type: str
    pipeline_display_name:
        description:
            - A display name for the pipeline.
        type: str
    pipeline_description:
        description:
            - A description of the pipeline.
        type: str
    parallelism_configuration:
        description:
            - The parallelism configuration for pipeline executions.
        type: dict
        suboptions:
            max_parallel_execution_steps:
                description:
                    - The maximum number of steps that can run in parallel.
                    - Must be greater than or equal to 1.
                type: int
                required: true
    tags:
        description:
            - Tags to apply to the pipeline.
        type: dict
        aliases: [resource_tags]
    purge_tags:
        description:
            - Whether tags omitted from O(tags) should be removed.
        type: bool
        default: true
    wait:
        description:
            - Whether to wait for the pipeline to become active or be deleted.
            - The module uses a custom waiter because SageMaker does not provide a pipeline waiter.
        type: bool
        default: true
    wait_timeout:
        description:
            - The maximum time in seconds to wait for the pipeline to reach the desired state.
        type: int
        default: 600
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
notes:
    - Required IAM actions include sagemaker:CreatePipeline, sagemaker:DescribePipeline,
      sagemaker:UpdatePipeline, sagemaker:DeletePipeline, and iam:PassRole.
    - When O(tags) is supplied, also requires sagemaker:AddTags, sagemaker:DeleteTags, and sagemaker:ListTags.
    - O(pipeline_definition_s3_location) requires s3:GetObject, or s3:GetObjectVersion when O(pipeline_definition_s3_location.version_id) is supplied.
    - Reading SSE-KMS encrypted definition objects also requires kms:Decrypt.
seealso:
    - module: amazon.ai.sagemaker_pipeline_info
"""

EXAMPLES = r"""
- name: Create a pipeline from an inline definition
  amazon.ai.sagemaker_pipeline:
    pipeline_name: example-pipeline
    role_arn: arn:aws:iam::123456789012:role/SageMakerPipelineRole
    pipeline_definition: '{"Version":"2020-12-01","Steps":[{"Name":"FailForExample","Type":"Fail","Arguments":{"ErrorMessage":"Example failure"}}]}'

- name: Create a pipeline from an S3 definition
  amazon.ai.sagemaker_pipeline:
    pipeline_name: example-pipeline
    role_arn: arn:aws:iam::123456789012:role/SageMakerPipelineRole
    pipeline_definition_s3_location:
      bucket: example-bucket
      object_key: definitions/pipeline.json
      version_id: 3Lg...example
    parallelism_configuration:
      max_parallel_execution_steps: 2

- name: Delete a pipeline definition
  amazon.ai.sagemaker_pipeline:
    state: absent
    pipeline_name: example-pipeline
"""

RETURN = r"""
pipeline:
    description: The pipeline definition returned by SageMaker.
    type: dict
    returned: on success when O(state=present), empty in check mode when the pipeline does not exist
    sample:
        pipeline_name: example-pipeline
        pipeline_status: Active
    contains:
        pipeline_arn:
            description: The ARN of the pipeline.
            returned: on success when O(state=present)
            type: str
            sample: "arn:aws:sagemaker:us-east-1:123456789012:pipeline/example-pipeline"
        pipeline_name:
            description: The name of the pipeline.
            returned: on success when O(state=present)
            type: str
            sample: "example-pipeline"
        pipeline_definition:
            description: The effective JSON definition of the pipeline.
            returned: on success when O(state=present)
            type: str
            sample: '{"Version":"2020-12-01","Steps":[{"Name":"FailForExample","Type":"Fail","Arguments":{"ErrorMessage":"Example failure"}}]}'
        role_arn:
            description: The IAM role ARN used by the pipeline.
            returned: on success when O(state=present)
            type: str
            sample: "arn:aws:iam::123456789012:role/SageMakerPipelineRole"
        pipeline_status:
            description: The current status of the pipeline.
            returned: on success when O(state=present)
            type: str
            sample: Active
        tags:
            description: The pipeline tags.
            returned: on success when O(state=present) and the pipeline exists
            type: dict
            sample:
                project: demo
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: Pipeline example-pipeline created successfully.
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_pipeline
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_pipeline
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_pipeline
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import pipeline_properties_to_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_pipeline_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_pipeline
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_pipeline_status
from ansible_collections.amazon.ai.plugins.module_utils.utils import parse_json

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _normalize_pipeline(pipeline: Dict[str, Any]) -> Dict[str, Any]:
    return camel_dict_to_snake_dict(pipeline, ignore_list=["tags"])


def _ensure_present(
    client, module: AnsibleAWSModule, existing: Optional[Dict[str, Any]]
) -> Tuple[bool, Dict[str, Any]]:
    pipeline_name = module.params["pipeline_name"]
    if existing is None:
        if not module.params.get("role_arn"):
            module.fail_json(msg="role_arn is required when creating a pipeline.")
        if module.params.get("pipeline_definition") is not None:
            parse_json(module.params["pipeline_definition"], module, "pipeline_definition")
        if module.check_mode:
            changed, msg = create_pipeline(client, module)
            return changed, dict(msg=msg, pipeline={})
    elif existing.get("PipelineStatus") == "Deleting":
        module.fail_json(
            msg=f"Pipeline {pipeline_name} is being deleted and cannot be updated. Retry after deletion completes."
        )

    s3_client = None
    if module.params.get("pipeline_definition_s3_location") is not None and (
        existing is not None or module.params.get("wait", True)
    ):
        try:
            s3_client = module.client("s3", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

    if existing is None:
        changed, msg = create_pipeline(client, module, s3_client=s3_client)
        existing = describe_pipeline(client, pipeline_name)
        result_pipeline = _normalize_pipeline(existing)
        result_pipeline["tags"] = list_tags(client, existing["PipelineArn"])
        return changed, dict(msg=msg, pipeline=result_pipeline)

    properties_to_update = pipeline_properties_to_update(existing, module, s3_client=s3_client)
    changed, msg, pipeline_version_id = update_pipeline(
        client, module, properties_to_update, existing, s3_client=s3_client
    )
    tags_changed, tags_msg = reconcile_pipeline_tags(client, module, existing)
    changed = changed or tags_changed
    if tags_msg and (not msg or msg.startswith("No updates needed")):
        msg = tags_msg
    elif tags_changed and tags_msg:
        msg = f"{msg} {tags_msg}"
    if not changed:
        msg = f"No updates needed for pipeline {pipeline_name}."

    if module.check_mode:
        result_pipeline = _normalize_pipeline(existing)
        result_pipeline["tags"] = list_tags(client, existing["PipelineArn"])
        return changed, dict(msg=msg, pipeline=result_pipeline)

    current = describe_pipeline(client, pipeline_name, pipeline_version_id=pipeline_version_id)
    if current is None:
        module.fail_json(msg=f"Pipeline {pipeline_name} could not be retrieved after reconciliation.")
    result_pipeline = _normalize_pipeline(current)
    result_pipeline["tags"] = list_tags(client, current["PipelineArn"])
    return changed, dict(msg=msg, pipeline=result_pipeline)


def _ensure_absent(client, module: AnsibleAWSModule, existing: Optional[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    pipeline_name = module.params["pipeline_name"]
    if existing is None:
        return False, dict(msg=f"Pipeline {pipeline_name} does not exist.")
    if existing.get("PipelineStatus") == "Deleting":
        if module.params.get("wait", True) and not module.check_mode:
            wait_for_pipeline_status(client, module, pipeline_name, deleted=True)
        return False, dict(msg=f"Pipeline {pipeline_name} is already being deleted.")
    changed, msg = delete_pipeline(client, module)
    return changed, dict(msg=msg)


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        pipeline_name=dict(type="str", required=True, aliases=["name"]),
        pipeline_definition=dict(type="str"),
        pipeline_definition_s3_location=dict(
            type="dict",
            options=dict(
                bucket=dict(type="str", required=True),
                object_key=dict(type="str", required=True, no_log=False),
                version_id=dict(type="str"),
            ),
        ),
        role_arn=dict(type="str"),
        pipeline_display_name=dict(type="str"),
        pipeline_description=dict(type="str"),
        parallelism_configuration=dict(
            type="dict",
            options=dict(max_parallel_execution_steps=dict(type="int", required=True)),
        ),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[["pipeline_definition", "pipeline_definition_s3_location"]],
        required_if=[("state", "present", ["pipeline_definition", "pipeline_definition_s3_location"], True)],
    )
    if module.params["wait_timeout"] < 1:
        module.fail_json(msg="wait_timeout must be greater than zero.")
    parallelism_configuration = module.params.get("parallelism_configuration")
    if (
        module.params["state"] == "present"
        and parallelism_configuration is not None
        and parallelism_configuration["max_parallel_execution_steps"] < 1
    ):
        module.fail_json(msg="parallelism_configuration.max_parallel_execution_steps must be at least 1.")

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing = describe_pipeline(client, module.params["pipeline_name"])
        if module.params["state"] == "present":
            changed, result = _ensure_present(client, module, existing)
        else:
            changed, result = _ensure_absent(client, module, existing)
        module.exit_json(changed=changed, **result)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
