#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: devopsguru_resource_collection_info
short_description: Fetch information about Amazon DevOps Guru resource collection
version_added: 1.0.0
description:
    - Fetch information about Amazon DevOps Guru resource collections.
options:
    resource_collection_type:
        description:
            - The type of Amazon Web Services resource collections to return.
            - The one valid value is V(CLOUD_FORMATION) for Amazon Web Services CloudFormation stacks.
        type: str
        required: True
        choices:
            - 'AWS_CLOUD_FORMATION'
            - 'AWS_SERVICE'
            - 'AWS_TAGS'
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
author:
    - Alina Buzachis (@alinabuzachis)
"""

EXAMPLES = r"""
- name: Gather information about DevOpsGuru Resource Collections
  amazon.ai.devopsguru_resource_collection_info:
    resource_collection_type: "AWS_CLOUD_FORMATION"
"""

RETURN = r"""
resource_collection:
    description: Information about the DevOps Guru resource collection of the specified type.
    returned: always
    type: dict
    contains:
        cloud_formation:
            description: Details about AWS CloudFormation stacks in the resource collection.
            type: dict
            contains:
                stack_names:
                    description: List of CloudFormation stack names included.
                    type: list
                    elements: str
                    sample: ["app-stack", "database-stack"]
        service:
            description: Details about AWS services included in the resource collection.
            type: dict
            contains:
                service_names:
                    description: List of AWS service names included.
                    type: list
                    elements: str
                    sample: ["ec2", "rds"]
        tags:
            description: Details about resource tags included in the resource collection.
            type: dict
            contains:
                app_boundary_key:
                    description: The key used to identify a set of AWS resources based on tags.
                    type: str
                    sample: "env"
                tag_values:
                    description: List of tag values defining the resource collection.
                    type: list
                    elements: str
                    sample: ["production", "staging"]
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.ai.plugins.module_utils.devopsguru import get_resource_collection_specified_type

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main() -> None:
    argument_spec = dict(
        resource_collection_type=dict(
            required=True,
            type="str",
            choices=["AWS_CLOUD_FORMATION", "AWS_SERVICE", "AWS_TAGS"],
        ),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    try:
        client = module.client("devops-guru", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    resource_collection_type = module.params["resource_collection_type"]

    try:
        resource_collection = get_resource_collection_specified_type(client, resource_collection_type)
        module.exit_json(changed=False, resource_collection=camel_dict_to_snake_dict(resource_collection))
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
