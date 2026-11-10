#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_space
short_description: Manage Amazon SageMaker AI Spaces
version_added: "2.0.0"
description:
    - Create, update, and delete Amazon SageMaker AI Spaces.
    - Spaces are created within a SageMaker Domain.
options:
    state:
        description:
            - The desired state of the Space.
        type: str
        choices: [present, absent]
        default: present
    domain_id:
        description:
            - The ID of the SageMaker Domain that contains the Space.
        type: str
        required: true
    space_name:
        description:
            - The name of the Space to manage.
        type: str
        required: true
        aliases: [name]
    space_display_name:
        description:
            - The display name for the Space.
            - This setting can be updated in place.
        type: str
    ownership_settings:
        description:
            - The ownership settings for the Space.
            - This setting is create-only; changing it requires replacement.
        type: dict
        suboptions:
            owner_user_profile_name:
                description:
                    - The user profile that owns the Space.
                type: str
                required: true
    space_settings:
        description:
            - Settings for the Space, including app, storage, file system, and remote access settings.
            - This option accepts the SageMaker SpaceSettings structure in snake_case.
            - O(space_settings.app_type) is create-only. Other settings accepted by UpdateSpace can be changed in place.
        type: dict
        suboptions:
            app_type:
                description:
                    - The application type for the Space.
                type: str
            code_editor_app_settings:
                description:
                    - Code Editor application settings.
                type: dict
            custom_file_systems:
                description:
                    - Custom file systems attached to the Space.
                type: list
                elements: dict
            jupyter_lab_app_settings:
                description:
                    - JupyterLab application settings.
                type: dict
            jupyter_server_app_settings:
                description:
                    - JupyterServer application settings.
                type: dict
            kernel_gateway_app_settings:
                description:
                    - KernelGateway application settings.
                type: dict
            remote_access:
                description:
                    - Whether remote access is enabled for the Space.
                type: str
                choices: [ENABLED, DISABLED]
            space_managed_resources:
                description:
                    - Whether SageMaker manages the Space's resources.
                type: str
                choices: [ENABLED, DISABLED]
            space_storage_settings:
                description:
                    - Storage settings for the Space.
                type: dict
    space_sharing_settings:
        description:
            - Sharing settings for the Space.
            - This setting is create-only; changing it requires replacement.
        type: dict
        suboptions:
            sharing_type:
                description:
                    - Whether the Space is private or shared.
                type: str
                required: true
                choices: [Private, Shared]
    tags:
        description:
            - Tags to associate with the Space.
        type: dict
        aliases: [resource_tags]
    purge_tags:
        description:
            - Whether to remove tags not specified in O(tags).
        type: bool
        default: true
    force:
        description:
            - Whether to replace the Space when a create-only setting differs.
            - Without this option, the module warns and leaves the Space unchanged.
        type: bool
        default: false
    wait:
        description:
            - Whether to wait for create, update, and delete operations to complete.
        type: bool
        default: true
    wait_timeout:
        description:
            - How long, in seconds, to wait for a Space lifecycle operation to complete.
        type: int
        default: 600
notes:
    - Required IAM actions include sagemaker:CreateSpace, sagemaker:DescribeSpace,
      sagemaker:UpdateSpace, sagemaker:DeleteSpace, sagemaker:ListTags,
      sagemaker:AddTags, and sagemaker:DeleteTags.
    - Space creation, updates, and deletion are asynchronous lifecycle operations.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
attributes:
    check_mode:
        description: Can run in check mode and report what would change without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_space_info
      description: Gather information about SageMaker Spaces.
author:
    - Jan Likar (@JanLikar)
"""

EXAMPLES = r"""
- name: Create a SageMaker Space
  amazon.ai.sagemaker_space:
    domain_id: "d-0123456789ab"
    space_name: "ml-engineering"
    space_display_name: "ML Engineering"
    space_settings:
      app_type: "JupyterLab"
      space_storage_settings:
        ebs_storage_settings:
          ebs_volume_size_in_gb: 16

