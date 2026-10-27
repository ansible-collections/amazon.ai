#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_feature_group
short_description: Manage Amazon SageMaker Feature Store feature groups
version_added: "2.0.0"
author:
    - Matej Artač (@matejart)
description:
    - Create, update, and delete Amazon SageMaker Feature Store feature groups.
    - A feature group holds a set of feature definitions and stores records in an online store, an offline store, or both.
    - Features can be added to an existing feature group but never changed or removed.
    - The online store TTL and storage type, the throughput configuration and the tags can be updated in place.
      Every other property is fixed at creation; changing it fails with a message naming the option.
options:
    state:
        description: The desired state of the feature group.
        type: str
        choices: [present, absent]
        default: present
    feature_group_name:
        description:
            - The name of the feature group, unique within the account and region.
            - Up to 64 alphanumeric characters, hyphens or underscores, starting and ending with an alphanumeric character.
        type: str
        required: true
        aliases: [name]
    record_identifier_feature_name:
        description:
            - The name of the feature that uniquely identifies a record.
            - Must be one of the features in O(feature_definitions).
            - Required when O(state=present). Cannot be changed after creation.
        type: str
    event_time_feature_name:
        description:
            - The name of the feature that stores the event time of a record.
            - The feature must be of type V(String) (ISO-8601) or V(Fractional) (Unix timestamp in seconds).
            - Required when O(state=present). Cannot be changed after creation.
        type: str
    feature_definitions:
        description:
            - The features of the feature group, 1 to 2500 entries.
            - On an existing feature group, features missing from the group are added.
              Removing a feature or changing an existing one fails.
            - Required when O(state=present).
        type: list
        elements: dict
        suboptions:
            feature_name:
                description:
                    - The name of the feature.
                    - Cannot be V(is_deleted), V(write_time) or V(api_invocation_time).
                type: str
                required: true
            feature_type:
                description: The data type of the feature.
                type: str
                required: true
                choices: [Integral, Fractional, String]
            collection_type:
                description:
                    - Makes the feature a collection of O(feature_definitions[].feature_type) values.
                    - A V(Vector) must hold V(Fractional) values.
                type: str
                choices: [List, Set, Vector]
            collection_config:
                description: Configuration of a collection feature.
                type: dict
                suboptions:
                    vector_config:
                        description: Configuration of a V(Vector) feature.
                        type: dict
                        suboptions:
                            dimension:
                                description: The number of elements in the vector, 1 to 8192.
                                type: int
                                required: true
    online_store_config:
        description:
            - Configuration of the online store.
            - At least one of O(online_store_config) and O(offline_store_config) is required to create a feature group.
        type: dict
        suboptions:
            enable_online_store:
                description:
                    - Whether to enable the online store.
                    - Cannot be changed after creation.
                type: bool
            security_config:
                description:
                    - Encryption settings of the online store.
                    - Cannot be changed after creation.
                type: dict
                suboptions:
                    kms_key_id:
                        description: The ID or ARN of the KMS key that encrypts the online store.
                        type: str
            storage_type:
                description:
                    - The storage type of the online store.
                    - The only change allowed after creation is from V(Standard) to V(Standard_V2), and it cannot be reversed.
                type: str
                choices: [Standard, Standard_V2, InMemory]
            ttl_duration:
                description:
                    - The default time to live of records in the online store.
                    - Can be changed after creation.
                type: dict
                suboptions:
                    unit:
                        description: The unit of O(online_store_config.ttl_duration.value).
                        type: str
                        required: true
                        choices: [Seconds, Minutes, Hours, Days, Weeks]
                    value:
                        description: The time to live, at least 1.
                        type: int
                        required: true
    offline_store_config:
        description:
            - Configuration of the offline store in Amazon S3.
            - Requires O(role_arn). Cannot be changed after creation.
        type: dict
        suboptions:
            s3_storage_config:
                description: Where the offline store keeps its data.
                type: dict
                required: true
                suboptions:
                    s3_uri:
                        description: The S3 URI under which the offline store writes data.
                        type: str
                        required: true
                    kms_key_id:
                        description: The ID or ARN of the KMS key that encrypts the offline store data.
                        type: str
            disable_glue_table_creation:
                description: Whether to skip creating an AWS Glue table for the offline store.
                type: bool
            data_catalog_config:
                description:
                    - The AWS Glue Data Catalog table of the offline store.
                    - When omitted, the catalog, database and table names are generated.
                type: dict
                suboptions:
                    catalog:
                        description: The name of the Glue catalog.
                        type: str
                        required: true
                    database:
                        description: The name of the Glue database.
                        type: str
                        required: true
                    table_name:
                        description: The name of the Glue table.
                        type: str
                        required: true
            table_format:
                description:
                    - The table format of the offline store.
                    - V(Iceberg) requires a V(String) event time feature and Glue table creation.
                type: str
                choices: [Default, Glue, Iceberg]
    throughput_config:
        description:
            - The read and write throughput mode of the feature group.
            - Can be changed after creation.
        type: dict
        suboptions:
            throughput_mode:
                description:
                    - The throughput mode.
                    - V(Provisioned) needs an online store with V(Standard) storage.
                type: str
                required: true
                choices: [OnDemand, Provisioned]
            provisioned_read_capacity_units:
                description:
                    - The provisioned read capacity units.
                    - Required, and non-zero, when O(throughput_config.throughput_mode=Provisioned).
                type: int
            provisioned_write_capacity_units:
                description:
                    - The provisioned write capacity units.
                    - Required, and non-zero, when O(throughput_config.throughput_mode=Provisioned).
                type: int
    role_arn:
        description:
            - The ARN of the IAM role the offline store uses to write data to Amazon S3.
            - Required when O(offline_store_config) is set. Cannot be changed after creation.
        type: str
    description:
        description:
            - A description of the feature group, up to 128 characters.
            - Cannot be changed after creation.
        type: str
    tags:
        description: Tags to associate with the feature group.
        type: dict
        aliases: [resource_tags]
    purge_tags:
        description: Whether to remove tags not specified in O(tags).
        type: bool
        default: true
    wait:
        description:
            - Whether to wait for the feature group to be created, updated or deleted.
            - When several kinds of change are applied, the module always waits between them;
              this option only governs the wait after the last one.
        type: bool
        default: true
    wait_timeout:
        description: How long, in seconds, to wait for the feature group.
        type: int
        default: 600
