#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_image_version_info
short_description: Gather information about SageMaker Image Versions
version_added: "2.0.0"
author:
    - Matej Artač (@matejart)
description:
    - This module retrieves details for a single version of a SageMaker Image or lists all versions of a SageMaker Image.
    - A missing image or image version is not an error, the result is an empty list.
options:
    image_name:
        description:
            - The name of the SageMaker Image to retrieve versions of.
        type: str
        required: true
        aliases: ["name"]
    version:
        description:
            - The version number of the image version to retrieve.
            - If neither O(version) nor O(alias) is provided, all versions of the image are listed.
            - Mutually exclusive with O(alias), O(sort_by), and O(sort_order).
        type: int
    alias:
        description:
            - An alias of the image version to retrieve.
            - Mutually exclusive with O(version), O(sort_by), and O(sort_order).
        type: str
    sort_by:
        description:
            - The field to sort the listed versions by.
            - Mutually exclusive with O(version) and O(alias).
        type: str
        choices: ['CREATION_TIME', 'LAST_MODIFIED_TIME', 'VERSION']
    sort_order:
        description:
            - The sort order for the listed versions.
            - Mutually exclusive with O(version) and O(alias).
        type: str
        choices: ['ASCENDING', 'DESCENDING']
notes:
    - Required IAM actions include sagemaker:DescribeImageVersion, sagemaker:ListImageVersions
      and sagemaker:ListAliases.
    - When listing, one additional API call per version is made to retrieve its details and aliases.
attributes:
    check_mode:
        description: Can run in check mode and return changed information.
        support: full
seealso:
    - module: amazon.ai.sagemaker_image_version
      description: Use the resource module to create, update, or delete SageMaker Image Versions.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""


EXAMPLES = r"""
- name: List all versions of a SageMaker Image
  amazon.ai.sagemaker_image_version_info:
    image_name: "my-image"

- name: List the versions of a SageMaker Image, newest first
  amazon.ai.sagemaker_image_version_info:
    image_name: "my-image"
    sort_by: "VERSION"
    sort_order: "DESCENDING"

- name: Get info about a specific SageMaker Image Version
  amazon.ai.sagemaker_image_version_info:
    image_name: "my-image"
    version: 1

- name: Get info about the SageMaker Image Version that has an alias
  amazon.ai.sagemaker_image_version_info:
    image_name: "my-image"
    alias: "latest"
"""


RETURN = r"""
image_versions:
    description: A list of SageMaker Image Versions. The list is empty if nothing matched.
    type: list
    elements: dict
    returned: always
    contains:
        image_version_arn:
            description: The Amazon Resource Name (ARN) of the image version.
            type: str
            returned: always
            sample: "arn:aws:sagemaker:us-east-1:123456789012:image-version/my-image/1"
        image_arn:
            description: The ARN of the image the version belongs to.
            type: str
            returned: always
            sample: "arn:aws:sagemaker:us-east-1:123456789012:image/my-image"
        version:
            description: The version number.
            type: int
            returned: always
            sample: 1
        image_version_status:
            description: The status of the image version.
            type: str
            returned: always
            sample: "CREATED"
        base_image:
            description: The registry path of the container image the version is based on.
            type: str
            returned: always
            sample: "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo:latest"
        container_image:
            description: The registry path of the container image that contains this image version, including its digest.
            type: str
            returned: always
            sample: "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo@sha256:0123456789abcdef"
        horovod:
            description: Whether the image version supports Horovod.
            type: bool
            returned: when set
            sample: false
        job_type:
            description: The type of job the image version is used for.
            type: str
            returned: when set
            sample: "TRAINING"
        ml_framework:
            description: The machine learning framework and its version.
            type: str
            returned: when set
            sample: "TensorFlow 1.1"
        processor:
            description: The processor the image version supports.
            type: str
            returned: when set
            sample: "CPU"
        programming_lang:
            description: The supported programming language and its version.
            type: str
            returned: when set
            sample: "Python 3.6"
        release_notes:
            description: The maintainer description of the image version.
            type: str
            returned: when set
            sample: "First release"
        vendor_guidance:
            description: The stability of the image version.
            type: str
            returned: when set
            sample: "STABLE"
        failure_reason:
            description: The reason the image version is in a failed state.
            type: str
            returned: when the image version is in a failed state
            sample: "Failed to pull the container image."
        aliases:
            description: The aliases of the image version.
            type: list
            elements: str
            returned: always
            sample: ["latest"]
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


from typing import Any
from typing import Dict

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import find_image_versions

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


def main() -> None:
    argument_spec = dict(
        image_name=dict(type="str", required=True, aliases=["name"]),
        version=dict(type="int"),
        alias=dict(type="str"),
        sort_by=dict(type="str", choices=["CREATION_TIME", "LAST_MODIFIED_TIME", "VERSION"]),
        sort_order=dict(type="str", choices=["ASCENDING", "DESCENDING"]),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ("version", "alias"),
            ("version", "sort_by"),
            ("version", "sort_order"),
            ("alias", "sort_by"),
            ("alias", "sort_order"),
        ],
    )

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        list_params: Dict[str, Any] = snake_dict_to_camel_dict(
            scrub_none_parameters({option: module.params.get(option) for option in ("sort_by", "sort_order")}),
            capitalize_first=True,
        )
        image_versions = find_image_versions(
            client,
            module.params["image_name"],
            version=module.params["version"],
            alias=module.params["alias"],
            **list_params,
        )
        module.exit_json(image_versions=[camel_dict_to_snake_dict(image_version) for image_version in image_versions])

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
