=======================
amazon.ai Release Notes
=======================

.. contents:: Topics

v2.0.0
======

Release Summary
---------------

amazon.ai 2.0.0 is a major release featuring extensive automation coverage for AWS AI/ML infrastructure and modernized platform dependencies:

* **Amazon SageMaker Suite:** Comprehensive lifecycle support across SageMaker AI Domains, Spaces, User Profiles, Notebook Instances, Lifecycle Configurations, Training Jobs, Pipelines, Models, and Endpoints.
* **Amazon Bedrock AgentCore:** Added management and info modules for Bedrock AgentCore runtimes and runtime endpoints.
* **Platform & Dependency Updates:** Raised minimum requirements to `ansible-core >= 2.18.0` and `boto3` / `botocore >= 1.38.0`.

Breaking Changes / Porting Guide
--------------------------------

- Collection - Minimum supported boto3 version is now 1.38.0 (https://github.com/ansible-collections/amazon.ai/pull/75).
- Collection - Minimum supported botocore version is now 1.38.0 (https://github.com/ansible-collections/amazon.ai/pull/75).
- Support for ansible-core < 2.18 has been dropped. The collection now requires ansible-core >= 2.18.0 (https://github.com/ansible-collections/amazon.ai/pull/77).

New Modules
-----------

- amazon.ai.bedrock_agentcore_runtime - Manage Amazon Bedrock AgentCore runtimes.
- amazon.ai.bedrock_agentcore_runtime_endpoint - Manage Amazon Bedrock AgentCore runtime endpoints.
- amazon.ai.bedrock_agentcore_runtime_endpoint_info - Gather information about Bedrock AgentCore runtime endpoints.
- amazon.ai.bedrock_agentcore_runtime_info - Gather information about Bedrock AgentCore runtimes.
- amazon.ai.sagemaker_app_image_config - Manage Amazon SageMaker AppImageConfigs.
- amazon.ai.sagemaker_app_image_config_info - Gather information about Amazon SageMaker AppImageConfigs.
- amazon.ai.sagemaker_domain - Manage Amazon SageMaker AI Domains.
- amazon.ai.sagemaker_domain_info - Gather information about SageMaker AI Domains.
- amazon.ai.sagemaker_endpoint - Manage Amazon SageMaker endpoints.
- amazon.ai.sagemaker_endpoint_config - Manage Amazon SageMaker endpoint configurations.
- amazon.ai.sagemaker_endpoint_config_info - Gather information about SageMaker endpoint configurations.
- amazon.ai.sagemaker_endpoint_info - Gather information about SageMaker endpoints.
- amazon.ai.sagemaker_image - Manage Amazon SageMaker Images.
- amazon.ai.sagemaker_image_info - Gather information about SageMaker Images.
- amazon.ai.sagemaker_image_version - Manage Amazon SageMaker Image Versions.
- amazon.ai.sagemaker_image_version_info - Gather information about SageMaker Image Versions.
- amazon.ai.sagemaker_model - Manage Amazon SageMaker Models.
- amazon.ai.sagemaker_model_info - Gather information about Amazon SageMaker Models.
- amazon.ai.sagemaker_model_package - Manage Amazon SageMaker model packages.
- amazon.ai.sagemaker_model_package_group - Manage Amazon SageMaker Model Package Groups.
- amazon.ai.sagemaker_model_package_group_info - Gather information about Amazon SageMaker Model Package Groups.
- amazon.ai.sagemaker_model_package_info - Gather information about Amazon SageMaker Model Packages.
- amazon.ai.sagemaker_notebook_instance - Manage Amazon SageMaker notebook instances.
- amazon.ai.sagemaker_notebook_instance_info - Gather information about SageMaker notebook instances.
- amazon.ai.sagemaker_notebook_instance_lifecycle_config - Manage Amazon SageMaker notebook instance lifecycle configurations.
- amazon.ai.sagemaker_notebook_instance_lifecycle_config_info - Gather information about Amazon SageMaker notebook instance lifecycle configurations.
- amazon.ai.sagemaker_pipeline - Manage Amazon SageMaker Pipelines.
- amazon.ai.sagemaker_pipeline_info - Gather information about Amazon SageMaker Pipelines.
- amazon.ai.sagemaker_space - Manage Amazon SageMaker AI Spaces.
- amazon.ai.sagemaker_space_info - Gather information about SageMaker AI Spaces.
- amazon.ai.sagemaker_training_job - Manage Amazon SageMaker training jobs.
- amazon.ai.sagemaker_training_job_info - Gather information about SageMaker training jobs.
- amazon.ai.sagemaker_user_profile - Manage Amazon SageMaker AI user profiles.
- amazon.ai.sagemaker_user_profile_info - Gather information about Amazon SageMaker AI user profiles.

v1.1.0
======

Release Summary
---------------

This minor release adds the ``sagemaker_code_repository`` modules and announces deprecation of the Amazon Bedrock Classic modules, ``bedrock_invoke_agent``, and Python 3.9 support.

Deprecated Features
-------------------

- Collection - Support for Python 3.9 is deprecated and will be removed in a release after 2027-04-01, following AWS SDK for Python's end of support for Python 3.9 in April 2026 (https://github.com/ansible-collections/amazon.ai/pull/76).
- bedrock_agent - Deprecated due to AWS Bedrock Agents Classic entering maintenance mode. New agent creation via this module is restricted by AWS to accounts with prior service usage. Use updated Bedrock AgentCore services/modules where available (https://github.com/ansible-collections/amazon.ai/pull/78).
- bedrock_agent_action_group - Deprecated due to AWS Bedrock Agents Classic entering maintenance mode. New agent creation via this module is restricted by AWS to accounts with prior service usage. Use updated Bedrock AgentCore services/modules where available (https://github.com/ansible-collections/amazon.ai/pull/78).
- bedrock_agent_action_group_info - Deprecated due to AWS Bedrock Agents Classic entering maintenance mode. New agent creation via this module is restricted by AWS to accounts with prior service usage. Use updated Bedrock AgentCore services/modules where available (https://github.com/ansible-collections/amazon.ai/pull/78).
- bedrock_agent_alias - Deprecated due to AWS Bedrock Agents Classic entering maintenance mode. New agent creation via this module is restricted by AWS to accounts with prior service usage. Use updated Bedrock AgentCore services/modules where available (https://github.com/ansible-collections/amazon.ai/pull/78).
- bedrock_agent_alias_info - Deprecated due to AWS Bedrock Agents Classic entering maintenance mode. New agent creation via this module is restricted by AWS to accounts with prior service usage. Use updated Bedrock AgentCore services/modules where available (https://github.com/ansible-collections/amazon.ai/pull/78).
- bedrock_agent_info - Deprecated due to AWS Bedrock Agents Classic entering maintenance mode. New agent creation via this module is restricted by AWS to accounts with prior service usage. Use updated Bedrock AgentCore services/modules where available (https://github.com/ansible-collections/amazon.ai/pull/78).
- bedrock_invoke_agent - Deprecated due to AWS Bedrock Agents Classic entering maintenance mode. New agent creation via this module is restricted by AWS to accounts with prior service usage. Use updated Bedrock AgentCore services/modules where available (https://github.com/ansible-collections/amazon.ai/pull/82).

New Modules
-----------

- amazon.ai.sagemaker_code_repository - Manage Amazon SageMaker Code Repositories.
- amazon.ai.sagemaker_code_repository_info - Gather information about SageMaker Code Repositories.

v1.0.1
======

Release Summary
---------------

This patch release includes bugfixes for the ``devopsguru_resource_collection`` module(s).

Bugfixes
--------

- devopsguru_resource_collection - Fix devopsguru_resource_collection module correctly handle notification channels.

v1.0.0
======

Release Summary
---------------

This is the first release of the ``amazon.ai`` collection, featuring several modules designed for Amazon DevOps Guru and Amazon Bedrock integration.

New Modules
-----------

- amazon.ai.bedrock_agent - Manage Amazon Bedrock Agents.
- amazon.ai.bedrock_agent_action_group - Manage Amazon Bedrock Agent Action Groups.
- amazon.ai.bedrock_agent_action_group_info - Gather information about a Bedrock Agent's Action Groups.
- amazon.ai.bedrock_agent_alias - Manage Amazon Bedrock Agent Aliases.
- amazon.ai.bedrock_agent_alias_info - Gather information about a Bedrock Agent's Aliases.
- amazon.ai.bedrock_agent_info - Gather information about Bedrock Agents.
- amazon.ai.bedrock_foundation_models_info - List or get details for Amazon Bedrock foundation models.
- amazon.ai.bedrock_invoke_agent - Invoke an Amazon Bedrock agent with a prompt.
- amazon.ai.bedrock_invoke_model - Run inference using Amazon Bedrock models.
- amazon.ai.devopsguru_insight_info - Fetch information about Amazon DevOps Guru insights.
- amazon.ai.devopsguru_resource_collection - Manage DevOps Guru resource collections.
- amazon.ai.devopsguru_resource_collection_info - Fetch information about Amazon DevOps Guru resource collection.