- name: Update Space tags
  amazon.ai.sagemaker_space:
    domain_id: "d-0123456789ab"
    space_name: "ml-engineering"
    tags:
      environment: "production"
      team: "ml-platform"

- name: Delete a SageMaker Space
  amazon.ai.sagemaker_space:
    domain_id: "d-0123456789ab"
    space_name: "ml-engineering"
    state: absent
"""

RETURN = r"""
space:
    description: The complete SageMaker Space returned by DescribeSpace.
    returned: on success when state is present; an empty dictionary when state is absent or in check mode before creation
    type: dict
    sample:
        domain_id: "d-0123456789ab"
        space_name: "ml-engineering"
        space_arn: "arn:aws:sagemaker:us-east-1:123456789012:space/d-0123456789ab/ml-engineering"
        status: "InService"
    contains:
        domain_id:
            description: The ID of the Domain that contains the Space.
            type: str
            sample: "d-0123456789ab"
        space_arn:
            description: The Amazon Resource Name of the Space.
            type: str
            sample: "arn:aws:sagemaker:us-east-1:123456789012:space/d-0123456789ab/ml-engineering"
        space_name:
            description: The name of the Space.
            type: str
            sample: "ml-engineering"
        space_display_name:
            description: The display name of the Space.
            type: str
            sample: "ML Engineering"
        home_efs_file_system_uid:
            description: The user ID used for the Space's home file system.
            type: str
            sample: "1001"
        ownership_settings:
            description: The ownership settings for the Space.
            type: dict
            sample:
                owner_user_profile_name: "ml-engineer"
            contains:
                owner_user_profile_name:
                    description: The user profile that owns the Space.
                    type: str
                    sample: "ml-engineer"
        space_settings:
            description: The settings of the Space.
            type: dict
            sample:
                app_type: "JupyterLab"
                space_storage_settings:
                    ebs_storage_settings:
                        ebs_volume_size_in_gb: 16
            contains:
                app_type:
                    description: The application type for the Space.
                    type: str
                    sample: "JupyterLab"
                code_editor_app_settings:
                    description: Code Editor application settings.
                    type: dict
                    sample: {}
                custom_file_systems:
                    description: Custom file systems attached to the Space.
                    type: list
                    elements: dict
                    sample:
                        - efs_file_system:
                              file_system_id: "fs-12345678"
                jupyter_lab_app_settings:
                    description: JupyterLab application settings.
                    type: dict
                    sample: {}
                jupyter_server_app_settings:
                    description: JupyterServer application settings.
                    type: dict
                    sample: {}
                kernel_gateway_app_settings:
                    description: KernelGateway application settings.
                    type: dict
                    sample: {}
                remote_access:
                    description: Remote access settings.
                    type: str
                    sample: "ENABLED"
                space_managed_resources:
                    description: Resources managed by SageMaker for the Space.
                    type: str
                    sample: "ENABLED"
                space_storage_settings:
                    description: Storage settings for the Space.
                    type: dict
                    sample:
                        ebs_storage_settings:
                            ebs_volume_size_in_gb: 16
        space_sharing_settings:
            description: The sharing settings for the Space.
            type: dict
            sample:
                sharing_type: "Private"
            contains:
                sharing_type:
                    description: Whether the Space is private or shared.
                    type: str
                    sample: "Private"
        creation_time:
            description: The time when the Space was created.
            type: str
            sample: "2025-01-01T12:00:00Z"
        last_modified_time:
            description: The time when the Space was last modified.
            type: str
            sample: "2025-01-01T12:00:00Z"
        status:
            description: The current status of the Space.
            type: str
            sample: "InService"
        failure_reason:
            description: The reason the Space entered a failed status.
            type: str
            sample: "The requested operation could not be completed."
        url:
            description: The URL of the Space.
            type: str
            sample: "https://example.aws"
