#!/usr/bin/python

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: nova_act_model_info
short_description: Gather information about Amazon Nova Act models
version_added: "2.1.0"
author:
    - Jan Likar (@janlikar)
description:
    - List the AI models available for Amazon Nova Act workflow execution, including their lifecycle
      status and compatibility information.
    - Nova Act requires botocore >= 1.42.1 to provide the service model.
    - The Nova Act service is currently available only in the US East (N. Virginia) Region (V(us-east-1)).
attributes:
    check_mode:
        description: Performs the same read-only request as in normal mode.
        support: full
    diff_mode:
        description: Does not support diff mode.
        support: none
options:
    client_compatibility_version:
        description:
            - The client compatibility version to filter models by compatibility.
            - AWS documents no default or valid range for this value.
        type: int
        required: true
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
notes:
    - Requires C(nova-act:ListModels).
"""

EXAMPLES = r"""
- name: List Nova Act models for a given client compatibility version
  amazon.ai.nova_act_model_info:
    client_compatibility_version: 1
  register: models_info

- name: Show the IDs of all returned models
  ansible.builtin.debug:
    msg: "{{ models_info.models | map(attribute='model_id') | list }}"
"""

RETURN = r"""
models:
    description: A list of available AI models with their status and compatibility information.
    returned: always
    type: list
    elements: dict
    sample:
        - model_id: "nova-pro-v1"
          model_lifecycle:
              status: "ACTIVE"
          minimum_compatibility_version: 1
    contains:
        model_id:
            description: The unique identifier of the model.
            returned: for each model
            type: str
            sample: "nova-pro-v1"
        model_lifecycle:
            description: The lifecycle information for the model.
            returned: for each model
            type: dict
            sample:
                status: "ACTIVE"
            contains:
                status:
                    description: The current lifecycle status of the model.
                    returned: for each model
                    type: str
                    sample: "ACTIVE"
        minimum_compatibility_version:
            description: The minimum client compatibility version required to use this model.
            returned: for each model
            type: int
            sample: 1
model_aliases:
    description: A list of model aliases that provide stable references to model versions.
    returned: always
    type: list
    elements: dict
    sample:
        - alias_name: "nova-pro-latest"
          latest_model_id: "nova-pro-v2"
          resolved_model_id: "nova-pro-v2"
    contains:
        alias_name:
            description: The name of the model alias.
            returned: for each alias
            type: str
            sample: "nova-pro-latest"
        latest_model_id:
            description: The model ID that this alias currently points to.
            returned: for each alias
            type: str
            sample: "nova-pro-v2"
        resolved_model_id:
            description: The resolved model ID after alias resolution.
            returned: for each alias
            type: str
            sample: "nova-pro-v2"
compatibility_information:
    description: Information about client compatibility and supported models.
    returned: always
    type: dict
    sample:
        client_compatibility_version: 1
        supported_model_ids: ["nova-pro-v1", "nova-lite-v1"]
    contains:
        client_compatibility_version:
            description: The client compatibility version that was requested.
            returned: always
            type: int
            sample: 1
        supported_model_ids:
            description: A list of model IDs that are supported for the client compatibility version.
            returned: always
            type: list
            sample: ["nova-pro-v1", "nova-lite-v1"]
        message:
            description: Additional information about compatibility requirements or recommendations.
            returned: when returned by AWS
            type: str
            sample: "A newer client compatibility version is available."
msg:
    description: Informative message about the query.
    returned: always
    type: str
    sample: "Retrieved 2 model(s)."
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.ai.plugins.module_utils.nova_act import _validate_nova_act_botocore
from ansible_collections.amazon.ai.plugins.module_utils.nova_act import list_models

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main() -> None:
    module = AnsibleAWSModule(
        argument_spec=dict(
            client_compatibility_version=dict(type="int", required=True),
        ),
        supports_check_mode=True,
    )
    _validate_nova_act_botocore(module)

    try:
        client = module.client("nova-act", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    result = list_models(client, module, module.params["client_compatibility_version"])

    module.exit_json(
        changed=False,
        msg=f"Retrieved {len(result['models'])} model(s).",
        **result,
    )


if __name__ == "__main__":
    main()
