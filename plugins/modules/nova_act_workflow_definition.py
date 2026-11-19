#!/usr/bin/python

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: nova_act_workflow_definition
short_description: Manage Amazon Nova Act workflow definitions
version_added: "2.1.0"
author:
    - Jan Likar (@janlikar)
description:
    - Create and delete Amazon Nova Act workflow definitions.
    - Workflow definition names and supplied configuration are immutable after creation.
    - Nova Act requires botocore >= 1.42.1 to provide the service model.
    - The Nova Act service is currently available only in the US East (N. Virginia) Region (V(us-east-1)).
attributes:
    check_mode:
        description: Can run in check mode without changing the target.
        support: full
    diff_mode:
        description: Does not support diff mode.
        support: none
options:
    state:
        description:
            - The desired state of the workflow definition.
        type: str
        choices: ['present', 'absent']
        default: present
    workflow_definition_name:
        description:
            - The name of the workflow definition to manage.
            - Must be 1 to 40 characters and contain only letters, numbers, underscores, or hyphens.
        type: str
        required: true
        aliases: ['name']
    description:
        description:
            - A description for the workflow definition.
            - This value is create-only.
        type: str
    export_config:
        description:
            - The optional S3 export configuration for workflow output.
            - This value is create-only.
            - Only the suboptions that are set are compared with an existing workflow definition.
        type: dict
        suboptions:
            s3_bucket_name:
                description:
                    - The name of the S3 bucket used to export workflow data.
                type: str
                required: true
            s3_key_prefix:
                description:
                    - The prefix for exported S3 object keys.
                type: str
    client_token:
        description:
            - A client token used by Nova Act to make workflow-definition creation idempotent.
            - When omitted, Boto3 automatically populates the token.
        type: str
    wait:
        description:
            - Whether to wait after deletion until the workflow definition is no longer returned by AWS.
            - Deletion polling is best-effort because AWS does not document not-found as a completion guarantee.
            - Only used when O(state=absent).
        type: bool
        default: true
    wait_timeout:
        description:
            - The maximum time in seconds to wait for deletion.
            - Only used when O(state=absent) and O(wait=true). Must be greater than zero.
        type: int
        default: 600
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
seealso:
    - module: amazon.ai.nova_act_workflow_definition_info
notes:
    - Requires C(nova-act:CreateWorkflowDefinition), C(nova-act:DeleteWorkflowDefinition), and C(nova-act:GetWorkflowDefinition).
    - When O(export_config) is set, the calling identity needs an identity-based policy granting
      C(s3:PutObject) to the destination bucket and prefix.
    - The destination bucket must be in the same AWS account; cross-account buckets are unsupported.
"""

EXAMPLES = r"""
- name: Create a Nova Act workflow definition
  amazon.ai.nova_act_workflow_definition:
    workflow_definition_name: "sample-workflow"
    description: "A sample Nova Act workflow"

- name: Create a Nova Act workflow definition that exports to S3
  amazon.ai.nova_act_workflow_definition:
    workflow_definition_name: "exported-workflow"
    export_config:
      s3_bucket_name: "example-bucket"
      s3_key_prefix: "workflow-exports/"

- name: Delete a Nova Act workflow definition
  amazon.ai.nova_act_workflow_definition:
    state: absent
    workflow_definition_name: "sample-workflow"