msg:
    description: Informative message about the action.
    returned: always
    type: str
    sample: "Space ml-engineering created successfully."
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import SpaceStatus
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _build_replacement_space_params
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_space
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_space
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_space
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_space_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import space_needs_replacement
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import space_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_space
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_space_status

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _space_result(space: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if space is None:
        return {}
    return camel_dict_to_snake_dict(space, ignore_list=["tags", "Tags"])


def _space_status_check(
    client,
    module: AnsibleAWSModule,
    space: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not space:
        return space

    domain_id = module.params["domain_id"]
    space_name = module.params["space_name"]
    status = space.get("Status")
    if status == SpaceStatus.IN_SERVICE:
        return space

    if status == SpaceStatus.DELETING:
        if module.params["state"] == "absent":
            if module.params["wait"]:
                wait_for_space_status(client, module, domain_id, space_name, SpaceStatus.DELETED)
                module.exit_json(changed=False, msg=f"Space {space_name} is deleted.", space={})
            module.exit_json(
                changed=False,
                msg=f"Space {space_name} is currently deleting (not waiting).",
                space=_space_result(space),
            )
        module.fail_json(msg=f"Cannot manage Space {space_name} while it is being deleted.")

    if status == SpaceStatus.DELETED:
        if module.params["state"] == "absent":
            module.exit_json(changed=False, msg=f"Space {space_name} is deleted.", space={})
        module.fail_json(msg=f"Space {space_name} is deleted and cannot be managed until AWS removes it.")

    if status in (SpaceStatus.FAILED, SpaceStatus.UPDATE_FAILED, SpaceStatus.DELETE_FAILED):
        if status in (SpaceStatus.FAILED, SpaceStatus.UPDATE_FAILED) and module.params["state"] == "absent":
            return space
        module.fail_json(msg=f"Cannot manage Space {space_name} while it is in terminal status {status}.")

    if status in (SpaceStatus.PENDING, SpaceStatus.UPDATING):
        if module.check_mode:
            module.exit_json(
                changed=False,
                msg=f"Space {space_name} is currently in {status} state (check mode).",
                space=_space_result(space),
            )
        if not module.params["wait"]:
            module.exit_json(
                changed=False,
                msg=f"Space {space_name} is currently in {status} state (not waiting).",
                space=_space_result(space),
            )
        wait_for_space_status(client, module, domain_id, space_name, SpaceStatus.IN_SERVICE)
        return describe_space(client, domain_id, space_name)

    module.fail_json(msg=f"Cannot manage Space {space_name} while it is in unknown status {status}.")


def _present(
    client,
    module: AnsibleAWSModule,
    existing: Optional[Dict[str, Any]],
) -> Tuple[bool, Dict[str, Any]]:
    space_name = module.params["space_name"]
    domain_id = module.params["domain_id"]
    if existing is None:
        changed, msg = create_space(client, module)
        if module.check_mode:
            return changed, {"msg": msg, "space": {}}
        existing = describe_space(client, domain_id, space_name)
        if existing is None:
            module.fail_json(msg=f"Space {space_name} was not found after it was created.")
        return changed, {"msg": msg, "space": _space_result(existing)}

    if space_needs_replacement(existing, module):
        if not module.params["force"]:
            module.warn(
                "Immutable Space settings differ. force=true is required to replace the resource; "
                "continuing without replacement."
            )
            tags_changed = reconcile_space_tags(client, module, existing)
            msg = (
                f"Space {space_name} was not replaced because immutable settings differ."
                if not tags_changed
                else f"Space {space_name} tags updated; immutable settings still differ."
            )
            if module.check_mode:
                if tags_changed:
                    msg = f"Check mode: would have updated tags for Space {space_name}; immutable settings differ."
                return tags_changed, {"msg": msg, "space": _space_result(existing)}
            if tags_changed:
                existing = describe_space(client, domain_id, space_name)
            return tags_changed, {"msg": msg, "space": _space_result(existing)}
        if module.check_mode:
            return True, {
                "msg": f"Check mode: would have replaced Space {space_name} because immutable settings differ.",
                "space": {},
            }

        delete_changed, delete_msg = delete_space(
            client,
            module,
            domain_id,
            space_name,
            wait_for_completion=True,
        )
        if not delete_changed:
            module.fail_json(msg=f"Space {space_name} disappeared during replacement.")
        changed, msg = create_space(
            client,
            module,
            _build_replacement_space_params(module, existing),
            wait_for_completion=True,
        )
        replacement = describe_space(client, domain_id, space_name)
        if replacement is None:
            module.fail_json(msg=f"Space {space_name} was not found after replacement.")
        return changed, {"msg": f"{delete_msg} {msg}", "space": _space_result(replacement)}

    update_changed = space_needs_update(existing, module)
    if update_changed:
        changed, msg = update_space(client, module)
    else:
        changed = False
        msg = f"Space {space_name} is already up to date."

    tags_changed = reconcile_space_tags(client, module, existing)
    changed = changed or tags_changed
    if tags_changed and not update_changed:
        msg = f"Space {space_name} tags updated successfully."
    if module.check_mode:
        if tags_changed and not update_changed:
            msg = f"Check mode: would have updated tags for Space {space_name}."
        return changed, {"msg": msg, "space": _space_result(existing)}

    if changed:
        existing = describe_space(client, domain_id, space_name)
        if existing is None:
            module.fail_json(msg=f"Space {space_name} was not found after it was updated.")
    return changed, {"msg": msg, "space": _space_result(existing)}


def _absent(
    client,
    module: AnsibleAWSModule,
    existing: Optional[Dict[str, Any]],
) -> Tuple[bool, Dict[str, Any]]:
    if existing is None:
        return False, {"msg": f"Space {module.params['space_name']} does not exist.", "space": {}}

    changed, msg = delete_space(
        client,
        module,
        module.params["domain_id"],
        module.params["space_name"],
    )
    return changed, {"msg": msg, "space": _space_result(existing) if module.check_mode else {}}


def main() -> None:
    module = AnsibleAWSModule(
        argument_spec=dict(
            state=dict(type="str", default="present", choices=["present", "absent"]),
            domain_id=dict(type="str", required=True),
            space_name=dict(type="str", required=True, aliases=["name"]),
            space_display_name=dict(type="str"),
            ownership_settings=dict(
                type="dict",
                options=dict(owner_user_profile_name=dict(type="str", required=True)),
            ),
            space_settings=dict(
                type="dict",
                options=dict(
                    app_type=dict(type="str"),
                    code_editor_app_settings=dict(type="dict"),
                    custom_file_systems=dict(type="list", elements="dict"),
                    jupyter_lab_app_settings=dict(type="dict"),
                    jupyter_server_app_settings=dict(type="dict"),
                    kernel_gateway_app_settings=dict(type="dict"),
                    remote_access=dict(type="str", choices=["ENABLED", "DISABLED"]),
                    space_managed_resources=dict(type="str", choices=["ENABLED", "DISABLED"]),
                    space_storage_settings=dict(type="dict"),
                ),
            ),
            space_sharing_settings=dict(
                type="dict",
                options=dict(sharing_type=dict(type="str", required=True, choices=["Private", "Shared"])),
            ),
            tags=dict(type="dict", aliases=["resource_tags"]),
            purge_tags=dict(type="bool", default=True),
            force=dict(type="bool", default=False),
            wait=dict(type="bool", default=True),
            wait_timeout=dict(type="int", default=600),
        ),
        supports_check_mode=True,
    )
    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing = describe_space(client, module.params["domain_id"], module.params["space_name"])
        existing = _space_status_check(client, module, existing)
        if module.params["state"] == "absent":
            changed, result = _absent(client, module, existing)
        else:
            changed, result = _present(client, module, existing)
        module.exit_json(changed=changed, **result)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
