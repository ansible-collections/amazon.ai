#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_feature_group_info
short_description: Gather information about Amazon SageMaker Feature Store feature groups
version_added: "2.0.0"
author:
    - Matej Artač (@matejart)
description:
    - Retrieve one feature group by name, or list feature groups matching filters.
    - Each feature group is returned with its full description and its tags.
options:
    feature_group_name:
        description:
            - The name of the feature group to retrieve.
            - Cannot be combined with O(name_contains), O(feature_group_status_equals), O(offline_store_status_equals),
              O(creation_time_after), O(creation_time_before), O(sort_by), O(sort_order) or O(max_results).
        type: str
        aliases: [name]
    name_contains:
        description: Only include feature groups whose name contains this string.
        type: str
    feature_group_status_equals:
        description: Only include feature groups with this status.
        type: str
        choices: [Creating, Created, CreateFailed, Deleting, DeleteFailed]
    offline_store_status_equals:
        description: Only include feature groups whose offline store has this status.
        type: str
        choices: [Active, Blocked, Disabled]
    creation_time_after:
        description: Only include feature groups created after this time.
        type: str
    creation_time_before:
        description: Only include feature groups created before this time.
        type: str
    sort_by:
        description: The field to sort by.
        type: str
        choices: [Name, FeatureGroupStatus, OfflineStoreStatus, CreationTime]
    sort_order:
        description: The sort order.
        type: str
        choices: [Ascending, Descending]
    max_results:
        description: The maximum number of feature groups to return.
        type: int
notes:
    - Required IAM actions include sagemaker:DescribeFeatureGroup, sagemaker:ListFeatureGroups and sagemaker:ListTags.
attributes:
    check_mode:
        description: Can run in check mode and return information without changing anything.
        support: full
seealso:
    - module: amazon.ai.sagemaker_feature_group
      description: Manage SageMaker feature groups.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Get a feature group by name
  amazon.ai.sagemaker_feature_group_info:
    feature_group_name: customers

- name: List created feature groups whose name contains "customer"
  amazon.ai.sagemaker_feature_group_info:
    name_contains: customer
    feature_group_status_equals: Created
    sort_by: CreationTime
    sort_order: Descending
