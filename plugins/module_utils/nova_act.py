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
_CREATE_READ_POLL_INTERVAL = 2
_CREATE_READ_TIMEOUT = 30
_WORKFLOW_DEFINITION_NAME_PATTERN = re.compile(r"[a-zA-Z0-9_-]{1,40}")


def validate_workflow_definition_name(module: AnsibleAWSModule, workflow_definition_name: Optional[str]) -> None:
    if workflow_definition_name is not None and not _WORKFLOW_DEFINITION_NAME_PATTERN.fullmatch(
        workflow_definition_name
    ):
        module.fail_json(
            msg="workflow_definition_name must be 1-40 characters: letters, numbers, underscores, or hyphens."
        )


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
    definitions = []
    for summary in summaries:
        # Summaries lack description and exportConfig; fetch each definition so
        # listing returns the same shape as a named lookup.
        definition = get_workflow_definition(client, module, summary["workflowDefinitionName"])
        if definition is not None:
            definitions.append(definition)
    return definitions


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


def _get_created_workflow_definition(
    client,
    module: AnsibleAWSModule,
    workflow_definition_name: str,
) -> Optional[Dict[str, Any]]:
    # GetWorkflowDefinition can briefly lag behind a successful create.
    deadline = time.monotonic() + _CREATE_READ_TIMEOUT
    while True:
        definition = get_workflow_definition(client, module, workflow_definition_name)
        remaining = deadline - time.monotonic()
        if definition is not None or remaining <= 0:
            return definition
        time.sleep(min(_CREATE_READ_POLL_INTERVAL, remaining))


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
                "description": module.params.get("description") or None,
                "export_config": module.params.get("export_config"),
                "client_token": module.params.get("client_token"),
            }
        )
    )
    try:
        response = client.create_workflow_definition(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Failed to create workflow definition '{name}'.")
    definition = _get_created_workflow_definition(client, module, name)
    if definition is None:
        module.warn(f"Workflow definition '{name}' was created but is not yet readable; returning partial data.")
        definition = _to_snake_dict(response)
        definition.update(
            scrub_none_parameters(
                {
                    "name": name,
                    "workflow_definition_name": name,
                    "description": module.params.get("description") or None,
                    "export_config": module.params.get("export_config"),
                }
            )
        )
    return True, definition, f"Workflow definition '{name}' created successfully ({response.get('status')})."


def delete_workflow_definition(
    client,
    module: AnsibleAWSModule,
) -> Tuple[bool, Dict[str, Any], str]:
    name = module.params["workflow_definition_name"]
    if module.check_mode:
        return True, {}, f"Check mode: would have deleted workflow definition '{name}'."

    try:
        client.delete_workflow_definition(workflowDefinitionName=name)
    except is_boto3_error_code("ResourceNotFoundException"):
        return False, {}, f"Workflow definition '{name}' does not exist."
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Failed to delete workflow definition '{name}'.")
    if module.params["wait"]:
        wait_for_workflow_definition_deleted(client, module, name)
    return True, {}, f"Workflow definition '{name}' deleted successfully."
