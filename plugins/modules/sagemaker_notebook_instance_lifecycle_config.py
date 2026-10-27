#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_notebook_instance_lifecycle_config
short_description: Manage Amazon SageMaker notebook instance lifecycle configurations
version_added: "2.0.0"
author:
    - Domen Dobnikar (@domendobnikar)
description:
    - Create, update, and delete Amazon SageMaker notebook instance lifecycle configurations.
    - Lifecycle scripts run when a notebook instance is created or started.
    - Changes to scripts take effect the next time a notebook instance using the configuration starts.
options:
    state:
        description:
            - The desired state of the lifecycle configuration.
        type: str
        choices: [present, absent]
        default: present
    notebook_instance_lifecycle_config_name:
        description:
            - The name of the notebook instance lifecycle configuration to manage.
        type: str
        required: true
        aliases: [name]
    on_create:
        description:
            - Shell script content to run when a notebook instance is created.
            - Updating this script affects notebook instances using the configuration the next time they start.
            - Each lifecycle configuration script has a limit of 16384 characters.
            - The value of the $PATH environment variable that is available to both scripts is /sbin:bin:/usr/sbin:/usr/bin.
            - Lifecycle configuration scripts cannot run for longer than 5 minutes.
            - If a script runs for longer than 5 minutes, it fails and the notebook instance is not created or started.
        type: str
    on_start:
        description:
            - Shell script content to run when a notebook instance is started.
            - Updating this script affects notebook instances using the configuration the next time they start.
            - Each lifecycle configuration script has a limit of 16384 characters.
            - The value of the $PATH environment variable that is available to both scripts is /sbin:bin:/usr/sbin:/usr/bin.
            - Lifecycle configuration scripts cannot run for longer than 5 minutes.
            - If a script runs for longer than 5 minutes, it fails and the notebook instance is not created or started.
        type: str
    tags:
        description:
            - Tags to associate with the lifecycle configuration.
        type: dict
        aliases: [resource_tags]
    purge_tags:
        description:
            - Whether to remove tags not specified in O(tags).
        type: bool
        default: true
notes:
    - 'Requires the following IAM permissions:'
    - sagemaker:CreateNotebookInstanceLifecycleConfig
    - sagemaker:DescribeNotebookInstanceLifecycleConfig
    - sagemaker:UpdateNotebookInstanceLifecycleConfig
    - sagemaker:DeleteNotebookInstanceLifecycleConfig
    - sagemaker:ListTags
    - sagemaker:AddTags
    - sagemaker:DeleteTags
seealso:
    - module: amazon.ai.sagemaker_notebook_instance_lifecycle_config_info
      description: Retrieve lifecycle configuration details or list matching configurations.
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
- name: Create a notebook instance lifecycle configuration
  amazon.ai.sagemaker_notebook_instance_lifecycle_config:
    notebook_instance_lifecycle_config_name: example-lifecycle-config
    on_create: |
      #!/bin/bash
      echo 'Preparing notebook'
    on_start: |
      #!/bin/bash
      echo 'Starting notebook'
    tags:
      project: demo

- name: Update a lifecycle configuration start script
  amazon.ai.sagemaker_notebook_instance_lifecycle_config:
    notebook_instance_lifecycle_config_name: example-lifecycle-config
    on_start: |
      #!/bin/bash
      echo 'Updated notebook startup'

- name: Delete a notebook instance lifecycle configuration
  amazon.ai.sagemaker_notebook_instance_lifecycle_config:
    state: absent
    notebook_instance_lifecycle_config_name: example-lifecycle-config
