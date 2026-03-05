# Ansible Collection for Amazon AI and ML Resources

## Contents

- [Our mission](#our-mission)
- [Code of Conduct](#code-of-conduct)
- [Communication](#communication)
- [Requirements](#requirements)
  - [Ansible version compatibility](#ansible-version-compatibility)
  - [Python version compatibility](#python-version-compatibility)
  - [AWS SDK version compatibility](#aws-sdk-version-compatibility)
- [Included content](#included-content)
- [Using this collection](#using-this-collection)
  - [Installing the Collection](#installing-the-collection)
- [Use Cases](#use-cases)
- [Testing](#testing)
- [Contributing to this collection](#contributing-to-this-collection)
- [More information](#more-information)
- [Support](#support)
- [Release notes](#release-notes)
- [License Information](#license-information)

The ``amazon.ai`` Ansible Collection provides automation modules for AWS AI and ML services. Currently, the collection includes modules for:
- **Amazon DevOps Guru**: Configure monitoring, manage insights, and integrate notification channels.
- **Amazon Bedrock**: Interact with foundation models for AI/ML applications.

The collection is designed to be extensible and will grow to support additional services such as Amazon SageMaker, Rekognition, Comprehend, Translate, and Textract.

As Red Hat Ansible [Certified Content](https://catalog.redhat.com/software/search?target_platforms=Red%20Hat%20Ansible%20Automation%20Platform), this collection is entitled to [support](https://access.redhat.com/support/) through [Ansible Automation Platform](https://www.redhat.com/en/technologies/management/ansible) (AAP).


## Our mission

At the `amazon.ai` collection, our mission is to empower users to deploy and manage AWS AI/ML services using simple, declarative automation workflows with Ansible.

We aim to lower the barrier to entry for machine learning operations (MLOps) on AWS, enabling developers, data scientists, and DevOps engineers to build intelligent applications faster and more reliably.


## Code of Conduct

We follow the [Ansible Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html) in all our interactions within this project.

If you encounter abusive behavior, please refer to the [policy violations](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html#policy-violations) section of the Code for information on how to raise a complaint.

## Communication

* Join the Ansible forum:
  * [Get Help](https://forum.ansible.com/c/help/6): get help or help others. Please add appropriate tags if you start new discussions.
  * [Social Spaces](https://forum.ansible.com/c/chat/4): gather and interact with fellow enthusiasts.
  * [News & Announcements](https://forum.ansible.com/c/news/5): track project-wide announcements including social events. The [Bullhorn newsletter](https://docs.ansible.com/ansible/devel/community/communication.html#the-bullhorn), which is used to announce releases and important changes, can also be found here.

For more information about communication, see the [Ansible communication guide](https://docs.ansible.com/ansible/devel/community/communication.html).

## Requirements

<!--start requires_ansible-->
### Ansible version compatibility

This collection has been tested against the following Ansible versions: **>=2.17.0**.

Plugins and modules within a collection may be tested with only specific Ansible versions.
A collection may contain metadata that identifies these versions.
PEP440 is the schema used to describe the versions of Ansible.
<!--end requires_ansible-->

### Python version compatibility

This collection depends on the AWS SDK for Python (Boto3 and Botocore). Due to the
[AWS SDK Python Support Policy](https://aws.amazon.com/blogs/developer/python-support-policy-updates-for-aws-sdks-and-tools/)
this collection requires Python 3.9 or greater.

### AWS SDK version compatibility

Version 1.0.0 of this collection supports ``boto3 >= 1.35.0`` and ``botocore >= 1.35.0``.

## Included content
<!--start collection content-->
### Modules
Name | Description
--- | ---
[amazon.ai.bedrock_agent](https://github.com/ansible-collections/amazon.ai/blob/main/docs/amazon.ai.bedrock_agent_module.rst)|Manage Amazon Bedrock Agents
[amazon.ai.bedrock_agent_action_group](https://github.com/ansible-collections/amazon.ai/blob/main/docs/amazon.ai.bedrock_agent_action_group_module.rst)|Manage Amazon Bedrock Agent Action Groups
[amazon.ai.bedrock_agent_action_group_info](https://github.com/ansible-collections/amazon.ai/blob/main/docs/amazon.ai.bedrock_agent_action_group_info_module.rst)|Gather information about a Bedrock Agent's Action Groups
[amazon.ai.bedrock_agent_alias](https://github.com/ansible-collections/amazon.ai/blob/main/docs/amazon.ai.bedrock_agent_alias_module.rst)|Manage Amazon Bedrock Agent Aliases
[amazon.ai.bedrock_agent_alias_info](https://github.com/ansible-collections/amazon.ai/blob/main/docs/amazon.ai.bedrock_agent_alias_info_module.rst)|Gather information about a Bedrock Agent's Aliases
[amazon.ai.bedrock_agent_info](https://github.com/ansible-collections/amazon.ai/blob/main/docs/amazon.ai.bedrock_agent_info_module.rst)|Gather information about Bedrock Agents
[amazon.ai.bedrock_foundation_models_info](https://github.com/ansible-collections/amazon.ai/blob/main/docs/amazon.ai.bedrock_foundation_models_info_module.rst)|List or get details for Amazon Bedrock foundation models
[amazon.ai.bedrock_invoke_agent](https://github.com/ansible-collections/amazon.ai/blob/main/docs/amazon.ai.bedrock_invoke_agent_module.rst)|Invoke an Amazon Bedrock agent with a prompt
[amazon.ai.bedrock_invoke_model](https://github.com/ansible-collections/amazon.ai/blob/main/docs/amazon.ai.bedrock_invoke_model_module.rst)|Run inference using Amazon Bedrock models
[amazon.ai.devopsguru_insight_info](https://github.com/ansible-collections/amazon.ai/blob/main/docs/amazon.ai.devopsguru_insight_info_module.rst)|Fetch information about Amazon DevOps Guru insights
[amazon.ai.devopsguru_resource_collection](https://github.com/ansible-collections/amazon.ai/blob/main/docs/amazon.ai.devopsguru_resource_collection_module.rst)|Manage DevOps Guru resource collections
[amazon.ai.devopsguru_resource_collection_info](https://github.com/ansible-collections/amazon.ai/blob/main/docs/amazon.ai.devopsguru_resource_collection_info_module.rst)|Fetch information about Amazon DevOps Guru resource collection

<!--end collection content-->

## Using this collection

### Installing the Collection

To consume this collection from Automation Hub, add the following lines to your ``ansible.cfg`` file.

```
[galaxy]
server_list = automation_hub

[galaxy_server.automation_hub]
url=https://cloud.redhat.com/api/automation-hub/
auth_url=https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token
token=<SecretToken>
```
The token can be obtained from the [Automation Hub Web UI](https://console.redhat.com/ansible/automation-hub/token).

Once the above steps are done, you can run the following command to install the collection.

```bash
ansible-galaxy collection install amazon.ai
```

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: amazon.ai
```

A specific version of the collection can be installed by specifying the version. For example, to install version `1.0.0`:

```bash
ansible-galaxy collection install amazon.ai:==1.0.0
```

See [using Ansible collections](https://docs.ansible.com/ansible/devel/user_guide/collections_using.html) for more details.

The Python module dependencies are not installed by `ansible-galaxy`.  They can
be manually installed using pip:

```shell
pip install -r requirements.txt
```

or:

```shell
pip install boto3 botocore
```

Refer to the following for more details:

* [Amazon Web Services Guide](https://docs.ansible.com/ansible/latest/collections/amazon/aws/docsite/guide_aws.html)
* [Using Ansible collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html)

## Use Cases

You can call modules by their Fully Qualified Collection Name (FQCN), such as ``amazon.ai.bedrock_agent``, or by their short name if you list the ``amazon.ai`` collection in the playbook's ``collections`` keyword:

```yaml
---
- name: Create Bedrock Agent
  amazon.ai.bedrock_agent:
    state: present
    agent_name: "{{ agent_name }}"
    foundation_model: "{{ foundation_model }}"
    instruction: "{{ instruction }}"
    agent_resource_role_arn: "{{ agent_role_arn }}"

- name: Create Bedrock Agent Alias
  amazon.ai.bedrock_agent_alias:
    state: present
    agent_name: "{{ agent_name }}"
    alias_name: "{{ alias_name }}"
```

## Testing

This collection is tested using GitHub Actions. To learn more about testing, refer to [CI.md](https://github.com/ansible-collections/amazon.ai/blob/main/CI.md).

## Contributing to this collection

The content of this collection is made by people like you, a community of individuals collaborating on making the world better through developing automation software.

We are actively accepting new contributors and all types of contributions are very welcome.

Don't know how to start? Refer to the [Ansible community guide](https://docs.ansible.com/ansible/devel/community/index.html)!

## More information

- [Ansible user guide](https://docs.ansible.com/ansible/devel/user_guide/index.html)
- [Ansible developer guide](https://docs.ansible.com/ansible/devel/dev_guide/index.html)
- [Ansible collections requirements](https://docs.ansible.com/ansible/devel/community/collection_contributors/collection_requirements.html)
- [Ansible community Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html)
- [The Bullhorn (the Ansible contributor newsletter)](https://docs.ansible.com/ansible/devel/community/communication.html#the-bullhorn)
- [Important announcements for maintainers](https://github.com/ansible-collections/news-for-maintainers)

## Support

As Red Hat Ansible Certified Content, this collection is entitled to support through Ansible Automation Platform (AAP) using the **Create issue** button on the top right corner. If a support case cannot be opened with Red Hat and the collection has been obtained from Galaxy or GitHub, community help may be available on the [Ansible Forum](https://forum.ansible.com/).

You can also join us on:

- The ``#ansible-aws`` channel on [Libera.Chat](https://libera.chat/) (IRC)

## Release notes

See the [changelog](https://github.com/ansible-collections/amazon.ai/tree/main/CHANGELOG.rst).

## License Information

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.

