#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: devopsguru_resource_collection
short_description: Manages DevOps Guru resource collections
version_added: 1.0.0
description:
    - Manages DevOps Guru resource collections.
options:
    state:
        description:
            - Specifies if the resource collection in the request is added or deleted to the resource collection.
        default: present
        choices: [ "present", "absent" ]
        type: str
    cloudformation_stack_names:
        description:
            - An array of the names of the Amazon Web Services CloudFormation stacks to update.
              You can specify up to 500 Amazon Web Services CloudFormation stacks.
            - Required when O(state=present).
        type: list
        elements: str
        aliases: ["stack_names"]
    tags:
        description:
            - Tags help you identify and organize your Amazon Web Services resources.
              Many Amazon Web Services services support tagging, so you can assign the same tag to
              resources from different services to indicate that the resources are related. For example,
              you can assign the same tag to an Amazon DynamoDB table resource that you assign to an Lambda function.
            - Required when O(state=present).
        type: list
        elements: dict
        suboptions:
            app_boundary_key:
                description:
                    - An Amazon Web Services tag key that is used to identify the Amazon Web Services resources that DevOps
                      Guru analyzes.
                    - All Amazon Web Services resources in your account and Region tagged with this key make up your DevOps
                      Guru application and analysis boundary.
                type: str
                required: true
            tag_values:
                description:
                    - The values in an Amazon Web Services tag collection.
                type: list
                elements: str
    notification_channel_config:
        description:
            - A NotificationChannelConfig that specifies what type of notification channel to add.
            - The one supported notification channel is Amazon Simple Notification Service (Amazon SNS).
        type: dict
        suboptions:
            sns:
                description:
                    - Information about a notification channel configured in DevOps Guru to send notifications when insights are created.
                type: dict
                suboptions:
                    topic_arn:
                        description:
                            - The Amazon Resource Name (ARN) of an Amazon Simple Notification Service topic.
                        type: str
            filters:
                description:
                    - The filter configurations for the Amazon SNS notification topic you use with DevOps Guru.
                suboptions:
                    severities:
                        description:
                            - The severity levels that you want to receive notifications for.
                        type: list
                        elements: str
                        choices:
                            - 'LOW'
                            - 'MEDIUM'
                            - 'HIGH'
                    message_types:
                        description:
                            - The events that you want to receive notifications for.
                        type: list
                        elements: str
                        choices:
                            - 'NEW_INSIGHT'
                            - 'CLOSED_INSIGHT'
                            - 'NEW_ASSOCIATION'
                            - 'SEVERITY_UPGRADED'
                            - 'NEW_RECOMMENDATION'
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
author:
    - Alina Buzachis (@alinabuzachis)
"""

EXAMPLES = r"""
- name: Add Cloudformation stacks to resource collection
  amazon.ai.devopsguru_resource_collection:
    state: present
    cloudformation_stack_names:
      - StackA
      - StackB

- name: Remove Cloudformation stacks to resource collection
  amazon.ai.devopsguru_resource_collection:
    state: absent
    cloudformation_stack_names:
      - StackA
      - StackB

- name: Add resource to resource collection using tags
  amazon.ai.devopsguru_resource_collection:
    state: absent
    tags:
      - app_boundary_key: devops-guru-workshop
        tag_values:
          - devops-guru-serverless
          - devops-guru-aurora
"""

RETURN = r"""
resource_collection:
    description: Details about the current DevOps Guru resource collection after the module operation.
    returned: always
    type: dict
    contains:
        cloud_formation:
            description: Information about the AWS CloudFormation stacks in the resource collection.
            type: dict
            contains:
                stack_names:
                    description: List of CloudFormation stack names included in the resource collection.
                    type: list
                    elements: str
        tags:
            description: List of tags used as the resource collection filters.
            type: list
            elements: dict
            contains:
                app_boundary_key:
                    description: The AWS tag key used to identify resources DevOps Guru analyzes.
                    type: str
                tag_values:
                    description: List of tag values for the given tag key.
                    type: list
                    elements: str
notification_channel:
    description: The ID of the added notification channel.
    type: str
    returned: when configured
msg:
    description: Informative message about the action.
    type: str
    returned: always
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


from typing import Any
from typing import Dict

