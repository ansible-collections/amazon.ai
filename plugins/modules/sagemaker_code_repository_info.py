#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_code_repository_info
short_description: Gather information about SageMaker Code Repositories
version_added: "1.1.0"
author:
    - Christian Jahnel (@cjahnel)
description:
    - This module retrieves details for a single SageMaker Code Repository or lists all code repositories.
options:
    name:
        description:
            - The name of the code repository to retrieve.
            - If not provided, the module will list all code repositories.
            - Mutually exclusive with O(name_contains).
        type: str
    name_contains:
        description:
            - A string in the code repository name.
            - This filter returns only repositories whose name contains the specified string.
            - Mutually exclusive with O(name).
        type: str
    sort_by:
        description:
            - The field to sort results by.
        type: str
        choices: ['Name', 'CreationTime', 'LastModifiedTime']
    sort_order:
        description:
            - The sort order for results.
        type: str
        choices: ['Ascending', 'Descending']
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""


EXAMPLES = r"""
- name: Get info about a specific code repository
  amazon.ai.sagemaker_code_repository_info:
    name: "my-code-repo"

- name: List all SageMaker Code Repositories
  amazon.ai.sagemaker_code_repository_info:

- name: List code repositories filtered by name
  amazon.ai.sagemaker_code_repository_info:
    name_contains: "my-project"
    sort_by: "CreationTime"
    sort_order: "Descending"
"""


RETURN = r"""
code_repositories:
    description: A list of dictionaries containing detailed configuration of SageMaker Code Repositories.
    type: list
    elements: dict
    returned: always
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
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_code_repository
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_code_repositories

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def find_code_repositories(client, repository_name: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
    if repository_name:
        repo = describe_code_repository(client, repository_name)
        return [repo] if repo else []

    params: Dict[str, Any] = {}
    name_contains = kwargs.get("name_contains")
    if name_contains:
        params["NameContains"] = name_contains
    sort_by = kwargs.get("sort_by")
    if sort_by:
        params["SortBy"] = sort_by
    sort_order = kwargs.get("sort_order")
    if sort_order:
        params["SortOrder"] = sort_order

    summaries = list_code_repositories(client, **params)
    if not summaries:
        return []

    return [repo for s in summaries if (repo := describe_code_repository(client, s["CodeRepositoryName"])) is not None]


def main():
    argument_spec = dict(
        name=dict(type="str"),
        name_contains=dict(type="str"),
        sort_by=dict(type="str", choices=["Name", "CreationTime", "LastModifiedTime"]),
        sort_order=dict(type="str", choices=["Ascending", "Descending"]),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[("name", "name_contains")],
    )

    try:
        client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    result: List[Dict[str, Any]] = []

    try:
        result = find_code_repositories(
            client,
            module.params.get("name"),
            name_contains=module.params.get("name_contains"),
            sort_by=module.params.get("sort_by"),
            sort_order=module.params.get("sort_order"),
        )
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(code_repositories=[camel_dict_to_snake_dict(repo) for repo in result])


if __name__ == "__main__":
    main()
