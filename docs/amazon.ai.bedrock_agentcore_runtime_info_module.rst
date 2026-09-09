.. _amazon.ai.bedrock_agentcore_runtime_info_module:


****************************************
amazon.ai.bedrock_agentcore_runtime_info
****************************************

**Gather information about Bedrock AgentCore runtimes**


Version added: 2.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Gets details for a single Bedrock AgentCore runtime or lists all runtimes.



Requirements
------------
The below requirements are needed on the host that executes this module.

- python >= 3.9
- boto3 >= 1.35.0
- botocore >= 1.35.0


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
                    <b>agent_runtime_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The name of the AgentCore runtime to retrieve. If not provided, the module will list all runtimes.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: name</div>
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
                        <div>Parameters can be found in the AWS documentation <a href='https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html#botocore.config.Config'>Botocore Config</a>.</div>
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
                        <div>See the AWS documentation for more information about named profiles <a href='https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html'>CLI configure profiles</a>.</div>
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
                        <div>See the Amazon AWS documentation for more information <a href='http://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region'>AWS EC2 region</a>.</div>
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
                        <div>See the AWS documentation for more information about access tokens <a href='https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys'>AWS Access Keys and Secret Access Keys</a>.</div>
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
                        <div>See the AWS documentation for more information about access tokens <a href='https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys'>AWS Access Keys and Secret Access Keys</a>.</div>
                        <div>The <code>AWS_SESSION_TOKEN</code> environment variable may also be used.</div>
                        <div>The <em>session_token</em> and <em>profile</em> options are mutually exclusive.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: aws_session_token</div>
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

    - name: Get info about a specific agent runtime
      amazon.ai.bedrock_agentcore_runtime_info:
        agent_runtime_name: "my-runtime"

    - name: List all Bedrock AgentCore runtimes
      amazon.ai.bedrock_agentcore_runtime_info:



Return Values
-------------
Common return values are documented in the `common return values section <https://docs.ansible.com/projects/ansible/latest/reference_appendices/common_return_values.html#common-return-values>`_ of the Ansible documentation, the following are the fields unique to this module:

.. raw:: html

    <table border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="4">Key</th>
            <th>Returned</th>
            <th width="100%">Description</th>
        </tr>
            <tr>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>agent_runtimes</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">complex</span>
                    </div>
                </td>
                <td>always, on success</td>
                <td>
                            <div>A list of dictionaries, where each dictionary contains detailed configuration of the managed Bedrock AgentCore runtime.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>agent_runtime_arn</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The Amazon Resource Name (ARN) of the runtime.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">arn:aws:bedrock:us-east-1:123456789901:agent-runtime/RNKFFDOKFN</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>agent_runtime_artifact</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The runtime artifact configuration.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>code_configuration</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Code-based runtime configuration.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>entry_point</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The entry point for the runtime code.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>runtime</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The language runtime.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>s3_bucket</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The S3 bucket containing the runtime code.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>s3_prefix</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The S3 prefix containing the runtime code.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>s3_version_id</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The S3 object version identifier.</div>
                    <br/>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>container_configuration</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Container-based runtime configuration.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>container_uri</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The URI of the container image.</div>
                    <br/>
                </td>
            </tr>


            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>agent_runtime_id</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The unique identifier of the runtime.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">RNKFFDOKFN</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>agent_runtime_name</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The name of the runtime.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">test-agentcore-runtime</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>agent_runtime_version</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The version of the runtime.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">1</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>authorizer_configuration</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The authorizer configuration for the runtime.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>custom_jwt_authorizer</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Custom JWT authorizer configuration.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>allowed_audience</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Allowed audience values.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>allowed_clients</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Allowed client IDs.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>allowed_scopes</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Allowed OAuth scopes.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>discovery_url</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The JWT discovery URL.</div>
                    <br/>
                </td>
            </tr>


            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>capacity_provider_configuration</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The capacity provider configuration for the runtime.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>capacity_provider_arn</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ARN of the capacity provider.</div>
                    <br/>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>created_at</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The timestamp when the runtime was created.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">2025-10-01T15:36:41.199376+00:00</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>description</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The description of the runtime.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>environment_variables</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Environment variables for the runtime.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>failure_reason</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The reason for a failed runtime (if applicable).</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>filesystem_configurations</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The filesystem configurations for the runtime.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>capacity_provider_volume</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The capacity provider volume configuration for the filesystem.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>mount_path</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The mount path for the capacity provider volume.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>volume_name</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The name of the capacity provider volume.</div>
                    <br/>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>efs_access_point</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The EFS Access Point configuration for the filesystem.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>access_point_arn</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ARN of the EFS Access Point.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>mount_path</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The mount path for the EFS Access Point.</div>
                    <br/>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>s3_files_access_point</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The S3 Files Access Point configuration for the filesystem.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>access_point_arn</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ARN of the S3 Files Access Point.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>mount_path</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The mount path for the S3 Files Access Point.</div>
                    <br/>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>session_storage</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The session storage configuration for the filesystem.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>access_point_arn</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ARN of the session storage access point.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>mount_path</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The mount path for the session storage.</div>
                    <br/>
                </td>
            </tr>


            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>last_updated_at</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The timestamp when the runtime was last updated.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">2025-10-01T15:36:42.201271+00:00</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>lifecycle_configuration</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The lifecycle configuration for the runtime.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>idle_runtime_session_timeout</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">integer</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The idle session timeout in seconds.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>max_lifetime</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">integer</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The maximum lifetime in seconds.</div>
                    <br/>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>network_configuration</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The network configuration for the runtime.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>network_mode</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The network mode (PUBLIC or VPC).</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>network_mode_config</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>VPC configuration.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>security_groups</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Security group IDs for VPC mode.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>subnets</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>Subnet IDs for VPC mode.</div>
                    <br/>
                </td>
            </tr>


            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>protocol_configuration</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The protocol configuration for the runtime.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>server_protocol</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The server protocol used (MCP, HTTP, A2A, or AGUI).</div>
                    <br/>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>role_arn</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The ARN of the IAM role assumed by the runtime.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">arn:aws:iam::123456789901:role/test-agentcore-runtime-role</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>status</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The current status of the runtime.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">READY</div>
                </td>
            </tr>

    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Domen Dobnikar (@domendobnikar)
