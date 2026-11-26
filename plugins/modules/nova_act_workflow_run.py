#!/usr/bin/python

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: nova_act_workflow_run
short_description: Manage Amazon Nova Act workflow runs
version_added: "2.1.0"
author:
    - Jan Likar (@janlikar)
description:
    - Create and delete Amazon Nova Act workflow runs.
    - A workflow run is an execution of an existing Amazon Nova Act workflow definition.
    - All creation inputs are immutable after creation; Amazon Nova Act provides no update operation for them.
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
            - The desired state of the workflow run.
        type: str
        choices: ['present', 'absent']
        default: present
    workflow_definition_name:
        description:
            - The name of the parent workflow definition.
            - Must be 1 to 40 characters and contain only letters, numbers, underscores, or hyphens.
        type: str
        required: true
    workflow_run_id:
        description:
            - The ID of an existing workflow run to look up or delete.
            - Amazon Nova Act assigns this ID when a run is created; it cannot be chosen by the caller.
            - When O(state=present) and this is omitted, a new workflow run is always created, since
              there is no way to check for an existing run without already knowing its ID.
            - When O(state=present), the task fails if the workflow run or its workflow definition does
              not exist, or if the workflow run has ended with V(FAILED) or V(TIMED_OUT).
            - Required when O(state=absent).
        type: str
    model_id:
        description:
            - The ID of the model to run the workflow with.
            - Required when O(state=present) and O(workflow_run_id) is not set.
            - This value is create-only.
        type: str
    client_info:
        description:
            - Information about the client creating the workflow run.
            - Required when O(state=present) and O(workflow_run_id) is not set.
            - This value is create-only.
        type: dict
        suboptions:
            compatibility_version:
                description:
                    - The compatibility version of the client.
                type: int
                required: true
            sdk_version:
                description:
                    - The version of the SDK used by the client.
                type: str
    client_token:
        description:
            - A client token used by Nova Act to make workflow-run creation idempotent.
            - When omitted, Boto3 automatically populates the token.
        type: str
    log_group_name:
        description:
            - The name of the CloudWatch log group to send the workflow run's logs to.
            - This value is create-only.
        type: str
    wait:
        description:
            - When O(state=present) and a new workflow run is created, whether to wait until it
              reaches a terminal status (V(SUCCEEDED), V(FAILED), or V(TIMED_OUT)).
            - When O(state=present) and O(workflow_run_id) refers to a V(RUNNING) workflow run, whether
              to wait until it reaches a terminal status.
            - The task fails when the workflow run ends with V(FAILED) or V(TIMED_OUT).
            - When O(state=absent), whether to wait after deletion until the workflow run is no
              longer returned by AWS.
            - Deletion polling is best-effort because AWS does not document not-found as a completion guarantee.
        type: bool
        default: true
    wait_timeout:
        description:
            - The maximum time in seconds to wait.
            - Only used when O(wait=true). Must be greater than zero.
        type: int
        default: 600
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
seealso:
    - module: amazon.ai.nova_act_workflow_run_info
    - module: amazon.ai.nova_act_workflow_definition
notes:
    - Requires C(nova-act:CreateWorkflowRun), C(nova-act:DeleteWorkflowRun), and C(nova-act:GetWorkflowRun).
    - Requires C(nova-act:GetWorkflowDefinition) when O(workflow_run_id) refers to a workflow run that is not found.
"""

EXAMPLES = r"""
- name: Create a Nova Act workflow run
  amazon.ai.nova_act_workflow_run:
    workflow_definition_name: "sample-workflow"
    model_id: "sample-model"
    client_info:
      compatibility_version: 1

- name: Create a Nova Act workflow run that sends logs to a log group
  amazon.ai.nova_act_workflow_run:
    workflow_definition_name: "sample-workflow"
    model_id: "sample-model"
    client_info:
      compatibility_version: 1
      sdk_version: "1.0.0"
    log_group_name: "/nova-act/sample-workflow"

