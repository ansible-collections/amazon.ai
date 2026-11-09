#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_user_profile
short_description: Manage Amazon SageMaker AI user profiles
version_added: "2.0.0"
author:
    - Domen Dobnikar (@domendobnikar)
description:
    - Creates, updates, and deletes Amazon SageMaker AI user profiles in an existing domain, and manages their tags.
    - A user profile is the identity of a user inside a SageMaker AI domain.
      It holds the execution role and the Studio, app, storage, and file system settings of the user.
options:
    state:
        description:
            - Whether the user profile should exist.
        type: str
        choices: [present, absent]
        default: present
    domain_id:
        description:
            - The ID of the domain the user profile belongs to.
            - The domain must already exist.
        type: str
        required: true
    user_profile_name:
        description:
            - The name of the user profile.
            - The name is unique within the domain and is not case-sensitive.
        type: str
        required: true
        aliases: [name]
    single_sign_on_user_identifier:
        description:
            - The IAM Identity Center user attribute that identifies the user. The only supported value is V(UserName).
            - Only valid for domains that use IAM Identity Center authentication.
            - Required together with O(single_sign_on_user_value).
            - This option is create-only. The module fails if it differs from the existing user profile.
        type: str
        choices: [UserName]
    single_sign_on_user_value:
        description:
            - The user name of the IAM Identity Center user the profile belongs to.
            - Required together with O(single_sign_on_user_identifier).
            - This option is create-only. The module fails if it differs from the existing user profile.
        type: str
    execution_role:
        description:
            - The ARN of the IAM role that the user's apps and jobs run as.
            - When omitted at creation, the default execution role of the domain is used.
        type: str
    security_groups:
        description:
            - The IDs of up to 5 security groups for the Amazon VPC that the domain uses for communication.
            - Compared as a set, the order does not matter.
        type: list
        elements: str
    sharing_settings:
        description:
            - How notebooks are shared.
        type: dict
        suboptions:
            notebook_output_option:
                description:
                    - Whether to include the notebook cell output when a notebook is shared.
                type: str
                choices: [Allowed, Disabled]
            s3_output_path:
                description:
                    - The Amazon S3 location where shared notebook snapshots are stored.
                type: str
            s3_kms_key_id:
                description:
                    - The ID of the AWS KMS key used to encrypt the shared notebook snapshots.
                type: str
    jupyter_server_app_settings:
        description:
            - The settings of the Jupyter server app.
        type: dict
        suboptions:
            default_resource_spec:
                description:
                    - The instance type and SageMaker AI image that the app runs on by default.
                type: dict
                suboptions:
                    sage_maker_image_arn:
                        description:
                            - The ARN of the SageMaker AI image.
                        type: str
                    sage_maker_image_version_arn:
                        description:
                            - The ARN of the SageMaker AI image version.
                        type: str
                    sage_maker_image_version_alias:
                        description:
                            - The alias of the SageMaker AI image version, for example V(2.0).
                        type: str
                    instance_type:
                        description:
                            - The instance type, for example V(ml.t3.medium).
                            - The value is validated by AWS.
                        type: str
                    lifecycle_config_arn:
                        description:
                            - The ARN of the lifecycle configuration attached to the app.
                        type: str
                    training_plan_arn:
                        description:
                            - The ARN of the training plan whose reserved capacity the app uses.
                        type: str
            lifecycle_config_arns:
                description:
                    - The ARNs of the lifecycle configurations attached to the app.
                type: list
                elements: str
            code_repositories:
                description:
                    - The Git repositories cloned into the app when it starts.
                type: list
                elements: dict
                suboptions:
                    repository_url:
                        description:
                            - The URL of the Git repository.
                        type: str
                        required: true
    kernel_gateway_app_settings:
        description:
            - The settings of the kernel gateway app.
        type: dict
        suboptions:
            default_resource_spec:
                description:
                    - The instance type and SageMaker AI image that the app runs on by default.
                type: dict
                suboptions:
                    sage_maker_image_arn:
                        description:
                            - The ARN of the SageMaker AI image.
                        type: str
                    sage_maker_image_version_arn:
                        description:
                            - The ARN of the SageMaker AI image version.
                        type: str
                    sage_maker_image_version_alias:
                        description:
                            - The alias of the SageMaker AI image version, for example V(2.0).
                        type: str
                    instance_type:
                        description:
                            - The instance type, for example V(ml.t3.medium).
                            - The value is validated by AWS.
                        type: str
                    lifecycle_config_arn:
                        description:
                            - The ARN of the lifecycle configuration attached to the app.
                        type: str
                    training_plan_arn:
                        description:
                            - The ARN of the training plan whose reserved capacity the app uses.
                        type: str
            custom_images:
                description:
                    - The custom SageMaker AI images available to the app.
                type: list
                elements: dict
                suboptions:
                    image_name:
                        description:
                            - The name of the custom image.
                        type: str
                        required: true
                    image_version_number:
                        description:
                            - The version number of the custom image.
                        type: int
                    app_image_config_name:
                        description:
                            - The name of the app image configuration of the custom image.
                        type: str
                        required: true
            lifecycle_config_arns:
                description:
                    - The ARNs of the lifecycle configurations attached to the app.
                type: list
                elements: str
    tensor_board_app_settings:
        description:
            - The settings of the TensorBoard app.
        type: dict
        suboptions:
            default_resource_spec:
                description:
                    - The instance type and SageMaker AI image that the app runs on by default.
                type: dict
                suboptions:
                    sage_maker_image_arn:
                        description:
                            - The ARN of the SageMaker AI image.
                        type: str
                    sage_maker_image_version_arn:
                        description:
                            - The ARN of the SageMaker AI image version.
                        type: str
                    sage_maker_image_version_alias:
                        description:
                            - The alias of the SageMaker AI image version, for example V(2.0).
                        type: str
                    instance_type:
                        description:
                            - The instance type, for example V(ml.t3.medium).
                            - The value is validated by AWS.
                        type: str
                    lifecycle_config_arn:
                        description:
                            - The ARN of the lifecycle configuration attached to the app.
                        type: str
                    training_plan_arn:
                        description:
                            - The ARN of the training plan whose reserved capacity the app uses.
                        type: str
    r_studio_server_pro_app_settings:
        description:
            - The settings of the RStudio Server Pro app.
        type: dict
        suboptions:
            access_status:
                description:
                    - Whether the user can access RStudio.
                type: str
                choices: [ENABLED, DISABLED]
            user_group:
                description:
                    - The RStudio user group the user belongs to.
                type: str
                choices: [R_STUDIO_ADMIN, R_STUDIO_USER]
    r_session_app_settings:
        description:
            - The settings of the RSession app.
        type: dict
        suboptions:
            default_resource_spec:
                description:
                    - The instance type and SageMaker AI image that the app runs on by default.
                type: dict
                suboptions:
                    sage_maker_image_arn:
                        description:
                            - The ARN of the SageMaker AI image.
                        type: str
                    sage_maker_image_version_arn:
                        description:
                            - The ARN of the SageMaker AI image version.
                        type: str
                    sage_maker_image_version_alias:
                        description:
                            - The alias of the SageMaker AI image version, for example V(2.0).
                        type: str
                    instance_type:
                        description:
                            - The instance type, for example V(ml.t3.medium).
                            - The value is validated by AWS.
                        type: str
                    lifecycle_config_arn:
                        description:
                            - The ARN of the lifecycle configuration attached to the app.
                        type: str
                    training_plan_arn:
                        description:
                            - The ARN of the training plan whose reserved capacity the app uses.
                        type: str
            custom_images:
                description:
                    - The custom SageMaker AI images available to the app.
                type: list
                elements: dict
                suboptions:
                    image_name:
                        description:
                            - The name of the custom image.
                        type: str
                        required: true
                    image_version_number:
                        description:
                            - The version number of the custom image.
                        type: int
                    app_image_config_name:
                        description:
                            - The name of the app image configuration of the custom image.
                        type: str
                        required: true
    canvas_app_settings:
        description:
            - The settings of the SageMaker Canvas app.
        type: dict
        suboptions:
            time_series_forecasting_settings:
                description:
                    - The time series forecasting settings of Canvas.
                type: dict
                suboptions:
                    status:
                        description:
                            - Whether time series forecasting is enabled.
                        type: str
                        choices: [ENABLED, DISABLED]
                    amazon_forecast_role_arn:
                        description:
                            - The ARN of the IAM role that Canvas passes to Amazon Forecast.
                        type: str
            model_register_settings:
                description:
                    - The model registry settings of Canvas.
                type: dict
                suboptions:
                    status:
                        description:
                            - Whether models can be registered in the SageMaker AI model registry.
                        type: str
                        choices: [ENABLED, DISABLED]
                    cross_account_model_register_role_arn:
                        description:
                            - The ARN of the IAM role in the account of the model registry that Canvas assumes.
                        type: str
            workspace_settings:
                description:
                    - The workspace settings of Canvas.
                type: dict
                suboptions:
                    s3_artifact_path:
                        description:
                            - The Amazon S3 location where Canvas stores its artifacts.
                        type: str
                    s3_kms_key_id:
                        description:
                            - The ID of the AWS KMS key used to encrypt the Canvas artifacts.
                        type: str
            identity_provider_o_auth_settings:
                description:
                    - The OAuth settings of the data sources that Canvas imports data from.
                type: list
                elements: dict
                suboptions:
                    data_source_name:
                        description:
                            - The name of the data source.
                        type: str
                        choices: [SalesforceGenie, Snowflake]
                    status:
                        description:
                            - Whether OAuth is enabled for the data source.
                        type: str
                        choices: [ENABLED, DISABLED]
                    secret_arn:
                        description:
                            - The ARN of the AWS Secrets Manager secret that holds the OAuth credentials.
                        type: str
            direct_deploy_settings:
                description:
                    - The model deployment settings of Canvas.
                type: dict
                suboptions:
                    status:
                        description:
                            - Whether the user can deploy models from Canvas.
                        type: str
                        choices: [ENABLED, DISABLED]
            kendra_settings:
                description:
                    - The Amazon Kendra settings of Canvas.
                type: dict
                suboptions:
                    status:
                        description:
                            - Whether document querying with Amazon Kendra is enabled.
                        type: str
                        choices: [ENABLED, DISABLED]
            generative_ai_settings:
                description:
                    - The generative AI settings of Canvas.
                type: dict
                suboptions:
                    amazon_bedrock_role_arn:
                        description:
                            - The ARN of the IAM role that Canvas uses to fine-tune models in Amazon Bedrock.
                        type: str
            emr_serverless_settings:
                description:
                    - The Amazon EMR Serverless settings of Canvas.
                type: dict
                suboptions:
                    execution_role_arn:
                        description:
                            - The ARN of the IAM role that Canvas passes to Amazon EMR Serverless jobs.
                        type: str
                    status:
                        description:
                            - Whether Amazon EMR Serverless jobs are enabled.
                        type: str
                        choices: [ENABLED, DISABLED]
    code_editor_app_settings:
        description:
            - The settings of the Code Editor app.
        type: dict
        suboptions:
            default_resource_spec:
                description:
                    - The instance type and SageMaker AI image that the app runs on by default.
                type: dict
                suboptions:
                    sage_maker_image_arn:
                        description:
                            - The ARN of the SageMaker AI image.
                        type: str
                    sage_maker_image_version_arn:
                        description:
                            - The ARN of the SageMaker AI image version.
                        type: str
                    sage_maker_image_version_alias:
                        description:
                            - The alias of the SageMaker AI image version, for example V(2.0).
                        type: str
                    instance_type:
                        description:
                            - The instance type, for example V(ml.t3.medium).
                            - The value is validated by AWS.
                        type: str
                    lifecycle_config_arn:
                        description:
                            - The ARN of the lifecycle configuration attached to the app.
                        type: str
                    training_plan_arn:
                        description:
                            - The ARN of the training plan whose reserved capacity the app uses.
                        type: str
            custom_images:
                description:
                    - The custom SageMaker AI images available to the app.
                type: list
                elements: dict
                suboptions:
                    image_name:
                        description:
                            - The name of the custom image.
                        type: str
                        required: true
                    image_version_number:
                        description:
                            - The version number of the custom image.
                        type: int
                    app_image_config_name:
                        description:
                            - The name of the app image configuration of the custom image.
                        type: str
                        required: true
            lifecycle_config_arns:
                description:
                    - The ARNs of the lifecycle configurations attached to the app.
                type: list
                elements: str
            app_lifecycle_management:
                description:
                    - The lifecycle management settings of the app.
                type: dict
                suboptions:
                    idle_settings:
                        description:
                            - The idle shutdown settings of the app.
                        type: dict
                        suboptions:
                            lifecycle_management:
                                description:
                                    - Whether idle shutdown is activated for the app.
                                type: str
                                choices: [ENABLED, DISABLED]
                            idle_timeout_in_minutes:
                                description:
                                    - The time, in minutes, that the app can be idle before it is shut down. Between V(60) and V(525600).
                                type: int
                            min_idle_timeout_in_minutes:
                                description:
                                    - The minimum idle timeout, in minutes, that the user can set. Between V(60) and V(525600).
                                type: int
                            max_idle_timeout_in_minutes:
                                description:
                                    - The maximum idle timeout, in minutes, that the user can set. Between V(60) and V(525600).
                                type: int
            built_in_lifecycle_config_arn:
                description:
                    - The ARN of the lifecycle configuration that runs before the default lifecycle configuration.
                type: str
    jupyter_lab_app_settings:
        description:
            - The settings of the JupyterLab app.
        type: dict
        suboptions:
            default_resource_spec:
                description:
                    - The instance type and SageMaker AI image that the app runs on by default.
                type: dict
                suboptions:
                    sage_maker_image_arn:
                        description:
                            - The ARN of the SageMaker AI image.
                        type: str
                    sage_maker_image_version_arn:
                        description:
                            - The ARN of the SageMaker AI image version.
                        type: str
                    sage_maker_image_version_alias:
                        description:
                            - The alias of the SageMaker AI image version, for example V(2.0).
                        type: str
                    instance_type:
                        description:
                            - The instance type, for example V(ml.t3.medium).
                            - The value is validated by AWS.
                        type: str
                    lifecycle_config_arn:
                        description:
                            - The ARN of the lifecycle configuration attached to the app.
                        type: str
                    training_plan_arn:
                        description:
                            - The ARN of the training plan whose reserved capacity the app uses.
                        type: str
            custom_images:
                description:
                    - The custom SageMaker AI images available to the app.
                type: list
                elements: dict
                suboptions:
                    image_name:
                        description:
                            - The name of the custom image.
                        type: str
                        required: true
                    image_version_number:
                        description:
                            - The version number of the custom image.
                        type: int
                    app_image_config_name:
                        description:
                            - The name of the app image configuration of the custom image.
                        type: str
                        required: true
            lifecycle_config_arns:
                description:
                    - The ARNs of the lifecycle configurations attached to the app.
                type: list
                elements: str
            code_repositories:
                description:
                    - The Git repositories cloned into the app when it starts.
                type: list
                elements: dict
                suboptions:
                    repository_url:
                        description:
                            - The URL of the Git repository.
                        type: str
                        required: true
            app_lifecycle_management:
                description:
                    - The lifecycle management settings of the app.
                type: dict
                suboptions:
                    idle_settings:
                        description:
                            - The idle shutdown settings of the app.
                        type: dict
                        suboptions:
                            lifecycle_management:
                                description:
                                    - Whether idle shutdown is activated for the app.
                                type: str
                                choices: [ENABLED, DISABLED]
                            idle_timeout_in_minutes:
                                description:
                                    - The time, in minutes, that the app can be idle before it is shut down. Between V(60) and V(525600).
                                type: int
                            min_idle_timeout_in_minutes:
                                description:
                                    - The minimum idle timeout, in minutes, that the user can set. Between V(60) and V(525600).
                                type: int
                            max_idle_timeout_in_minutes:
                                description:
                                    - The maximum idle timeout, in minutes, that the user can set. Between V(60) and V(525600).
                                type: int
            emr_settings:
                description:
                    - The Amazon EMR settings of the app.
                type: dict
                suboptions:
                    assumable_role_arns:
                        description:
                            - The ARNs of up to 5 IAM roles the execution role can assume to reach Amazon EMR clusters in other accounts.
                        type: list
                        elements: str
                    execution_role_arns:
                        description:
                            - The ARNs of up to 5 IAM runtime roles used to connect to Amazon EMR clusters.
                        type: list
                        elements: str
            built_in_lifecycle_config_arn:
                description:
                    - The ARN of the lifecycle configuration that runs before the default lifecycle configuration.
                type: str
    space_storage_settings:
        description:
            - The default storage settings of the user's spaces.
        type: dict
        suboptions:
            default_ebs_storage_settings:
                description:
                    - The default EBS storage settings of a space.
                type: dict
                suboptions:
                    default_ebs_volume_size_in_gb:
                        description:
                            - The default size, in GB, of the EBS storage volume of a space. Between V(5) and V(16384).
                        type: int
                        required: true
                    maximum_ebs_volume_size_in_gb:
                        description:
                            - The maximum size, in GB, of the EBS storage volume of a space. Between V(5) and V(16384).
                        type: int
                        required: true
    default_landing_uri:
        description:
            - The page the user lands on when opening Studio, for example V(studio::) or V(app:JupyterServer:).
        type: str
    studio_web_portal:
        description:
            - Whether the user can access Studio.
        type: str
        choices: [ENABLED, DISABLED]
    custom_posix_user_config:
        description:
            - The POSIX identity used for file system operations.
        type: dict
        suboptions:
            uid:
                description:
                    - The POSIX user ID. Between V(10000) and V(4000000).
                type: int
                required: true
            gid:
                description:
                    - The POSIX group ID. Between V(1001) and V(4000000).
                type: int
                required: true
    custom_file_system_configs:
        description:
            - Up to 10 custom file systems available to the user's spaces.
            - Each element sets exactly one of O(custom_file_system_configs[].efs_file_system_config),
              O(custom_file_system_configs[].fsx_lustre_file_system_config) and
              O(custom_file_system_configs[].s3_file_system_config).
        type: list
        elements: dict
        suboptions:
            efs_file_system_config:
                description:
                    - An Amazon EFS file system.
                type: dict
                suboptions:
                    file_system_id:
                        description:
                            - The ID of the Amazon EFS file system.
                        type: str
                        required: true
                    file_system_path:
                        description:
                            - The path within the file system that is mounted.
                        type: str
            fsx_lustre_file_system_config:
                description:
                    - An Amazon FSx for Lustre file system.
                type: dict
                suboptions:
                    file_system_id:
                        description:
                            - The ID of the Amazon FSx for Lustre file system.
                        type: str
                        required: true
                    file_system_path:
                        description:
                            - The path within the file system that is mounted.
                        type: str
            s3_file_system_config:
                description:
                    - An Amazon S3 location.
                type: dict
                suboptions:
                    mount_path:
                        description:
                            - The path in the user's spaces where the location is mounted.
                        type: str
                    s3_uri:
                        description:
                            - The Amazon S3 URI of the location that is mounted.
                        type: str
                        required: true
    studio_web_portal_settings:
        description:
            - The settings of the Studio user interface.
        type: dict
        suboptions:
            hidden_ml_tools:
                description:
                    - The machine learning tools hidden from the Studio navigation pane.
                    - The values are validated by AWS.
                type: list
                elements: str
            hidden_app_types:
                description:
                    - The app types hidden from the Studio navigation pane.
                    - The values are validated by AWS.
                type: list
                elements: str
            hidden_instance_types:
                description:
                    - The instance types hidden from the Studio instance type list.
                    - The values are validated by AWS.
                type: list
                elements: str
            hidden_sage_maker_image_version_aliases:
                description:
                    - The SageMaker AI image version aliases hidden from Studio.
                type: list
                elements: dict
                suboptions:
                    sage_maker_image_name:
                        description:
                            - The name of the SageMaker AI image.
                        type: str
                        choices: [sagemaker_distribution]
                    version_aliases:
                        description:
                            - The version aliases to hide.
                        type: list
                        elements: str
            execution_role_session_name_mode:
                description:
                    - How the session name of the assumed execution role is set.
                type: str
                choices: [STATIC, USER_IDENTITY]
    auto_mount_home_efs:
        description:
            - Whether the home Amazon EFS file system of the domain is mounted automatically in the user's spaces.
        type: str
        choices: [Enabled, Disabled, DefaultAsDomain]
    tags:
        description:
            - Tags to associate with the user profile.
            - When omitted, the tags of the user profile are left unchanged.
        type: dict
        aliases: [resource_tags]
    purge_tags:
        description:
            - Whether to remove tags that are not specified in O(tags).
            - Has no effect when O(tags) is omitted.
        type: bool
        default: true
    wait:
        description:
            - Whether to wait for the user profile to become V(InService) after it is created or updated,
              and to be removed after it is deleted.
            - With O(wait=false) and O(state=present), the module exits without changes when the user profile is
              V(Pending) or V(Updating).
            - With O(state=absent), a user profile that is V(Pending) or V(Updating) is always waited for before it is
              deleted, because it can only be deleted once it is V(InService).
        type: bool
        default: true
    wait_timeout:
        description:
            - How long, in seconds, to wait for the user profile to reach the desired status.
        type: int
        default: 600