"""

RETURN = r"""
notebook_instance_lifecycle_config:
    description: The managed notebook instance lifecycle configuration.
    type: dict
    returned: always, on success
    contains:
        notebook_instance_lifecycle_config_name:
            description: The name of the lifecycle configuration.
            type: str
            sample: "example-lifecycle-config"
        notebook_instance_lifecycle_config_arn:
            description: The Amazon Resource Name (ARN) of the lifecycle configuration.
            type: str
            sample: "arn:aws:sagemaker:us-east-1:123456789012:notebook-instance-lifecycle-config/example-lifecycle-config"
        on_create:
            description: The decoded shell script run when a notebook instance is created, or null when unset.
            type: str
            sample: "#!/bin/bash\necho 'Preparing notebook'"
        on_start:
            description: The decoded shell script run when a notebook instance starts, or null when unset.
            type: str
            sample: "#!/bin/bash\necho 'Starting notebook'"
        creation_time:
            description: The date and time the lifecycle configuration was created.
            type: str
            sample: "2026-01-01T00:00:00+00:00"
        last_modified_time:
            description: The date and time the lifecycle configuration was last modified.
            type: str
            sample: "2026-01-01T00:00:00+00:00"
        tags:
            description: The tags assigned to the lifecycle configuration.
            type: dict
            sample:
                project: demo
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: "Lifecycle configuration example-lifecycle-config created successfully."
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_notebook_instance_lifecycle_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import decode_lifecycle_script
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_notebook_instance_lifecycle_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_notebook_instance_lifecycle_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import lifecycle_config_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_notebook_instance_lifecycle_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_notebook_instance_lifecycle_config_tags

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _lifecycle_config_result(client, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if config is None:
        return {}

    result: Dict[str, Any] = camel_dict_to_snake_dict(config, ignore_list=["tags", "Tags"])
    result["on_create"] = decode_lifecycle_script(config.get("OnCreate"))
    result["on_start"] = decode_lifecycle_script(config.get("OnStart"))
    result["tags"] = list_tags(client, config["NotebookInstanceLifecycleConfigArn"])
    return result


def _ensure_present(client, module, existing: Optional[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    name = module.params["notebook_instance_lifecycle_config_name"]
    if existing is None:
        changed, msg = create_notebook_instance_lifecycle_config(client, module)
        if module.check_mode:
            return changed, {"notebook_instance_lifecycle_config": {}, "msg": msg}
        created = describe_notebook_instance_lifecycle_config(client, name)
        return changed, {
            "notebook_instance_lifecycle_config": _lifecycle_config_result(client, created),
            "msg": msg,
        }

    changed = False
    messages = []
    if lifecycle_config_needs_update(existing, module):
        script_changed, script_msg = update_notebook_instance_lifecycle_config(client, module, existing)
        changed = changed or script_changed
        messages.append(script_msg)

    if module.params.get("tags") is not None:
        tags_changed, tags_msg = update_notebook_instance_lifecycle_config_tags(
            client,
            module,
            existing["NotebookInstanceLifecycleConfigArn"],
            module.params["tags"],
            purge_tags=module.params["purge_tags"],
        )
        changed = changed or tags_changed
        if tags_changed:
            messages.append(tags_msg)

    if not messages and not changed:
        messages.append(f"Lifecycle configuration {name} is already up to date.")

    config = existing if module.check_mode else describe_notebook_instance_lifecycle_config(client, name)
    return changed, {
        "notebook_instance_lifecycle_config": _lifecycle_config_result(client, config),
        "msg": " ".join(messages),
    }


def _ensure_absent(client, module, existing: Optional[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    name = module.params["notebook_instance_lifecycle_config_name"]
    if existing is None:
        return False, {
            "notebook_instance_lifecycle_config": {},
            "msg": f"Lifecycle configuration {name} does not exist.",
        }

    changed, msg = delete_notebook_instance_lifecycle_config(client, module)
    return changed, {"msg": msg, "notebook_instance_lifecycle_config": {}}


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        notebook_instance_lifecycle_config_name=dict(type="str", required=True, aliases=["name"]),
        on_create=dict(type="str"),
        on_start=dict(type="str"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    name = module.params["notebook_instance_lifecycle_config_name"]

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing = describe_notebook_instance_lifecycle_config(client, name)
        if module.params["state"] == "present":
            changed, result = _ensure_present(client, module, existing)
        else:
            changed, result = _ensure_absent(client, module, existing)

        module.exit_json(changed=changed, **result)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
