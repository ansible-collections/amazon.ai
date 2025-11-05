# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def update_tags(
    current_tags: List[Dict[str, Any]],
    new_tags: List[Dict[str, Any]],
    state: str = "present",
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Updates a list of tags by adding, updating, or removing tags based on the state.
    Args:
        current_tags (List[Dict[str, Any]]): Existing list of tags. Each tag should have
            'AppBoundaryKey' and 'TagValues' fields.
        new_tags (List[Dict[str, Any]]): List of new tags to add, update, or remove.
        state (str, optional): Operation mode. "present" to add/update tags, "absent" to remove tags.
            Defaults to "present".
    Returns:
        Tuple[bool, List[Dict[str, Any]]]:
            - Boolean indicating if an update occurred.
            - Updated list of tags.
    """
    updated_tags = current_tags[:]
    update = False

    # Remove tags
    if new_tags == [] and state == "absent":
        return True, updated_tags

    for new_tag in new_tags:
        app_boundary_key = new_tag.get("app_boundary_key")
        new_tag_values = new_tag.get("tag_values", [])

        # Find the tag with the same AppBoundaryKey
        matching_tag = next(
            (tag for tag in updated_tags if tag.get("AppBoundaryKey") == app_boundary_key),
            None,
        )

        if state == "present":
            if matching_tag:
                # Add missing TagValues
                if matching_tag["TagValues"] != new_tag_values:
                    matching_tag["TagValues"] = new_tag_values
                    update = True
            else:
                # If no matching AppBoundaryKey, add the new tag
                updated_tags.append({"AppBoundaryKey": app_boundary_key, "TagValues": new_tag_values})
                update = True

        elif state == "absent" and matching_tag:
            # If TagValues match and we want to remove them, remove the tag
            if matching_tag["TagValues"] == new_tag_values:
                updated_tags = [tag for tag in updated_tags if tag.get("AppBoundaryKey") != app_boundary_key]
                update = True
            else:
                # If TagValues don't match, just update the tag with remaining values
                matching_tag["TagValues"] = [
                    value for value in matching_tag["TagValues"] if value not in new_tag_values
                ]
                if not matching_tag["TagValues"]:
                    updated_tags = [tag for tag in updated_tags if tag.get("AppBoundaryKey") != app_boundary_key]
                update = True

    return update, updated_tags


@AWSRetry.jittered_backoff(retries=10)
def get_resource_collection(client, module) -> Dict[str, Any]:
    """
    Retrieves an AWS resource collection using CloudFormation stack names or tags.
    Args:
        client: Boto3 client for AWS DevOpsGuru.
        module: AnsibleAWSModule containing parameters 'cloudformation_stack_names' or 'tags'.
    Returns:
        dict: Resource collection dictionary. Returns empty dict if not found.
    """
    stack_names = module.params.get("cloudformation_stack_names")
    tags = module.params.get("tags")
    params = {}
    if stack_names is not None:
        params["ResourceCollectionType"] = "AWS_CLOUD_FORMATION"
    elif tags is not None:
        params["ResourceCollectionType"] = "AWS_TAGS"

    try:
        paginator = client.get_paginator("get_resource_collection")
        return paginator.paginate(**params).build_full_result()["ResourceCollection"]
    except is_boto3_error_code("ResourceNotFoundException"):
        return {}


def update_resource_collection(client, module: AnsibleAWSModule, **params) -> str:
    """
    Updates a resource collection or simulates the update in check mode.
    Args:
        client: Boto3 client for AWS DevOpsGuru.
        module (Any): Ansible module with 'check_mode' support.
        **params: Parameters to pass to the AWS API for updating the resource collection.
    Returns:
        str: Status message indicating success or check mode simulation.
    """
    if module.check_mode:
        return "Check mode: would have updated resource collection."
    else:
        client.update_resource_collection(**params)
        return "Resource collection updated successfully."


def add_notification_channel(client, module: AnsibleAWSModule, config: Dict[str, Any]) -> Tuple[Optional[str], str]:
    """
    Adds a notification channel to a service or simulates it in check mode.
    Args:
        client: Boto3 client for AWS DevOpsGuru.
        module (Any): Ansible module with 'check_mode' support.
        config (dict): Notification channel configuration.
    Returns:
        Tuple[Optional[str], str]: Notification channel ID and status message indicating success or check mode simulation.
    """
    if module.check_mode:
        return None, "Check mode: would have added notification channel."
    else:
        response = client.add_notification_channel(**{"Config": config})
        return response.get("Id"), "Notification channel added successfully."


@AWSRetry.jittered_backoff(retries=10)
def get_resource_collection_specified_type(client, resource_collection_type: str) -> Dict[str, Any]:
    """
    Retrieves a resource collection of a specified type.
    Args:
        client: Boto3 client for AWS DevOpsGuru.
        resource_collection_type (str): Type of resource collection, e.g., 'AWS_CLOUD_FORMATION' or 'AWS_TAGS'.
    Returns:
        dict: Resource collection dictionary. Returns empty dict if not found.
    """
    params = {"ResourceCollectionType": resource_collection_type}

    try:
        paginator = client.get_paginator("get_resource_collection")
        return paginator.paginate(**params).build_full_result()["ResourceCollection"]
    except is_boto3_error_code("ResourceNotFoundException"):
        return {}


@AWSRetry.jittered_backoff(retries=10)
def fetch_data(client, api_call: str, **params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic function to fetch data from AWS using paginators.
    Args:
        client: Boto3 client for AWS DevOpsGuru.
        api_call (str): Name of the API call to paginate.
        **params: Parameters to pass to the paginator.
    Returns:
        dict: Full paginated results combined into a single dictionary.
    """
    paginator = client.get_paginator(api_call)
    return paginator.paginate(**params).build_full_result()


