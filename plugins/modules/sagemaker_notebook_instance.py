#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_notebook_instance
short_description: Manage Amazon SageMaker notebook instances
version_added: "2.0.0"
author:
    - Domen Dobnikar (@domendobnikar)
description:
    - Create, update, tag, and delete Amazon SageMaker notebook instances.
    - A notebook instance is a managed Jupyter environment backed by a SageMaker execution role.
options:
    state:
        description:
            - The desired state of the notebook instance.
        type: str
        choices: [present, absent]
        default: present
    notebook_instance_name:
        description:
            - The name of the notebook instance.
        type: str
        required: true
        aliases: ["name"]
    instance_type:
        description:
            - The ML compute instance type used by the notebook instance.
            - Required when O(state=present).
        type: str
    role_arn:
        description:
            - The ARN of the IAM role that SageMaker can assume to access AWS services.
            - Required when O(state=present).
        type: str
    subnet_id:
        description:
            - The ID of the subnet where the notebook instance is deployed.
            - This setting is create-only.
        type: str
    security_groups:
        description:
            - The IDs of the security groups attached to the notebook instance.
            - This setting is create-only.
        type: list
        elements: str
    volume_size_in_gb:
        description:
            - The size of the EBS volume attached to the notebook instance, in GB.
            - This value can only increase in place.
            - Required when O(state=present).
        type: int
    direct_internet_access:
        description:
            - Whether to enable or disable direct internet access.
        type: str
        choices: [Enabled, Disabled]
    kms_key_id:
        description:
            - The ID of the AWS KMS key to use to encrypt the notebook instance storage.
            - This setting is create-only.
        type: str
    lifecycle_config_name:
        description:
            - The name of the notebook instance lifecycle configuration to associate.
            - Passing an empty value or omitting this option disassociates the existing lifecycle config.
        type: str
    default_code_repository:
        description:
            - The default code repository to associate with the notebook instance.
            - Passing an empty value or omitting this option disassociates the repository.
        type: str
    additional_code_repositories:
        description:
            - A list of additional code repositories to attach to the notebook instance.
            - Passing an empty list or omitting this option disassociates all additional repositories.
        type: list
        elements: str
    root_access:
        description:
            - Whether root access is enabled for the notebook instance.
            - This setting is create-only.
        type: str
        choices: [Enabled, Disabled]
    platform_identifier:
        description:
            - The platform identifier for the notebook instance.
            - This setting is create-only.
        type: str
    ip_address_type:
        description:
            - The IP address type for the notebook instance.
            - Specify ipv4 for IPv4-only connectivity.
            - Specify dualstack for both IPv4 and IPv6 connectivity.
            - When you specify dualstack, the subnet must support IPv6 CIDR blocks.
            - Required when O(state=present).
        type: str
        choices: [ipv4, dualstack]
    tags:
        description:
            - Tags to apply to the notebook instance.
        type: dict
        aliases: ["resource_tags"]
    purge_tags:
        description:
            - Whether to remove tags not present in O(tags).
        type: bool
        default: true
    wait:
        description:
            - Whether to wait for the notebook instance to reach a terminal state.
        type: bool
        default: true
    wait_timeout:
        description:
            - The time, in seconds, to wait for notebook instance lifecycle operations to complete.
        type: int
        default: 600
notes:
    - Required IAM actions include sagemaker:CreateNotebookInstance, sagemaker:DescribeNotebookInstance,
      sagemaker:UpdateNotebookInstance, sagemaker:DeleteNotebookInstance,
      sagemaker:StartNotebookInstance, sagemaker:StopNotebookInstance, sagemaker:ListNotebookInstances,
      sagemaker:ListTags, sagemaker:AddTags, sagemaker:DeleteTags, and iam:PassRole.
attributes:
    check_mode:
        description: Can run in check mode and report what would change without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_notebook_instance_info
      description: Gather information about SageMaker notebook instances.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Create a SageMaker notebook instance
  amazon.ai.sagemaker_notebook_instance:
    notebook_instance_name: my-notebook
    instance_type: ml.t3.medium
    role_arn: arn:aws:iam::123456789012:role/service-role/AmazonSageMaker-ExecutionRole
    tags:
      Environment: dev

- name: Update an in-place notebook instance property
  amazon.ai.sagemaker_notebook_instance:
    notebook_instance_name: my-notebook
    instance_type: ml.t3.large
    volume_size_in_gb: 20

- name: Delete a SageMaker notebook instance
  amazon.ai.sagemaker_notebook_instance:
    state: absent
    notebook_instance_name: my-notebook
