#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_app_image_config
short_description: Manage Amazon SageMaker AppImageConfigs
version_added: "2.0.0"
author:
    - Matej Artač (@matejart)
description:
    - Create, update and delete Amazon SageMaker AppImageConfigs.
    - An AppImageConfig tells SageMaker Studio how to run a custom image as a kernel gateway, JupyterLab or Code Editor app.
    - Reconcile tags on an existing AppImageConfig.
    - A supplied configuration block replaces the block of the same kind as a whole, so every sub-option that should be kept must be given again.
    - A block that is not supplied is left untouched, and a block can not be removed once it has been set.
options:
    app_image_config_name:
        description:
            - The name of the AppImageConfig.
            - The name can not be changed after the AppImageConfig is created.
        type: str
        required: true
        aliases: ["name"]
    state:
        description:
            - The desired state of the AppImageConfig.
        type: str
        choices: ['present', 'absent']
        default: present
    kernel_gateway_image_config:
        description:
            - The configuration of the image as a kernel gateway app.
            - Mutually exclusive with O(jupyter_lab_app_image_config) and O(code_editor_app_image_config).
        type: dict
        suboptions:
            kernel_specs:
                description:
                    - The kernels in the image.
                type: list
                elements: dict
                required: true
                suboptions:
                    name:
                        description:
                            - The name of the kernel. The name is case sensitive.
                        type: str
                        required: true
                    display_name:
                        description:
                            - The display name of the kernel.
                        type: str
            file_system_config:
                description:
                    - The Amazon Elastic File System storage configuration of the image.
                type: dict
                suboptions:
                    default_gid:
                        description:
                            - The default POSIX group ID, between V(0) and V(65535).
                        type: int
                    default_uid:
                        description:
                            - The default POSIX user ID, between V(0) and V(65535).
                        type: int
                    mount_path:
                        description:
                            - The path within the image to mount the user's home directory at.
                        type: str
    jupyter_lab_app_image_config:
        description:
            - The configuration of the image as a JupyterLab app.
            - Mutually exclusive with O(kernel_gateway_image_config) and O(code_editor_app_image_config).
        type: dict
        suboptions:
            container_config:
                description:
                    - The configuration of the container the image runs in.
                type: dict
                suboptions:
                    container_arguments:
                        description:
                            - The arguments for the container when it is run.
                        type: list
                        elements: str
                    container_entrypoint:
                        description:
                            - The entrypoint used to run the container. AWS accepts at most one item.
                        type: list
                        elements: str
                    container_environment_variables:
                        description:
                            - The environment variables to set in the container, as a dictionary of names and values.
                            - Values that are not strings are converted to strings; booleans become V(true) or V(false).
                            - The values are stored in plain text and are returned as such, so do not put secrets in them.
                        type: dict
            file_system_config:
                description:
                    - The Amazon Elastic File System storage configuration of the image.
                    - AWS only accepts O(jupyter_lab_app_image_config.file_system_config.mount_path=/home/sagemaker-user),
                      O(jupyter_lab_app_image_config.file_system_config.default_uid=1000) and
                      O(jupyter_lab_app_image_config.file_system_config.default_gid=100) for this block.
                type: dict
                suboptions:
                    default_gid:
                        description:
                            - The default POSIX group ID.
                        type: int
                    default_uid:
                        description:
                            - The default POSIX user ID.
                        type: int
                    mount_path:
                        description:
                            - The path within the image to mount the user's home directory at.
                        type: str
    code_editor_app_image_config:
        description:
            - The configuration of the image as a Code Editor app.
            - Mutually exclusive with O(kernel_gateway_image_config) and O(jupyter_lab_app_image_config).
        type: dict
        suboptions:
            container_config:
                description:
                    - The configuration of the container the image runs in.
                type: dict
                suboptions:
                    container_arguments:
                        description:
                            - The arguments for the container when it is run.
                        type: list
                        elements: str
                    container_entrypoint:
                        description:
                            - The entrypoint used to run the container. AWS accepts at most one item.
                        type: list
                        elements: str
                    container_environment_variables:
                        description:
                            - The environment variables to set in the container, as a dictionary of names and values.
                            - Values that are not strings are converted to strings; booleans become V(true) or V(false).
                            - The values are stored in plain text and are returned as such, so do not put secrets in them.
                        type: dict
            file_system_config:
                description:
                    - The Amazon Elastic File System storage configuration of the image.
                    - AWS only accepts O(code_editor_app_image_config.file_system_config.mount_path=/home/sagemaker-user),
                      O(code_editor_app_image_config.file_system_config.default_uid=1000) and
                      O(code_editor_app_image_config.file_system_config.default_gid=100) for this block.
                type: dict
                suboptions:
                    default_gid:
                        description:
                            - The default POSIX group ID.
                        type: int
                    default_uid:
                        description:
                            - The default POSIX user ID.
                        type: int
                    mount_path:
                        description:
                            - The path within the image to mount the user's home directory at.
                        type: str
    tags:
        description:
            - A dictionary of tags to assign to the AppImageConfig.
            - When omitted, the tags of an existing AppImageConfig are left unchanged.
        type: dict
        aliases: ["resource_tags"]
    purge_tags:
        description:
            - Whether tags on the AppImageConfig that are not in O(tags) are removed.
            - Only used when O(tags) is set.
        type: bool
        default: true
