#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: devopsguru_insight_info
short_description: Fetches information about Amazon DevOps Guru insights
version_added: 1.0.0
description:
    - Fetches information about Amazon DevOps Guru insights.
options:
    status_filter:
        description:
            - A dict of filters to apply.
            - You can specify which insights are returned by their start time and status (ONGOING, CLOSED, or ANY).
            - See U(https://docs.aws.amazon.com/devops-guru/latest/APIReference/API_ListInsightsStatusFilter.html).
        type: dict
        aliases: ["filter"]
    account_id:
        description:
            - The ID of the Amazon Web Services account.
        type: str
    insight_id:
        description:
            - The ID of the insight.
        type: str
    include_anomalies:
        description:
            - Dictionary for getting insight's anomalies.
        type: dict
        suboptions:
            start_time_range:
                description:
                    - A time range used to specify when the requested anomalies started.
                    - All returned anomalies started during this time range.
                type: dict
                suboptions:
                    from_time:
                        description:
                            - The start time of the time range.
                        type: str
                    to_time:
                        description:
                            - The end time of the time range.
                        type: str
            filters:
                description:
                    - Specifies one or more service names that are used to list anomalies.
                type: dict
                suboptions:
                    service_collection:
                        description:
                            - A collection of the names of Amazon Web Services services.
                        type: dict
                        suboptions:
                            service_names:
                                description:
                                    - An array of strings that each specifies the name of an Amazon Web Services service.
                                type: list
                                elements: str
                                choices:
                                    - "API_GATEWAY"
                                    - "APPLICATION_ELB"
                                    - "AUTO_SCALING_GROUP"
                                    - "CLOUD_FRONT"
                                    - "DYNAMO_DB"
                                    - "EC2"
                                    - "ECS"
                                    - "EKS"
                                    - "ELASTIC_BEANSTALK"
                                    - "ELASTI_CACHE"
                                    - "ELB"
                                    - "ES"
                                    - "KINESIS"
                                    - "LAMBDA"
                                    - "NAT_GATEWAY"
                                    - "NETWORK_ELB"
                                    - "RDS"
                                    - "REDSHIFT"
                                    - "ROUTE_53"
                                    - "S3"
                                    - "SAGE_MAKER"
                                    - "SNS"
                                    - "SQS"
                                    - "STEP_FUNCTIONS"
                                    - "SWF"
    include_recommendations:
        description:
            - Dictionary for getting insight's recommendations.
        type: dict
        suboptions:
            locale:
                description:
                    - A locale that specifies the language to use for recommendations.
                type: str
                choices:
                    - 'DE_DE'
                    - 'EN_US'
                    - 'EN_GB'
                    - 'ES_ES'
                    - 'FR_FR'
                    - 'IT_IT'
                    - 'JA_JP'
                    - 'KO_KR'
                    - 'PT_BR'
                    - 'ZH_CN'
                    - 'ZH_TW'

extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
author:
    - Alina Buzachis (@alinabuzachis)
"""


EXAMPLES = r"""
- name: Gather information about DevOpsGuru Resource Insights
  amazon.ai.devopsguru_insight_info:
    status_filter:
      any:
        type: 'REACTIVE'
        start_time_range:
          from_time: "2025-02-10"
          to_time: "2025-02-12"

- name: Gather information about DevOpsGuru Resource Insights including recommendations and anomalies
  amazon.ai.devopsguru_insight_info:
    status_filter:
      closed:
        type: 'REACTIVE'
        end_time_range:
          from_time: "2025-03-04"
          to_time: "2025-03-06"
    include_recommendations:
      locale: EN_US
    include_anomalies:
      filters:
        service_collection:
          service_names:
            - RDS

- name: Gather information about a specific DevOpsGuru Insight
  amazon.ai.devopsguru_insight_info:
    insight_id: "{{ insight_id }}"
    include_recommendations:
      locale: EN_US
    include_anomalies:
      filters:
        service_collection:
          service_names:
            - RDS
"""

RETURN = r"""
proactive_insight:
    description: Details about a proactive insight (predictive alerts) returned by Amazon DevOps Guru.
    returned: when the specified or filtered insight is proactive
    type: dict
    contains:
        id:
            description: The unique identifier of the proactive insight.
            type: str
            sample: "abcdef12-3456-7890-abcd-ef1234567890"
        name:
            description: The name assigned to the insight by DevOps Guru.
            type: str
            sample: "high_rds_latency_predicted"
        severity:
            description: The severity level of the insight.
            type: str
            sample: "high"
        status:
            description: The current status of the insight.
            type: str
            sample: "ongoing"
        insight_time_range:
            description: The time period during which the insight is active.
            type: dict
            contains:
                start_time:
                    description: When the insight started.
                    type: str
                    sample: "2025-02-10T12:34:56Z"
                end_time:
                    description: When the insight ended, or null if ongoing.
                    type: str
                    sample: null
        prediction_time_range:
            description: The predicted start and end times for the potential issue.
            type: dict
            contains:
                start_time:
                    description: Start of the prediction range.
                    type: str
                    sample: "2025-02-10T12:00:00Z"
                end_time:
                    description: End of the prediction range.
                    type: str
                    sample: "2025-02-11T12:00:00Z"
        resource_collection:
            description: The collection of AWS resources analyzed for this insight.
            type: dict
            contains:
                service:
                    description: Services involved in the insight.
                    type: dict
                    contains:
                        service_names:
                            description: List of service names.
                            type: list
                            elements: str
                            sample: ["rds", "ec2"]
        ssm_ops_items:
            description: Related AWS Systems Manager OpsItem IDs created for this insight.
            type: list
            elements: str
            sample: ["ops-item-1234abcd"]
        anomalies:
            description: A list of anomalies related to this insight (returned when include_anomalies is specified).
            type: list
            elements: dict
            contains:
                id:
                    description: Unique identifier for the anomaly.
                    type: str
                    sample: "anomaly-1234"
                start_time:
                    description: When the anomaly began.
                    type: str
                    sample: "2025-02-10T12:30:00Z"
                end_time:
                    description: When the anomaly ended, if applicable.
                    type: str
                    sample: "2025-02-10T13:00:00Z"
                source_details:
                    description: Information about the service and metrics causing the anomaly.
                    type: dict
                    sample:
                        service_name: "rds"
                        metric_name: "cpu_utilization"
        recommendations:
            description: A list of recommendations to address the predicted issue (returned when include_recommendations is specified).
            type: list
            elements: dict
            contains:
                name:
                    description: The name/title of the recommendation.
                    type: str
                    sample: "optimize_database_connections"
                description:
                    description: Details about the recommended action.
                    type: str
                    sample: "review connection pooling and query optimization to avoid saturation."
                link:
                    description: URL to AWS documentation or relevant troubleshooting guide.
                    type: str
                    sample: "https://docs.aws.amazon.com/devops-guru/latest/advice/rds-connection-optimization.html"

reactive_insight:
    description: Details about a reactive insight (detected after an operational issue occurs).
    returned: when the specified or filtered insight is reactive
    type: dict
    contains:
        id:
            description: The unique identifier of the reactive insight.
            type: str
            sample: "fedcba98-7654-3210-abcd-ef9876543210"
        name:
            description: The name assigned to the insight by DevOps Guru.
            type: str
            sample: "high_latency_detected_on_api_gateway"
        severity:
            description: The severity level of the insight.
            type: str
            sample: "medium"
        status:
            description: The current status of the insight.
            type: str
            sample: "closed"
        insight_time_range:
            description: The time period during which the insight was active.
            type: dict
            contains:
                start_time:
                    description: When the issue was first detected.
                    type: str
                    sample: "2025-03-04T10:15:00Z"
                end_time:
                    description: When the issue ended.
                    type: str
                    sample: "2025-03-04T11:45:00Z"
        resource_collection:
            description: The set of AWS resources impacted by this insight.
            type: dict
            contains:
                cloud_formation:
                    description: Affected CloudFormation stack names.
                    type: dict
                    contains:
                        stack_names:
                            description:
                                - List of CloudFormation stack names associated with the reactive insight.
                            type: list
                            elements: str
                            sample: ["api-stack"]
        ssm_ops_items:
            description: Related AWS Systems Manager OpsItem IDs created for this insight.
            type: list
            elements: str
            sample: ["ops-item-5678abcd"]
        anomalies:
            description: A list of anomalies related to this reactive issue.
            type: list
            elements: dict
            sample:
                - id: "anomaly-5678"
                  start_time: "2025-03-04T10:00:00Z"
                  end_time: "2025-03-04T10:30:00Z"
                  source_details:
                      service_name: "api_gateway"
                      metric_name: "latency"
        recommendations:
            description: A list of recommendations to resolve or prevent future occurrences of this issue.
            type: list
            elements: dict
            sample:
                - name: "check_backend_integrations"
                  description: "investigate slow responses from backend lambda functions."
                  link: "https://docs.aws.amazon.com/devops-guru/latest/advice/api-gateway-latency.html"
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.ai.plugins.module_utils.devopsguru import describe_insight
from ansible_collections.amazon.ai.plugins.module_utils.devopsguru import fetch_data
from ansible_collections.amazon.ai.plugins.module_utils.devopsguru import get_insight_type
from ansible_collections.amazon.ai.plugins.module_utils.utils import convert_time_ranges
from ansible_collections.amazon.ai.plugins.module_utils.utils import merge_data

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main() -> None:
    argument_spec = dict(
        status_filter=dict(type="dict", aliases=["filter"]),
        account_id=dict(type="str"),
        insight_id=dict(type="str"),
        include_anomalies=dict(type="dict"),
        include_recommendations=dict(type="dict"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[("status_filter", "insight_id")],
    )

    try:
        client = module.client("devops-guru", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    status_filter = module.params.get("status_filter")
    account_id = module.params.get("account_id")
    insight_id = module.params.get("insight_id")
    include_anomalies = module.params.get("include_anomalies")
    include_recommendations = module.params.get("include_recommendations")

    if status_filter:
        status_filter = convert_time_ranges(snake_dict_to_camel_dict(status_filter, capitalize_first=True))

    try:
        insight_info = (
            describe_insight(client, insight_id, account_id)
            if insight_id
            else fetch_data(client, "list_insights", StatusFilter=status_filter)
        )
        insight_type = get_insight_type(insight_info)
        if insight_type:
            data_to_fetch = {
                "anomalies": (
                    include_anomalies,
                    "fetch_data",
                    "list_anomalies_for_insight",
                ),
                "recommendations": (
                    include_recommendations,
                    "fetch_data",
                    "list_recommendations",
                ),
            }

            for data_type, (
                include_flag,
                fetch_func,
                api_call,
            ) in data_to_fetch.items():
                if include_flag:
                    params = {}
                    if account_id:
                        params["AccountId"] = account_id

                    if data_type == "anomalies":
                        if include_flag.get("filters"):
                            params["Filters"] = {
                                "ServiceCollection": {
                                    "ServiceNames": include_flag["filters"]["service_collection"]["service_names"]
                                }
                            }
                        if include_flag.get("start_time_range"):
                            params["StartTimeRange"] = include_flag["start_time_range"]

                    if data_type == "recommendations":
                        params["Locale"] = include_flag["locale"]

                    if isinstance(insight_info[insight_type], dict):
                        params["InsightId"] = insight_info[insight_type]["Id"]
                        fetched_data = globals()[fetch_func](client, api_call, **params)
                        merge_data(insight_info[insight_type], fetched_data)
                    elif isinstance(insight_info[insight_type], list):
                        for insight in insight_info[insight_type]:
                            params["InsightId"] = insight["Id"]
                            fetched_data = globals()[fetch_func](client, api_call, **params)
                            merge_data(insight, fetched_data)

        module.exit_json(**camel_dict_to_snake_dict(insight_info))

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