from ansible_collections.amazon.ai.plugins.module_utils.devopsguru import ensure_notification_channel
from ansible_collections.amazon.ai.plugins.module_utils.devopsguru import get_resource_collection
from ansible_collections.amazon.ai.plugins.module_utils.devopsguru import update_resource_collection
from ansible_collections.amazon.ai.plugins.module_utils.devopsguru import update_tags

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def process_resource_collection(client, module: AnsibleAWSModule) -> Dict[str, Any]:
    """
    Processes adding or removing CloudFormation stacks and tags in a DevOps Guru resource collection.

    This function handles:
        - Initial creation of a resource collection if none exists.
        - Adding new CloudFormation stacks.
        - Removing specified CloudFormation stacks.
        - Adding or removing tags.
        - Ensuring idempotency: `update_resource_collection` is only called when changes are needed.

    Args:
        client (Any): Boto3 client for AWS DevOps Guru.
        module (AnsibleAWSModule): Ansible module instance with access to parameters and check mode.

    Returns:
        Dict[str, Any]: Dictionary containing at least:
            - "changed" (bool): Whether the resource collection was modified.
            - "msg" (str): Informational message about the operation.
    """
    state = module.params.get("state")
    params: Dict[str, Any] = {}

    resource_collection = get_resource_collection(client, module)

    existing_cloud_stacks = resource_collection.get("CloudFormation", {}).get("StackNames", [])
    existing_tags = resource_collection.get("Tags", [])
    stack_names = module.params.get("cloudformation_stack_names")
    tags = module.params.get("tags")
    result: Dict[str, Any] = {"changed": False}

    # If no resource collection exists at all, treat as initial creation
    if not existing_cloud_stacks and not existing_tags and (stack_names or tags):
        if stack_names:
            params = {
                "Action": "ADD",
                "ResourceCollection": {"CloudFormation": {"StackNames": stack_names}},
            }
        elif tags:
            params = {"Action": "ADD", "ResourceCollection": {"Tags": tags}}
        result["msg"] = update_resource_collection(client, module, **params)
        result["changed"] = True
    else:
        # Process CloudFormation stacks
        if stack_names is not None:
            if state == "present" and stack_names:
                new_stacks = [s for s in stack_names if s not in existing_cloud_stacks]
                if new_stacks:
                    params = {
                        "Action": "ADD",
                        "ResourceCollection": {"CloudFormation": {"StackNames": new_stacks}},
                    }
                    result["msg"] = update_resource_collection(client, module, **params)
                    result["changed"] = True
                else:
                    result["msg"] = "All specified stacks already exist. Nothing changed."
            elif state == "absent":
                if stack_names:
                    # Remove only stacks that actually exist
                    stacks_to_remove = [s for s in stack_names if s in existing_cloud_stacks]
                    if stacks_to_remove:
                        params = {
                            "Action": "REMOVE",
                            "ResourceCollection": {"CloudFormation": {"StackNames": stacks_to_remove}},
                        }
                        result["msg"] = update_resource_collection(client, module, **params)
                        result["changed"] = True
                    else:
                        result["msg"] = "Some specified stacks do not exist. Nothing changed."
                elif stack_names == [] and existing_cloud_stacks:
                    params = {
                        "Action": "REMOVE",
                        "ResourceCollection": {"CloudFormation": {"StackNames": existing_cloud_stacks}},
                    }
                    result["msg"] = update_resource_collection(client, module, **params)
                    result["changed"] = True
                else:
                    result["msg"] = "No CloudFormation stacks exist to remove. Nothing changed."

        # Process tags
        if tags is not None:
            update, updated_tags = update_tags(existing_tags, tags, state=state)
            if update:
                action = "ADD" if state == "present" else "REMOVE"
                params = {"Action": action, "ResourceCollection": {"Tags": updated_tags}}
                result["msg"] = update_resource_collection(client, module, **params)
                result["changed"] = True
            else:
                result["msg"] = "No changes to tags required. Nothing changed."
    return result


def main() -> None:
    argument_spec = dict(
        state=dict(choices=["present", "absent"], default="present"),
        cloudformation_stack_names=dict(type="list", elements="str", aliases=["stack_names"]),
        tags=dict(type="list", elements="dict"),
        notification_channel_config=dict(type="dict"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[("cloudformation_stack_names", "tags")],
    )

    try:
        client = module.client("devops-guru", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    result = {"resource_collection": {}}
    notification_channel_config = module.params.get("notification_channel_config")

    try:
        result = process_resource_collection(client, module)
        # Notification channel setup
        if notification_channel_config:
            changed, notification_channel_id, msg = ensure_notification_channel(
                client, module, notification_channel_config
            )
            result["msg"] = result.get("msg", "") + str(msg)
            result["changed"] |= changed
            if notification_channel_id:
                result["notification_channel"] = notification_channel_id

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    result["resource_collection"] = camel_dict_to_snake_dict(get_resource_collection(client, module))

    module.exit_json(**result)


if __name__ == "__main__":
    main()
