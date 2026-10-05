#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_notebook_instance_info
short_description: Gather information about SageMaker notebook instances
version_added: "2.0.0"
author:
    - Domen Dobnikar (@domendobnikar)
description:
    - Retrieve a SageMaker notebook instance by name or list instances with supported filters.
    - When O(tags) is provided, return tags and include only instances matching every key/value pair.
options:
    notebook_instance_name:
        description:
            - The name of the notebook instance to retrieve.
            - If omitted, the module lists notebook instances.
        type: str
        aliases: [name]
    name_contains:
        description:
            - A substring in the notebook instance name used to filter list results.
        type: str
    tags:
        description:
            - Tag key/value pairs that every returned instance must contain.
            - Tags are retrieved and included in results only when this option is provided.
        type: dict
notes:
    - Required IAM actions include sagemaker:DescribeNotebookInstance, sagemaker:ListNotebookInstances, and sagemaker:ListTags.
attributes:
    check_mode:
        description: Can run in check mode without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_notebook_instance
      description: Manage SageMaker notebook instances.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Get a notebook instance by name
  amazon.ai.sagemaker_notebook_instance_info:
    name: my-notebook

- name: List notebook instances containing a name and matching tags
  amazon.ai.sagemaker_notebook_instance_info:
    name_contains: my-notebook
    tags:
      Environment: dev
"""

RETURN = r"""
notebook_instances:
    description: The matching notebook instances.
    type: list
    elements: dict
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
changed:
    description: Whether the module changed any resources.
    type: bool
    returned: always
    sample: false
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_notebook_instance
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_notebook_instances
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _enrich_notebook_instance(
    client, instance: Dict[str, Any], desired_tags: Optional[Dict[str, str]]
) -> Optional[Dict[str, Any]]:
    notebook_instance = describe_notebook_instance(client, instance["NotebookInstanceName"])
    if notebook_instance is None:
        return None

    if desired_tags is not None:
        tags = list_tags(client, notebook_instance["NotebookInstanceArn"])
        if not desired_tags.items() <= tags.items():
            return None
        notebook_instance["Tags"] = tags

    return camel_dict_to_snake_dict(notebook_instance, ignore_list=["tags", "Tags"])


def find_notebook_instances(client, module: AnsibleAWSModule) -> List[Dict[str, Any]]:
    name: Optional[str] = module.params.get("notebook_instance_name")
    desired_tags: Optional[Dict[str, str]] = module.params.get("tags")

    if name:
        instance = describe_notebook_instance(client, name)
        if instance is None:
            return list()
        enriched = _enrich_notebook_instance(client, instance, desired_tags)
        return [enriched] if enriched is not None else list()

    params: Dict[str, Any] = dict()
    if module.params.get("name_contains"):
        params["NameContains"] = module.params["name_contains"]

    summaries = list_notebook_instances(client, **params)
    instances: List[Dict[str, Any]] = list()
    for summary in summaries:
        instance = _enrich_notebook_instance(client, summary, desired_tags)
        if instance is not None:
            instances.append(instance)
    return instances


def main() -> None:
    argument_spec = dict(
        notebook_instance_name=dict(type="str", aliases=["name"]),
        name_contains=dict(type="str"),
        tags=dict(type="dict"),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[("notebook_instance_name", "name_contains")],
    )

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        instances = find_notebook_instances(client, module)
        if module.params.get("notebook_instance_name"):
            module.exit_json(changed=False, notebook_instance=instances[0] if instances else list())
        module.exit_json(changed=False, notebook_instances=instances)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