notes:
    - Required IAM actions include sagemaker:CreateUserProfile, sagemaker:DescribeUserProfile,
      sagemaker:UpdateUserProfile, sagemaker:DeleteUserProfile, sagemaker:ListUserProfiles,
      sagemaker:ListTags, sagemaker:AddTags, and sagemaker:DeleteTags.
    - Setting O(execution_role) or another IAM role ARN may also require iam:PassRole on that role.
    - A user profile can only be deleted after all apps and spaces it owns are deleted. This module does not delete them.
    - O(domain_id), O(user_profile_name), O(single_sign_on_user_identifier) and O(single_sign_on_user_value)
      cannot be changed on an existing user profile.
    - With O(state=present), the module fails for a user profile that is being deleted or whose creation or
      deletion failed. Use O(state=absent) to remove a failed user profile.
    - Lists of strings are compared as sets, and lists of dictionaries are compared without regard to order.
    - When a dictionary option differs, the module sends its current value merged with the supplied suboptions,
      so suboptions that are omitted keep their current value.
attributes:
    check_mode:
        description: Can run in check mode and report what would change without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_user_profile_info
      description: Gather information about SageMaker AI user profiles.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Create a user profile with the default settings of the domain
  amazon.ai.sagemaker_user_profile:
    domain_id: "d-xxxxxxxxxxxx"
    user_profile_name: "my-user"

