#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_training_job_info
short_description: Gather information about SageMaker training jobs
version_added: "2.0.0"
author:
    - Jan Likar (@JanLikar)
description:
    - Retrieve one training job by name or list matching jobs.
    - Listing consumes all pages returned by SageMaker.
options:
    training_job_name:
        description: The name of the training job to retrieve.
        type: str
        aliases: [name]
    creation_time_after:
        description: Only include jobs created after this timestamp.
        type: str
    creation_time_before:
        description: Only include jobs created before this timestamp.
        type: str
    last_modified_time_after:
        description: Only include jobs last modified after this timestamp.
        type: str
    last_modified_time_before:
        description: Only include jobs last modified before this timestamp.
        type: str
    name_contains:
        description: Only include jobs whose names contain this string.
        type: str
    status_equals:
        description: Only include jobs with this status.
        type: str
        choices: [InProgress, Completed, Failed, Stopping, Stopped, Deleting]
    sort_by:
        description: The field by which to sort listed jobs.
        type: str
        choices: [Name, CreationTime, Status]
        default: CreationTime
    sort_order:
        description: The sort order for listed jobs.
        type: str
        choices: [Ascending, Descending]
        default: Ascending
    warm_pool_status_equals:
        description: Only include jobs with this managed warm-pool status.
        type: str
        choices: [Available, Terminated, Reused, InUse]
    training_plan_arn_equals:
        description: Only include jobs associated with this training plan ARN.
        type: str
    include_tags:
        description: Whether to retrieve and include each job's tags.
        type: bool
        default: false
notes:
    - Required IAM actions include sagemaker:DescribeTrainingJob and sagemaker:ListTrainingJobs.
    - Retrieving tags additionally requires sagemaker:ListTags.
attributes:
    check_mode:
        description: Can run in check mode without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_training_job
      description: Manage SageMaker training jobs.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Get a training job by name
  amazon.ai.sagemaker_training_job_info:
    training_job_name: example-training-job

- name: List completed training jobs and include their tags
  amazon.ai.sagemaker_training_job_info:
    status_equals: Completed
    sort_by: CreationTime
    sort_order: Descending
    include_tags: true
"""

RETURN = r"""
training_job:
    description: The detailed training job when a named job is found.
    type: dict
    returned: when O(training_job_name) is specified and the job exists
    contains:
        training_job_name:
            description: The name of the training job.
            type: str
            returned: always
            sample: example-training-job
        training_job_arn:
            description: The Amazon Resource Name of the training job.
            type: str
            returned: when returned by SageMaker
            sample: arn:aws:sagemaker:us-east-1:123456789012:training-job/example-training-job
        training_job_status:
            description: The current execution status.
            type: str
            returned: when returned by SageMaker
            sample: Completed
        secondary_status:
            description: The current secondary execution status.
            type: str
            returned: when returned by SageMaker
            sample: Completed
        tags:
            description: The training job tags when O(include_tags=true).
            type: dict
            returned: when O(include_tags=true)
            sample: {project: demo}
    sample:
        training_job_name: example-training-job
        training_job_status: Completed
training_jobs:
    description: Matching training job summaries when listing jobs.
    type: list
    elements: dict
    returned: when O(training_job_name) is not specified
    contains:
        training_job_name:
            description: The name of the training job.
            type: str
            returned: always
            sample: example-training-job
        training_job_arn:
            description: The Amazon Resource Name of the training job.
            type: str
            returned: when returned by SageMaker
            sample: arn:aws:sagemaker:us-east-1:123456789012:training-job/example-training-job
        training_job_status:
            description: The current execution status.
            type: str
            returned: when returned by SageMaker
            sample: Completed
        secondary_status:
            description: The current secondary execution status.
            type: str
            returned: when returned by SageMaker
            sample: Completed
        warm_pool_status:
            description: The managed warm-pool status, when present.
            type: dict
            returned: when returned by SageMaker
            sample: {status: Available}
        tags:
            description: The training job tags when O(include_tags=true).
            type: dict
            returned: when O(include_tags=true)
            sample: {project: demo}
    sample:
        - training_job_name: example-training-job
          training_job_status: Completed
"""

try:
    import botocore
except ImportError:
    pass

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_training_job
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_training_jobs
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import normalize_training_job

from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


def _include_tags(client, training_job: dict) -> dict:
    training_job = dict(training_job)
    training_job["Tags"] = list_tags(client, training_job["TrainingJobArn"])
    return training_job


def main() -> None:
    argument_spec = dict(
        training_job_name=dict(type="str", aliases=["name"]),
        creation_time_after=dict(type="str"),
        creation_time_before=dict(type="str"),
        last_modified_time_after=dict(type="str"),
        last_modified_time_before=dict(type="str"),
        name_contains=dict(type="str"),
        status_equals=dict(
            type="str",
            choices=["InProgress", "Completed", "Failed", "Stopping", "Stopped", "Deleting"],
        ),
        sort_by=dict(type="str", choices=["Name", "CreationTime", "Status"], default="CreationTime"),
        sort_order=dict(type="str", choices=["Ascending", "Descending"], default="Ascending"),
        warm_pool_status_equals=dict(type="str", choices=["Available", "Terminated", "Reused", "InUse"]),
        training_plan_arn_equals=dict(type="str"),
        include_tags=dict(type="bool", default=False),
    )
    list_filters = (
        "creation_time_after",
        "creation_time_before",
        "last_modified_time_after",
        "last_modified_time_before",
        "name_contains",
        "status_equals",
        "warm_pool_status_equals",
        "training_plan_arn_equals",
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[("training_job_name", filter_name) for filter_name in list_filters],
    )
    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        if module.params.get("training_job_name"):
            job = describe_training_job(client, module.params["training_job_name"])
            if job is not None and module.params["include_tags"]:
                job = _include_tags(client, job)
            if job is not None:
                module.exit_json(training_job=normalize_training_job(job))
            module.exit_json()

        raw_filters = {key: module.params.get(key) for key in list_filters}
        raw_filters["sort_by"] = module.params["sort_by"]
        raw_filters["sort_order"] = module.params["sort_order"]
        filters = snake_dict_to_camel_dict(scrub_none_parameters(raw_filters), capitalize_first=True)
        jobs = list_training_jobs(client, **filters)
        if module.params["include_tags"]:
            jobs = [_include_tags(client, job) for job in jobs]
        module.exit_json(training_jobs=[normalize_training_job(job) for job in jobs])
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