notes:
    - Required IAM actions include sagemaker:CreateFeatureGroup, sagemaker:DescribeFeatureGroup,
      sagemaker:UpdateFeatureGroup, sagemaker:DeleteFeatureGroup, sagemaker:ListFeatureGroups,
      sagemaker:AddTags, sagemaker:ListTags, sagemaker:DeleteTags, and iam:PassRole for O(role_arn).
    - Deleting a feature group does not delete the offline store data in Amazon S3 or the AWS Glue table.
attributes:
    check_mode:
        description: Can run in check mode and report what would change without changing the target.
        support: full
seealso:
    - module: amazon.ai.sagemaker_feature_group_info
      description: Gather information about SageMaker feature groups.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""

EXAMPLES = r"""
- name: Create a feature group with an online and an offline store
  amazon.ai.sagemaker_feature_group:
    feature_group_name: customers
    record_identifier_feature_name: customer_id
    event_time_feature_name: event_time
    feature_definitions:
      - feature_name: customer_id
        feature_type: String
      - feature_name: event_time
        feature_type: Fractional
      - feature_name: lifetime_value
        feature_type: Fractional
    online_store_config:
      enable_online_store: true
      storage_type: Standard
    offline_store_config:
      s3_storage_config:
        s3_uri: s3://my-sagemaker-bucket/feature-store
      disable_glue_table_creation: true
    role_arn: arn:aws:iam::123456789012:role/FeatureStoreRole
    tags:
      team: ml

- name: Add a feature and set a TTL on the online store
  amazon.ai.sagemaker_feature_group:
    feature_group_name: customers
    record_identifier_feature_name: customer_id
    event_time_feature_name: event_time
    feature_definitions:
      - feature_name: customer_id
        feature_type: String
      - feature_name: event_time
        feature_type: Fractional
      - feature_name: lifetime_value
        feature_type: Fractional
      - feature_name: segment
        feature_type: String
    online_store_config:
      ttl_duration:
        unit: Days
        value: 30

- name: Switch to provisioned throughput
  amazon.ai.sagemaker_feature_group:
    feature_group_name: customers
    record_identifier_feature_name: customer_id
    event_time_feature_name: event_time
    feature_definitions:
      - feature_name: customer_id
        feature_type: String
      - feature_name: event_time
        feature_type: Fractional
      - feature_name: lifetime_value
        feature_type: Fractional
      - feature_name: segment
        feature_type: String
    throughput_config:
      throughput_mode: Provisioned
      provisioned_read_capacity_units: 10
      provisioned_write_capacity_units: 10

- name: Delete a feature group
  amazon.ai.sagemaker_feature_group:
    state: absent
    feature_group_name: customers
"""

