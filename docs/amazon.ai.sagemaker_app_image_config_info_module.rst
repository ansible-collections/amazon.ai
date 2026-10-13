.. _amazon.ai.sagemaker_app_image_config_info_module:


*****************************************
amazon.ai.sagemaker_app_image_config_info
*****************************************

**Gather information about Amazon SageMaker AppImageConfigs**


Version added: 2.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Retrieve a single Amazon SageMaker AppImageConfig by name, or list AppImageConfigs with optional filters.
- Every returned AppImageConfig carries its configuration blocks, and its tags when O(include_tags) or O(tags) is set.



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
                    <b>app_image_config_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The name of the AppImageConfig to retrieve.</div>
                        <div>When it is omitted, AppImageConfigs are listed, optionally filtered by the other options.</div>
                        <div>An AppImageConfig that does not exist gives an empty list.</div>
                        <div>Mutually exclusive with O(name_contains), O(creation_time_after), O(creation_time_before), O(modified_time_after), O(modified_time_before), O(sort_by), O(sort_order) and O(tags).</div>
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
                        <div>Parameters can be found in the AWS documentation <a href='https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html#botocore.config.Config'>https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html#botocore.config.Config</a>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>creation_time_after</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Only include AppImageConfigs created on or after this time, in ISO 8601 format.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>creation_time_before</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Only include AppImageConfigs created on or before this time, in ISO 8601 format.</div>
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
                    <b>include_tags</b>
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
                        <div>Whether to read the tags of every returned AppImageConfig and return them as RV(app_image_configs[].tags).</div>
                        <div>Reading the tags costs one extra API call for each AppImageConfig returned, so it is off by default.</div>
                        <div>The tags are always read when O(tags) is set.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>modified_time_after</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Only include AppImageConfigs last modified on or after this time, in ISO 8601 format.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>modified_time_before</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Only include AppImageConfigs last modified on or before this time, in ISO 8601 format.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>name_contains</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A string that must be contained in the AppImageConfig name.</div>
                        <div>AWS rejects O(sort_by=Name) together with this option.</div>
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
                    <b>sort_by</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>CreationTime</li>
                                    <li>LastModifiedTime</li>
                                    <li>Name</li>
                        </ul>
                </td>
                <td>
                        <div>The field to sort the results by. AWS sorts by V(CreationTime) when it is omitted.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>sort_order</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>Ascending</li>
                                    <li>Descending</li>
                        </ul>
                </td>
                <td>
                        <div>The sort order of the results. AWS sorts V(Descending) when it is omitted.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>tags</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A dictionary of tags to filter by.</div>
                        <div>Only AppImageConfigs whose tags contain all the given key/value pairs are returned.</div>
                        <div>Values that are not strings are converted to strings before comparing; booleans become V(true) or V(false).</div>
                        <div>The filter is applied after the list call, so it does not reduce the number of API calls.</div>
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
   - The module needs the ``sagemaker:DescribeAppImageConfig``, ``sagemaker:ListAppImageConfigs`` and ``sagemaker:ListTags`` IAM permissions.
   - Reading the tags (O(include_tags) or O(tags)) costs one extra API call for each AppImageConfig returned.
   - **Caution:** For modules, environment variables and configuration files are read from the Ansible 'host' context and not the 'controller' context. As such, files may need to be explicitly copied to the 'host'.  For lookup and connection plugins, environment variables and configuration files are read from the Ansible 'controller' context and not the 'host' context.
   - The AWS SDK (boto3) that Ansible uses may also read defaults for credentials and other settings, such as the region, from its configuration files in the Ansible 'host' context (typically ``~/.aws/credentials``). See https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html for more information.


See Also
--------

.. seealso::

   :ref:`amazon.ai.sagemaker_app_image_config_module`
      The official documentation on the **amazon.ai.sagemaker_app_image_config** module.


Examples
--------

.. code-block:: yaml

    - name: Get a specific AppImageConfig
      amazon.ai.sagemaker_app_image_config_info:
        name: example-app-image-config

    - name: List all AppImageConfigs
      amazon.ai.sagemaker_app_image_config_info:

    - name: List AppImageConfigs whose name contains a string, newest modification first
      amazon.ai.sagemaker_app_image_config_info:
        name_contains: example
        sort_by: LastModifiedTime
        sort_order: Descending

    - name: Get a specific AppImageConfig together with its tags
      amazon.ai.sagemaker_app_image_config_info:
        name: example-app-image-config
        include_tags: true

    - name: List AppImageConfigs created after a date and carrying a tag
      amazon.ai.sagemaker_app_image_config_info:
        creation_time_after: "2025-01-01T00:00:00Z"
        tags:
          project: demo



Return Values
-------------
Common return values are documented `here <https://docs.ansible.com/projects/ansible/latest/reference_appendices/common_return_values.html#common-return-values>`_, the following are the fields unique to this module:

.. raw:: html

    <table border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="2">Key</th>
            <th>Returned</th>
            <th width="100%">Description</th>
        </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>app_image_configs</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>A list of AppImageConfigs. The list is empty when none match.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">[{&#x27;app_image_config_name&#x27;: &#x27;example-app-image-config&#x27;, &#x27;app_image_config_arn&#x27;: &#x27;arn:aws:sagemaker:eu-north-1:123456789012:app-image-config/example-app-image-config&#x27;, &#x27;creation_time&#x27;: &#x27;2025-01-01T00:00:00+00:00&#x27;, &#x27;last_modified_time&#x27;: &#x27;2025-01-01T00:00:00+00:00&#x27;, &#x27;jupyter_lab_app_image_config&#x27;: {&#x27;container_config&#x27;: {&#x27;container_arguments&#x27;: [&#x27;--debug&#x27;]}}, &#x27;tags&#x27;: {&#x27;project&#x27;: &#x27;demo&#x27;}}]</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>app_image_config_arn</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The Amazon Resource Name (ARN) of the AppImageConfig.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">arn:aws:sagemaker:eu-north-1:123456789012:app-image-config/example-app-image-config</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>app_image_config_name</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The name of the AppImageConfig.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">example-app-image-config</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>code_editor_app_image_config</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The Code Editor configuration, when the AppImageConfig has one.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;container_config&#x27;: {&#x27;container_arguments&#x27;: [&#x27;--debug&#x27;]}}</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>creation_time</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The date and time the AppImageConfig was created.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">2025-01-01T00:00:00+00:00</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>jupyter_lab_app_image_config</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The JupyterLab configuration, when the AppImageConfig has one.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;container_config&#x27;: {&#x27;container_arguments&#x27;: [&#x27;--debug&#x27;]}}</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>kernel_gateway_image_config</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The kernel gateway configuration, when the AppImageConfig has one.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;kernel_specs&#x27;: [{&#x27;name&#x27;: &#x27;python3&#x27;}]}</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>last_modified_time</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The date and time the AppImageConfig was last modified.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">2025-01-01T00:00:00+00:00</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>tags</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>The tags assigned to the AppImageConfig. Only returned when O(include_tags=true) or O(tags) is set.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;project&#x27;: &#x27;demo&#x27;}</div>
                </td>
            </tr>

    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Matej Artač (@matejart)
