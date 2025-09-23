#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: bedrock_model_inference
short_description: Runs inference using Amazon Bedrock models
version_added: "1.0.0"
description:
    - This module invokes a specified model on Amazon Bedrock with a given prompt to run inference.
author:
    - Alina Buzachis (@alinabuzachis)
options:
    model_id:
        description:
            - The ID of the Bedrock model to invoke.
        type: str
        required: true
    prompt:
        description:
            - The text prompt to send to the model.
        type: str
        required: true
    trace:
        description:
            - Specifies whether to enable or disable Bedrock tracing.
        type: str
        choices: ['ENABLED', 'DISABLED', 'ENABLED_FULL']
        default: 'DISABLED'
    guardrail_identifier:
        description:
            - The unique identifier of the guardrail to use.
        type: str
    guardrail_version:
        description:
            - The version number for the guardrail. Can also be 'DRAFT'.
            - O(guardrail_version) is required when O(guardrail_identifier) is specified.
        type: str
    performance_config_latency:
        description:
            - Model performance settings for the request, optimizing for latency.
        type: str
        choices: ['standard', 'optimized']
        default: 'standard'
    max_tokens:
        description:
            - The maximum number of tokens to generate in the response.
        type: int
        default: 250
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""


EXAMPLES = r"""
- name: Invoke Claude v3 Haiku with a guardrail
  amazon.ai.bedrock_model_inference:
    model_id: "anthropic.claude-3-haiku-20240307-v1:0"
    prompt: "What is the key to a good cup of coffee?"
    guardrai_identifier: "example-guardrail-id"
    guardrail_version: "1"
  register: bedrock_response

- name: Invoke a model with tracing enabled
  amazon.ai.bedrock_model_inference:
    model_id: "anthropic.claude-3-haiku-20240307-v1:0"
    prompt: "Write a haiku about a mountain stream."
    trace: "ENABLED_FULL"
  register: bedrock_response_with_trace
"""


RETURN = r"""
model_id:
    description: The ID of the Bedrock model that was invoked.
    type: str
    returned: success
    sample: "anthropic.claude-3-haiku-20240307-v1:0"
prompt:
    description: The original prompt that was sent to the model.
    type: str
    returned: success
    sample: "What is the key to a good cup of coffee?"
raw_response:
    description: >
        The full, unprocessed JSON response returned by Bedrock. This includes
        additional fields such as usage metrics, stop reason, and any other
        provider-specific metadata. Useful for debugging or accessing fields
        not exposed in the top-level return values.
    type: dict
    returned: always
    sample:
      {
        "output": {
            "message": {
                "content": [
                    {
                        "text": "The capital of the United States is Washington, D.C. (District of Columbia)."
                    }
                ],
                "role": "assistant"
            }
        },
        "stopReason": "end_turn",
        "usage": {
            "cacheReadInputTokenCount": 0,
            "cacheWriteInputTokenCount": 0,
            "inputTokens": 9,
            "outputTokens": 129,
            "totalTokens": 138
        }
      }
"""


import json

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def build_request_body(model_id: str, prompt: str, max_tokens: int) -> Dict[str, Any]:
    """
    Construct the request body for Claude or Nova micro models based on model_id.
    """
    model_id_lower: str = model_id.lower()
    body: Dict[str, Any]

    # Claude v3+ (Anthropic) expects messages array, string shorthand allowed
    if "claude" in model_id_lower:
        body = {
            "messages": [{"role": "user", "content": prompt}],  # string shorthand
            "max_tokens": max_tokens,
        }

    # Nova micro / other generic models expect structured array of content blocks
    else:
        body = {
            "messages": [{"role": "user", "content": [{"text": prompt}]}],  # always array of text blocks
            # Optionally include inference params if needed
            "inferenceConfig": {"maxTokens": max_tokens},
        }
    return body


def main():
    module_args = dict(
        model_id=dict(type="str", required=True),
        prompt=dict(type="str", required=True),
        trace=dict(type="str", choices=["ENABLED", "DISABLED", "ENABLED_FULL"], default="DISABLED"),
        guardrail_identifier=dict(type="str", required=False),
        guardrail_version=dict(type="str", required=False),
        performance_config_latency=dict(type="str", choices=["standard", "optimized"], default="standard"),
        max_tokens=dict(type="int", default=250, no_log=True),
    )

    module = AnsibleAWSModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if module.check_mode:
        module.exit_json(changed=False)

    model_id: str = module.params["model_id"]
    prompt: str = module.params["prompt"]
    max_tokens: int = module.params["max_tokens"]

    # Optional API params
    optional_params: Dict[str, Any] = {}
    if module.params["trace"] != "DISABLED":
        optional_params["trace"] = module.params["trace"]

    if module.params.get("guardrail_identifier"):
        optional_params["guardrailIdentifier"] = module.params["guardrail_identifier"]
        if not module.params.get("guardrail_version"):
            module.fail_json(msg="guardrail_version is required when guardrail_identifier is specified.")
        optional_params["guardrailVersion"] = module.params["guardrail_version"]

    if module.params["performance_config_latency"] != "standard":
        optional_params["performanceConfigLatency"] = module.params["performance_config_latency"]

    try:
        client = module.client("bedrock-runtime", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    body: Dict[str, Any] = build_request_body(model_id, prompt, max_tokens)

    try:
        response: Dict[str, Any] = client.invoke_model(
            body=json.dumps(body),
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            **optional_params,
        )

        response_body: Dict[str, Any] = json.loads(response["body"].read())

        module.exit_json(changed=True, model_id=model_id, prompt=prompt, raw_response=response_body)

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