RETURN = r"""
feature_group:
    description: The feature group after the operation.
    type: dict
    returned: on success when O(state=present), except in check mode
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
    type: dict
    returned: on success when O(state=present) and the feature group was created or O(tags) is set, except in check mode
    sample: {"team": "ml"}
msg:
    description: Informative message about the action.
    type: str
    returned: always
    sample: Feature group customers created successfully.
"""

try:
    import botocore
except ImportError:
    pass

from typing import Any
from typing import Dict
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_feature_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_feature_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_feature_group
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import feature_group_desired_config
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_feature_group_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_feature_group_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_feature_group
from ansible_collections.amazon.ai.plugins.module_utils.utils import feature_group_properties_to_update
from ansible_collections.amazon.ai.plugins.module_utils.waiters import wait_for_feature_group_status

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _feature_group_status_check(client, module, existing: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Exit early, fail or wait on a feature group in a transitional or failed state; return it refreshed."""
    if not existing:
        return existing
    name = module.params["feature_group_name"]
    state = module.params["state"]
    status = existing["FeatureGroupStatus"]
    update_status = (existing.get("LastUpdateStatus") or {}).get("Status")
    can_wait = module.params["wait"] and not module.check_mode

    if status == "Deleting":
        if state == "present":
            module.fail_json(msg=f"Feature group {name} is being deleted; wait for the deletion to finish first.")
        if can_wait:
            wait_for_feature_group_status(client, module, name, "feature_group_deleted")
        module.exit_json(changed=False, msg=f"Feature group {name} is already being deleted.")

    if status == "Creating" or update_status == "InProgress":
        transition = "being created" if status == "Creating" else "being updated"
        if module.check_mode:
            return existing
        if not can_wait:
            if state == "absent":
                module.fail_json(msg=f"Feature group {name} cannot be deleted while it is {transition}.")
            module.exit_json(
                changed=False,
                msg=f"Feature group {name} is {transition}.",
                feature_group=camel_dict_to_snake_dict(existing, ignore_list=["Tags", "tags"]),
            )
        waiter_name = "feature_group_created" if status == "Creating" else "feature_group_updated"
        wait_for_feature_group_status(client, module, name, waiter_name)
        return describe_feature_group(client, name)

    if state == "present" and status in ("CreateFailed", "DeleteFailed"):
        module.fail_json(
            msg=(
                f"Feature group {name} is in state {status}: {existing.get('FailureReason', 'no reason reported')}. "
                "Delete it with state=absent and recreate it."
            )
        )
    return existing


def _exit_with_feature_group(client, module, changed: bool, msg: str, include_tags: bool) -> None:
    feature_group = describe_feature_group(client, module.params["feature_group_name"])
    result = dict(
        changed=changed, msg=msg, feature_group=camel_dict_to_snake_dict(feature_group, ignore_list=["Tags", "tags"])
    )
    if include_tags:
        result["tags"] = list_feature_group_tags(client, feature_group["FeatureGroupArn"])
    module.exit_json(**result)


def _absent(client, module, existing: Optional[Dict[str, Any]]) -> None:
    name = module.params["feature_group_name"]
    if not existing or not delete_feature_group(client, module):
        module.exit_json(changed=False, msg=f"Feature group {name} does not exist.")
    module.exit_json(changed=True, msg=f"Feature group {name} deleted successfully.")


def _present(client, module, existing: Optional[Dict[str, Any]]) -> None:
    name = module.params["feature_group_name"]
    desired = feature_group_desired_config(module)
    if not existing:
        if "online_store_config" not in desired and "offline_store_config" not in desired:
            module.fail_json(
                msg="At least one of online_store_config or offline_store_config is required to create a feature group."
            )
        create_feature_group(client, module)
        _exit_with_feature_group(
            client, module, changed=True, msg=f"Feature group {name} created successfully.", include_tags=True
        )

    try:
        properties_to_update = feature_group_properties_to_update(
            camel_dict_to_snake_dict(existing, ignore_list=["Tags", "tags"]), desired
        )
    except ValueError as e:
        module.fail_json(msg=f"Feature group {name}: {e}")

    updated = update_feature_group(client, module, properties_to_update)
    tags_changed = reconcile_feature_group_tags(client, module, existing["FeatureGroupArn"])
    if module.check_mode:
        if tags_changed:
            module.exit_json(changed=True, msg=f"Check mode: would have updated feature group {name} tags.")
        module.exit_json(changed=False, msg=f"Feature group {name} already matches the requested configuration.")
    if updated or tags_changed:
        msg = f"Feature group {name} updated successfully."
    else:
        msg = f"Feature group {name} already matches the requested configuration."
    _exit_with_feature_group(
        client,
        module,
        changed=updated or tags_changed,
        msg=msg,
        include_tags=module.params.get("tags") is not None,
    )


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        feature_group_name=dict(type="str", required=True, aliases=["name"]),
        record_identifier_feature_name=dict(type="str"),
        event_time_feature_name=dict(type="str"),
        feature_definitions=dict(
            type="list",
            elements="dict",
            options=dict(
                feature_name=dict(type="str", required=True),
                feature_type=dict(type="str", required=True, choices=["Integral", "Fractional", "String"]),
                collection_type=dict(type="str", choices=["List", "Set", "Vector"]),
                collection_config=dict(
                    type="dict",
                    options=dict(
                        vector_config=dict(
                            type="dict",
                            options=dict(dimension=dict(type="int", required=True)),
                        ),
                    ),
                ),
            ),
        ),
        online_store_config=dict(
            type="dict",
            options=dict(
                enable_online_store=dict(type="bool"),
                security_config=dict(type="dict", options=dict(kms_key_id=dict(type="str"))),
                storage_type=dict(type="str", choices=["Standard", "Standard_V2", "InMemory"]),
                ttl_duration=dict(
                    type="dict",
                    options=dict(
                        unit=dict(type="str", required=True, choices=["Seconds", "Minutes", "Hours", "Days", "Weeks"]),
                        value=dict(type="int", required=True),
                    ),
                ),
            ),
        ),
        offline_store_config=dict(
            type="dict",
            options=dict(
                s3_storage_config=dict(
                    type="dict",
                    required=True,
                    options=dict(
                        s3_uri=dict(type="str", required=True),
                        kms_key_id=dict(type="str"),
                    ),
                ),
                disable_glue_table_creation=dict(type="bool"),
                data_catalog_config=dict(
                    type="dict",
                    options=dict(
                        catalog=dict(type="str", required=True),
                        database=dict(type="str", required=True),
                        table_name=dict(type="str", required=True),
                    ),
                ),
                table_format=dict(type="str", choices=["Default", "Glue", "Iceberg"]),
            ),
        ),
        throughput_config=dict(
            type="dict",
            options=dict(
                throughput_mode=dict(type="str", required=True, choices=["OnDemand", "Provisioned"]),
                provisioned_read_capacity_units=dict(type="int"),
                provisioned_write_capacity_units=dict(type="int"),
            ),
            required_if=[
                (
                    "throughput_mode",
                    "Provisioned",
                    ["provisioned_read_capacity_units", "provisioned_write_capacity_units"],
                )
            ],
        ),
        role_arn=dict(type="str"),
        description=dict(type="str"),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            (
                "state",
                "present",
                ["record_identifier_feature_name", "event_time_feature_name", "feature_definitions"],
            )
        ],
        required_by=dict(offline_store_config="role_arn"),
    )
    try:
        try:
            client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing = describe_feature_group(client, module.params["feature_group_name"])
        existing = _feature_group_status_check(client, module, existing)
        if module.params["state"] == "absent":
            _absent(client, module, existing)
        _present(client, module, existing)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
