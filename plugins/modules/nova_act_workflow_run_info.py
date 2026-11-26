#!/usr/bin/python

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: nova_act_workflow_run_info
short_description: Gather information about Amazon Nova Act workflow runs
version_added: "2.1.0"
author:
    - Jan Likar (@janlikar)
description:
    - Retrieve a single Amazon Nova Act workflow run or list all workflow run summaries for a
      workflow definition.
    - Named lookups return the full workflow run, while listing returns summaries.
    - A missing workflow run returns an empty list.
    - A missing workflow definition causes the task to fail.
    - Nova Act requires botocore >= 1.42.1 to provide the service model.
    - The Nova Act service is currently available only in the US East (N. Virginia) Region (V(us-east-1)).
attributes:
    check_mode:
        description: Performs the same read-only requests as in normal mode.
        support: full
    diff_mode:
        description: Does not support diff mode.
        support: none
options:
    workflow_definition_name:
        description:
            - The name of the parent workflow definition to look up or list workflow runs under.
            - Must be 1 to 40 characters and contain only letters, numbers, underscores, or hyphens.
        type: str
        required: true
    workflow_run_id:
        description:
            - The ID of a workflow run to retrieve.
            - When omitted, lists all workflow run summaries for O(workflow_definition_name) across
              all pages.
        type: str
        aliases: ['name']
    sort_order:
        description:
            - The service-side sort order when listing workflow runs.
            - Only used when O(workflow_run_id) is not given.
        type: str
        choices: ['Ascending', 'Descending']
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
seealso:
    - module: amazon.ai.nova_act_workflow_run
    - module: amazon.ai.nova_act_workflow_definition_info
notes:
    - Named lookups require C(nova-act:GetWorkflowRun), and C(nova-act:GetWorkflowDefinition) when the
      workflow run is not found.
    - Listing requires C(nova-act:ListWorkflowRuns).
"""

EXAMPLES = r"""
- name: Get a Nova Act workflow run
  amazon.ai.nova_act_workflow_run_info:
    workflow_definition_name: "sample-workflow"
    workflow_run_id: "11111111-2222-3333-4444-555555555555"

- name: List all Nova Act workflow run summaries for a workflow definition
  amazon.ai.nova_act_workflow_run_info:
    workflow_definition_name: "sample-workflow"

- name: List summaries in descending service order
  amazon.ai.nova_act_workflow_run_info:
    workflow_definition_name: "sample-workflow"
    sort_order: "Descending"
  register: workflow_runs_info

- name: Show the status of all workflow runs
  ansible.builtin.debug:
    msg: "{{ workflow_runs_info.workflow_runs | map(attribute='status') | list }}"
"""

RETURN = r"""
workflow_runs:
    description:
        - Workflow runs or summaries returned by AWS.
        - An empty list is returned when no runs match.
    returned: always
    type: list
    elements: dict
    sample:
        - workflow_run_arn: "arn:aws:nova-act:us-east-1:123456789012:workflow-definition/sample-workflow/workflow-run/11111111-2222-3333-4444-555555555555"
          workflow_run_id: "11111111-2222-3333-4444-555555555555"
          status: "SUCCEEDED"
          started_at: "2026-10-29T10:00:00+00:00"
          ended_at: "2026-10-29T10:05:00+00:00"
    contains:
        workflow_run_arn:
            description: The Amazon Resource Name of the workflow run.
            returned: for each run
            type: str
            sample: "arn:aws:nova-act:us-east-1:123456789012:workflow-definition/sample-workflow/workflow-run/11111111-2222-3333-4444-555555555555"
        workflow_run_id:
            description: The ID of the workflow run.
            returned: for each run
            type: str
            sample: "11111111-2222-3333-4444-555555555555"
        status:
            description:
                - The status of the workflow run.
                - One of V(RUNNING), V(SUCCEEDED), V(FAILED), V(TIMED_OUT), or V(DELETING).
            returned: for each run
            type: str
            sample: "SUCCEEDED"
        started_at:
            description: The time when the workflow run started.
            returned: for each run
            type: str
            sample: "2026-10-29T10:00:00+00:00"
        ended_at:
            description: The time when the workflow run ended.
            returned: for each run that has ended
            type: str
            sample: "2026-10-29T10:05:00+00:00"
        model_id:
            description: The ID of the model the workflow run used.
            returned: on named lookup
            type: str
            sample: "sample-model"
        log_group_name:
            description: The name of the CloudWatch log group the workflow run's logs were sent to.
            returned: on named lookup when set
            type: str
            sample: "/nova-act/sample-workflow"
        trace_location:
            description: The location of the workflow run's trace, when listed.
            returned: when listed and returned by AWS
            type: dict
            sample:
                location_type: "S3"
                location: "s3://example-bucket/traces/11111111-2222-3333-4444-555555555555"
            contains:
                location_type:
                    description: The type of the trace location.
                    returned: when trace_location is returned by AWS
                    type: str
                    sample: "S3"
                location:
                    description: The location of the trace.
                    returned: when trace_location is returned by AWS
                    type: str
                    sample: "s3://example-bucket/traces/11111111-2222-3333-4444-555555555555"
msg:
    description: Informative message about the query.
    returned: always
    type: str
    sample: "Retrieved 1 workflow run(s)."
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.ai.plugins.module_utils.nova_act import _validate_nova_act_botocore
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import get_workflow_definition
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import get_workflow_run
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import list_workflow_runs
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import validate_workflow_definition_name
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import validate_workflow_run_id

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main() -> None:
    module = AnsibleAWSModule(
        argument_spec=dict(
            workflow_definition_name=dict(type="str", required=True),
            workflow_run_id=dict(type="str", aliases=["name"]),
            sort_order=dict(type="str", choices=["Ascending", "Descending"]),
        ),
        supports_check_mode=True,
    )
    _validate_nova_act_botocore(module)
    name = module.params["workflow_definition_name"]
    workflow_run_id = module.params["workflow_run_id"]
    validate_workflow_definition_name(module, name)
    validate_workflow_run_id(module, workflow_run_id)

    try:
        try:
            client = module.client("nova-act", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        if workflow_run_id is not None:
            run = get_workflow_run(client, module, name, workflow_run_id)
            if run is None and get_workflow_definition(client, module, name) is None:
                module.fail_json(msg=f"Workflow definition '{name}' does not exist.", changed=False, workflow_runs=[])
            runs = [run] if run is not None else []
        else:
            runs = list_workflow_runs(client, module, name, module.params["sort_order"])
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(
        changed=False,
        msg=f"Retrieved {len(runs)} workflow run(s).",
        workflow_runs=runs,
    )


if __name__ == "__main__":
    main()