attributes:
    check_mode:
        support: full
        description: Can run in check_mode and return changed status prediction without modifying the target.
    diff_mode:
        support: none
        description: Will not return details on what has changed.
seealso:
    - module: amazon.ai.sagemaker_app_image_config_info
notes:
    - The module needs the C(sagemaker:CreateAppImageConfig), C(sagemaker:DescribeAppImageConfig), C(sagemaker:UpdateAppImageConfig),
      C(sagemaker:DeleteAppImageConfig), C(sagemaker:AddTags), C(sagemaker:ListTags) and C(sagemaker:DeleteTags) IAM permissions.
    - AWS deletes an AppImageConfig even when a SageMaker Domain still uses it, which leaves the Domain referring to a missing
      AppImageConfig. Remove it from the Domain settings before using O(state=absent).
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Create an AppImageConfig for a JupyterLab image
  amazon.ai.sagemaker_app_image_config:
    name: example-app-image-config
    jupyter_lab_app_image_config:
      container_config:
        container_arguments: ["--debug"]
        container_entrypoint: ["/usr/local/bin/start"]
        container_environment_variables:
          LOG_LEVEL: info
    tags:
      project: demo

- name: Create an AppImageConfig for a kernel gateway image
  amazon.ai.sagemaker_app_image_config:
    name: example-kernel-config
    kernel_gateway_image_config:
      kernel_specs:
        - name: python3
          display_name: Python 3
      file_system_config:
        mount_path: /home/sagemaker-user
        default_uid: 1000
        default_gid: 100

- name: Update the tags of an AppImageConfig and keep other tags
  amazon.ai.sagemaker_app_image_config:
    name: example-app-image-config
    tags:
      owner: platform
    purge_tags: false

- name: Delete an AppImageConfig
  amazon.ai.sagemaker_app_image_config:
    name: example-app-image-config
    state: absent
