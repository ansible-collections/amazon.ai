# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import re
import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters

_POLL_INTERVAL = 5
_WORKFLOW_DEFINITION_NAME_PATTERN = re.compile(r"[a-zA-Z0-9_-]{1,40}")
_WORKFLOW_RUN_ID_PATTERN = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

_WORKFLOW_RUN_TERMINAL_STATUSES = frozenset({"SUCCEEDED", "FAILED", "TIMED_OUT"})
_WORKFLOW_RUN_FAILURE_STATUSES = frozenset({"FAILED", "TIMED_OUT"})


def validate_workflow_definition_name(module: AnsibleAWSModule, workflow_definition_name: Optional[str]) -> None:
    if workflow_definition_name is not None and not _WORKFLOW_DEFINITION_NAME_PATTERN.fullmatch(
        workflow_definition_name
    ):
        module.fail_json(
            msg="workflow_definition_name must be 1-40 characters: letters, numbers, underscores, or hyphens."
        )


def validate_workflow_run_id(module: AnsibleAWSModule, workflow_run_id: Optional[str]) -> None:
    if workflow_run_id is not None and not _WORKFLOW_RUN_ID_PATTERN.fullmatch(workflow_run_id):
        module.fail_json(msg="workflow_run_id must be a UUID.")


def _validate_nova_act_botocore(module: AnsibleAWSModule) -> None:
    if not module.botocore_at_least("1.42.1"):
        module.fail_json(msg="Nova Act requires botocore >= 1.42.1 to provide the nova-act service model.")


_KEY_ALIASES = (("name", "workflow_definition_name"), ("arn", "workflow_definition_arn"))


def _to_snake_dict(response: Dict[str, Any]) -> Dict[str, Any]:
    response.pop("ResponseMetadata", None)
    result = camel_dict_to_snake_dict(response, ignore_list=["tags", "Tags"])
    # GetWorkflowDefinition returns name/arn, ListWorkflowDefinitions returns
    # workflowDefinitionName/workflowDefinitionArn; expose both spellings in every result.
    for short_key, long_key in _KEY_ALIASES:
        if short_key in result:
            result.setdefault(long_key, result[short_key])
        elif long_key in result:
            result[short_key] = result[long_key]
    return result


@AWSRetry.jittered_backoff(retries=10)
def _get_workflow_definition(client, workflow_definition_name: str) -> Optional[Dict[str, Any]]:
    try:
        return client.get_workflow_definition(workflowDefinitionName=workflow_definition_name)
    except is_boto3_error_code("ResourceNotFoundException"):
        return None


def get_workflow_definition(
    client,
    module: AnsibleAWSModule,
    workflow_definition_name: str,
) -> Optional[Dict[str, Any]]:
    try:
        response = _get_workflow_definition(client, workflow_definition_name)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Failed to get workflow definition '{workflow_definition_name}'.")
    if response is None:
        return None
    return _to_snake_dict(response)


@AWSRetry.jittered_backoff(retries=10)
def _list_workflow_definitions(client, **params) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("list_workflow_definitions")
    return paginator.paginate(**params).build_full_result()["workflowDefinitionSummaries"]