- name: Look up an existing workflow run, waiting for it to finish
  amazon.ai.nova_act_workflow_run:
    workflow_definition_name: "sample-workflow"
    workflow_run_id: "11111111-2222-3333-4444-555555555555"

- name: Delete a Nova Act workflow run
  amazon.ai.nova_act_workflow_run:
    state: absent
    workflow_definition_name: "sample-workflow"
    workflow_run_id: "11111111-2222-3333-4444-555555555555"
"""

RETURN = r"""
workflow_run:
    description:
        - The workflow run returned by GetWorkflowRun.
        - When O(state=absent) and the workflow run existed, its last known state with
          RV(workflow_run.status) taken from the delete response, even when O(wait=true) and the
          workflow run has since been removed.
        - An empty dict when O(state=absent) and the workflow run did not exist, or in check mode
          when creating.
    returned: always
    type: dict
    sample:
        workflow_run_arn: "arn:aws:nova-act:us-east-1:123456789012:workflow-definition/sample-workflow/workflow-run/11111111-2222-3333-4444-555555555555"
        workflow_run_id: "11111111-2222-3333-4444-555555555555"
        status: "SUCCEEDED"
        started_at: "2026-10-29T10:00:00+00:00"
        ended_at: "2026-10-29T10:05:00+00:00"
        model_id: "sample-model"
        log_group_name: "/nova-act/sample-workflow"
    contains:
        workflow_run_arn:
            description: The Amazon Resource Name of the workflow run.
            returned: when the workflow run exists
            type: str
            sample: "arn:aws:nova-act:us-east-1:123456789012:workflow-definition/sample-workflow/workflow-run/11111111-2222-3333-4444-555555555555"
        workflow_run_id:
            description: The ID of the workflow run.
            returned: when the workflow run exists
            type: str
            sample: "11111111-2222-3333-4444-555555555555"
        status:
            description:
                - The status of the workflow run.
                - One of V(RUNNING), V(SUCCEEDED), V(FAILED), V(TIMED_OUT), or V(DELETING).
            returned: when the workflow run exists
            type: str
            sample: "SUCCEEDED"
        started_at:
            description: The time when the workflow run started.
            returned: when the workflow run exists
            type: str
            sample: "2026-10-29T10:00:00+00:00"
        ended_at:
            description: The time when the workflow run ended.
            returned: when the workflow run exists and has ended
            type: str
            sample: "2026-10-29T10:05:00+00:00"
        model_id:
            description: The ID of the model the workflow run used.
            returned: when the workflow run exists
            type: str
            sample: "sample-model"
        log_group_name:
            description: The name of the CloudWatch log group the workflow run's logs were sent to.
            returned: when the workflow run exists and has a log group configured
            type: str
            sample: "/nova-act/sample-workflow"
