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
author:
    - Alina Buzachis (@alinabuzachis)
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
            Sns:
                description:
                    - Information about a notification channel configured in DevOps Guru to send notifications when insights are created.
                type: dict
                suboptions:
                    TopicArn:
                        description:
                            - The Amazon Resource Name (ARN) of an Amazon Simple Notification Service topic.
                        type: str
            Filters:
                description:
                    - The filter configurations for the Amazon SNS notification topic you use with DevOps Guru.
                suboptions:
                    Severities:
                        description:
                            - The severity levels that you want to receive notifications for.
                        type: list
                        elements: str
                        choices:
                            - 'LOW'
                            - 'MEDIUM'
                            - 'HIGH'
                    MessageTypes:
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
changed:
    description: Whether any changes were made by the module.
    returned: always
    type: bool
"""


from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def update_tags(
    current_tags: List[Dict[str, Any]],
    new_tags: List[Dict[str, Any]],
    state: str = "present",
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Updates the tags list by adding, updating, or removing tags and TagValues based on the state.

    :param current_tags: The existing list of tags to update.
    :param new_tags: The list of new tags to process.
    :param state: Determines whether to add ("present") or remove ("absent") tags.
    :return: A dictionary with 'update' (bool) and 'tags' (new updated list of tags).
    """
    updated_tags = current_tags[:]
    update = False

    for new_tag in new_tags:
        app_boundary_key = new_tag.get("app_boundary_key")
        new_tag_values = new_tag.get("tag_values", [])

        # Find the tag with the same AppBoundaryKey
        matching_tag = next(
            (tag for tag in updated_tags if tag.get("AppBoundaryKey") == app_boundary_key),
            None,
        )

        if state == "present":
            if matching_tag:
                # Add missing TagValues
                if matching_tag["TagValues"] != new_tag_values:
                    matching_tag["TagValues"] = new_tag_values
                    update = True
            else:
                # If no matching AppBoundaryKey, add the new tag
                updated_tags.append({"AppBoundaryKey": app_boundary_key, "TagValues": new_tag_values})
                update = True

        elif state == "absent" and matching_tag:
            # If TagValues match and we want to remove them, remove the tag
            if matching_tag["TagValues"] == new_tag_values:
                updated_tags = [tag for tag in updated_tags if tag.get("AppBoundaryKey") != app_boundary_key]
                update = True
            else:
                # If TagValues don't match, just update the tag with remaining values
                matching_tag["TagValues"] = [
                    value for value in matching_tag["TagValues"] if value not in new_tag_values
                ]
                if not matching_tag["TagValues"]:
                    updated_tags = [tag for tag in updated_tags if tag.get("AppBoundaryKey") != app_boundary_key]
                update = True

    return update, updated_tags


@AWSRetry.jittered_backoff(retries=10)
def _get_resource_collection(client, module) -> Dict[str, Any]:
    stack_names = module.params.get("cloudformation_stack_names")
    tags = module.params.get("tags")
    params = {}
    if stack_names is not None:
        params["ResourceCollectionType"] = "AWS_CLOUD_FORMATION"
    elif tags is not None:
        params["ResourceCollectionType"] = "AWS_TAGS"

    try:
        paginator = client.get_paginator("get_resource_collection")
        return paginator.paginate(**params).build_full_result()["ResourceCollection"]
    except is_boto3_error_code("ResourceNotFoundException"):
        return {}


def update_resource_collection(client, **params) -> Dict[str, Any]:
    return client.update_resource_collection(**params)


def add_notification_channel(client, config: Dict[str, Any]):
    client.add_notification_channel(**{"Config": config})


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

    changed = False
    state = module.params.get("state")
    stack_names = module.params.get("cloudformation_stack_names")
    tags = module.params.get("tags")
    notification_channel_config = module.params.get("notification_channel_config")
    params = {"ResourceCollection": {}}

    try:
        resource_collection = _get_resource_collection(client, module)
        if resource_collection and (
            resource_collection.get("CloudFormation", {}).get("StackNames", []) or resource_collection.get("Tags", [])
        ):
            if stack_names is not None and resource_collection.get("CloudFormation", {}).get("StackNames", []):
                if set(stack_names).issubset(set(resource_collection["CloudFormation"]["StackNames"])):
                    if state == "absent":
                        changed = True
                        params["Action"] = "REMOVE"
                        params["ResourceCollection"]["CloudFormation"] = {"StackNames": stack_names}
                        update_resource_collection(client, **params)
                    if stack_names == [] and state == "absent":
                        changed = True
                        params["Action"] = "REMOVE"
                        params["ResourceCollection"]["CloudFormation"] = {
                            "StackNames": resource_collection["CloudFormation"]["StackNames"]
                        }
                        update_resource_collection(client, **params)
                else:
                    if state == "present":
                        changed = True
                        params["Action"] = "ADD"
                        params["ResourceCollection"]["CloudFormation"] = {"StackNames": stack_names}
                        update_resource_collection(client, **params)
            elif tags is not None and resource_collection.get("Tags", []):
                update, updated_tags = update_tags(resource_collection["Tags"], tags, state="present")
                if update:
                    changed = True
                    if state == "present":
                        params["Action"] = "ADD"
                    else:
                        params["Action"] = "REMOVE"
                    params["ResourceCollection"]["Tags"] = updated_tags
                    update_resource_collection(client, **params)
        else:
            params["Action"] = "ADD"
            if stack_names:
                params["ResourceCollection"]["CloudFormation"] = {"StackNames": stack_names}
            elif tags:
                params["ResourceCollection"]["Tags"] = tags
            changed = True
            update_resource_collection(client, **params)

        if notification_channel_config:
            add_notification_channel(client, notification_channel_config)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(_get_resource_collection(client, module)))


if __name__ == "__main__":
    main()
