#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_image_version
short_description: Manage Amazon SageMaker Image Versions
version_added: "2.0.0"
author:
    - Matej Artač (@matejart)
description:
    - This module creates, updates, and deletes versions of an Amazon SageMaker Image.
    - A SageMaker Image Version points at a container image in Amazon ECR and belongs to a SageMaker Image.
options:
    state:
        description:
            - The desired state of the image version.
        type: str
        choices: ['present', 'absent']
        default: 'present'
    image_name:
        description:
            - The name of the SageMaker Image the version belongs to.
            - The image must already exist, for example created with M(amazon.ai.sagemaker_image).
        type: str
        required: true
        aliases: ["name"]
    version:
        description:
            - The version number of an existing image version.
            - The version number is assigned by SageMaker when the version is created, it cannot be chosen.
            - Required when O(state=absent).
            - When O(state=present) and this option is omitted, a new version is always created.
            - When O(state=present) and this option is set, the existing version is updated.
              The module fails if the version does not exist.
        type: int
    base_image:
        description:
            - The registry path of the container image in Amazon ECR that the version is based on.
            - Required when O(state=present) and O(version) is not set.
            - This value cannot be changed after the version is created. When O(version) is set, the module
              fails if this option differs from the value of the existing version.
        type: str
    aliases:
        description:
            - The complete list of aliases of the image version.
            - Aliases that are not listed are removed from the version, aliases that are missing are added.
            - When omitted, the aliases of the version are left unchanged.
        type: list
        elements: str
    horovod:
        description:
            - Whether the image version supports Horovod.
            - Updatable in place.
        type: bool
    job_type:
        description:
            - The type of job the image version is used for.
            - Updatable in place.
        type: str
        choices: ['TRAINING', 'INFERENCE', 'NOTEBOOK_KERNEL']
    ml_framework:
        description:
            - The machine learning framework and its version, for example V(TensorFlow 1.1).
            - Updatable in place.
        type: str
    processor:
        description:
            - The processor the image version supports.
            - Updatable in place.
        type: str
        choices: ['CPU', 'GPU']
    programming_lang:
        description:
            - The supported programming language and its version, for example V(Python 3.6).
            - Updatable in place.
        type: str
    release_notes:
        description:
            - The maintainer description of the image version.
            - Updatable in place.
        type: str
    vendor_guidance:
        description:
            - The stability of the image version, specified by the maintainer.
            - Updatable in place.
        type: str
        choices: ['NOT_PROVIDED', 'STABLE', 'TO_BE_ARCHIVED', 'ARCHIVED']
    wait:
        description:
            - Whether to wait for the create or delete operation to complete.
        type: bool
        default: true
    wait_timeout:
        description:
            - The number of seconds to wait for the operation to complete when O(wait=true).
        type: int
        default: 600
notes:
    - Required IAM actions include sagemaker:CreateImageVersion, sagemaker:DescribeImageVersion,
      sagemaker:UpdateImageVersion, sagemaker:DeleteImageVersion, sagemaker:ListImageVersions,
      sagemaker:ListAliases and sagemaker:DescribeImage.
    - The service reads the container image in Amazon ECR when a version is created, so it needs access to it.
    - Image versions cannot be tagged.
    - Without O(version) the module is not idempotent, every run with O(state=present) creates a new version.
      Register the version number from the first run and pass it as O(version) on later runs.
attributes:
    check_mode:
        description: Can run in check mode and report what would change without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_image_version_info
      description: Use the info module to list the versions of a SageMaker Image or retrieve details for one version.
    - module: amazon.ai.sagemaker_image
      description: Manage SageMaker Images.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""


EXAMPLES = r"""
- name: Create a SageMaker Image Version
  amazon.ai.sagemaker_image_version:
    state: present
    image_name: "my-image"
    base_image: "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo:latest"
    aliases:
      - "latest"
    release_notes: "First release"
  register: created_version

- name: Update an existing SageMaker Image Version
  amazon.ai.sagemaker_image_version:
    state: present
    image_name: "my-image"
    version: "{{ created_version.image_version.version }}"
    vendor_guidance: "STABLE"
    aliases:
      - "latest"
      - "stable"

- name: Delete a SageMaker Image Version
  amazon.ai.sagemaker_image_version:
    state: absent
    image_name: "my-image"
    version: 1
"""


RETURN = r"""
image_version:
    description: A dictionary containing the details of the managed SageMaker Image Version.
    type: dict
    returned: on success when O(state=present), except when a new version would be created in check mode.
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
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: "SageMaker image version my-image:1 created successfully."
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


from typing import Any
from typing import Dict
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_image_version
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_image_version
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_image
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_image_version
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import get_image_version
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_image_version

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        image_name=dict(type="str", required=True, aliases=["name"]),
        version=dict(type="int"),
        base_image=dict(type="str"),
        aliases=dict(type="list", elements="str"),
        horovod=dict(type="bool"),
        job_type=dict(type="str", choices=["TRAINING", "INFERENCE", "NOTEBOOK_KERNEL"]),
        ml_framework=dict(type="str"),
        processor=dict(type="str", choices=["CPU", "GPU"]),
        programming_lang=dict(type="str"),
        release_notes=dict(type="str"),
        vendor_guidance=dict(type="str", choices=["NOT_PROVIDED", "STABLE", "TO_BE_ARCHIVED", "ARCHIVED"]),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[("state", "absent", ["version"])],
    )

    state: str = module.params["state"]
    image_name: str = module.params["image_name"]
    version: Optional[int] = module.params["version"]

    if state == "present" and version is None and not module.params["base_image"]:
        module.fail_json(msg="base_image is required to create a new image version when version is not set.")

    result: Dict[str, Any] = {}

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        image = describe_image(client, image_name)

        if state == "present":
            if image is None:
                module.fail_json(msg=f"SageMaker image {image_name} does not exist.")

            if version is None:
                changed, msg, new_version = create_image_version(client, module)
                image_version = get_image_version(client, image_name, new_version) if new_version else None
            else:
                existing = get_image_version(client, image_name, version)
                if existing is None:
                    module.fail_json(msg=f"SageMaker image version {image_name}:{version} does not exist.")
                if existing.get("ImageVersionStatus") == "DELETING":
                    module.fail_json(
                        msg=(
                            f"SageMaker image version {image_name}:{version} is currently being deleted. "
                            "Wait for deletion to complete before using state=present."
                        )
                    )
                changed, msg, image_version = update_image_version(client, module, existing)

            if image_version:
                result["image_version"] = camel_dict_to_snake_dict(image_version)
        else:
            existing = describe_image_version(client, image_name, version=version) if image else None
            changed, msg = delete_image_version(client, module, existing)

        module.exit_json(changed=changed, msg=msg, **result)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
