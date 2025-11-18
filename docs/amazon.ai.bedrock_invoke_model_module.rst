.. _amazon.ai.bedrock_invoke_model_module:


******************************
amazon.ai.bedrock_invoke_model
******************************

**Run inference using Amazon Bedrock models**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- This module invokes a specified model on Amazon Bedrock with a user-provided request body.
- The request body is passed as raw bytes or JSON (dict), depending on the model requirements.
- The module supports customizing request and response MIME types.



Requirements
------------
The below requirements are needed on the host that executes this module.

- python >= 3.6
- boto3 >= 1.34.0
- botocore >= 1.34.0


Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>accept</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"application/json"</div>
                </td>
                <td>
                        <div>The desired MIME type of the inference response.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>access_key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>AWS access key ID.</div>
                        <div>See the AWS documentation for more information about access tokens <a href='https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys'>https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys</a>.</div>
                        <div>The <code>AWS_ACCESS_KEY_ID</code> or <code>AWS_ACCESS_KEY</code> environment variables may also be used in decreasing order of preference.</div>
                        <div>The <em>aws_access_key</em> and <em>profile</em> options are mutually exclusive.</div>
                        <div>The <em>aws_access_key_id</em> alias was added in release 5.1.0 for consistency with the AWS botocore SDK.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_access_key_id, aws_access_key</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>aws_ca_bundle</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">path</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The location of a CA Bundle to use when validating SSL certificates.</div>
                        <div>The <code>AWS_CA_BUNDLE</code> environment variable may also be used.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>aws_config</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A dictionary to modify the botocore configuration.</div>
                        <div>Parameters can be found in the AWS documentation <a href='https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html#botocore.config.Config'>https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html#botocore.config.Config</a>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>body</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">raw</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The request body to send to the model.</div>
                        <div>Must be a JSON object, string, or plain text depending on the model.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>content_type</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"application/json"</div>
                </td>
                <td>
                        <div>Desired MIME type of the response.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>debug_botocore_endpoint_logs</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>no</b>&nbsp;&larr;</div></li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Use a <code>botocore.endpoint</code> logger to parse the unique (rather than total) <code>&quot;resource:action&quot;</code> API calls made during a task, outputing the set to the resource_actions key in the task results. Use the <code>aws_resource_action</code> callback to output to total list made during a playbook.</div>
                        <div>The <code>ANSIBLE_DEBUG_BOTOCORE_LOGS</code> environment variable may also be used.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>endpoint_url</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>URL to connect to instead of the default AWS endpoints.  While this can be used to connection to other AWS-compatible services the amazon.aws and community.aws collections are only tested against AWS.</div>
                        <div>The  <code>AWS_URL</code> environment variable may also be used.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_endpoint_url</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>guardrail_identifier</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The unique identifier of the guardrail to use.</div>
                        <div>This option requires boto3 &gt;= 1.35.8.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>guardrail_version</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The version number for the guardrail. Can also be &#x27;DRAFT&#x27;.</div>
                        <div>O(guardrail_version) is required when O(guardrail_identifier) is specified.</div>
                        <div>This option requires boto3 &gt;= 1.35.8.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>model_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The ID of the Bedrock model to invoke.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>performance_config_latency</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>standard</b>&nbsp;&larr;</div></li>
                                    <li>optimized</li>
                        </ul>
                </td>
                <td>
                        <div>Model performance settings for the request, optimizing for latency.</div>
                        <div>This option requires boto3 &gt;= 1.35.8.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>profile</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A named AWS profile to use for authentication.</div>
                        <div>See the AWS documentation for more information about named profiles <a href='https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html'>https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html</a>.</div>
                        <div>The <code>AWS_PROFILE</code> environment variable may also be used.</div>
                        <div>The <em>profile</em> option is mutually exclusive with the <em>aws_access_key</em>, <em>aws_secret_key</em> and <em>session_token</em> options.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_profile</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>region</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The AWS region to use.</div>
                        <div>For global services such as IAM, Route53 and CloudFront, <em>region</em> is ignored.</div>
                        <div>The <code>AWS_REGION</code> environment variable may also be used.</div>
                        <div>See the Amazon AWS documentation for more information <a href='http://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region'>http://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region</a>.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_region</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>secret_key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>AWS secret access key.</div>
                        <div>See the AWS documentation for more information about access tokens <a href='https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys'>https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys</a>.</div>
                        <div>The <code>AWS_SECRET_ACCESS_KEY</code> or <code>AWS_SECRET_KEY</code> environment variables may also be used in decreasing order of preference.</div>
                        <div>The <em>secret_key</em> and <em>profile</em> options are mutually exclusive.</div>
                        <div>The <em>aws_secret_access_key</em> alias was added in release 5.1.0 for consistency with the AWS botocore SDK.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_secret_access_key, aws_secret_key</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>session_token</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>AWS STS session token for use with temporary credentials.</div>
                        <div>See the AWS documentation for more information about access tokens <a href='https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys'>https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys</a>.</div>
                        <div>The <code>AWS_SESSION_TOKEN</code> environment variable may also be used.</div>
                        <div>The <em>session_token</em> and <em>profile</em> options are mutually exclusive.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_session_token</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>trace</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>ENABLED</li>
                                    <li><div style="color: blue"><b>DISABLED</b>&nbsp;&larr;</div></li>
                                    <li>ENABLED_FULL</li>
                        </ul>
                </td>
                <td>
                        <div>Specifies whether to enable or disable Bedrock tracing.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>validate_certs</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li><div style="color: blue"><b>yes</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>When set to <code>false</code>, SSL certificates will not be validated for communication with the AWS APIs.</div>
                        <div>Setting <em>validate_certs=false</em> is strongly discouraged, as an alternative, consider setting <em>aws_ca_bundle</em> instead.</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - **Caution:** For modules, environment variables and configuration files are read from the Ansible 'host' context and not the 'controller' context. As such, files may need to be explicitly copied to the 'host'.  For lookup and connection plugins, environment variables and configuration files are read from the Ansible 'controller' context and not the 'host' context.
   - The AWS SDK (boto3) that Ansible uses may also read defaults for credentials and other settings, such as the region, from its configuration files in the Ansible 'host' context (typically ``~/.aws/credentials``). See https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html for more information.