- name: Create a user profile with custom settings and tags
  amazon.ai.sagemaker_user_profile:
    domain_id: "d-xxxxxxxxxxxx"
    user_profile_name: "my-user"
    execution_role: "arn:aws:iam::123456789012:role/SageMakerExecutionRole"
    default_landing_uri: "studio::"
    studio_web_portal: "ENABLED"
    auto_mount_home_efs: "DefaultAsDomain"
    sharing_settings:
      notebook_output_option: "Allowed"
      s3_output_path: "s3://my-bucket/sharing/"
    jupyter_lab_app_settings:
      default_resource_spec:
        instance_type: "ml.t3.medium"
      app_lifecycle_management:
        idle_settings:
          lifecycle_management: "ENABLED"
          idle_timeout_in_minutes: 120
      code_repositories:
        - repository_url: "https://github.com/example/repo.git"
    space_storage_settings:
      default_ebs_storage_settings:
        default_ebs_volume_size_in_gb: 5
        maximum_ebs_volume_size_in_gb: 100
    tags:
      team: "data-science"

- name: Change only the default JupyterLab instance type, keeping the other JupyterLab settings
  amazon.ai.sagemaker_user_profile:
    domain_id: "d-xxxxxxxxxxxx"
    user_profile_name: "my-user"
    jupyter_lab_app_settings:
      default_resource_spec:
        instance_type: "ml.m5.large"

