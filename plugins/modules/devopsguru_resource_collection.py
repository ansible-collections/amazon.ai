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


from ansible_collections.amazon.ai.plugins.module_utils.devopsguru import add_notification_channel
from ansible_collections.amazon.ai.plugins.module_utils.devopsguru import get_resource_collection
from ansible_collections.amazon.ai.plugins.module_utils.devopsguru import update_resource_collection
from ansible_collections.amazon.ai.plugins.module_utils.devopsguru import update_tags

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


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
        resource_collection = get_resource_collection(client, module)
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

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(get_resource_collection(client, module)))


if __name__ == "__main__":
    main()