"""

RETURN = r"""
feature_groups:
    description: The matching feature groups; an empty list when none match.
    type: list
    elements: dict
    returned: always
    contains:
        feature_group_arn:
            description: The ARN of the feature group.
            returned: always
            type: str
            sample: arn:aws:sagemaker:eu-north-1:123456789012:feature-group/customers
        feature_group_name:
            description: The name of the feature group.
            returned: always
            type: str
            sample: customers
        record_identifier_feature_name:
            description: The name of the feature that identifies a record.
            returned: always
            type: str
            sample: customer_id
        event_time_feature_name:
            description: The name of the feature that stores the event time.
            returned: always
            type: str
            sample: event_time
        feature_definitions:
            description: The features of the feature group.
            returned: always
            type: list
            elements: dict
            sample: [{"feature_name": "customer_id", "feature_type": "String"}]
            contains:
                feature_name:
                    description: The name of the feature.
                    returned: always
                    type: str
                    sample: customer_id
                feature_type:
                    description: The data type of the feature.
                    returned: always
                    type: str
                    sample: String
                collection_type:
                    description: The collection type of the feature, if it is a collection.
                    returned: when the feature is a collection
                    type: str
                    sample: Vector
                collection_config:
                    description: Configuration of a collection feature.
                    returned: when the feature is a collection
                    type: dict
                    sample: {"vector_config": {"dimension": 4}}
                    contains:
                        vector_config:
                            description: Configuration of a vector collection.
                            returned: when the collection type is Vector
                            type: dict
                            sample: {"dimension": 4}
                            contains:
                                dimension:
                                    description: The number of elements in the vector.
                                    returned: when the collection type is Vector
                                    type: int
                                    sample: 4
        creation_time:
            description: When the feature group was created.
            returned: always
            type: str
            sample: "2026-10-22T12:14:10.298000+02:00"
        last_modified_time:
            description: When the feature group was last modified.
            returned: when the feature group was modified
            type: str
            sample: "2026-10-22T12:14:55.083000+02:00"
        online_store_config:
            description: Configuration of the online store.
            returned: when the online store is configured
            type: dict
            sample: {"enable_online_store": true, "storage_type": "Standard", "ttl_duration": {"unit": "Hours", "value": 2}}
            contains:
                security_config:
                    description: Security configuration of the online store.
                    returned: when a KMS key is configured for the online store
                    type: dict
                    sample: {"kms_key_id": "1234abcd-12ab-34cd-56ef-1234567890ab"}
                    contains:
                        kms_key_id:
                            description: The KMS key ID used to encrypt the online store.
                            returned: when a KMS key is configured for the online store
                            type: str
                            sample: "1234abcd-12ab-34cd-56ef-1234567890ab"
                enable_online_store:
                    description: Whether the online store is enabled.
                    returned: when the online store is configured
                    type: bool
                    sample: true
                ttl_duration:
                    description: The time to live duration of records in the online store.
                    returned: when a TTL is configured
                    type: dict
                    sample: {"unit": "Hours", "value": 2}
                    contains:
                        unit:
                            description: The unit of the TTL duration.
                            returned: when a TTL is configured
                            type: str
                            sample: Hours
                        value:
                            description: The value of the TTL duration.
                            returned: when a TTL is configured
                            type: int
                            sample: 2
                storage_type:
                    description: The storage type of the online store.
                    returned: when the online store is configured
                    type: str
                    sample: Standard
        offline_store_config:
            description: Configuration of the offline store, including the resolved S3 output URI.
            returned: when the offline store is configured
            type: dict
            sample: {"s3_storage_config": {"s3_uri": "s3://my-sagemaker-bucket/feature-store"}, "disable_glue_table_creation": true}
            contains:
                s3_storage_config:
                    description: The Amazon S3 location of the offline store.
                    returned: always
                    type: dict
                    sample: {"s3_uri": "s3://my-sagemaker-bucket/feature-store"}
                    contains:
                        s3_uri:
                            description: The S3 URI of the offline store.
                            returned: always
                            type: str
                            sample: s3://my-sagemaker-bucket/feature-store
                        kms_key_id:
                            description: The KMS key ID used to encrypt the offline store.
                            returned: when a KMS key is configured
                            type: str
                            sample: "1234abcd-12ab-34cd-56ef-1234567890ab"
                        resolved_output_s3_uri:
                            description: The S3 path where the offline store data is written.
                            returned: when the offline store has been created
                            type: str
                            sample: s3://my-sagemaker-bucket/feature-store/123456789012/sagemaker/eu-north-1/offline-store/customers-1792663961/data
                disable_glue_table_creation:
                    description: Whether the Glue table creation is disabled.
                    returned: when the offline store is configured
                    type: bool
                    sample: true
                data_catalog_config:
                    description: The Glue Data Catalog the offline store table is registered in.
                    returned: when a data catalog is configured
                    type: dict
                    sample: {"table_name": "customers", "catalog": "AwsDataCatalog", "database": "sagemaker_featurestore"}
                    contains:
                        table_name:
                            description: The name of the Glue table.
                            returned: when a data catalog is configured
                            type: str
                            sample: customers
                        catalog:
                            description: The name of the Glue catalog.
                            returned: when a data catalog is configured
                            type: str
                            sample: AwsDataCatalog
                        database:
                            description: The name of the Glue database.
                            returned: when a data catalog is configured
                            type: str
                            sample: sagemaker_featurestore
                table_format:
                    description: The table format of the offline store.
                    returned: when the table format is reported
                    type: str
                    sample: Glue
        throughput_config:
            description: The throughput mode and provisioned capacity units.
            returned: when a throughput configuration is reported
            type: dict
            sample: {"throughput_mode": "OnDemand"}
            contains:
                throughput_mode:
                    description: The throughput mode, OnDemand or Provisioned.
                    returned: always
                    type: str
                    sample: OnDemand
                provisioned_read_capacity_units:
                    description: The provisioned read capacity units.
                    returned: when the throughput mode is Provisioned
                    type: int
                    sample: 10
                provisioned_write_capacity_units:
                    description: The provisioned write capacity units.
                    returned: when the throughput mode is Provisioned
                    type: int
                    sample: 10
        role_arn:
            description: The ARN of the IAM role used by the offline store.
            returned: when the offline store is configured
            type: str
            sample: arn:aws:iam::123456789012:role/FeatureStoreRole
        feature_group_status:
            description: The status of the feature group.
            returned: always
            type: str
            sample: Created
        offline_store_status:
            description: The status of the offline store and the reason it is blocked, if it is.
            returned: when the offline store is configured
            type: dict
            sample: {"status": "Active"}
            contains:
                status:
                    description: The status of the offline store.
                    returned: always
                    type: str
                    sample: Active
                blocked_reason:
                    description: The reason the offline store is blocked.
                    returned: when the offline store is blocked
                    type: str
                    sample: "Offline store blocked: the KMS key is not accessible"
        last_update_status:
            description: The status of the last asynchronous update and its failure reason, if it failed.
            returned: when the feature group has been updated
            type: dict
            sample: {"status": "Successful"}
            contains:
                status:
                    description: The status of the last update.
                    returned: always
                    type: str
                    sample: Successful
                failure_reason:
                    description: The reason the last update failed.
                    returned: when the last update failed
                    type: str
                    sample: Access denied
        failure_reason:
            description: Why the feature group failed to be created or deleted.
            returned: when the feature group creation or deletion failed
            type: str
            sample: Access denied
        description:
            description: The description of the feature group.
            returned: when a description is set
            type: str
            sample: Customer features
        online_store_total_size_bytes:
            description: The size of the online store in bytes.
            returned: when the online store is configured
            type: int
            sample: 0
        tags:
            description: The tags of the feature group.
            returned: always
            type: dict
            sample: {"team": "ml"}