def describe_insight(client, insight_id: str, account_id: str = None) -> Dict[str, Any]:
    """
    Retrieves the details of a specific DevOpsGuru Insight.
    Args:
        client: Boto3 client for AWS DevOpsGuru.
        insight_id (str): The unique ID of the insight to describe.
        account_id (str, optional): AWS account ID to scope the insight. Defaults to None.
    Returns:
        dict: Insight details returned from the AWS API.
    """
    params: Dict[str, Any] = {"Id": insight_id}
    if account_id:
        params["AccountId"] = account_id

    return client.describe_insight(**params)


def get_insight_type(data: Dict[str, Any]) -> Union[str, None]:
    """
    Determines the type of insight from the provided data dictionary.
    Args:
        data (dict): Data dictionary potentially containing insight keys.
    Returns:
        str | None: The key indicating the insight type ('ProactiveInsight', 'ReactiveInsight', etc.)
                    or None if no recognized key is present.
    """
    possible_keys = [
        "ProactiveInsight",
        "ReactiveInsight",
        "ProactiveInsights",
        "ReactiveInsights",
    ]
    try:
        key = next(key for key in possible_keys if key in data)
        return key
    except StopIteration:
        return None


@AWSRetry.jittered_backoff(retries=10)
def list_notification_channels(client) -> List[Dict[str, Any]]:
    """
    Retrieve a list of DevOpsGuru Notification Channels using pagination.
    Args:
        client: The boto3 DevOpsGuru client.
    Returns:
        A list of notification channels.
    """
    paginator = client.get_paginator("list_notification_channels")
    return paginator.paginate().build_full_result()["Channels"]


def remove_notification_channel(client, module: AnsibleAWSModule) -> Tuple[bool, Optional[str], str]:
    notification_channel_id = module.params.get("notification_channel_id")
    existing_channels = list_notification_channels(client)

    # Remove notification channel
    if any(channel["Id"] == notification_channel_id for channel in existing_channels):
        if module.check_mode:
            msg = f"Check mode: would have removed notification channel {notification_channel_id}."
            return True, notification_channel_id, msg

        msg = f"Notification channel {notification_channel_id} removed."
        client.remove_notification_channel(Id=notification_channel_id)
        return True, None, msg
    else:
        msg = f"Notification channel {notification_channel_id} is not assiciated to DevOpsGuru ."
        return False, None, msg


def ensure_notification_channel(client, module: AnsibleAWSModule) -> Tuple[bool, Optional[str], str]:
    """
    Ensures the notification channel exists and matches the desired config (idempotent).
    Returns:
        (changed, channel_id, message)
    """
    changed: bool = False
    existing_channels = list_notification_channels(client)
    desired_config = module.params.get("notification_channel_config")

    # Normalize both sides for comparison
    desired = snake_dict_to_camel_dict(desired_config, capitalize_first=True)

    def normalize_channel(channel: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify channel for equality checks."""
        config = channel.get("Config", {})
        return {
            "Sns": config.get("Sns", {}),
            "Filters": config.get("Filters", {}),
        }

    desired_normalized = normalize_channel({"Config": desired})

    # Find if the desired channel already exists
    for ch in existing_channels:
        if normalize_channel(ch) == desired_normalized:
            channel_id = ch.get("Id")
            msg = f"Notification channel {channel_id} already exists. No changes made."
            return changed, channel_id, msg

    # Otherwise, add a new one
    if not module.check_mode:
        response = client.add_notification_channel(Config=desired)
        channel_id = response["Id"]
        msg = f"Notification channel {channel_id} added successfully."
    else:
        channel_id = None
        msg = "Check mode: would have added notification channel."

    changed = True
    return changed, channel_id, msg