def list_workflow_definitions(
    client,
    module: AnsibleAWSModule,
    sort_order: Optional[str] = None,
) -> List[Dict[str, Any]]:
    params = snake_dict_to_camel_dict(scrub_none_parameters({"sort_order": sort_order}))
    try:
        summaries = _list_workflow_definitions(client, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to list workflow definitions.")
    return [_to_snake_dict(summary) for summary in summaries]


def wait_for_workflow_definition_deleted(
    client,
    module: AnsibleAWSModule,
    workflow_definition_name: str,
) -> None:
    deadline = time.monotonic() + module.params["wait_timeout"]
    while True:
        if get_workflow_definition(client, module, workflow_definition_name) is None:
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            module.fail_json(
                msg=f"Timed out waiting for workflow definition '{workflow_definition_name}' to be deleted."
            )
        time.sleep(min(_POLL_INTERVAL, remaining))


def create_workflow_definition(
    client,
    module: AnsibleAWSModule,
) -> Tuple[bool, Dict[str, Any], str]:
    name = module.params["workflow_definition_name"]
    if module.check_mode:
        return True, {}, f"Check mode: would have created workflow definition '{name}'."

    params = snake_dict_to_camel_dict(
        scrub_none_parameters(
            {
                "name": name,
                "description": module.params.get("description"),
                "export_config": module.params.get("export_config"),
                "client_token": module.params.get("client_token"),
            }
        )
    )
    try:
        response = client.create_workflow_definition(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Failed to create workflow definition '{name}'.")
    definition = get_workflow_definition(client, module, name)
    if definition is None:
        module.fail_json(msg=f"Workflow definition '{name}' was created but could not be retrieved.")
    return True, definition, f"Workflow definition '{name}' created successfully ({response.get('status')})."


def delete_workflow_definition(
    client,
    module: AnsibleAWSModule,
    existing: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any], str]:
    name = module.params["workflow_definition_name"]
    if module.check_mode:
        return True, existing, f"Check mode: would have deleted workflow definition '{name}'."

    try:
        response = client.delete_workflow_definition(workflowDefinitionName=name)
    except is_boto3_error_code("ResourceNotFoundException"):
        return False, {}, f"Workflow definition '{name}' does not exist."
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Failed to delete workflow definition '{name}'.")
    definition = {**existing, "status": response.get("status", existing.get("status"))}
    if module.params["wait"]:
        wait_for_workflow_definition_deleted(client, module, name)
    return True, definition, f"Workflow definition '{name}' deleted successfully."


@AWSRetry.jittered_backoff(retries=10)
def _get_workflow_run(client, workflow_definition_name: str, workflow_run_id: str) -> Optional[Dict[str, Any]]:
    try:
        return client.get_workflow_run(workflowDefinitionName=workflow_definition_name, workflowRunId=workflow_run_id)
    except is_boto3_error_code("ResourceNotFoundException"):
        return None


def get_workflow_run(
    client,
    module: AnsibleAWSModule,
    workflow_definition_name: str,
    workflow_run_id: str,
) -> Optional[Dict[str, Any]]:
    try:
        response = _get_workflow_run(client, workflow_definition_name, workflow_run_id)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Failed to get workflow run '{workflow_run_id}'.")
    if response is None:
        return None
    return _to_snake_dict(response)


@AWSRetry.jittered_backoff(retries=10)
def _list_workflow_runs(client, **params) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("list_workflow_runs")
    return paginator.paginate(**params).build_full_result()["workflowRunSummaries"]


def list_workflow_runs(
    client,
    module: AnsibleAWSModule,
    workflow_definition_name: str,
    sort_order: Optional[str] = None,
) -> List[Dict[str, Any]]:
    params = snake_dict_to_camel_dict(
        scrub_none_parameters({"workflow_definition_name": workflow_definition_name, "sort_order": sort_order})
    )
    try:
        summaries = _list_workflow_runs(client, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(
            e, msg=f"Failed to list workflow runs for workflow definition '{workflow_definition_name}'."
        )
    return [_to_snake_dict(summary) for summary in summaries]


def wait_for_workflow_run_status(
    client,
    module: AnsibleAWSModule,
    workflow_definition_name: str,
    workflow_run_id: str,
    changed: bool,
) -> Dict[str, Any]:
    deadline = time.monotonic() + module.params["wait_timeout"]
    while True:
        run = get_workflow_run(client, module, workflow_definition_name, workflow_run_id)
        if run is None:
            module.fail_json(
                msg=f"Workflow run '{workflow_run_id}' disappeared while waiting for a terminal status.",
                changed=changed,
                workflow_run={},
            )
        elif run.get("status") in _WORKFLOW_RUN_FAILURE_STATUSES:
            module.fail_json(
                msg=f"Workflow run '{workflow_run_id}' ended with status '{run.get('status')}'.",
                changed=changed,
                workflow_run=run,
            )
        elif run.get("status") in _WORKFLOW_RUN_TERMINAL_STATUSES:
            return run
        else:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                module.fail_json(
                    msg=f"Timed out waiting for workflow run '{workflow_run_id}' to reach a terminal status.",
                    changed=changed,
                    workflow_run=run,
                )
            time.sleep(min(_POLL_INTERVAL, remaining))


def wait_for_workflow_run_deleted(
    client,
    module: AnsibleAWSModule,
    workflow_definition_name: str,
    workflow_run_id: str,
) -> None:
    deadline = time.monotonic() + module.params["wait_timeout"]
    while True:
        if get_workflow_run(client, module, workflow_definition_name, workflow_run_id) is None:
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            module.fail_json(msg=f"Timed out waiting for workflow run '{workflow_run_id}' to be deleted.")
        time.sleep(min(_POLL_INTERVAL, remaining))


def create_workflow_run(
    client,
    module: AnsibleAWSModule,
) -> Tuple[bool, Dict[str, Any], str]:
    name = module.params["workflow_definition_name"]
    if module.check_mode:
        return True, {}, f"Check mode: would have created a workflow run for workflow definition '{name}'."

    params = snake_dict_to_camel_dict(
        scrub_none_parameters(
            {
                "workflow_definition_name": name,
                "model_id": module.params.get("model_id"),
                "client_info": module.params.get("client_info"),
                "client_token": module.params.get("client_token"),
                "log_group_name": module.params.get("log_group_name"),
            }
        )
    )
    try:
        response = client.create_workflow_run(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Failed to create a workflow run for workflow definition '{name}'.")
    workflow_run_id = response["workflowRunId"]
    if module.params["wait"]:
        run = wait_for_workflow_run_status(client, module, name, workflow_run_id, changed=True)
    else:
        run = get_workflow_run(client, module, name, workflow_run_id)
        if run is None:
            module.fail_json(
                msg=f"Workflow run '{workflow_run_id}' was created but could not be retrieved.",
                changed=True,
                workflow_run={},
            )
    return True, run, f"Workflow run '{workflow_run_id}' created successfully ({run.get('status')})."


def delete_workflow_run(
    client,
    module: AnsibleAWSModule,
    existing: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any], str]:
    name = module.params["workflow_definition_name"]
    workflow_run_id = module.params["workflow_run_id"]
    if module.check_mode:
        return True, existing, f"Check mode: would have deleted workflow run '{workflow_run_id}'."

    try:
        response = client.delete_workflow_run(workflowDefinitionName=name, workflowRunId=workflow_run_id)
    except is_boto3_error_code("ResourceNotFoundException"):
        return False, {}, f"Workflow run '{workflow_run_id}' does not exist."
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Failed to delete workflow run '{workflow_run_id}'.")
    run = {**existing, "status": response.get("status", existing.get("status"))}
    if module.params["wait"]:
        wait_for_workflow_run_deleted(client, module, name, workflow_run_id)
    return True, run, f"Workflow run '{workflow_run_id}' deleted successfully."
