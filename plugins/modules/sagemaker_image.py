#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_image
short_description: Manage Amazon SageMaker Images
version_added: "2.0.0"
author:
    - Jan Likar (@JanLikar)
description:
    - This module creates, updates, and deletes Amazon SageMaker Images.
    - A SageMaker Image is the top-level container resource that Image Versions attach to.
options:
    state:
        description:
            - The desired state of the image.
        type: str
        choices: ['present', 'absent']
        default: 'present'
    image_name:
        description:
            - The name of the image to manage.
            - This value cannot be modified after the image is created; a changed name is
              treated as a different resource.
        type: str
        required: true
        aliases: ["name"]
    display_name:
        description:
            - The display name of the image.
            - Updatable in place. Omitting this option on an update never clears a previously set
              value. Pass an explicit empty string to clear it.
        type: str
    description:
        description:
            - The description of the image.
            - Updatable in place. Omitting this option on an update never clears a previously set
              value. Pass an explicit empty string to clear it.
        type: str
    role_arn:
        description:
            - The Amazon Resource Name (ARN) of the IAM role that enables Amazon SageMaker to
              perform tasks on your behalf.
            - Required when O(state=present).
            - Updatable in place.
        type: str
    tags:
        description:
            - Tags to associate with the image.
        type: dict
        aliases: ["resource_tags"]
    purge_tags:
        description:
            - Whether to remove tags that are present on the image but not specified in O(tags).
        type: bool
        default: true
    wait:
        description:
            - Whether to wait for the create, update, or delete operation to complete.
        type: bool
        default: true
    wait_timeout:
        description:
            - The number of seconds to wait for the operation to complete when O(wait=true).
        type: int
        default: 600
seealso:
    - module: amazon.ai.sagemaker_image_info
      description: Use the info module to list SageMaker Images or retrieve details for one image.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""


EXAMPLES = r"""
- name: Create a SageMaker Image
  amazon.ai.sagemaker_image:
    state: present
    image_name: "my-image"
    role_arn: "arn:aws:iam::123456789012:role/my-sagemaker-role"

- name: Update a SageMaker Image's display name and description
  amazon.ai.sagemaker_image:
    state: present
    image_name: "my-image"
    role_arn: "arn:aws:iam::123456789012:role/my-sagemaker-role"
    display_name: "My Image"
    description: "My image description"

- name: Clear a SageMaker Image's description
  amazon.ai.sagemaker_image:
    state: present
    image_name: "my-image"
    role_arn: "arn:aws:iam::123456789012:role/my-sagemaker-role"
    description: ""

- name: Delete a SageMaker Image
  amazon.ai.sagemaker_image:
    state: absent
    image_name: "my-image"
"""


RETURN = r"""
image:
    description: A dictionary containing the detailed configuration of the managed SageMaker Image.
    type: dict
    returned: on success when state is present.
    contains:
        image_arn:
            description: The Amazon Resource Name (ARN) of the image.
            type: str
            sample: "arn:aws:sagemaker:us-east-1:123456789012:image/my-image"
        image_name:
            description: The name of the image.
            type: str
            sample: "my-image"
        image_status:
            description: The status of the image.
            type: str
            sample: "CREATED"
        creation_time:
            description: The date and time the image was created.
            type: str
            sample: "2025-10-01T15:36:41.199376+00:00"
        last_modified_time:
            description: The date and time the image was last modified.
            type: str
            sample: "2025-10-01T15:36:42.201271+00:00"
        description:
            description: The description of the image.
            type: str
            sample: "My image description"
        display_name:
            description: The display name of the image.
            type: str
            sample: "My Image"
        failure_reason:
            description: The failure reason, if the image is in a failed state.
            type: str
            sample: ""
        role_arn:
            description: The ARN of the IAM role associated with the image.
            type: str
            sample: "arn:aws:iam::123456789012:role/my-sagemaker-role"
        tags:
            description: A dictionary of tags associated with the image.
            type: dict
            sample: {"Environment": "dev"}
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: "SageMaker Image my-image created successfully."
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_image
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags


def _wait_for_image_deletion(
    client,
    module: AnsibleAWSModule,
    image_name: str,
    delay: int,
    max_attempts: int,
) -> None:
    """Poll for the image to be deleted.

    As of 2026-08-20 the built-in waiter does not work correctly. See https://github.com/boto/botocore/issues/3782.
    """
    for attempt in range(max_attempts):
        try:
            image = describe_image(client, image_name)
            if image is None:
                return
            elif image.get("ImageStatus") == "DELETE_FAILED":
                module.fail_json(
                    msg=f"SageMaker Image {image_name} entered DELETE_FAILED state.",
                )
        except (
            is_boto3_error_code("ResourceNotFound"),
            is_boto3_error_code("ResourceNotFoundException"),
        ):
            return

        if attempt < max_attempts - 1:
            time.sleep(delay)

    module.fail_json(
        msg=(
            f"Timeout waiting for SageMaker Image {image_name} to be deleted. "
            "The built-in waiter timed out and polling did not confirm deletion."
        )
    )


def _wait_for_image_status(client, module: AnsibleAWSModule, image_name: str, waiter_name: str) -> None:
    if not module.params.get("wait"):
        return

    wait_timeout: int = module.params["wait_timeout"]
    delay = 15
    max_attempts = max(1, wait_timeout // delay)

    if waiter_name == "image_deleted":
        _wait_for_image_deletion(client, module, image_name, delay, max_attempts)
        return

    try:
        client.get_waiter(waiter_name).wait(
            ImageName=image_name,
            WaiterConfig={"Delay": delay, "MaxAttempts": max_attempts},
        )
    except botocore.exceptions.WaiterError:
        module.fail_json(msg=f"Timeout waiting for SageMaker Image {image_name} to reach the desired status.")


def create_image(client, module: AnsibleAWSModule) -> Tuple[bool, str]:
    image_name: str = module.params["image_name"]

    if module.check_mode:
        return True, f"Check mode: would have created SageMaker Image {image_name}."

    params: Dict[str, Any] = {
        "ImageName": image_name,
        "RoleArn": module.params["role_arn"],
    }
    if module.params.get("display_name"):
        params["DisplayName"] = module.params["display_name"]
    if module.params.get("description"):
        params["Description"] = module.params["description"]
    if module.params.get("tags"):
        params["Tags"] = ansible_dict_to_boto3_tag_list(module.params["tags"])

    client.create_image(**params)
    _wait_for_image_status(client, module, image_name, "image_created")
    return True, f"SageMaker Image {image_name} created successfully."


def _build_update_params(module: AnsibleAWSModule, existing: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Diff the requested display_name/description/role_arn against the existing image.

    Returns the fields to send to `update_image` and the list of `DeleteProperties` to clear.
    An omitted (`None`) option never triggers a change or a clear; only an explicit empty string
    clears a field that is currently set.
    """
    properties_to_update: Dict[str, Any] = {}
    properties_to_remove: List[str] = []

    for option, aws_field in (("display_name", "DisplayName"), ("description", "Description")):
        new_value: Optional[str] = module.params.get(option)
        if new_value is None:
            continue
        current_value: str = existing.get(aws_field, "")
        if new_value == "" and current_value != "":
            properties_to_remove.append(aws_field)
        elif new_value != current_value:
            properties_to_update[aws_field] = new_value

    role_arn: Optional[str] = module.params.get("role_arn")
    if role_arn and role_arn != existing.get("RoleArn"):
        properties_to_update["RoleArn"] = role_arn

    return properties_to_update, properties_to_remove


