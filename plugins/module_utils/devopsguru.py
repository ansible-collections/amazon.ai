# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def update_tags(
    current_tags: List[Dict[str, Any]],
    new_tags: List[Dict[str, Any]],
    state: str = "present",
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Updates the tags list by adding, updating, or removing tags and TagValues based on the state.

    :param current_tags: The existing list of tags to update.
    :param new_tags: The list of new tags to process.
    :param state: Determines whether to add ("present") or remove ("absent") tags.
    :return: A dictionary with 'update' (bool) and 'tags' (new updated list of tags).
    """
    updated_tags = current_tags[:]
    update = False

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


def update_resource_collection(client, **params) -> Dict[str, Any]:
    return client.update_resource_collection(**params)


def add_notification_channel(client, config: Dict[str, Any]):
    client.add_notification_channel(**{"Config": config})


@AWSRetry.jittered_backoff(retries=10)
def get_resource_collection(client, resource_collection_type: str) -> Dict[str, Any]:
    """Retrieves a resource collection"""
    params = {"ResourceCollectionType": resource_collection_type}

    try:
        paginator = client.get_paginator("get_resource_collection")
        return paginator.paginate(**params).build_full_result()["ResourceCollection"]
    except is_boto3_error_code("ResourceNotFoundException"):
        return {}


@AWSRetry.jittered_backoff(retries=10)
def fetch_data(client, api_call: str, **params: Dict[str, Any]) -> Dict[str, Any]:
    """Generic function to fetch data using paginators."""
    paginator = client.get_paginator(api_call)
    return paginator.paginate(**params).build_full_result()


def describe_insight(client, insight_id: str, account_id: str = None) -> Dict[str, Any]:
    params: Dict[str, Any] = {"Id": insight_id}
    if account_id:
        params["AccountId"] = account_id

    return client.describe_insight(**params)


def get_insight_type(data: Dict[str, Any]) -> Union[str, None]:
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
