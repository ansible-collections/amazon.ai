=======================
amazon.ai Release Notes
=======================

.. contents:: Topics

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

- amazon.ai.bedrock_agent - Manage Amazon Bedrock Agents
- amazon.ai.bedrock_agent_action_group - Manage Amazon Bedrock Agent Action Groups
- amazon.ai.bedrock_agent_action_group_info - Gather information about a Bedrock Agent's Action Groups
- amazon.ai.bedrock_agent_alias - Manage Amazon Bedrock Agent Aliases
- amazon.ai.bedrock_agent_alias_info - Gather information about a Bedrock Agent's Aliases
- amazon.ai.bedrock_agent_info - Gather information about Bedrock Agents
- amazon.ai.bedrock_foundation_models_info - List or get details for Amazon Bedrock foundation models
- amazon.ai.bedrock_invoke_agent - Invoke an Amazon Bedrock agent with a prompt
- amazon.ai.bedrock_invoke_model - Run inference using Amazon Bedrock models
- amazon.ai.devopsguru_insight_info - Fetch information about Amazon DevOps Guru insights
- amazon.ai.devopsguru_resource_collection - Manage DevOps Guru resource collections
- amazon.ai.devopsguru_resource_collection_info - Fetch information about Amazon DevOps Guru resource collection
