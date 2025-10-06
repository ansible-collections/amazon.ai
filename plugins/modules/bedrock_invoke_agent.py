#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: bedrock_invoke_agent
short_description: Invokes an Amazon Bedrock agent with a prompt
version_added: "1.0.0"
author:
    - Alina Buzachis (@alinabuzachis)
description:
    - This module interacts with a deployed Amazon Bedrock agent by sending it a user prompt.
    - It creates a new session if one is not provided and processes the streaming response to return a complete answer.
options:
    agent_id:
        description:
            - The unique identifier of the Bedrock agent to invoke.
        type: str
        required: true
    agent_alias_id:
        description:
            - The unique identifier of the agent's alias.
        type: str
        required: true
    input_text:
        description:
            - The text prompt or question to send to the agent.
        type: str
        required: true
    session_id:
        description:
            - The session ID for the conversation. If not provided, a new unique session ID is generated.
        type: str
    end_session:
        description:
            - Specifies whether to end the session with the agent after this invocation.
        type: bool
        default: false
    enable_trace:
        description:
            - Specifies whether to turn on the trace to follow the agent's reasoning process.
        type: bool
        default: false
    session_state:
        description:
            - A dictionary containing session state information, such as conversation history or attributes.
            - This maps directly to the sessionState parameter in the InvokeAgent API.
        type: dict
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Invoke a Bedrock agent with a new session and enable tracing
  amazon.ai.bedrock_invoke_agent:
    agent_id: "ABCDEFGHIJKLMNOP"
    agent_alias_id: "1234567890"
    input_text: "What is the current time?"
    enable_trace: true

- name: Invoke a Bedrock agent and end the session
  amazon.ai.bedrock_invoke_agent:
    agent_id: "ABCDEFGHIJKLMNOP"
    agent_alias_id: "1234567890"
    session_id: "{{ agent_response.session_id }}"
    input_text: "Thank you, goodbye."
    end_session: true
"""

RETURN = r"""
session_id:
    description: The unique session ID for the conversation.
    type: str
    returned: always
    sample: "5c80d463-5491-450b-80a2-212d26f634b0"
response_text:
    description: The complete response text from the agent.
    type: str
    returned: always
    sample: "The current time is Monday, September 22, 2025 at 5:01:06 PM CEST."
raw_api_response:
    description: The complete, raw event stream from the InvokeAgent API call. This is returned as a list of dictionaries.
    type: list
    returned: always
    contains:
        chunk:
            description: An event containing a part of the agent's response.
            type: dict
        trace:
            description: An event containing a trace of the agent's reasoning process.
            type: dict
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

import uuid
from typing import Any
from typing import Dict
from typing import Optional

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main():
    argument_spec = dict(
        agent_id=dict(type="str", required=True),
        agent_alias_id=dict(type="str", required=True),
        input_text=dict(type="str", required=True),
        session_id=dict(type="str"),
        end_session=dict(type="bool", default=False),
        enable_trace=dict(type="bool", default=False),
        session_state=dict(type="dict"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    session_id: Optional[str] = module.params["session_id"]
    if session_id is None:
        session_id = str(uuid.uuid4())

    try:
        client = module.client("bedrock-agent-runtime", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS Bedrock Agent Runtime.")

    result: Dict[str, Any] = dict(changed=True, session_id=session_id, raw_api_response=[], response_text="")
    completion: str = ""

    try:
        if module.check_mode:
            module.exit_json(msg="Check mode: Would have invoked the agent.", **camel_dict_to_snake_dict(result))
        else:
            params: Dict[str, Any] = {
                "agentId": module.params["agent_id"],
                "agentAliasId": module.params["agent_alias_id"],
                "sessionId": session_id,
                "inputText": module.params["input_text"],
                "endSession": module.params["end_session"],
                "enableTrace": module.params["enable_trace"],
            }
            if module.params.get("session_state"):
                params["sessionState"] = module.params["session_state"]

            response: Dict[str, Any] = client.invoke_agent(aws_retry=True, **params)
            for event in response.get("completion", []):
                result["raw_api_response"].append(event)

                # Extract the completion text from the chunk event
                chunk: Optional[Dict[str, Any]] = event.get("chunk")
                if chunk and chunk.get("bytes"):
                    completion += chunk["bytes"].decode()

            result["response_text"] = completion

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(**camel_dict_to_snake_dict(result))


if __name__ == "__main__":
    main()