def update_image(client, module: AnsibleAWSModule, existing: Dict[str, Any]) -> Tuple[bool, str]:
    image_name: str = existing["ImageName"]
    properties_to_update: Dict[str, Any]
    properties_to_remove: List[str]
    properties_to_update, properties_to_remove = _build_update_params(module, existing)

    new_tags: Optional[Dict[str, str]] = module.params.get("tags")
    tags_to_set: Dict[str, str] = {}
    tags_to_remove: List[str] = []
    if new_tags is not None:
        current_tags: Dict[str, str] = list_tags(client, existing["ImageArn"])
        purge_tags: bool = module.params["purge_tags"]
        tags_to_set, tags_to_remove = compare_aws_tags(current_tags, new_tags, purge_tags)

    if not properties_to_update and not properties_to_remove and not tags_to_set and not tags_to_remove:
        return False, f"SageMaker Image {image_name} is already up to date."

    if module.check_mode:
        return True, f"Check mode: would have updated SageMaker Image {image_name}."

    if properties_to_update or properties_to_remove:
        client.update_image(ImageName=image_name, DeleteProperties=properties_to_remove, **properties_to_update)
        _wait_for_image_status(client, module, image_name, "image_updated")

    if tags_to_set:
        client.add_tags(ResourceArn=existing["ImageArn"], Tags=ansible_dict_to_boto3_tag_list(tags_to_set))
    if tags_to_remove:
        client.delete_tags(ResourceArn=existing["ImageArn"], TagKeys=tags_to_remove)

    return True, f"SageMaker Image {image_name} updated successfully."


def delete_image(client, module: AnsibleAWSModule, existing: Dict[str, Any]) -> Tuple[bool, str]:
    image_name: str = existing["ImageName"]

    if module.check_mode:
        return True, f"Check mode: would have deleted SageMaker Image {image_name}."

    client.delete_image(ImageName=image_name)
    _wait_for_image_status(client, module, image_name, "image_deleted")
    return True, f"SageMaker Image {image_name} deleted successfully."


def main():
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        image_name=dict(type="str", required=True, aliases=["name"]),
        display_name=dict(type="str"),
        description=dict(type="str"),
        role_arn=dict(type="str"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[("state", "present", ["role_arn"])],
    )

    state: str = module.params["state"]
    image_name: str = module.params["image_name"]

    try:
        client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    changed: bool = False
    result: Dict[str, Any] = {"image": {}}

    try:
        existing: Optional[Dict[str, Any]] = describe_image(client, image_name)

        if state == "present":
            if existing:
                if existing.get("ImageStatus") == "DELETING":
                    module.fail_json(
                        msg=(
                            f"SageMaker Image {image_name} is currently being deleted. "
                            "Wait for deletion to complete before using state=present."
                        )
                    )
                changed, msg = update_image(client, module, existing)
            else:
                changed, msg = create_image(client, module)
            result["msg"] = msg

            if not module.check_mode:
                image = describe_image(client, image_name)
                if image:
                    tags = list_tags(client, image["ImageArn"])
                    result["image"] = camel_dict_to_snake_dict(image, ignore_list=["tags"])
                    result["image"]["tags"] = tags

        elif state == "absent":
            if existing:
                if existing.get("ImageStatus") == "DELETING":
                    _wait_for_image_status(client, module, image_name, "image_deleted")
                    changed = False
                    msg = f"SageMaker Image {image_name} is already being deleted."
                else:
                    changed, msg = delete_image(client, module, existing)
            else:
                msg = f"SageMaker Image {image_name} does not exist."
            result["msg"] = msg

        module.exit_json(changed=changed, **result)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