"""

RETURN = r"""
workflow_definition:
    description:
        - The workflow definition returned by GetWorkflowDefinition.
        - When O(state=absent) and the workflow definition existed, its last known state with RV(workflow_definition.status) taken from the delete response.
        - An empty dict when O(state=absent) and the workflow definition did not exist, or in check mode when creating.
    returned: always
    type: dict
    sample:
        name: "sample-workflow"
        workflow_definition_name: "sample-workflow"
        arn: "arn:aws:nova-act:us-east-1:123456789012:workflow-definition/sample-workflow"
        workflow_definition_arn: "arn:aws:nova-act:us-east-1:123456789012:workflow-definition/sample-workflow"
        created_at: "2026-10-29T10:00:00+00:00"
        description: "A sample Nova Act workflow"
        status: "ACTIVE"
    contains:
        name:
            description: The name of the workflow definition.
            returned: when the workflow definition exists
            type: str
            sample: "sample-workflow"
        workflow_definition_name:
            description: Alias of RV(workflow_definition.name), for consistency with M(amazon.ai.nova_act_workflow_definition_info) listings.
            returned: when the workflow definition exists
            type: str
            sample: "sample-workflow"
        arn:
            description: The Amazon Resource Name of the workflow definition.
            returned: when the workflow definition exists
            type: str
            sample: "arn:aws:nova-act:us-east-1:123456789012:workflow-definition/sample-workflow"
        workflow_definition_arn:
            description: Alias of RV(workflow_definition.arn), for consistency with M(amazon.ai.nova_act_workflow_definition_info) listings.
            returned: when the workflow definition exists
            type: str
            sample: "arn:aws:nova-act:us-east-1:123456789012:workflow-definition/sample-workflow"
        created_at:
            description: The time when the workflow definition was created.
            returned: when the workflow definition exists
            type: str
            sample: "2026-10-29T10:00:00+00:00"
        description:
            description: The description of the workflow definition.
            returned: when the workflow definition exists and has a description
            type: str
            sample: "A sample Nova Act workflow"
        export_config:
            description: The S3 export configuration for the workflow definition.
            returned: when the workflow definition exists and has an export configuration
            type: dict
            sample:
                s3_bucket_name: "example-bucket"
                s3_key_prefix: "workflow-exports/"
            contains:
                s3_bucket_name:
                    description: The name of the S3 bucket used for exports.
                    returned: when the workflow definition has an export configuration
                    type: str
                    sample: "example-bucket"
                s3_key_prefix:
                    description: The prefix for exported object keys.
                    returned: when the export configuration has a key prefix
                    type: str
                    sample: "workflow-exports/"
        status:
            description:
                - The status of the workflow definition.
                - One of V(ACTIVE) or V(DELETING).
            returned: when the workflow definition exists
            type: str
            sample: "ACTIVE"
msg:
    description: Informative message about the action.
    returned: always
    type: str
    sample: "Workflow definition 'sample-workflow' created successfully."
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.nova_act import _validate_nova_act_botocore
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import create_workflow_definition
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import delete_workflow_definition
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import get_workflow_definition
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import validate_workflow_definition_name
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import wait_for_workflow_definition_deleted

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _workflow_definition_status_check(
    client,
    module: AnsibleAWSModule,
    existing: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not existing or existing.get("status") != "DELETING":
        return existing

    name = module.params["workflow_definition_name"]
    if module.params["state"] == "present":
        module.fail_json(msg=f"Workflow definition '{name}' is currently DELETING and cannot be made present.")

    if module.check_mode or not module.params["wait"]:
        return existing

    wait_for_workflow_definition_deleted(client, module, name)
    return None


def _definition_needs_replacement(module: AnsibleAWSModule, existing: Dict[str, Any]) -> bool:
    description = module.params.get("description")
    if description is not None and description != existing.get("description"):
        return True

    export_config = module.params.get("export_config")
    if export_config is not None:
        existing_export_config = existing.get("export_config") or {}
        return any(
            value is not None and value != existing_export_config.get(key) for key, value in export_config.items()
        )
    return False


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        workflow_definition_name=dict(type="str", required=True, aliases=["name"]),
        description=dict(type="str"),
        export_config=dict(
            type="dict",
            options=dict(
                s3_bucket_name=dict(type="str", required=True),
                s3_key_prefix=dict(type="str", no_log=True),
            ),
        ),
        client_token=dict(type="str", no_log=True),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    _validate_nova_act_botocore(module)
    validate_workflow_definition_name(module, module.params["workflow_definition_name"])
    if module.params["state"] == "absent" and module.params["wait"] and module.params["wait_timeout"] < 1:
        module.fail_json(msg="wait_timeout must be greater than zero.")

    try:
        try:
            client = module.client("nova-act", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        name = module.params["workflow_definition_name"]
        existing: Optional[Dict[str, Any]] = get_workflow_definition(client, module, name)
        existing = _workflow_definition_status_check(client, module, existing)

        if module.params["state"] == "present":
            if existing is None:
                changed, definition, msg = create_workflow_definition(client, module)
            elif _definition_needs_replacement(module, existing):
                module.fail_json(
                    msg=(
                        f"Workflow definition '{name}' already exists and its name, description, "
                        "and export configuration are create-only."
                    )
                )
            else:
                changed = False
                definition = existing
                msg = f"Workflow definition '{name}' already exists and no changes are needed."
        elif existing is None:
            changed = False
            definition = {}
            msg = f"Workflow definition '{name}' does not exist."
        elif existing.get("status") == "DELETING":
            changed = False
            definition = existing
            msg = f"Workflow definition '{name}' is already being deleted."
        else:
            changed, definition, msg = delete_workflow_definition(client, module, existing)

        module.exit_json(changed=changed, msg=msg, workflow_definition=definition)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
