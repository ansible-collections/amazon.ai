#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_training_job
short_description: Manage Amazon SageMaker training jobs
version_added: "2.0.0"
author:
    - Jan Likar (@JanLikar)
description:
    - Create, update, stop, and delete provisioned Amazon SageMaker AI training jobs.
    - Creating a job starts a billable training execution.
    - A stopped or completed job cannot be restarted; O(force=true) replaces it with a new execution.
options:
    state:
        description:
            - The desired state of the training job.
            - V(started) is synonymous with V(present) and does not resume a previous execution.
            - V(stopped) stops an active execution while retaining its metadata.
        type: str
        choices: [present, started, stopped, absent]
        default: present
    training_job_name:
        description: The name of the training job.
        type: str
        required: true
        aliases: [name]
    role_arn:
        description:
            - The ARN of the IAM role SageMaker assumes to run the training job.
            - Required when creating or replacing a job.
        type: str
    algorithm_specification:
        description:
            - The algorithm and input-mode configuration for the training job.
            - Required when creating or replacing a job.
            - Exactly one of O(algorithm_specification.training_image) and
              O(algorithm_specification.algorithm_name) must be supplied.
        type: dict
        suboptions:
            training_input_mode:
                description: How training data is made available to the algorithm.
                type: str
                required: true
            training_image:
                description: The URI of the Docker image that contains the training algorithm.
                type: str
            algorithm_name:
                description: The name of a built-in SageMaker algorithm.
                type: str
            metric_definitions:
                description: Metrics emitted by the algorithm and their extraction expressions.
                type: list
                elements: dict
                suboptions:
                    name:
                        description: The metric name.
                        type: str
                        required: true
                    regex:
                        description: The regular expression used to extract the metric value.
                        type: str
                        required: true
            enable_sage_maker_metrics_time_series:
                description: Whether to emit SageMaker metrics as a time series.
                type: bool
    input_data_config:
        description: The input channels used by the training job.
        type: list
        elements: dict
        suboptions:
            channel_name:
                description: The name of the input channel.
                type: str
                required: true
            data_source:
                description: The S3 data source for the input channel.
                type: dict
                required: true
                suboptions:
                    s3_data_source:
                        description: The S3 location and distribution configuration.
                        type: dict
                        required: true
                        suboptions:
                            s3_data_type:
                                description: The type of S3 data location.
                                type: str
                                required: true
                            s3_uri:
                                description: The S3 URI for the input data.
                                type: str
                                required: true
                            s3_data_distribution_type:
                                description: How S3 data is distributed across instances.
                                type: str
                            attribute_names:
                                description: Record attributes to select from the input data.
                                type: list
                                elements: str
                            instance_group_names:
                                description: Instance groups to receive this input channel.
                                type: list
                                elements: str
            content_type:
                description: The MIME type of the input data.
                type: str
            compression_type:
                description: The compression type of the input data.
                type: str
            record_wrapper_type:
                description: The record wrapper applied to each input record.
                type: str
            input_mode:
                description: How this channel is made available to the algorithm.
                type: str
            shuffle_config:
                description: Configuration for shuffling input records.
                type: dict
                suboptions:
                    seed:
                        description: The seed used to shuffle input records.
                        type: int
    output_data_config:
        description:
            - The S3 location for training output.
            - Required when creating or replacing a job.
        type: dict
        suboptions:
            s3_output_path:
                description: The S3 URI where SageMaker stores model artifacts.
                type: str
                required: true
            kms_key_id:
                description: The KMS key used to encrypt output artifacts.
                type: str
            compression_type:
                description: The compression type for model artifacts.
                type: str
    resource_config:
        description:
            - The compute and storage resources for the training job.
            - Required when creating or replacing a provisioned job.
            - Only O(resource_config.keep_alive_period_in_seconds) can be changed in place.
        type: dict
        suboptions:
            instance_type:
                description: The type of ML compute instance to use.
                type: str
            instance_count:
                description: The number of instances to use for training.
                type: int
            volume_size_in_gb:
                description: The size of the ML storage volume in GiB.
                type: int
            volume_kms_key_id:
                description: The KMS key used to encrypt the storage volume.
                type: str
            keep_alive_period_in_seconds:
                description: How long a managed warm pool retains compute resources.
                type: int
    stopping_condition:
        description: Runtime and pending-time limits for the training job.
        type: dict
        suboptions:
            max_runtime_in_seconds:
                description: The maximum runtime of the training job.
                type: int
            max_wait_time_in_seconds:
                description: The maximum time the job can wait for capacity.
                type: int
            max_pending_time_in_seconds:
                description: The maximum time the job can remain pending.
                type: int
    vpc_config:
        description: The VPC configuration for the training job.
        type: dict
        suboptions:
            security_group_ids:
                description: VPC security group IDs.
                type: list
                elements: str
            subnets:
                description: VPC subnet IDs.
                type: list
                elements: str
    hyper_parameters:
        description: String key/value hyperparameters passed to the training algorithm.
        type: dict
    environment:
        description: Environment variables passed to the training container.
        type: dict
    enable_network_isolation:
        description: Whether to isolate the training container from the network.
        type: bool
        default: false
    enable_inter_container_traffic_encryption:
        description: Whether to encrypt traffic between training containers.
        type: bool
        default: false
    enable_managed_spot_training:
        description: Whether to use managed spot training.
        type: bool
        default: false
    checkpoint_config:
        description: The S3 location and local path used for checkpoints.
        type: dict
        suboptions:
            s3_uri:
                description: The S3 URI where checkpoints are persisted.
                type: str
                required: true
            local_path:
                description: The local directory where checkpoints are stored.
                type: str
    retry_strategy:
        description: The retry policy for training-job interruptions.
        type: dict
        suboptions:
            maximum_retry_attempts:
                description: The maximum number of retry attempts.
                type: int
    profiler_config:
        description:
            - SageMaker Debugger profiler configuration.
            - This is one of the few job settings that can be updated in place.
        type: dict
        suboptions:
            s3_output_path:
                description: The S3 output location for profiler data.
                type: str
            profiling_interval_in_milliseconds:
                description: The interval between profiler samples.
                type: int
            profiling_parameters:
                description: Profiler parameters as string key/value pairs.
                type: dict
            disable_profiler:
                description: Whether profiling is disabled.
                type: bool
    profiler_rule_configurations:
        description: Profiler rules for the training job; these can be updated in place.
        type: list
        elements: dict
        suboptions:
            rule_configuration_name:
                description: The name of the profiler rule configuration.
                type: str
                required: true
            rule_evaluator_image:
                description: The URI of the rule evaluator image.
                type: str
                required: true
            local_path:
                description: The local path for rule output.
                type: str
            s3_output_path:
                description: The S3 path for rule output.
                type: str
            instance_type:
                description: The instance type used to evaluate the rule.
                type: str
            volume_size_in_gb:
                description: The storage volume size in GiB for rule evaluation.
                type: int
            rule_parameters:
                description: Parameters for the profiler rule.
                type: dict
    remote_debug_config:
        description:
            - Configuration for remote debugging; updates are accepted only while the secondary status is
              V(Downloading) or V(Training).
        type: dict
        suboptions:
            enable_remote_debug:
                description: Whether remote debugging is enabled.
                type: bool
    tags:
        description: Tags to associate with the training job.
        type: dict
        aliases: [resource_tags]
    purge_tags:
        description: Whether to remove existing tags omitted from O(tags).
        type: bool
        default: true
    force:
        description:
            - Replace a job when a create-only setting differs or when restarting a terminal job.
            - Replacement stops an active execution, removes eligible warm-pool capacity, deletes the job,
              and starts a new billable execution with the same name.
        type: bool
        default: false
    wait:
        description: Whether to wait for job completion, stopping, warm-pool termination, and deletion.
        type: bool
        default: true
    wait_timeout:
        description: The maximum number of seconds to wait for each asynchronous operation.
        type: int
        default: 600
