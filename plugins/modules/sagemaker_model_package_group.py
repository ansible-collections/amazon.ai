#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_model_package_group
short_description: Manage Amazon SageMaker Model Package Groups
version_added: "2.0.0"
author:
    - Jan Likar (@janlikar)
description:
    - Create and delete Amazon SageMaker model package groups.
    - Reconcile tags on an existing model package group.
    - Replace a group when a create-only field changes and O(force=true) is enabled.
    - "This replacement is destructive: AWS deletes the current group and recreates it, and the group must be empty before deletion succeeds."
options:
    state:
        description:
            - The desired state of the model package group.
        type: str
        choices: ['present', 'absent']
        default: present
    model_package_group_name:
        description:
            - The name of the model package group to manage.
        type: str
        required: true
        aliases: ['name']
    model_package_group_description:
        description:
            - The description of the model package group.
        type: str
    tags:
        description:
            - Tags to apply to the model package group.
        type: dict
        aliases: ['resource_tags']
    purge_tags:
        description:
            - Whether tags omitted from O(tags) should be removed.
        type: bool
        default: true
    force:
        description:
            - Whether to delete and recreate the model package group when O(model_package_group_description)
              differs from the existing resource.
            - This is destructive and permanently removes the existing group before creating a new one.
            - AWS requires the group to be empty before deletion succeeds; if model versions are still attached,
              the delete fails and the replacement is not performed.
        type: bool
        default: false
    wait:
        description:
            - Whether to wait for the delete operation to complete before returning.
        type: bool
        default: true
    wait_timeout:
        description:
            - The number of seconds to wait for a delete to complete when O(wait=true).
        type: int
        default: 600
notes:
    - 'Requires the following IAM permissions:'
    - sagemaker:CreateModelPackageGroup
    - sagemaker:DescribeModelPackageGroup
    - sagemaker:DeleteModelPackageGroup
    - sagemaker:AddTags
    - sagemaker:ListTags
    - sagemaker:DeleteTags
seealso:
    - module: amazon.ai.sagemaker_model_package_group_info
      description: Retrieve details for a single model package group or list matching groups.
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
- name: Create a SageMaker model package group
  amazon.ai.sagemaker_model_package_group:
    state: present
    model_package_group_name: example-model-package-group
    model_package_group_description: Demo model group
    tags:
      project: demo

- name: Update tags on a model package group
  amazon.ai.sagemaker_model_package_group:
    state: present
    model_package_group_name: example-model-package-group
    tags:
      project: demo-v2
      owner: platform

- name: Delete a model package group
  amazon.ai.sagemaker_model_package_group:
    state: absent
    model_package_group_name: example-model-package-group
"""

RETURN = r"""
model_package_group:
    description: A dictionary containing the managed model package group.
    type: dict
    returned: when O(state=present)
    sample:
        model_package_group_name: example-model-package-group
        model_package_group_arn: arn:aws:sagemaker:us-east-1:123456789012:model-package-group/example-model-package-group
        model_package_group_description: Demo model group
        creation_time: '2025-01-01T00:00:00+00:00'
        model_package_group_status: Completed
        tags:
            project: demo
    contains:
        model_package_group_name:
            description: The name of the model package group.
            type: str
            sample: example-model-package-group
        model_package_group_arn:
            description: The Amazon Resource Name (ARN) of the model package group.
            type: str
            sample: arn:aws:sagemaker:us-east-1:123456789012:model-package-group/example-model-package-group
        model_package_group_description:
            description: The description of the model package group.
            type: str
            sample: Demo model group
        creation_time:
            description: The date and time the model package group was created.
            type: str
            sample: '2025-01-01T00:00:00+00:00'
        model_package_group_status:
            description: The current status of the model package group.
            type: str
            sample: Completed
        tags:
            description: The tags assigned to the model package group.
            type: dict
            sample:
                project: demo
tags:
    description: A dictionary of tags assigned to the model package group.
    type: dict
    returned: when O(state=present)
    sample:
        project: demo
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: Model package group example-model-package-group created successfully.
"""

try:
    import botocore
except ImportError:
    pass

from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_model_package_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_model_package_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_model_package_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import model_package_group_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_model_package_group_tags

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _normalize_model_package_group(group: Dict[str, Any], tags: Dict[str, str]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = camel_dict_to_snake_dict(group, ignore_list=["tags"])
    normalized["tags"] = tags
    return normalized


def _model_package_group_result(group: Optional[Dict[str, Any]], msg: str, client) -> Dict[str, Any]:
    result: Dict[str, Any] = {"msg": msg, "model_package_group": {}, "tags": {}}
    if group is not None:
        tags: Dict[str, str] = list_tags(client, group["ModelPackageGroupArn"])
        result["model_package_group"] = _normalize_model_package_group(group, tags)
        result["tags"] = tags
    return result


def _created_model_package_group_result(client, module) -> Tuple[bool, Dict[str, Any]]:
    changed, msg = create_model_package_group(client, module)
    if module.check_mode:
        return changed, _model_package_group_result(None, msg, client)

    group = describe_model_package_group(client, module.params["model_package_group_name"])
    return changed, _model_package_group_result(group, msg, client)


def _ensure_present(client, module, existing: Optional[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    if existing is None:
        return _created_model_package_group_result(client, module)

    if model_package_group_needs_update(existing, module):
        if not module.params["force"]:
            module.warn(
                "Model package group description drift detected. force=true is required to replace the resource; "
                "continuing without replacement."
            )
        else:
            if module.check_mode:
                return True, {"msg": "Model package group would be replaced because its description differs."}

            _deleted, delete_msg = delete_model_package_group(client, module)
            changed, result = _created_model_package_group_result(client, module)
            result["msg"] = f"{delete_msg} {result['msg']}"
            return changed, result

    changed = False
    msg = "No updates needed."
    if module.params.get("tags") is not None:
        changed, msg = update_model_package_group_tags(
            client,
            module,
            existing["ModelPackageGroupArn"],
            module.params.get("tags"),
            purge_tags=module.params["purge_tags"],
        )
    return changed, _model_package_group_result(existing, msg, client)


def _ensure_absent(client, module, existing: Optional[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    if existing is None:
        return False, {"msg": "Model package group does not exist."}

    changed, msg = delete_model_package_group(client, module)
    return changed, {"msg": msg}


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        model_package_group_name=dict(type="str", required=True, aliases=["name"]),
        model_package_group_description=dict(type="str"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        force=dict(type="bool", default=False),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing: Optional[Dict[str, Any]] = describe_model_package_group(
            client, module.params["model_package_group_name"]
        )
        if module.params["state"] == "present":
            changed, result = _ensure_present(client, module, existing)
        else:
            changed, result = _ensure_absent(client, module, existing)

        module.exit_json(changed=changed, **result)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
