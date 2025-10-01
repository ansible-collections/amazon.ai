#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: bedrock_foundation_models_info
short_description: Lists or gets details for Amazon Bedrock foundation models
version_added: "1.0.0"
author:
    - Alina Buzachis (@alinabuzachis)
description:
    - This module lists or gets details for Amazon Bedrock foundation models
    - It supports filtering the results by provider, customization type, output modality, and inference type.
options:
    model_id:
        description:
            - The model ID of the specific foundation model to retrieve.
            - When this option is provided, all other filtering options are ignored.
        type: str
    by_provider:
        description:
            - Return models belonging to the model provider that you specify.
        type: str
    by_customization_type:
        description:
            - Return models that support the customization type that you specify.
        type: str
        choices: ['FINE_TUNING', 'CONTINUED_PRE_TRAINING', 'DISTILLATION']
    by_output_modality:
        description:
            - Return models that support the output modality that you specify.
        type: str
        choices: ['TEXT', 'IMAGE', 'EMBEDDING']
    by_inference_type:
        description:
            - Return models that support the inference type that you specify.
        type: str
        choices: ['ON_DEMAND', 'PROVISIONED']
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""


EXAMPLES = r"""
- name: List all available foundation models
  amazon.ai.bedrock_foundation_models_info:
  register: all_models

- name: Get info for a specific model by ID
  amazon.ai.bedrock_foundation_models_info:
    model_id: 'anthropic.claude-v2'
  register: claude_info

- name: List only models from the 'anthropic' provider
  amazon.ai.bedrock_foundation_models_info:
    by_provider: 'Anthropic'
  register: anthropic_models

- name: List models that support 'IMAGE' output
  amazon.ai.bedrock_foundation_models_info:
    by_output_modality: 'IMAGE'
  register: image_models

- name: List models that support on-demand inference
  amazon.ai.bedrock_foundation_models_info:
    by_inference_type: 'ON_DEMAND'
  register: on_demand_models
"""


RETURN = r"""
foundation_model:
    description: A dictionary or a list of dictionaries, where each dictionary contains summary information for a foundation model.
    type: complex
    returned: success if no O(model_id) is provided
    contains:
        model_arn:
            description: The Amazon Resource Name (ARN) of the foundation model.
            type: str
        model_id:
            description: The model ID of the foundation model.
            type: str
        model_name:
            description: The name of the model.
            type: str
        provider_name:
            description: The model's provider name.
            type: str
        input_modalities:
            description: The input modalities that the model supports.
            type: list
        output_modalities:
            description: The output modalities that the model supports.
            type: list
        response_streaming_supported:
            description: Indicates whether the model supports streaming.
            type: bool
        customizations_supported:
            description: Whether the model supports fine-tuning or continual pre-training.
            type: list
        inference_types_supported:
            description: The inference types that the model supports.
            type: list
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _get_model_details(client, model_id: str) -> Dict[str, Any]:
    """
    Handles the get_foundation_model API call.
    """
    response = client.get_foundation_model(modelIdentifier=model_id)
    return camel_dict_to_snake_dict(response.get("modelDetails", {}))


def _list_models_with_filters(module: AnsibleAWSModule, client) -> List[Dict[str, Any]]:
    """
    Handles the list_foundation_models API call with optional filters.
    """
    params: Dict[str, Any] = {}

    if module.params.get("by_provider"):
        params["byProvider"] = module.params["by_provider"]

    if module.params.get("by_customization_type"):
        params["byCustomizationType"] = module.params["by_customization_type"]

    if module.params.get("by_output_modality"):
        params["byOutputModality"] = module.params["by_output_modality"]

    if module.params.get("by_inference_type"):
        params["byInferenceType"] = module.params["by_inference_type"]

    response = client.list_foundation_models(**params)
    return [camel_dict_to_snake_dict(model) for model in response.get("modelSummaries", [])]


def main():
    module_args = dict(
        model_id=dict(type="str", required=False),
        by_provider=dict(type="str", required=False),
        by_customization_type=dict(
            type="str", choices=["FINE_TUNING", "CONTINUED_PRE_TRAINING", "DISTILLATION"], required=False
        ),
        by_output_modality=dict(type="str", choices=["TEXT", "IMAGE", "EMBEDDING"], required=False),
        by_inference_type=dict(type="str", choices=["ON_DEMAND", "PROVISIONED"], required=False),
    )

    module = AnsibleAWSModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    result = {}

    try:
        client = module.client("bedrock", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    # Route the request based on whether a model_id was provided
    try:
        if module.params.get("model_id"):
            result = _get_model_details(client, module.params["model_id"])
        else:
            result = _list_models_with_filters(module, client)

        module.exit_json(changed=False, foundation_model=result)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