notes:
    - Required IAM actions include sagemaker:CreateTrainingJob, sagemaker:DescribeTrainingJob,
      sagemaker:UpdateTrainingJob, sagemaker:StopTrainingJob, sagemaker:DeleteTrainingJob,
      sagemaker:AddTags, sagemaker:DeleteTags, and sagemaker:ListTags.
    - Creating a job requires iam:PassRole for the execution role, constrained where possible with
      iam:PassedToService=sagemaker.amazonaws.com.
attributes:
    check_mode:
        description: Can run in check mode and report what would change without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_training_job_info
      description: Gather information about SageMaker training jobs.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Create a SageMaker training job
  amazon.ai.sagemaker_training_job:
    training_job_name: example-training-job
    role_arn: arn:aws:iam::123456789012:role/SageMakerExecutionRole
    algorithm_specification:
      training_input_mode: File
      training_image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest
    output_data_config:
      s3_output_path: s3://example-bucket/training-output/
    resource_config:
      instance_type: ml.m5.large
      instance_count: 1
      volume_size_in_gb: 10
    stopping_condition:
      max_runtime_in_seconds: 3600

- name: Stop a training job and retain its metadata
  amazon.ai.sagemaker_training_job:
    state: stopped
    training_job_name: example-training-job

- name: Delete a training job
  amazon.ai.sagemaker_training_job:
    state: absent
    training_job_name: example-training-job