"""

RETURN = r"""
app_image_config:
    description: A dictionary containing the managed AppImageConfig.
    type: dict
    returned: always; an empty dictionary when the AppImageConfig does not exist after the run, or in check mode when it would be created
    sample:
        app_image_config_name: example-app-image-config
        app_image_config_arn: arn:aws:sagemaker:eu-north-1:123456789012:app-image-config/example-app-image-config
        creation_time: '2025-01-01T00:00:00+00:00'
        last_modified_time: '2025-01-01T00:00:00+00:00'
        jupyter_lab_app_image_config:
            container_config:
                container_arguments: ["--debug"]
                container_environment_variables:
                    LOG_LEVEL: info
        tags:
            project: demo
    contains:
        app_image_config_name:
            description: The name of the AppImageConfig.
            type: str
            sample: example-app-image-config
        app_image_config_arn:
            description: The Amazon Resource Name (ARN) of the AppImageConfig.
            type: str
            sample: arn:aws:sagemaker:eu-north-1:123456789012:app-image-config/example-app-image-config
        creation_time:
            description: The date and time the AppImageConfig was created.
            type: str
            sample: '2025-01-01T00:00:00+00:00'
        last_modified_time:
            description: The date and time the AppImageConfig was last modified.
            type: str
            sample: '2025-01-01T00:00:00+00:00'
        kernel_gateway_image_config:
            description: The kernel gateway configuration, when the AppImageConfig has one.
            type: dict
            sample:
                kernel_specs:
                    - name: python3
        jupyter_lab_app_image_config:
            description: The JupyterLab configuration, when the AppImageConfig has one.
            type: dict
            sample:
                container_config:
                    container_arguments: ["--debug"]
        code_editor_app_image_config:
            description: The Code Editor configuration, when the AppImageConfig has one.
            type: dict
            sample:
                container_config:
                    container_arguments: ["--debug"]
        tags:
            description: The tags assigned to the AppImageConfig. Only returned when O(tags) is set.
            type: dict
            sample:
                project: demo
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: SageMaker AppImageConfig example-app-image-config created successfully.
"""

try:
    import botocore
except ImportError:
    pass

from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import APP_IMAGE_CONFIG_BLOCK_OPTIONS
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import app_image_config_to_snake_dict
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_app_image_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_app_image_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_app_image_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_app_image_config

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _file_system_config_spec() -> Dict[str, Any]:
    return dict(
        type="dict",
        options=dict(
            default_gid=dict(type="int"),
            default_uid=dict(type="int"),
            mount_path=dict(type="str"),
        ),
    )


def _app_config_spec() -> Dict[str, Any]:
    return dict(
        type="dict",
        options=dict(
            container_config=dict(
                type="dict",
                options=dict(
                    container_arguments=dict(type="list", elements="str"),
                    container_entrypoint=dict(type="list", elements="str"),
                    container_environment_variables=dict(type="dict"),
                ),
            ),
            file_system_config=_file_system_config_spec(),
        ),
    )


def _app_image_config_result(
    client, module, config: Optional[Dict[str, Any]], msg: str, current_tags: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    result: Dict[str, Any] = {"msg": msg, "app_image_config": {}}
    if config is not None:
        normalized: Dict[str, Any] = app_image_config_to_snake_dict(config)
        if module.params.get("tags") is not None:
            if current_tags is None:
                current_tags = list_tags(client, config["AppImageConfigArn"])
            normalized["tags"] = current_tags
        result["app_image_config"] = normalized
    return result


def _ensure_present(client, module, existing: Optional[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    name: str = module.params["app_image_config_name"]
    if existing is None:
        changed, msg = create_app_image_config(client, module)
        if module.check_mode:
            return changed, _app_image_config_result(client, module, None, msg)
    else:
        current_tags: Optional[Dict[str, str]] = None
        if module.params.get("tags") is not None:
            current_tags = list_tags(client, existing["AppImageConfigArn"])
        changed, msg = update_app_image_config(client, module, existing, current_tags)
        if module.check_mode or not changed:
            return changed, _app_image_config_result(client, module, existing, msg, current_tags)
    return changed, _app_image_config_result(client, module, describe_app_image_config(client, name), msg)


def _ensure_absent(client, module, existing: Optional[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    if existing is None:
        name: str = module.params["app_image_config_name"]
        return False, _app_image_config_result(client, module, None, f"SageMaker AppImageConfig {name} does not exist.")
    changed, msg = delete_app_image_config(client, module)
    return changed, _app_image_config_result(client, module, None, msg)


def main() -> None:
    argument_spec = dict(
        app_image_config_name=dict(type="str", required=True, aliases=["name"]),
        state=dict(type="str", default="present", choices=["present", "absent"]),
        kernel_gateway_image_config=dict(
            type="dict",
            options=dict(
                kernel_specs=dict(
                    type="list",
                    elements="dict",
                    required=True,
                    options=dict(
                        name=dict(type="str", required=True),
                        display_name=dict(type="str"),
                    ),
                ),
                file_system_config=_file_system_config_spec(),
            ),
        ),
        jupyter_lab_app_image_config=_app_config_spec(),
        code_editor_app_image_config=_app_config_spec(),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[APP_IMAGE_CONFIG_BLOCK_OPTIONS],
        supports_check_mode=True,
    )

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing: Optional[Dict[str, Any]] = describe_app_image_config(client, module.params["app_image_config_name"])
        if module.params["state"] == "present":
            changed, result = _ensure_present(client, module, existing)
        else:
            changed, result = _ensure_absent(client, module, existing)

        module.exit_json(changed=changed, **result)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