- name: Add a tag without removing the existing ones
  amazon.ai.sagemaker_user_profile:
    domain_id: "d-xxxxxxxxxxxx"
    user_profile_name: "my-user"
    tags:
      owner: "alice"
    purge_tags: false

- name: Delete a user profile without waiting for the deletion to finish
  amazon.ai.sagemaker_user_profile:
    state: "absent"
    domain_id: "d-xxxxxxxxxxxx"
    user_profile_name: "my-user"
    wait: false
"""

RETURN = r"""
user_profile:
    description: The user profile after the operation.
    type: dict
    returned: on success when O(state=present), except when a user profile would be created in check mode or the
              module exits early because the user profile is V(Pending) or V(Updating)
    contains:
        domain_id:
            description: The ID of the domain the user profile belongs to.
            type: str
            returned: always
            sample: "d-xxxxxxxxxxxx"
        user_profile_arn:
            description: The Amazon Resource Name (ARN) of the user profile.
            type: str
            returned: always
            sample: "arn:aws:sagemaker:us-east-1:123456789012:user-profile/d-xxxxxxxxxxxx/my-user"
        user_profile_name:
            description: The name of the user profile.
            type: str
            returned: always
            sample: "my-user"
        status:
            description: The status of the user profile.
            type: str
            returned: always
            sample: "InService"
        home_efs_file_system_uid:
            description: The ID of the user's profile in the home Amazon EFS volume of the domain.
            type: str
            returned: when set
            sample: "200001"
        creation_time:
            description: The date and time the user profile was created.
            type: str
            returned: always
            sample: "2026-10-21T12:00:00.000000+00:00"
        last_modified_time:
            description: The date and time the user profile was last modified.
            type: str
            returned: always
            sample: "2026-10-21T12:05:00.000000+00:00"
        failure_reason:
            description: The reason the last operation on the user profile failed.
            type: str
            returned: when set
            sample: "The execution role could not be assumed."
        single_sign_on_user_identifier:
            description: The IAM Identity Center user attribute that identifies the user.
            type: str
            returned: when set
            sample: "UserName"
        single_sign_on_user_value:
            description: The user name of the IAM Identity Center user.
            type: str
            returned: when set
            sample: "alice"
        user_settings:
            description:
                - The settings of the user profile, the C(UserSettings) structure of the SageMaker AI API.
                - Each member has the same nested shape as the module option of the same name, for example O(jupyter_lab_app_settings).
            type: dict
            returned: on success when set
            contains:
                execution_role:
                    description: The ARN of the IAM role that the user's apps and jobs run as.
                    type: str
                    returned: when set
                    sample: "arn:aws:iam::123456789012:role/SageMakerExecutionRole"
                security_groups:
                    description: The IDs of up to 5 security groups for the Amazon VPC that the domain uses for communication.
                    type: list
                    elements: str
                    returned: when set
                    sample: ["sg-0123456789abcdef0"]
                sharing_settings:
                    description: How notebooks are shared.
                    type: dict
                    returned: when set
                    contains:
                        notebook_output_option:
                            description: Whether to include the notebook cell output when a notebook is shared.
                            type: str
                            returned: when set
                            sample: "Allowed"
                        s3_output_path:
                            description: The Amazon S3 location where shared notebook snapshots are stored.
                            type: str
                            returned: when set
                            sample: "s3://my-bucket/sharing/"
                        s3_kms_key_id:
                            description: The ID of the AWS KMS key used to encrypt the shared notebook snapshots.
                            type: str
                            returned: when set
                            sample: "arn:aws:kms:us-east-1:123456789012:key/0123abcd-01ab-23cd-45ef-0123456789ab"
                jupyter_server_app_settings:
                    description: The settings of the Jupyter server app.
                    type: dict
                    returned: when set
                    contains:
                        default_resource_spec:
                            description: The instance type and SageMaker AI image that the app runs on by default.
                            type: dict
                            returned: when set
                            contains:
                                sage_maker_image_arn:
                                    description: The ARN of the SageMaker AI image.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:image/my-image"
                                sage_maker_image_version_arn:
                                    description: The ARN of the SageMaker AI image version.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:image-version/my-image/1"
                                sage_maker_image_version_alias:
                                    description: The alias of the SageMaker AI image version, for example V(2.0).
                                    type: str
                                    returned: when set
                                    sample: "2.0"
                                instance_type:
                                    description: The instance type, for example V(ml.t3.medium).
                                    type: str
                                    returned: when set
                                    sample: "ml.t3.medium"
                                lifecycle_config_arn:
                                    description: The ARN of the lifecycle configuration attached to the app.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:studio-lifecycle-config/my-config"
                                training_plan_arn:
                                    description: The ARN of the training plan whose reserved capacity the app uses.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:training-plan/my-plan"
                        lifecycle_config_arns:
                            description: The ARNs of the lifecycle configurations attached to the app.
                            type: list
                            elements: str
                            returned: when set
                            sample: ["arn:aws:sagemaker:us-east-1:123456789012:studio-lifecycle-config/my-config"]
                        code_repositories:
                            description: The Git repositories cloned into the app when it starts.
                            type: list
                            elements: dict
                            returned: when set
                            contains:
                                repository_url:
                                    description: The URL of the Git repository.
                                    type: str
                                    returned: when set
                                    sample: "https://github.com/my-org/my-repo.git"
                kernel_gateway_app_settings:
                    description: The settings of the kernel gateway app.
                    type: dict
                    returned: when set
                    contains:
                        default_resource_spec:
                            description: The instance type and SageMaker AI image that the app runs on by default.
                            type: dict
                            returned: when set
                            contains:
                                sage_maker_image_arn:
                                    description: The ARN of the SageMaker AI image.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:image/my-image"
                                sage_maker_image_version_arn:
                                    description: The ARN of the SageMaker AI image version.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:image-version/my-image/1"
                                sage_maker_image_version_alias:
                                    description: The alias of the SageMaker AI image version, for example V(2.0).
                                    type: str
                                    returned: when set
                                    sample: "2.0"
                                instance_type:
                                    description: The instance type, for example V(ml.t3.medium).
                                    type: str
                                    returned: when set
                                    sample: "ml.t3.medium"
                                lifecycle_config_arn:
                                    description: The ARN of the lifecycle configuration attached to the app.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:studio-lifecycle-config/my-config"
                                training_plan_arn:
                                    description: The ARN of the training plan whose reserved capacity the app uses.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:training-plan/my-plan"
                        custom_images:
                            description: The custom SageMaker AI images available to the app.
                            type: list
                            elements: dict
                            returned: when set
                            contains:
                                image_name:
                                    description: The name of the custom image.
                                    type: str
                                    returned: when set
                                    sample: "my-image"
                                image_version_number:
                                    description: The version number of the custom image.
                                    type: int
                                    returned: when set
                                    sample: 1
                                app_image_config_name:
                                    description: The name of the app image configuration of the custom image.
                                    type: str
                                    returned: when set
                                    sample: "my-app-image-config"
                        lifecycle_config_arns:
                            description: The ARNs of the lifecycle configurations attached to the app.
                            type: list
                            elements: str
                            returned: when set
                            sample: ["arn:aws:sagemaker:us-east-1:123456789012:studio-lifecycle-config/my-config"]
                tensor_board_app_settings:
                    description: The settings of the TensorBoard app.
                    type: dict
                    returned: when set
                    contains:
                        default_resource_spec:
                            description: The instance type and SageMaker AI image that the app runs on by default.
                            type: dict
                            returned: when set
                            contains:
                                sage_maker_image_arn:
                                    description: The ARN of the SageMaker AI image.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:image/my-image"
                                sage_maker_image_version_arn:
                                    description: The ARN of the SageMaker AI image version.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:image-version/my-image/1"
                                sage_maker_image_version_alias:
                                    description: The alias of the SageMaker AI image version, for example V(2.0).
                                    type: str
                                    returned: when set
                                    sample: "2.0"
                                instance_type:
                                    description: The instance type, for example V(ml.t3.medium).
                                    type: str
                                    returned: when set
                                    sample: "ml.t3.medium"
                                lifecycle_config_arn:
                                    description: The ARN of the lifecycle configuration attached to the app.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:studio-lifecycle-config/my-config"
                                training_plan_arn:
                                    description: The ARN of the training plan whose reserved capacity the app uses.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:training-plan/my-plan"
                r_studio_server_pro_app_settings:
                    description: The settings of the RStudio Server Pro app.
                    type: dict
                    returned: when set
                    contains:
                        access_status:
                            description: Whether the user can access RStudio.
                            type: str
                            returned: when set
                            sample: "ENABLED"
                        user_group:
                            description: The RStudio user group the user belongs to.
                            type: str
                            returned: when set
                            sample: "R_STUDIO_USER"
                r_session_app_settings:
                    description: The settings of the RSession app.
                    type: dict
                    returned: when set
                    contains:
                        default_resource_spec:
                            description: The instance type and SageMaker AI image that the app runs on by default.
                            type: dict
                            returned: when set
                            contains:
                                sage_maker_image_arn:
                                    description: The ARN of the SageMaker AI image.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:image/my-image"
                                sage_maker_image_version_arn:
                                    description: The ARN of the SageMaker AI image version.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:image-version/my-image/1"
                                sage_maker_image_version_alias:
                                    description: The alias of the SageMaker AI image version, for example V(2.0).
                                    type: str
                                    returned: when set
                                    sample: "2.0"
                                instance_type:
                                    description: The instance type, for example V(ml.t3.medium).
                                    type: str
                                    returned: when set
                                    sample: "ml.t3.medium"
                                lifecycle_config_arn:
                                    description: The ARN of the lifecycle configuration attached to the app.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:studio-lifecycle-config/my-config"
                                training_plan_arn:
                                    description: The ARN of the training plan whose reserved capacity the app uses.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:training-plan/my-plan"
                        custom_images:
                            description: The custom SageMaker AI images available to the app.
                            type: list
                            elements: dict
                            returned: when set
                            contains:
                                image_name:
                                    description: The name of the custom image.
                                    type: str
                                    returned: when set
                                    sample: "my-image"
                                image_version_number:
                                    description: The version number of the custom image.
                                    type: int
                                    returned: when set
                                    sample: 1
                                app_image_config_name:
                                    description: The name of the app image configuration of the custom image.
                                    type: str
                                    returned: when set
                                    sample: "my-app-image-config"
                canvas_app_settings:
                    description: The settings of the SageMaker Canvas app.
                    type: dict
                    returned: when set
                    contains:
                        time_series_forecasting_settings:
                            description: The time series forecasting settings of Canvas.
                            type: dict
                            returned: when set
                            contains:
                                status:
                                    description: Whether time series forecasting is enabled.
                                    type: str
                                    returned: when set
                                    sample: "ENABLED"
                                amazon_forecast_role_arn:
                                    description: The ARN of the IAM role that Canvas passes to Amazon Forecast.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:iam::123456789012:role/CanvasForecastRole"
                        model_register_settings:
                            description: The model registry settings of Canvas.
                            type: dict
                            returned: when set
                            contains:
                                status:
                                    description: Whether models can be registered in the SageMaker AI model registry.
                                    type: str
                                    returned: when set
                                    sample: "ENABLED"
                                cross_account_model_register_role_arn:
                                    description: The ARN of the IAM role in the account of the model registry that Canvas assumes.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:iam::123456789012:role/CanvasModelRegisterRole"
                        workspace_settings:
                            description: The workspace settings of Canvas.
                            type: dict
                            returned: when set
                            contains:
                                s3_artifact_path:
                                    description: The Amazon S3 location where Canvas stores its artifacts.
                                    type: str
                                    returned: when set
                                    sample: "s3://my-bucket/canvas/"
                                s3_kms_key_id:
                                    description: The ID of the AWS KMS key used to encrypt the Canvas artifacts.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:kms:us-east-1:123456789012:key/0123abcd-01ab-23cd-45ef-0123456789ab"
                        identity_provider_o_auth_settings:
                            description: The OAuth settings of the data sources that Canvas imports data from.
                            type: list
                            elements: dict
                            returned: when set
                            contains:
                                data_source_name:
                                    description: The name of the data source.
                                    type: str
                                    returned: when set
                                    sample: "Snowflake"
                                status:
                                    description: Whether OAuth is enabled for the data source.
                                    type: str
                                    returned: when set
                                    sample: "ENABLED"
                                secret_arn:
                                    description: The ARN of the AWS Secrets Manager secret that holds the OAuth credentials.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret"
                        direct_deploy_settings:
                            description: The model deployment settings of Canvas.
                            type: dict
                            returned: when set
                            contains:
                                status:
                                    description: Whether the user can deploy models from Canvas.
                                    type: str
                                    returned: when set
                                    sample: "ENABLED"
                        kendra_settings:
                            description: The Amazon Kendra settings of Canvas.
                            type: dict
                            returned: when set
                            contains:
                                status:
                                    description: Whether document querying with Amazon Kendra is enabled.
                                    type: str
                                    returned: when set
                                    sample: "ENABLED"
                        generative_ai_settings:
                            description: The generative AI settings of Canvas.
                            type: dict
                            returned: when set
                            contains:
                                amazon_bedrock_role_arn:
                                    description: The ARN of the IAM role that Canvas uses to fine-tune models in Amazon Bedrock.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:iam::123456789012:role/CanvasBedrockRole"
                        emr_serverless_settings:
                            description: The Amazon EMR Serverless settings of Canvas.
                            type: dict
                            returned: when set
                            contains:
                                execution_role_arn:
                                    description: The ARN of the IAM role that Canvas passes to Amazon EMR Serverless jobs.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:iam::123456789012:role/CanvasEmrServerlessRole"
                                status:
                                    description: Whether Amazon EMR Serverless jobs are enabled.
                                    type: str
                                    returned: when set
                                    sample: "ENABLED"
                code_editor_app_settings:
                    description: The settings of the Code Editor app.
                    type: dict
                    returned: when set
                    contains:
                        default_resource_spec:
                            description: The instance type and SageMaker AI image that the app runs on by default.
                            type: dict
                            returned: when set
                            contains:
                                sage_maker_image_arn:
                                    description: The ARN of the SageMaker AI image.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:image/my-image"
                                sage_maker_image_version_arn:
                                    description: The ARN of the SageMaker AI image version.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:image-version/my-image/1"
                                sage_maker_image_version_alias:
                                    description: The alias of the SageMaker AI image version, for example V(2.0).
                                    type: str
                                    returned: when set
                                    sample: "2.0"
                                instance_type:
                                    description: The instance type, for example V(ml.t3.medium).
                                    type: str
                                    returned: when set
                                    sample: "ml.t3.medium"
                                lifecycle_config_arn:
                                    description: The ARN of the lifecycle configuration attached to the app.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:studio-lifecycle-config/my-config"
                                training_plan_arn:
                                    description: The ARN of the training plan whose reserved capacity the app uses.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:training-plan/my-plan"
                        custom_images:
                            description: The custom SageMaker AI images available to the app.
                            type: list
                            elements: dict
                            returned: when set
                            contains:
                                image_name:
                                    description: The name of the custom image.
                                    type: str
                                    returned: when set
                                    sample: "my-image"
                                image_version_number:
                                    description: The version number of the custom image.
                                    type: int
                                    returned: when set
                                    sample: 1
                                app_image_config_name:
                                    description: The name of the app image configuration of the custom image.
                                    type: str
                                    returned: when set
                                    sample: "my-app-image-config"
                        lifecycle_config_arns:
                            description: The ARNs of the lifecycle configurations attached to the app.
                            type: list
                            elements: str
                            returned: when set
                            sample: ["arn:aws:sagemaker:us-east-1:123456789012:studio-lifecycle-config/my-config"]
                        app_lifecycle_management:
                            description: The lifecycle management settings of the app.
                            type: dict
                            returned: when set
                            contains:
                                idle_settings:
                                    description: The idle shutdown settings of the app.
                                    type: dict
                                    returned: when set
                                    contains:
                                        lifecycle_management:
                                            description: Whether idle shutdown is activated for the app.
                                            type: str
                                            returned: when set
                                            sample: "ENABLED"
                                        idle_timeout_in_minutes:
                                            description: The time, in minutes, that the app can be idle before it is shut down. Between V(60) and V(525600).
                                            type: int
                                            returned: when set
                                            sample: 120
                                        min_idle_timeout_in_minutes:
                                            description: The minimum idle timeout, in minutes, that the user can set. Between V(60) and V(525600).
                                            type: int
                                            returned: when set
                                            sample: 60
                                        max_idle_timeout_in_minutes:
                                            description: The maximum idle timeout, in minutes, that the user can set. Between V(60) and V(525600).
                                            type: int
                                            returned: when set
                                            sample: 240
                        built_in_lifecycle_config_arn:
                            description: The ARN of the lifecycle configuration that runs before the default lifecycle configuration.
                            type: str
                            returned: when set
                            sample: "arn:aws:sagemaker:us-east-1:123456789012:studio-lifecycle-config/my-built-in-config"
                jupyter_lab_app_settings:
                    description: The settings of the JupyterLab app.
                    type: dict
                    returned: when set
                    contains:
                        default_resource_spec:
                            description: The instance type and SageMaker AI image that the app runs on by default.
                            type: dict
                            returned: when set
                            contains:
                                sage_maker_image_arn:
                                    description: The ARN of the SageMaker AI image.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:image/my-image"
                                sage_maker_image_version_arn:
                                    description: The ARN of the SageMaker AI image version.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:image-version/my-image/1"
                                sage_maker_image_version_alias:
                                    description: The alias of the SageMaker AI image version, for example V(2.0).
                                    type: str
                                    returned: when set
                                    sample: "2.0"
                                instance_type:
                                    description: The instance type, for example V(ml.t3.medium).
                                    type: str
                                    returned: when set
                                    sample: "ml.t3.medium"
                                lifecycle_config_arn:
                                    description: The ARN of the lifecycle configuration attached to the app.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:studio-lifecycle-config/my-config"
                                training_plan_arn:
                                    description: The ARN of the training plan whose reserved capacity the app uses.
                                    type: str
                                    returned: when set
                                    sample: "arn:aws:sagemaker:us-east-1:123456789012:training-plan/my-plan"
                        custom_images:
                            description: The custom SageMaker AI images available to the app.
                            type: list
                            elements: dict
                            returned: when set
                            contains:
                                image_name:
                                    description: The name of the custom image.
                                    type: str
                                    returned: when set
                                    sample: "my-image"
                                image_version_number:
                                    description: The version number of the custom image.
                                    type: int
                                    returned: when set
                                    sample: 1
                                app_image_config_name:
                                    description: The name of the app image configuration of the custom image.
                                    type: str
                                    returned: when set
                                    sample: "my-app-image-config"
                        lifecycle_config_arns:
                            description: The ARNs of the lifecycle configurations attached to the app.
                            type: list
                            elements: str
                            returned: when set
                            sample: ["arn:aws:sagemaker:us-east-1:123456789012:studio-lifecycle-config/my-config"]
                        code_repositories:
                            description: The Git repositories cloned into the app when it starts.
                            type: list
                            elements: dict
                            returned: when set
                            contains:
                                repository_url:
                                    description: The URL of the Git repository.
                                    type: str
                                    returned: when set
                                    sample: "https://github.com/my-org/my-repo.git"
                        app_lifecycle_management:
                            description: The lifecycle management settings of the app.
                            type: dict
                            returned: when set
                            contains:
                                idle_settings:
                                    description: The idle shutdown settings of the app.
                                    type: dict
                                    returned: when set
                                    contains:
                                        lifecycle_management:
                                            description: Whether idle shutdown is activated for the app.
                                            type: str
                                            returned: when set
                                            sample: "ENABLED"
                                        idle_timeout_in_minutes:
                                            description: The time, in minutes, that the app can be idle before it is shut down. Between V(60) and V(525600).
                                            type: int
                                            returned: when set
                                            sample: 120
                                        min_idle_timeout_in_minutes:
                                            description: The minimum idle timeout, in minutes, that the user can set. Between V(60) and V(525600).
                                            type: int
                                            returned: when set
                                            sample: 60
                                        max_idle_timeout_in_minutes:
                                            description: The maximum idle timeout, in minutes, that the user can set. Between V(60) and V(525600).
                                            type: int
                                            returned: when set
                                            sample: 240
                        emr_settings:
                            description: The Amazon EMR settings of the app.
                            type: dict
                            returned: when set
                            contains:
                                assumable_role_arns:
                                    description: The ARNs of up to 5 IAM roles the execution role can assume to reach Amazon EMR clusters in other accounts.
                                    type: list
                                    elements: str
                                    returned: when set
                                    sample: ["arn:aws:iam::123456789012:role/EmrAssumableRole"]
                                execution_role_arns:
                                    description: The ARNs of up to 5 IAM runtime roles used to connect to Amazon EMR clusters.
                                    type: list
                                    elements: str
                                    returned: when set
                                    sample: ["arn:aws:iam::123456789012:role/EmrRuntimeRole"]
                        built_in_lifecycle_config_arn:
                            description: The ARN of the lifecycle configuration that runs before the default lifecycle configuration.
                            type: str
                            returned: when set
                            sample: "arn:aws:sagemaker:us-east-1:123456789012:studio-lifecycle-config/my-built-in-config"
                space_storage_settings:
                    description: The default storage settings of the user's spaces.
                    type: dict
                    returned: when set
                    contains:
                        default_ebs_storage_settings:
                            description: The default EBS storage settings of a space.
                            type: dict
                            returned: when set
                            contains:
                                default_ebs_volume_size_in_gb:
                                    description: The default size, in GB, of the EBS storage volume of a space. Between V(5) and V(16384).
                                    type: int
                                    returned: when set
                                    sample: 5
                                maximum_ebs_volume_size_in_gb:
                                    description: The maximum size, in GB, of the EBS storage volume of a space. Between V(5) and V(16384).
                                    type: int
                                    returned: when set
                                    sample: 100
                default_landing_uri:
                    description: The page the user lands on when opening Studio, for example V(studio::) or V(app:JupyterServer:).
                    type: str
                    returned: when set
                    sample: "studio::"
                studio_web_portal:
                    description: Whether the user can access Studio.
                    type: str
                    returned: when set
                    sample: "ENABLED"
                custom_posix_user_config:
                    description: The POSIX identity used for file system operations.
                    type: dict
                    returned: when set
                    contains:
                        uid:
                            description: The POSIX user ID. Between V(10000) and V(4000000).
                            type: int
                            returned: when set
                            sample: 10000
                        gid:
                            description: The POSIX group ID. Between V(1001) and V(4000000).
                            type: int
                            returned: when set
                            sample: 1001
                custom_file_system_configs:
                    description: Up to 10 custom file systems available to the user's spaces.
                    type: list
                    elements: dict
                    returned: when set
                    contains:
                        efs_file_system_config:
                            description: An Amazon EFS file system.
                            type: dict
                            returned: when set
                            contains:
                                file_system_id:
                                    description: The ID of the Amazon EFS file system.
                                    type: str
                                    returned: when set
                                    sample: "fs-0123456789abcdef0"
                                file_system_path:
                                    description: The path within the file system that is mounted.
                                    type: str
                                    returned: when set
                                    sample: "/"
                        fsx_lustre_file_system_config:
                            description: An Amazon FSx for Lustre file system.
                            type: dict
                            returned: when set
                            contains:
                                file_system_id:
                                    description: The ID of the Amazon FSx for Lustre file system.
                                    type: str
                                    returned: when set
                                    sample: "fs-0123456789abcdef0"
                                file_system_path:
                                    description: The path within the file system that is mounted.
                                    type: str
                                    returned: when set
                                    sample: "/"
                        s3_file_system_config:
                            description: An Amazon S3 location.
                            type: dict
                            returned: when set
                            contains:
                                mount_path:
                                    description: The path in the user's spaces where the location is mounted.
                                    type: str
                                    returned: when set
                                    sample: "/mnt/data"
                                s3_uri:
                                    description: The Amazon S3 URI of the location that is mounted.
                                    type: str
                                    returned: when set
                                    sample: "s3://my-bucket/data/"
                studio_web_portal_settings:
                    description: The settings of the Studio user interface.
                    type: dict
                    returned: when set
                    contains:
                        hidden_ml_tools:
                            description: The machine learning tools hidden from the Studio navigation pane.
                            type: list
                            elements: str
                            returned: when set
                            sample: ["DataWrangler"]
                        hidden_app_types:
                            description: The app types hidden from the Studio navigation pane.
                            type: list
                            elements: str
                            returned: when set
                            sample: ["JupyterServer"]
                        hidden_instance_types:
                            description: The instance types hidden from the Studio instance type list.
                            type: list
                            elements: str
                            returned: when set
                            sample: ["ml.p4d.24xlarge"]
                        hidden_sage_maker_image_version_aliases:
                            description: The SageMaker AI image version aliases hidden from Studio.
                            type: list
                            elements: dict
                            returned: when set
                            contains:
                                sage_maker_image_name:
                                    description: The name of the SageMaker AI image.
                                    type: str
                                    returned: when set
                                    sample: "sagemaker_distribution"
                                version_aliases:
                                    description: The version aliases to hide.
                                    type: list
                                    elements: str
                                    returned: when set
                                    sample: ["1.0"]
                        execution_role_session_name_mode:
                            description: How the session name of the assumed execution role is set.
                            type: str
                            returned: when set
                            sample: "STATIC"
                auto_mount_home_efs:
                    description: Whether the home Amazon EFS file system of the domain is mounted automatically in the user's spaces.
                    type: str
                    returned: when set
                    sample: "DefaultAsDomain"
        tags:
            description: The tags of the user profile.
            type: dict
            returned: always
            sample:
                team: "data-science"
    sample:
        domain_id: "d-xxxxxxxxxxxx"
        user_profile_arn: "arn:aws:sagemaker:us-east-1:123456789012:user-profile/d-xxxxxxxxxxxx/my-user"
        user_profile_name: "my-user"
        status: "InService"
        home_efs_file_system_uid: "200001"
        creation_time: "2026-10-21T12:00:00.000000+00:00"
        last_modified_time: "2026-10-21T12:05:00.000000+00:00"
        user_settings:
            execution_role: "arn:aws:iam::123456789012:role/SageMakerExecutionRole"
            jupyter_lab_app_settings:
                default_resource_spec:
                    instance_type: "ml.t3.medium"
                app_lifecycle_management:
                    idle_settings:
                        idle_timeout_in_minutes: 120
                        lifecycle_management: "ENABLED"
        tags:
            team: "data-science"