"""

RETURN = r"""
training_job:
    description: The final or last-known description of the training job.
    type: dict
    returned: always
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
        failure_reason:
            description: The reason a training job failed.
            type: str
            returned: when the job fails
            sample: Training container exited with a non-zero status.
        algorithm_specification:
            description: The algorithm configuration used for training.
            type: dict
            returned: when returned by SageMaker
            sample: {}
        input_data_config:
            description: The configured training input channels.
            type: list
            elements: dict
            returned: when returned by SageMaker
            sample: []
        output_data_config:
            description: The output location and encryption configuration.
            type: dict
            returned: when returned by SageMaker
            sample: {s3_output_path: s3://example-bucket/training-output/}
        resource_config:
            description: The compute and storage configuration.
            type: dict
            returned: when returned by SageMaker
            sample: {instance_type: ml.m5.large, instance_count: 1}
        model_artifacts:
            description: The S3 location of the resulting model artifacts.
            type: dict
            returned: when returned by SageMaker
            sample: {s3_model_artifacts: s3://example-bucket/training-output/model.tar.gz}
        creation_time:
            description: The time the training job was created.
            type: str
            returned: when returned by SageMaker
            sample: '2025-01-01T12:00:00+00:00'
        training_start_time:
            description: The time the training job started.
            type: str
            returned: when returned by SageMaker
            sample: '2025-01-01T12:05:00+00:00'
        training_end_time:
            description: The time the training job ended.
            type: str
            returned: when returned by SageMaker
            sample: '2025-01-01T12:30:00+00:00'
        tags:
            description: The training job tags when tag management was requested.
            type: dict
            returned: when tags were requested
            sample: {project: demo}
    sample:
        training_job_name: example-training-job
        training_job_arn: arn:aws:sagemaker:us-east-1:123456789012:training-job/example-training-job
        training_job_status: Completed
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: Training job example-training-job created successfully.
changed:
    description: Whether a job operation or tag update was performed or planned.
    type: bool
    returned: always
    sample: true
"""

try:
    import botocore
except ImportError:
    pass

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import find_training_job
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import manage_training_job
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import normalize_training_job

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _validate_algorithm_specification(module: AnsibleAWSModule) -> None:
    algorithm = module.params.get("algorithm_specification")
    if algorithm is not None:
        if not algorithm.get("training_input_mode"):
            module.fail_json(msg="algorithm_specification.training_input_mode is required.")
        image = algorithm.get("training_image")
        name = algorithm.get("algorithm_name")
        if bool(image) == bool(name):
            module.fail_json(
                msg=(
                    "Exactly one of algorithm_specification.training_image and "
                    "algorithm_specification.algorithm_name must be specified."
                )
            )


def _validate_input_data_config(module: AnsibleAWSModule) -> None:
    for index, channel in enumerate(module.params.get("input_data_config") or []):
        if not channel.get("channel_name"):
            module.fail_json(msg=f"input_data_config[{index}].channel_name is required.")
        data_source = channel.get("data_source")
        if not data_source or not data_source.get("s3_data_source"):
            module.fail_json(msg=f"input_data_config[{index}].data_source.s3_data_source is required.")
        s3_data_source = data_source["s3_data_source"]
        for field in ("s3_data_type", "s3_uri"):
            if not s3_data_source.get(field):
                module.fail_json(msg=f"input_data_config[{index}].data_source.s3_data_source.{field} is required.")


def _validate_nested_params(module: AnsibleAWSModule) -> None:
    _validate_algorithm_specification(module)
    _validate_input_data_config(module)
    output_config = module.params.get("output_data_config")
    if output_config is not None and not output_config.get("s3_output_path"):
        module.fail_json(msg="output_data_config.s3_output_path is required.")

    resource_config = module.params.get("resource_config")
    create_resource_fields = ("instance_type", "instance_count", "volume_size_in_gb")
    if resource_config and any(resource_config.get(field) is not None for field in create_resource_fields):
        missing = [field for field in create_resource_fields if resource_config.get(field) is None]
        if missing:
            module.fail_json(msg=f"These resource_config options must be supplied together: {', '.join(missing)}.")

    checkpoint_config = module.params.get("checkpoint_config")
    if checkpoint_config is not None and not checkpoint_config.get("s3_uri"):
        module.fail_json(msg="checkpoint_config.s3_uri is required.")


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "started", "stopped", "absent"]),
        training_job_name=dict(type="str", required=True, aliases=["name"]),
        role_arn=dict(type="str"),
        algorithm_specification=dict(
            type="dict",
            options=dict(
                training_input_mode=dict(type="str", required=True),
                training_image=dict(type="str"),
                algorithm_name=dict(type="str"),
                metric_definitions=dict(
                    type="list",
                    elements="dict",
                    options=dict(name=dict(type="str", required=True), regex=dict(type="str", required=True)),
                ),
                enable_sage_maker_metrics_time_series=dict(type="bool"),
            ),
        ),
        input_data_config=dict(
            type="list",
            elements="dict",
            options=dict(
                channel_name=dict(type="str", required=True),
                data_source=dict(
                    type="dict",
                    required=True,
                    options=dict(
                        s3_data_source=dict(
                            type="dict",
                            required=True,
                            options=dict(
                                s3_data_type=dict(type="str", required=True),
                                s3_uri=dict(type="str", required=True),
                                s3_data_distribution_type=dict(type="str"),
                                attribute_names=dict(type="list", elements="str"),
                                instance_group_names=dict(type="list", elements="str"),
                            ),
                        )
                    ),
                ),
                content_type=dict(type="str"),
                compression_type=dict(type="str"),
                record_wrapper_type=dict(type="str"),
                input_mode=dict(type="str"),
                shuffle_config=dict(type="dict", options=dict(seed=dict(type="int"))),
            ),
        ),
        output_data_config=dict(
            type="dict",
            options=dict(
                s3_output_path=dict(type="str", required=True),
                kms_key_id=dict(type="str"),
                compression_type=dict(type="str"),
            ),
        ),
        resource_config=dict(
            type="dict",
            options=dict(
                instance_type=dict(type="str"),
                instance_count=dict(type="int"),
                volume_size_in_gb=dict(type="int"),
                volume_kms_key_id=dict(type="str"),
                keep_alive_period_in_seconds=dict(type="int"),
            ),
        ),
        stopping_condition=dict(
            type="dict",
            options=dict(
                max_runtime_in_seconds=dict(type="int"),
                max_wait_time_in_seconds=dict(type="int"),
                max_pending_time_in_seconds=dict(type="int"),
            ),
        ),
        vpc_config=dict(
            type="dict",
            options=dict(
                security_group_ids=dict(type="list", elements="str"),
                subnets=dict(type="list", elements="str"),
            ),
        ),
        hyper_parameters=dict(type="dict"),
        environment=dict(type="dict"),
        enable_network_isolation=dict(type="bool", default=False),
        enable_inter_container_traffic_encryption=dict(type="bool", default=False),
        enable_managed_spot_training=dict(type="bool", default=False),
        checkpoint_config=dict(
            type="dict", options=dict(s3_uri=dict(type="str", required=True), local_path=dict(type="str"))
        ),
        retry_strategy=dict(type="dict", options=dict(maximum_retry_attempts=dict(type="int"))),
        profiler_config=dict(
            type="dict",
            options=dict(
                s3_output_path=dict(type="str"),
                profiling_interval_in_milliseconds=dict(type="int"),
                profiling_parameters=dict(type="dict"),
                disable_profiler=dict(type="bool"),
            ),
        ),
        profiler_rule_configurations=dict(
            type="list",
            elements="dict",
            options=dict(
                rule_configuration_name=dict(type="str", required=True),
                rule_evaluator_image=dict(type="str", required=True),
                local_path=dict(type="str"),
                s3_output_path=dict(type="str"),
                instance_type=dict(type="str"),
                volume_size_in_gb=dict(type="int"),
                rule_parameters=dict(type="dict"),
            ),
        ),
        remote_debug_config=dict(type="dict", options=dict(enable_remote_debug=dict(type="bool"))),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        force=dict(type="bool", default=False),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    _validate_nested_params(module)
    name = module.params["training_job_name"]
    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing = find_training_job(client, name)
        job, changed, msg = manage_training_job(client, module, existing)
        if job is not None and module.params.get("tags") is not None and module.params["state"] != "absent":
            job = dict(job)
            job["Tags"] = list_tags(client, job["TrainingJobArn"])
        module.exit_json(
            changed=changed,
            msg=msg,
            training_job=normalize_training_job(job or {}),
        )
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