"""

try:
    import botocore
except ImportError:
    pass

from typing import Any
from typing import Dict

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_feature_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_feature_group_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_feature_groups

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters

LIST_FILTERS = (
    "name_contains",
    "feature_group_status_equals",
    "offline_store_status_equals",
    "creation_time_after",
    "creation_time_before",
    "sort_by",
    "sort_order",
    "max_results",
)


def _with_tags(client, feature_group: Dict[str, Any]) -> Dict[str, Any]:
    result = camel_dict_to_snake_dict(feature_group, ignore_list=["Tags", "tags"])
    result["tags"] = list_feature_group_tags(client, feature_group["FeatureGroupArn"])
    return result


def main() -> None:
    argument_spec = dict(
        feature_group_name=dict(type="str", aliases=["name"]),
        name_contains=dict(type="str"),
        feature_group_status_equals=dict(
            type="str", choices=["Creating", "Created", "CreateFailed", "Deleting", "DeleteFailed"]
        ),
        offline_store_status_equals=dict(type="str", choices=["Active", "Blocked", "Disabled"]),
        creation_time_after=dict(type="str"),
        creation_time_before=dict(type="str"),
        sort_by=dict(type="str", choices=["Name", "FeatureGroupStatus", "OfflineStoreStatus", "CreationTime"]),
        sort_order=dict(type="str", choices=["Ascending", "Descending"]),
        max_results=dict(type="int"),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[("feature_group_name", filter_name) for filter_name in LIST_FILTERS],
    )
    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        if module.params.get("feature_group_name"):
            found = describe_feature_group(client, module.params["feature_group_name"])
            feature_groups = [found] if found else []
        else:
            filters = {key: module.params.get(key) for key in LIST_FILTERS}
            summaries = list_feature_groups(
                client,
                **snake_dict_to_camel_dict(scrub_none_parameters(filters), capitalize_first=True),
            )
            # A group deleted between the list and the describe is skipped.
            feature_groups = [
                feature_group
                for summary in summaries
                if (feature_group := describe_feature_group(client, summary["FeatureGroupName"])) is not None
            ]
        module.exit_json(feature_groups=[_with_tags(client, feature_group) for feature_group in feature_groups])
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
