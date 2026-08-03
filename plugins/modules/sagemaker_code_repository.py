#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_code_repository
short_description: Manage Amazon SageMaker Code Repositories
version_added: "1.1.0"
author:
    - Christian Jahnel (@cjahnel)
description:
    - This module creates, updates, and deletes Amazon SageMaker Code Repositories.
    - A SageMaker Code Repository is a Git repository that is linked to a SageMaker account.
options:
    state:
        description:
            - The desired state of the code repository.
        type: str
        choices: ['present', 'absent']
        default: 'present'
    name:
        description:
            - The name of the code repository to manage.
            - Must be unique within your AWS account and region.
        type: str
        required: true
    git_config:
        description:
            - Configuration details for the Git repository.
            - Required when O(state=present).
            - Only O(git_config.secret_arn) can be modified after the code repository is created.
        type: dict
        suboptions:
            repository_url:
                description:
                    - The URL where the Git repository is located.
                    - This value cannot be modified after the code repository is created.
                type: str
                required: true
            branch:
                description:
                    - The default branch for the Git repository.
                    - This value cannot be modified after the code repository is created.
                type: str
            secret_arn:
                description:
                    - The Amazon Resource Name (ARN) of the AWS Secrets Manager secret
                      that contains the credentials used to access the git repository.
                    - 'The secret must have a staging label of AWSCURRENT and must be in
                      the following format: V({"username": "UserName", "password": "Password"})'
                type: str
    tags:
        description:
            - Tags to associate with the code repository.
            - Tags cannot be modified. They are only applied when a new code repository is created.
        type: dict
        aliases: ["resource_tags"]
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""


EXAMPLES = r"""
- name: Create a SageMaker Code Repository
  amazon.ai.sagemaker_code_repository:
    state: present
    name: "my-code-repo"
    git_config:
      repository_url: "https://github.com/my-org/my-repo.git"
      branch: "main"

- name: Create a SageMaker Code Repository with credentials
  amazon.ai.sagemaker_code_repository:
    state: present
    name: "my-private-repo"
    git_config:
      repository_url: "https://github.com/my-org/private-repo.git"
      branch: "main"
      secret_arn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-git-secret"

- name: Update the secret ARN of an existing code repository
  amazon.ai.sagemaker_code_repository:
    state: present
    name: "my-private-repo"
    git_config:
      repository_url: "https://github.com/my-org/private-repo.git"
      secret_arn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:new-git-secret"

- name: Delete a SageMaker Code Repository
  amazon.ai.sagemaker_code_repository:
    state: absent
    name: "my-code-repo"
"""


RETURN = r"""
code_repository:
    description: A dictionary containing the detailed configuration of the managed SageMaker Code Repository.
    type: dict
    returned: on success when state is present
    contains:
        code_repository_name:
            description: The name of the code repository.
            type: str
            sample: "my-code-repo"
        code_repository_arn:
            description: The Amazon Resource Name (ARN) of the code repository.
            type: str
            sample: "arn:aws:sagemaker:us-east-1:123456789012:code-repository/my-code-repo"
        git_config:
            description: Configuration details for the Git repository.
            type: dict
            contains:
                repository_url:
                    description: The URL where the Git repository is located.
                    type: str
                    sample: "https://github.com/my-org/my-repo.git"
                branch:
                    description: The default branch for the Git repository.
                    type: str
                    sample: "main"
                secret_arn:
                    description: The ARN of the secret containing Git credentials.
                    type: str
                    sample: "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-git-secret"
        creation_time:
            description: The date and time the code repository was created.
            type: str
            sample: "2025-10-01T15:36:41.199376+00:00"
        last_modified_time:
            description: The date and time the code repository was last modified.
            type: str
            sample: "2025-10-01T15:36:42.201271+00:00"
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: "Code repository 'my-code-repo' created successfully."
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_code_repository
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.utils import normalize_url

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def create_code_repository(client, module: AnsibleAWSModule) -> Tuple[bool, str]:
    repository_name = module.params["name"]

    if module.check_mode:
        return True, f"Check mode: would have created code repository {repository_name}."

    git_config: Dict[str, Any] = {"RepositoryUrl": module.params["git_config"]["repository_url"]}
    if module.params["git_config"].get("branch"):
        git_config["Branch"] = module.params["git_config"]["branch"]
    if module.params["git_config"].get("secret_arn"):
        git_config["SecretArn"] = module.params["git_config"]["secret_arn"]

    params: Dict[str, Any] = {
        "CodeRepositoryName": repository_name,
        "GitConfig": git_config,
    }

    if module.params.get("tags"):
        params["Tags"] = [{"Key": k, "Value": v} for k, v in module.params["tags"].items()]

    client.create_code_repository(**params)
    return True, f"Code repository {repository_name} created successfully."


def update_code_repository(client, module: AnsibleAWSModule, existing: Dict[str, Any]) -> Tuple[bool, str]:
    repository_name = module.params["name"]
    existing_git_config = existing["GitConfig"]
    new_git_config = module.params["git_config"]

    if module.params.get("tags") is not None:
        existing_tags = list_tags(client, existing["CodeRepositoryArn"])
        if module.params["tags"] != existing_tags:
            module.warn("Tags cannot be modified after the code repository is created.")

    if normalize_url(existing_git_config["RepositoryUrl"]) != normalize_url(new_git_config["repository_url"]):
        module.warn("The repository URL cannot be updated after the code repository is created.")
    if new_git_config.get("branch") and existing_git_config.get("Branch") != new_git_config["branch"]:
        module.warn("The branch cannot be updated after the code repository is created.")

    if not new_git_config.get("secret_arn") or existing_git_config.get("SecretArn") == new_git_config["secret_arn"]:
        return False, "No updates needed."

    if module.check_mode:
        return True, f"Check mode: would have updated code repository {repository_name}."

    client.update_code_repository(
        CodeRepositoryName=repository_name,
        GitConfig={"SecretArn": new_git_config["secret_arn"]},
    )
    return True, f"Code repository {repository_name} updated successfully."


def delete_code_repository(client, module: AnsibleAWSModule, existing: Dict[str, Any]) -> Tuple[bool, str]:
    repository_name = existing["CodeRepositoryName"]

    if module.check_mode:
        return True, f"Check mode: would have deleted code repository '{repository_name}'."

    client.delete_code_repository(CodeRepositoryName=repository_name)
    return True, f"Code repository {repository_name} deleted successfully."


def main():
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        name=dict(type="str", required=True),
        git_config=dict(
            type="dict",
            options=dict(
                repository_url=dict(type="str", required=True),
                branch=dict(type="str"),
                secret_arn=dict(type="str", no_log=False),
            ),
        ),
        tags=dict(type="dict", aliases=["resource_tags"]),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[("state", "present", ["git_config"])],
    )

    state: str = module.params["state"]

    try:
        client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    changed: bool = False
    result: Dict[str, Any] = dict(code_repository={})
    existing: Optional[Dict[str, Any]] = describe_code_repository(client, module.params["name"])

    try:
        if state == "present":
            if existing:
                changed, msg = update_code_repository(client, module, existing)
                result["code_repository"] = describe_code_repository(client, module.params["name"])
                result["msg"] = msg
            else:
                changed, msg = create_code_repository(client, module)
                if not module.check_mode:
                    result["code_repository"] = describe_code_repository(client, module.params["name"])
                result["msg"] = msg

        elif state == "absent":
            if existing:
                changed, msg = delete_code_repository(client, module, existing)
                result["msg"] = msg
            else:
                result["msg"] = "Code repository does not exist."

        module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