msg:
    description: Informative message about the action.
    returned: always
    type: str
    sample: "Workflow run '11111111-2222-3333-4444-555555555555' created successfully (SUCCEEDED)."
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from ansible_collections.amazon.ai.plugins.module_utils.nova_act import _WORKFLOW_RUN_FAILURE_STATUSES
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import _validate_nova_act_botocore
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import create_workflow_run
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import delete_workflow_run
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import get_workflow_definition
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import get_workflow_run
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import validate_workflow_definition_name
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import validate_workflow_run_id
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import wait_for_workflow_run_deleted
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import wait_for_workflow_run_status

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _workflow_run_status_check(
    client,
    module: AnsibleAWSModule,
    existing: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not existing:
        return existing

    name = module.params["workflow_definition_name"]
    workflow_run_id = module.params["workflow_run_id"]
    status = existing.get("status")

    if status == "DELETING":
        if module.params["state"] == "present":
            module.fail_json(
                msg=f"Workflow run '{workflow_run_id}' is currently DELETING and cannot be made present.",
                changed=False,
                workflow_run=existing,
            )
        if module.check_mode or not module.params["wait"]:
            return existing
        wait_for_workflow_run_deleted(client, module, name, workflow_run_id)
        return None

    # A RUNNING, FAILED or TIMED_OUT run can still be deleted, so only state=present is gated here.
    if module.params["state"] == "absent":
        return existing

    if status in _WORKFLOW_RUN_FAILURE_STATUSES:
        module.fail_json(
            msg=f"Workflow run '{workflow_run_id}' ended with status '{status}'.",
            changed=False,
            workflow_run=existing,
        )

    if status == "RUNNING" and module.params["wait"] and not module.check_mode:
        return wait_for_workflow_run_status(client, module, name, workflow_run_id, changed=False)

    return existing


def _validate_params(module: AnsibleAWSModule) -> None:
    workflow_run_id = module.params["workflow_run_id"]
    validate_workflow_definition_name(module, module.params["workflow_definition_name"])
    validate_workflow_run_id(module, workflow_run_id)
    if module.params["wait"] and module.params["wait_timeout"] < 1:
        module.fail_json(msg="wait_timeout must be greater than zero.")
    if module.params["state"] != "present" or workflow_run_id is not None:
        return
    for option in ("model_id", "client_info"):
        if module.params[option] is None:
            module.fail_json(msg=f"{option} is required when workflow_run_id is not set.")


def _ensure_present(
    client,
    module: AnsibleAWSModule,
    existing: Optional[Dict[str, Any]],
    definition_missing: bool,
) -> Tuple[bool, Dict[str, Any], str]:
    name = module.params["workflow_definition_name"]
    workflow_run_id = module.params["workflow_run_id"]
    if definition_missing:
        module.fail_json(msg=f"Workflow definition '{name}' does not exist.", changed=False, workflow_run={})
    if workflow_run_id is None:
        return create_workflow_run(client, module)
    if existing is None:
        module.fail_json(msg=f"Workflow run '{workflow_run_id}' does not exist.", changed=False, workflow_run={})
    return False, existing, f"Workflow run '{workflow_run_id}' already exists and no changes are needed."


def _ensure_absent(
    client,
    module: AnsibleAWSModule,
    existing: Optional[Dict[str, Any]],
    definition_missing: bool,
) -> Tuple[bool, Dict[str, Any], str]:
    name = module.params["workflow_definition_name"]
    workflow_run_id = module.params["workflow_run_id"]
    if existing is None:
        msg = f"Workflow run '{workflow_run_id}' does not exist."
        if definition_missing:
            msg = f"Workflow run '{workflow_run_id}' does not exist: workflow definition '{name}' does not exist."
        return False, {}, msg
    if existing.get("status") == "DELETING":
        return False, existing, f"Workflow run '{workflow_run_id}' is already being deleted."
    return delete_workflow_run(client, module, existing)


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        workflow_definition_name=dict(type="str", required=True),
        workflow_run_id=dict(type="str"),
        model_id=dict(type="str"),
        client_info=dict(
            type="dict",
            options=dict(
                compatibility_version=dict(type="int", required=True),
                sdk_version=dict(type="str"),
            ),
        ),
        client_token=dict(type="str", no_log=False),
        log_group_name=dict(type="str"),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[("state", "absent", ["workflow_run_id"])],
        supports_check_mode=True,
    )
    _validate_nova_act_botocore(module)
    name = module.params["workflow_definition_name"]
    workflow_run_id = module.params["workflow_run_id"]
    _validate_params(module)

    try:
        try:
            client = module.client("nova-act", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing: Optional[Dict[str, Any]] = (
            get_workflow_run(client, module, name, workflow_run_id) if workflow_run_id is not None else None
        )
        existing = _workflow_run_status_check(client, module, existing)
        definition_missing = (
            workflow_run_id is not None and existing is None and get_workflow_definition(client, module, name) is None
        )

        if module.params["state"] == "present":
            changed, run, msg = _ensure_present(client, module, existing, definition_missing)
        else:
            changed, run, msg = _ensure_absent(client, module, existing, definition_missing)

        module.exit_json(changed=changed, msg=msg, workflow_run=run)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
