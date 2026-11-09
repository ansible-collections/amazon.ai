#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_user_profile_info
short_description: Gather information about Amazon SageMaker AI user profiles
version_added: "2.0.0"
author:
    - Domen Dobnikar (@domendobnikar)
description:
    - Retrieves one Amazon SageMaker AI user profile by domain ID and name, or lists user profiles with optional filters.
    - Every listed user profile is described, so the result holds the full settings of each user profile.
    - Each member of the returned user settings has the same nested shape as the option of the same name of
      M(amazon.ai.sagemaker_user_profile).
    - Tags are not returned. Use M(amazon.ai.sagemaker_user_profile) to manage them.
options:
    domain_id:
        description:
            - The ID of the domain the user profiles belong to.
            - Required with O(user_profile_name).
            - When omitted, user profiles of all domains are listed.
        type: str
    user_profile_name:
        description:
            - The exact name of the user profile to retrieve.
            - Requires O(domain_id).
            - When omitted, user profiles are listed.
        type: str
        aliases: [name]
    user_profile_name_contains:
        description:
            - Only list user profiles whose name contains this string.
            - Mutually exclusive with O(user_profile_name).
        type: str
    sort_by:
        description:
            - The field to sort the listed user profiles by.
            - Ignored when O(user_profile_name) is set.
        type: str
        choices: [CreationTime, LastModifiedTime]
    sort_order:
        description:
            - The order to sort the listed user profiles in.
            - Ignored when O(user_profile_name) is set.
        type: str
        choices: [Ascending, Descending]
notes:
    - Required IAM actions include sagemaker:DescribeUserProfile and sagemaker:ListUserProfiles.
    - A user profile that does not exist is not an error. The module returns an empty list instead.
attributes:
    check_mode:
        description: Can run in check mode without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_user_profile
      description: Manage SageMaker AI user profiles.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Get a user profile
  amazon.ai.sagemaker_user_profile_info:
    domain_id: "d-xxxxxxxxxxxx"
    user_profile_name: "my-user"

- name: List the user profiles of a domain, most recently modified first
  amazon.ai.sagemaker_user_profile_info:
    domain_id: "d-xxxxxxxxxxxx"
    sort_by: "LastModifiedTime"
    sort_order: "Descending"

- name: List the user profiles of all domains whose name contains "data"
  amazon.ai.sagemaker_user_profile_info:
    user_profile_name_contains: "data"
"""

RETURN = r"""
user_profiles:
    description:
        - The matching user profiles.
        - Empty when no user profile matches.
    type: list
    elements: dict
    returned: always
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
                - Each member has the same nested shape as the option of the same name of M(amazon.ai.sagemaker_user_profile).
            type: dict
            returned: when set
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
    sample:
        - domain_id: "d-xxxxxxxxxxxx"
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
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_user_profile
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import format_user_profile
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_user_profiles

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _get_user_profiles(client, module) -> List[Dict[str, Any]]:
    params = module.params
    if params.get("user_profile_name"):
        found = describe_user_profile(client, params["domain_id"], params["user_profile_name"])
        return [found] if found else []

    summaries = list_user_profiles(
        client,
        domain_id=params.get("domain_id"),
        user_profile_name_contains=params.get("user_profile_name_contains"),
        sort_by=params.get("sort_by"),
        sort_order=params.get("sort_order"),
    )
    # A profile deleted between the list and the describe call is skipped.
    return [
        profile
        for summary in summaries
        if (profile := describe_user_profile(client, summary["DomainId"], summary["UserProfileName"])) is not None
    ]


def main() -> None:
    argument_spec = dict(
        domain_id=dict(type="str"),
        user_profile_name=dict(type="str", aliases=["name"]),
        user_profile_name_contains=dict(type="str"),
        sort_by=dict(type="str", choices=["CreationTime", "LastModifiedTime"]),
        sort_order=dict(type="str", choices=["Ascending", "Descending"]),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_by=dict(user_profile_name="domain_id"),
        mutually_exclusive=[("user_profile_name", "user_profile_name_contains")],
        supports_check_mode=True,
    )

    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        user_profiles = _get_user_profiles(client, module)
        module.exit_json(changed=False, user_profiles=[format_user_profile(profile) for profile in user_profiles])
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
