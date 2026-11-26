#!/usr/bin/python

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: nova_act_workflow_definition_info
short_description: Gather information about Amazon Nova Act workflow definitions
version_added: "2.1.0"
author:
    - Jan Likar (@janlikar)
description:
    - Retrieve a single Amazon Nova Act workflow definition or list all workflow definition summaries.
    - Named lookups return full configuration, while listing returns summaries without additional detail requests.
    - Every returned element contains both RV(workflow_definitions[].name) and RV(workflow_definitions[].workflow_definition_name),
      and both RV(workflow_definitions[].arn) and RV(workflow_definitions[].workflow_definition_arn), regardless of lookup mode.
    - A missing workflow definition returns an empty list.
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
            - The name of the workflow definition to retrieve.
            - Must be 1 to 40 characters and contain only letters, numbers, underscores, or hyphens.
            - When omitted, lists all workflow definition summaries across all pages.
            - Mutually exclusive with O(sort_order).
        type: str
        aliases: ['name']
    sort_order:
        description:
            - The service-side sort order when listing workflow definitions.
            - Mutually exclusive with O(workflow_definition_name).
        type: str
        choices: ['Ascending', 'Descending']
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
seealso:
    - module: amazon.ai.nova_act_workflow_definition
notes:
    - Named lookups require C(nova-act:GetWorkflowDefinition).
    - Listing requires C(nova-act:ListWorkflowDefinitions).
"""

EXAMPLES = r"""
- name: Get a Nova Act workflow definition
  amazon.ai.nova_act_workflow_definition_info:
    workflow_definition_name: "sample-workflow"

- name: List all Nova Act workflow definition summaries
  amazon.ai.nova_act_workflow_definition_info:

- name: List summaries in descending service order
  amazon.ai.nova_act_workflow_definition_info:
    sort_order: "Descending"
  register: workflow_definitions_info

- name: Show the names of all workflow definitions
  ansible.builtin.debug:
    msg: "{{ workflow_definitions_info.workflow_definitions | map(attribute='name') | list }}"
"""

RETURN = r"""
workflow_definitions:
    description:
        - Workflow definitions or summaries returned by AWS.
        - An empty list is returned when no definitions match.
    returned: always
    type: list
    elements: dict
    sample:
        - name: "sample-workflow"
          workflow_definition_name: "sample-workflow"
          arn: "arn:aws:nova-act:us-east-1:123456789012:workflow-definition/sample-workflow"
          workflow_definition_arn: "arn:aws:nova-act:us-east-1:123456789012:workflow-definition/sample-workflow"
          created_at: "2026-10-29T10:00:00+00:00"
          status: "ACTIVE"
    contains:
        name:
            description: The name of the workflow definition.
            returned: for each definition
            type: str
            sample: "sample-workflow"
        arn:
            description: The Amazon Resource Name of the workflow definition.
            returned: for each definition
            type: str
            sample: "arn:aws:nova-act:us-east-1:123456789012:workflow-definition/sample-workflow"
        workflow_definition_name:
            description: Alias of RV(workflow_definitions[].name).
            returned: for each definition
            type: str
            sample: "sample-workflow"
        workflow_definition_arn:
            description: Alias of RV(workflow_definitions[].arn).
            returned: for each definition
            type: str
            sample: "arn:aws:nova-act:us-east-1:123456789012:workflow-definition/sample-workflow"
        created_at:
            description: The time when the workflow definition was created.
            returned: for each definition
            type: str
            sample: "2026-10-29T10:00:00+00:00"
        status:
            description: The status of the workflow definition.
            returned: for each definition
            type: str
            sample: "ACTIVE"
        description:
            description: The description of the workflow definition.
            returned: on named lookup when returned by AWS
            type: str
            sample: "A sample Nova Act workflow"
        export_config:
            description: The S3 export configuration for the workflow definition.
            returned: on named lookup when returned by AWS
            type: dict
            sample:
                s3_bucket_name: "example-bucket"
                s3_key_prefix: "workflow-exports/"
            contains:
                s3_bucket_name:
                    description: The name of the S3 bucket used for exports.
                    returned: when export_config is returned by AWS
                    type: str
                    sample: "example-bucket"
                s3_key_prefix:
                    description: The prefix for exported object keys.
                    returned: when set
                    type: str
                    sample: "workflow-exports/"
msg:
    description: Informative message about the query.
    returned: always
    type: str
    sample: "Retrieved 1 workflow definition(s)."
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.ai.plugins.module_utils.nova_act import _validate_nova_act_botocore
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import get_workflow_definition
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import list_workflow_definitions
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import validate_workflow_definition_name

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main() -> None:
    module = AnsibleAWSModule(
        argument_spec=dict(
            workflow_definition_name=dict(type="str", aliases=["name"]),
            sort_order=dict(type="str", choices=["Ascending", "Descending"]),
        ),
        mutually_exclusive=[["workflow_definition_name", "sort_order"]],
        supports_check_mode=True,
    )
    _validate_nova_act_botocore(module)
    name = module.params["workflow_definition_name"]
    validate_workflow_definition_name(module, name)

    try:
        try:
            client = module.client("nova-act", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        if name is not None:
            definition = get_workflow_definition(client, module, name)
            definitions = [definition] if definition is not None else []
        else:
            definitions = list_workflow_definitions(client, module, module.params["sort_order"])
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(
        changed=False,
        msg=f"Retrieved {len(definitions)} workflow definition(s).",
        workflow_definitions=definitions,
    )


if __name__ == "__main__":
    main()