msg:
    description: A message describing what the module did, or would have done in check mode.
    type: str
    returned: always
    sample: "Created user profile my-user in domain d-xxxxxxxxxxxx."
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import UserProfileStatus
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_user_profile
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_user_profile
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_user_profile
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import ensure_user_profile_create_only_unchanged
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import format_user_profile
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_user_profile_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_user_profile
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import user_settings_to_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_user_profile_status

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

_ENABLED_DISABLED = ["ENABLED", "DISABLED"]

_DEFAULT_RESOURCE_SPEC_OPTION = dict(
    type="dict",
    options=dict(
        sage_maker_image_arn=dict(type="str"),
        sage_maker_image_version_arn=dict(type="str"),
        sage_maker_image_version_alias=dict(type="str"),
        instance_type=dict(type="str"),
        lifecycle_config_arn=dict(type="str"),
        training_plan_arn=dict(type="str"),
    ),
)

_APP_LIFECYCLE_MANAGEMENT_OPTION = dict(
    type="dict",
    options=dict(
        idle_settings=dict(
            type="dict",
            options=dict(
                lifecycle_management=dict(type="str", choices=_ENABLED_DISABLED),
                idle_timeout_in_minutes=dict(type="int"),
                min_idle_timeout_in_minutes=dict(type="int"),
                max_idle_timeout_in_minutes=dict(type="int"),
            ),
        ),
    ),
)