Examples
--------

.. code-block:: yaml

    - name: Invoke Claude v3 Haiku with custom JSON body
      amazon.ai.bedrock_invoke_model:
        model_id: "anthropic.claude-3-haiku-20240307-v1:0"
        body:
          messages:
            - role: "user"
              content:
                - type: "text"
                  text: "What is the key to a good cup of coffee?"
          max_tokens: 250
        content_type: "application/json"
        accept: "application/json"

    - name: Invoke a model with plain text input
      amazon.ai.bedrock_invoke_model:
        model_id: "some-text-model"
        body: "Once upon a time..."
        content_type: "text/plain"
        accept: "text/plain"



Return Values
-------------
Common return values are documented `here <https://docs.ansible.com/ansible/latest/reference_appendices/common_return_values.html#common-return-values>`_, the following are the fields unique to this module:

.. raw:: html

    <table border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Key</th>
            <th>Returned</th>
            <th width="100%">Description</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>model_id</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td>success</td>
                <td>
                            <div>The ID of the Bedrock model that was invoked.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">anthropic.claude-3-haiku-20240307-v1:0</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>raw_response</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>The full, unprocessed JSON response returned by Bedrock. Useful for debugging or accessing provider-specific metadata.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;output&#x27;: {&#x27;message&#x27;: {&#x27;content&#x27;: [{&#x27;text&#x27;: &#x27;It looks like you\&#x27;re interested in testing a prompt! Here are a few examples of different types of prompts you might find useful, depending on what you\&#x27;re aiming to achieve:\n\n### Creative Writing Prompt\n&quot;Write a short story about a world&#x27;}], &#x27;role&#x27;: &#x27;assistant&#x27;}}, &#x27;stopReason&#x27;: &#x27;max_tokens&#x27;, &#x27;usage&#x27;: {&#x27;cacheReadInputTokenCount&#x27;: 0, &#x27;cacheWriteInputTokenCount&#x27;: 0, &#x27;inputTokens&#x27;: 3, &#x27;outputTokens&#x27;: 50, &#x27;totalTokens&#x27;: 53}}</div>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Alina Buzachis (@alinabuzachis)