"""

RETURN = r"""
notebook_instance:
    description: The notebook instance configuration after the operation.
    type: dict
    returned: always, on success
    contains:
        notebook_instance_name:
            description: The name of the notebook instance.
            type: str
            sample: my-notebook
        notebook_instance_arn:
            description: The Amazon Resource Name (ARN) of the notebook instance.
            type: str
            sample: arn:aws:sagemaker:us-east-1:123456789012:notebook-instance/my-notebook
        notebook_instance_status:
            description: The lifecycle status. One of Pending, InService, Stopping, Stopped, Failed, Deleting, Updating, PendingMaintenance, or InMaintenance.
            type: str
            sample: InService
        failure_reason:
            description: The reason a notebook instance failed to start.
            type: str
            sample: The instance failed to start.
        url:
            description: The URL used to access the notebook instance.
            type: str
            sample: my-notebook.notebook.us-east-1.sagemaker.aws
        instance_type:
            description: The compute instance type, with the supported values documented under notebook_instance.instance_type.
            type: str
            sample: ml.t3.medium
        ip_address_type:
            description: The IP address type. One of ipv4 or dualstack.
            type: str
            sample: ipv4
        subnet_id:
            description: The ID of the subnet in the notebook instance VPC.
            type: str
            sample: subnet-0123456789abcdef0
        security_groups:
            description: The IDs of the security groups attached to the notebook instance.
            type: list
            elements: str
            sample: [sg-0123456789abcdef0]
        role_arn:
            description: The Amazon Resource Name (ARN) of the IAM role associated with the notebook instance.
            type: str
            sample: arn:aws:iam::123456789012:role/SageMakerExecutionRole
        kms_key_id:
            description: The ID of the KMS key used to encrypt the notebook instance storage volume.
            type: str
            sample: 12345678-1234-1234-1234-123456789012
        network_interface_id:
            description: The ID of the network interface attached to the notebook instance.
            type: str
            sample: eni-0123456789abcdef0
        last_modified_time:
            description: The time when the notebook instance was last modified.
            type: str
            sample: '2025-01-01T12:00:00Z'
        creation_time:
            description: The time when the notebook instance was created.
            type: str
            sample: '2025-01-01T12:00:00Z'
        notebook_instance_lifecycle_config_name:
            description: The name of the notebook instance lifecycle configuration.
            type: str
            sample: my-lifecycle-config
        direct_internet_access:
            description: Whether direct internet access is enabled. One of Enabled or Disabled.
            type: str
            sample: Enabled
        volume_size_in_gb:
            description: The size of the notebook instance storage volume in gigabytes.
            type: int
            sample: 5
        accelerator_types:
            description:
                - The accelerator types attached to the notebook instance.
                - Values include ml.eia1.medium, ml.eia1.large, ml.eia1.xlarge, ml.eia2.medium, ml.eia2.large, and ml.eia2.xlarge.
            type: list
            elements: str
            sample: [ml.eia1.medium]
        default_code_repository:
            description: The URL of the default Git repository associated with the notebook instance.
            type: str
            sample: https://github.com/example/repository.git
        additional_code_repositories:
            description: The URLs of additional Git repositories associated with the notebook instance.
            type: list
            elements: str
            sample: [https://github.com/example/another-repository.git]
        root_access:
            description: Whether root access is enabled. One of Enabled or Disabled.
            type: str
            sample: Enabled
        platform_identifier:
            description: The platform identifier of the notebook instance operating system.
            type: str
            sample: notebook-al2-v1
        instance_metadata_service_configuration:
            description: The instance metadata service configuration for the notebook instance.
            type: dict
            contains:
                minimum_instance_metadata_service_version:
                    description: The minimum supported instance metadata service version.
                    type: str
                    sample: '1'
        tags:
            description: The notebook instance tags, returned when O(tags) is provided.
            type: dict
            sample:
                Environment: dev
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: Notebook instance my-notebook created successfully.
tags:
    description: A dictionary containing the notebook instance's current tags.
    type: dict
    returned: on success when state is present
    sample: {"Environment": "dev"}
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import NotebookInstanceStatus
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_notebook_instance
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_notebook_instance
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_notebook_instance
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import (
    notebook_instance_immutable_parameters_needs_replacement,
)
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import notebook_instance_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_notebook_instance_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_notebook_instance
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_notebook_instance_status

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _notebook_instance_status_check(
    client, existing_notebook: Optional[Dict[str, Any]], module: AnsibleAWSModule
) -> None:
    # Early exit if is deleting, creating, updating or stopping
    if existing_notebook:
        if existing_notebook.get("NotebookInstanceStatus") in {
            NotebookInstanceStatus.PENDING,
            NotebookInstanceStatus.UPDATING,
        }:
            if not module.params.get("wait", False) or module.check_mode:
                module.exit_json(
                    msg=f"Notebook instance {existing_notebook.get('NotebookInstanceName')} "
                    f"is currently in {existing_notebook.get('NotebookInstanceStatus')} state."
                )
            else:
                wait_for_notebook_instance_status(client, module, NotebookInstanceStatus.IN_SERVICE)
        elif existing_notebook.get("NotebookInstanceStatus") == NotebookInstanceStatus.DELETING:
            if not module.params.get("wait", False) or module.check_mode:
                module.exit_json(
                    msg=f"Notebook instance {existing_notebook.get('NotebookInstanceName')} "
                    f"is currently in {existing_notebook.get('NotebookInstanceStatus')} state."
                )
            else:
                wait_for_notebook_instance_status(client, module, NotebookInstanceStatus.DELETED)
        elif existing_notebook.get("NotebookInstanceStatus") == NotebookInstanceStatus.STOPPING:
            if not module.params.get("wait", False) or module.check_mode:
                module.exit_json(
                    msg=f"Notebook instance {existing_notebook.get('NotebookInstanceName')} "
                    f"is currently in {existing_notebook.get('NotebookInstanceStatus')} state."
                )
            else:
                wait_for_notebook_instance_status(client, module, NotebookInstanceStatus.STOPPED)


def _notebook_instance_result(client, name: str) -> Dict[str, Any]:
    existing = describe_notebook_instance(client, name)
    if existing is None:
        return {}
    return camel_dict_to_snake_dict(existing, ignore_list=["tags", "Tags"])


def _absent(module: AnsibleAWSModule, client, name: str, existing_notebook_instance: Optional[Dict[str, Any]]) -> None:
    if not existing_notebook_instance:
        module.exit_json(changed=False, msg=f"Notebook instance {name} does not exist.")
    else:
        if module.check_mode:
            module.exit_json(changed=True, msg=f"Check mode: would have deleted notebook instance {name}.")

        delete_notebook_instance(client, module, existing_notebook_instance)
        module.exit_json(
            changed=True,
            notebook_instance={},
            tags={},
            msg=f"Notebook instance {name} deleted successfully.",
        )


def _present(module: AnsibleAWSModule, client, name: str, existing_notebook_instance: Optional[Dict[str, Any]]) -> None:
    if existing_notebook_instance:
        if notebook_instance_immutable_parameters_needs_replacement(existing_notebook_instance, module):
            module.fail_json(
                msg=(
                    f"Notebook instance {name} has create-only configuration drift. "
                    "Update is not supported for the changed property; recreate the notebook instance with the desired values."
                )
            )
        changed = False
        needs_change, update_params = notebook_instance_needs_update(existing_notebook_instance, module)
        if reconcile_notebook_instance_tags(client, module, existing_notebook_instance):
            changed = True
        if needs_change:
            update_notebook_instance(client, module, existing_notebook_instance, update_params)
            changed = True
        if module.check_mode:
            if changed:
                module.exit_json(changed=changed, msg=f"Check mode: would have updated notebook instance {name}.")
            module.exit_json(changed=changed, msg=f"Check mode: no changes needed for notebook instance {name}.")

        notebook_instance = _notebook_instance_result(client, name)
        tags = list_tags(client, notebook_instance["notebook_instance_arn"]) if notebook_instance else {}
        message = (
            f"Notebook instance {name} is already up to date."
            if not changed
            else f"Notebook instance {name} updated successfully."
        )
        module.exit_json(changed=changed, notebook_instance=notebook_instance, tags=tags, msg=message)

    if module.check_mode:
        module.exit_json(changed=True, msg=f"Check mode: would have created notebook instance {name}.")

    create_notebook_instance(client, module)
    notebook_instance = _notebook_instance_result(client, name)
    tags = list_tags(client, notebook_instance["notebook_instance_arn"]) if notebook_instance else {}
    module.exit_json(
        changed=True,
        notebook_instance=notebook_instance,
        tags=tags,
        msg=f"Notebook instance {name} created successfully.",
    )


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        notebook_instance_name=dict(type="str", required=True, aliases=["name"]),
        instance_type=dict(type="str"),
        role_arn=dict(type="str"),
        subnet_id=dict(type="str"),
        security_groups=dict(type="list", elements="str"),
        volume_size_in_gb=dict(type="int"),
        direct_internet_access=dict(type="str", choices=["Enabled", "Disabled"]),
        kms_key_id=dict(type="str"),
        lifecycle_config_name=dict(type="str"),
        default_code_repository=dict(type="str"),
        additional_code_repositories=dict(type="list", elements="str"),
        root_access=dict(type="str", choices=["Enabled", "Disabled"]),
        platform_identifier=dict(type="str"),
        ip_address_type=dict(type="str", choices=["ipv4", "dualstack"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ["ip_address_type", "instance_type", "role_arn", "volume_size_in_gb"]),
        ],
    )
    name = module.params["notebook_instance_name"]

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing_notebook_instance = describe_notebook_instance(client, name)
        _notebook_instance_status_check(client, existing_notebook_instance, module)
        # Refresh status of the existing notebook instance
        existing_notebook_instance = describe_notebook_instance(client, name)

        if module.params["state"] == "present":
            _present(module, client, name, existing_notebook_instance)
        else:
            _absent(module, client, name, existing_notebook_instance)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