_CUSTOM_IMAGES_OPTION = dict(
    type="list",
    elements="dict",
    options=dict(
        image_name=dict(type="str", required=True),
        image_version_number=dict(type="int"),
        app_image_config_name=dict(type="str", required=True),
    ),
)

_CODE_REPOSITORIES_OPTION = dict(
    type="list",
    elements="dict",
    options=dict(repository_url=dict(type="str", required=True)),
)

_FILE_SYSTEM_OPTIONS = dict(
    file_system_id=dict(type="str", required=True),
    file_system_path=dict(type="str"),
)

_FILE_SYSTEM_CONFIG_KEYS = ["efs_file_system_config", "fsx_lustre_file_system_config", "s3_file_system_config"]


def _status_option() -> Dict[str, Any]:
    return dict(type="dict", options=dict(status=dict(type="str", choices=_ENABLED_DISABLED)))


def _user_settings_options() -> Dict[str, Any]:
    """The UserSettings members as top-level options, mirroring the API structure."""
    return dict(
        execution_role=dict(type="str"),
        security_groups=dict(type="list", elements="str"),
        sharing_settings=dict(
            type="dict",
            options=dict(
                notebook_output_option=dict(type="str", choices=["Allowed", "Disabled"]),
                s3_output_path=dict(type="str"),
                s3_kms_key_id=dict(type="str"),
            ),
        ),
        jupyter_server_app_settings=dict(
            type="dict",
            options=dict(
                default_resource_spec=_DEFAULT_RESOURCE_SPEC_OPTION,
                lifecycle_config_arns=dict(type="list", elements="str"),
                code_repositories=_CODE_REPOSITORIES_OPTION,
            ),
        ),
        kernel_gateway_app_settings=dict(
            type="dict",
            options=dict(
                default_resource_spec=_DEFAULT_RESOURCE_SPEC_OPTION,
                custom_images=_CUSTOM_IMAGES_OPTION,
                lifecycle_config_arns=dict(type="list", elements="str"),
            ),
        ),
        tensor_board_app_settings=dict(
            type="dict",
            options=dict(default_resource_spec=_DEFAULT_RESOURCE_SPEC_OPTION),
        ),
        r_studio_server_pro_app_settings=dict(
            type="dict",
            options=dict(
                access_status=dict(type="str", choices=_ENABLED_DISABLED),
                user_group=dict(type="str", choices=["R_STUDIO_ADMIN", "R_STUDIO_USER"]),
            ),
        ),
        r_session_app_settings=dict(
            type="dict",
            options=dict(
                default_resource_spec=_DEFAULT_RESOURCE_SPEC_OPTION,
                custom_images=_CUSTOM_IMAGES_OPTION,
            ),
        ),
        canvas_app_settings=dict(
            type="dict",
            options=dict(
                time_series_forecasting_settings=dict(
                    type="dict",
                    options=dict(
                        status=dict(type="str", choices=_ENABLED_DISABLED),
                        amazon_forecast_role_arn=dict(type="str"),
                    ),
                ),
                model_register_settings=dict(
                    type="dict",
                    options=dict(
                        status=dict(type="str", choices=_ENABLED_DISABLED),
                        cross_account_model_register_role_arn=dict(type="str"),
                    ),
                ),
                workspace_settings=dict(
                    type="dict",
                    options=dict(
                        s3_artifact_path=dict(type="str"),
                        s3_kms_key_id=dict(type="str"),
                    ),
                ),
                identity_provider_o_auth_settings=dict(
                    type="list",
                    elements="dict",
                    options=dict(
                        data_source_name=dict(type="str", choices=["SalesforceGenie", "Snowflake"]),
                        status=dict(type="str", choices=_ENABLED_DISABLED),
                        secret_arn=dict(type="str", no_log=False),
                    ),
                ),
                direct_deploy_settings=_status_option(),
                kendra_settings=_status_option(),
                generative_ai_settings=dict(
                    type="dict",
                    options=dict(amazon_bedrock_role_arn=dict(type="str")),
                ),
                emr_serverless_settings=dict(
                    type="dict",
                    options=dict(
                        execution_role_arn=dict(type="str"),
                        status=dict(type="str", choices=_ENABLED_DISABLED),
                    ),
                ),
            ),
        ),
        code_editor_app_settings=dict(
            type="dict",
            options=dict(
                default_resource_spec=_DEFAULT_RESOURCE_SPEC_OPTION,
                custom_images=_CUSTOM_IMAGES_OPTION,
                lifecycle_config_arns=dict(type="list", elements="str"),
                app_lifecycle_management=_APP_LIFECYCLE_MANAGEMENT_OPTION,
                built_in_lifecycle_config_arn=dict(type="str"),
            ),
        ),
        jupyter_lab_app_settings=dict(
            type="dict",
            options=dict(
                default_resource_spec=_DEFAULT_RESOURCE_SPEC_OPTION,
                custom_images=_CUSTOM_IMAGES_OPTION,
                lifecycle_config_arns=dict(type="list", elements="str"),
                code_repositories=_CODE_REPOSITORIES_OPTION,
                app_lifecycle_management=_APP_LIFECYCLE_MANAGEMENT_OPTION,
                emr_settings=dict(
                    type="dict",
                    options=dict(
                        assumable_role_arns=dict(type="list", elements="str"),
                        execution_role_arns=dict(type="list", elements="str"),
                    ),
                ),
                built_in_lifecycle_config_arn=dict(type="str"),
            ),
        ),
        space_storage_settings=dict(
            type="dict",
            options=dict(
                default_ebs_storage_settings=dict(
                    type="dict",
                    options=dict(
                        default_ebs_volume_size_in_gb=dict(type="int", required=True),
                        maximum_ebs_volume_size_in_gb=dict(type="int", required=True),
                    ),
                ),
            ),
        ),
        default_landing_uri=dict(type="str"),
        studio_web_portal=dict(type="str", choices=_ENABLED_DISABLED),
        custom_posix_user_config=dict(
            type="dict",
            options=dict(
                uid=dict(type="int", required=True),
                gid=dict(type="int", required=True),
            ),
        ),
        custom_file_system_configs=dict(
            type="list",
            elements="dict",
            options=dict(
                efs_file_system_config=dict(type="dict", options=_FILE_SYSTEM_OPTIONS),
                fsx_lustre_file_system_config=dict(type="dict", options=_FILE_SYSTEM_OPTIONS),
                s3_file_system_config=dict(
                    type="dict",
                    options=dict(
                        mount_path=dict(type="str"),
                        s3_uri=dict(type="str", required=True),
                    ),
                ),
            ),
            mutually_exclusive=[_FILE_SYSTEM_CONFIG_KEYS],
            required_one_of=[_FILE_SYSTEM_CONFIG_KEYS],
        ),
        studio_web_portal_settings=dict(
            type="dict",
            options=dict(
                hidden_ml_tools=dict(type="list", elements="str"),
                hidden_app_types=dict(type="list", elements="str"),
                hidden_instance_types=dict(type="list", elements="str"),
                hidden_sage_maker_image_version_aliases=dict(
                    type="list",
                    elements="dict",
                    options=dict(
                        sage_maker_image_name=dict(type="str", choices=["sagemaker_distribution"]),
                        version_aliases=dict(type="list", elements="str"),
                    ),
                ),
                execution_role_session_name_mode=dict(type="str", choices=["STATIC", "USER_IDENTITY"]),
            ),
        ),
        auto_mount_home_efs=dict(type="str", choices=["Enabled", "Disabled", "DefaultAsDomain"]),
    )


def _label(module) -> str:
    return f"User profile {module.params['user_profile_name']} in domain {module.params['domain_id']}"


def _get_user_profile(client, module, with_tags: bool = False) -> Optional[Dict[str, Any]]:
    profile = describe_user_profile(client, module.params["domain_id"], module.params["user_profile_name"])
    if profile is None:
        return None
    tags = list_tags(client, profile["UserProfileArn"]) if with_tags else None
    return format_user_profile(profile, tags=tags)


def _user_profile_status_check(client, module, existing: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Handle a user profile that is mid-transition or failed, before any diff is computed.

    Returns the profile to act on, re-described after any wait so that callers never act on a stale
    snapshot; None when the profile does not exist.
    """
    if existing:
        status = existing.get("status")
        present = module.params["state"] == "present"
        domain_id = module.params["domain_id"]
        user_profile_name = module.params["user_profile_name"]

        if status in (
            UserProfileStatus.IN_SERVICE,
            UserProfileStatus.UPDATE_FAILED,
            UserProfileStatus.DELETE_FAILED,
            UserProfileStatus.FAILED,
        ):
            return existing

        if module.check_mode:
            module.exit_json(
                changed=False,
                msg=f"User profile {user_profile_name} in domain {domain_id} is currently in {status} state (check mode).",
                user_profile={},
            )

        if not module.params["wait"]:
            module.exit_json(
                changed=False,
                msg=f"User profile {user_profile_name} in domain {domain_id} is currently in {status} state (not waiting).",
                user_profile={},
            )

        if status == UserProfileStatus.DELETING:
            wait_for_user_profile_status(client, module, domain_id, user_profile_name, True)
            if not present:
                module.exit_json(
                    changed=False,
                    msg=f"User profile {user_profile_name} in domain {domain_id} is deleted.",
                    user_profile={},
                )
        elif status in (UserProfileStatus.PENDING, UserProfileStatus.UPDATING):
            wait_for_user_profile_status(client, module, domain_id, user_profile_name)

        # Refresh the user profile information after waiting for the status change
        existing = _get_user_profile(client, module)

    return existing


def _absent(client, module, existing: Optional[Dict[str, Any]]) -> None:
    changed = False
    msg = f"{_label(module)} does not exist."
    if existing:
        changed, msg = delete_user_profile(client, module)
    module.exit_json(changed=changed, msg=msg, user_profile={})


def _present(client, module, existing: Optional[Dict[str, Any]]) -> None:
    if existing is None:
        changed, msg = create_user_profile(client, module)
        if module.check_mode:
            module.exit_json(changed=changed, msg=msg, user_profile={})
        module.exit_json(changed=changed, msg=msg, user_profile=_get_user_profile(client, module, with_tags=True))
    else:
        ensure_user_profile_create_only_unchanged(module, existing)
        settings_changed, msg = update_user_profile(client, module, user_settings_to_update(module, existing))
        tags_changed = reconcile_user_profile_tags(client, module, existing["user_profile_arn"])

        if not settings_changed:
            if not tags_changed:
                msg = f"{_label(module)} is already in the desired state."
            elif module.check_mode:
                msg = f"Check mode: would have updated the tags of {_label(module)}."
            else:
                msg = f"Updated the tags of {_label(module)}."

        module.exit_json(
            changed=settings_changed or tags_changed,
            msg=msg,
            user_profile=_get_user_profile(client, module, with_tags=True),
        )


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        domain_id=dict(type="str", required=True),
        user_profile_name=dict(type="str", required=True, aliases=["name"]),
        single_sign_on_user_identifier=dict(type="str", choices=["UserName"]),
        single_sign_on_user_value=dict(type="str"),
        **_user_settings_options(),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_together=[("single_sign_on_user_identifier", "single_sign_on_user_value")],
        supports_check_mode=True,
    )

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing = _get_user_profile(client, module)
        existing = _user_profile_status_check(client, module, existing)
        if module.params["state"] == "absent":
            _absent(client, module, existing)
        _present(client, module, existing)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
