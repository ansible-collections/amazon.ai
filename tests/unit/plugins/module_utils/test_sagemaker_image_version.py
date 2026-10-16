#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for the SageMaker image version helpers in the sagemaker module_utils."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import _ensure_image_version_updatable
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_image_version
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_image_version
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_image_version
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import find_image_versions
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import image_version_needs_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_image_version
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_image_version_created
from botocore.exceptions import ClientError
from botocore.exceptions import WaiterError

SAGEMAKER = "ansible_collections.amazon.ai.plugins.module_utils.sagemaker"
BASE_IMAGE = "123456789012.dkr.ecr.eu-north-1.amazonaws.com/repo:latest"


class FailJson(Exception):
    """Raised by the mocked module.fail_json, which exits the module in real life."""


def make_module(check_mode=False, **params):
    module = MagicMock()
    module.check_mode = check_mode
    module.params = dict(
        image_name="img",
        version=3,
        base_image=None,
        aliases=None,
        horovod=None,
        job_type=None,
        ml_framework=None,
        processor=None,
        programming_lang=None,
        release_notes=None,
        vendor_guidance=None,
        wait=True,
        wait_timeout=600,
    )
    module.params.update(params)
    module.fail_json.side_effect = FailJson
    return module


def existing_version(status="CREATED", **extra):
    version = {"ImageVersionStatus": status, "Version": 3, "BaseImage": BASE_IMAGE, "Aliases": []}
    version.update(extra)
    return version


def not_found(operation):
    return ClientError({"Error": {"Code": "ResourceNotFound", "Message": "not found"}}, operation)


# --------------------------------------------------------------------------------------
# _ensure_image_version_updatable
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "status,fragments",
    [
        ("DELETING", ["being deleted"]),
        ("CREATE_FAILED", ["failed to be created", "boom", "state=absent"]),
        ("DELETE_FAILED", ["could not be deleted", "boom", "state=absent"]),
    ],
)
def test_ensure_updatable_fails_for_unusable_statuses(status, fragments):
    module = make_module()

    with pytest.raises(FailJson):
        _ensure_image_version_updatable(existing_version(status, FailureReason="boom"), module)

    kwargs = module.fail_json.call_args.kwargs
    for fragment in fragments:
        assert fragment in kwargs["msg"]
    assert kwargs["image_version"]["image_version_status"] == status


@pytest.mark.parametrize("status", ["CREATING", "CREATED"])
def test_ensure_updatable_allows_other_statuses(status):
    module = make_module()

    _ensure_image_version_updatable(existing_version(status), module)

    module.fail_json.assert_not_called()


# --------------------------------------------------------------------------------------
# image_version_needs_update
# --------------------------------------------------------------------------------------
def test_needs_update_no_options_means_no_changes():
    module = make_module()

    assert image_version_needs_update(existing_version(), module) == ({}, [], [])


def test_needs_update_reports_only_differing_properties_and_renames_ml_framework():
    module = make_module(release_notes="new", job_type="TRAINING", ml_framework="PyTorch 2")
    existing = existing_version(ReleaseNotes="new", JobType="INFERENCE", MLFramework="PyTorch 1")

    properties, to_add, to_delete = image_version_needs_update(existing, module)

    assert properties == {"JobType": "TRAINING", "MLFramework": "PyTorch 2"}
    assert to_add == []
    assert to_delete == []


def test_needs_update_aliases_are_a_complete_desired_set():
    module = make_module(aliases=["b", "c"])
    existing = existing_version(Aliases=["a", "b"])

    assert image_version_needs_update(existing, module) == ({}, ["c"], ["a"])


def test_needs_update_leaves_aliases_alone_when_omitted():
    module = make_module(aliases=None)

    assert image_version_needs_update(existing_version(Aliases=["a"]), module) == ({}, [], [])


def test_needs_update_does_not_compare_base_image():
    module = make_module(base_image="other/repo:tag")

    assert image_version_needs_update(existing_version(), module) == ({}, [], [])

    module.warn.assert_not_called()
    module.fail_json.assert_not_called()


# --------------------------------------------------------------------------------------
# update_image_version
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("status", ["CREATE_FAILED", "DELETE_FAILED", "DELETING"])
@patch(f"{SAGEMAKER}.wait_for_image_version_created")
def test_update_fails_early_on_unusable_status_even_without_a_diff(mock_wait, status):
    client = MagicMock()
    module = make_module()

    with pytest.raises(FailJson):
        update_image_version(client, module, existing_version(status))

    client.update_image_version.assert_not_called()
    mock_wait.assert_not_called()


@pytest.mark.parametrize("check_mode", [False, True])
def test_update_fails_when_base_image_differs_from_the_existing_version(check_mode):
    client = MagicMock()
    module = make_module(check_mode=check_mode, base_image="other/repo:tag", release_notes="new")

    with pytest.raises(FailJson):
        update_image_version(client, module, existing_version())

    message = module.fail_json.call_args.kwargs["msg"]
    assert "base_image cannot be changed" in message
    assert BASE_IMAGE in message
    client.update_image_version.assert_not_called()


@patch(f"{SAGEMAKER}.get_image_version")
def test_update_accepts_a_base_image_equal_to_the_existing_one(mock_get):
    client = MagicMock()
    existing = existing_version()

    changed, msg, result = update_image_version(client, make_module(base_image=BASE_IMAGE), existing)

    assert (changed, result) == (False, existing)
    client.update_image_version.assert_not_called()


@patch(f"{SAGEMAKER}.get_image_version")
@patch(f"{SAGEMAKER}.wait_for_image_version_created")
def test_update_created_no_diff_is_a_noop_without_waiting(mock_wait, mock_get):
    client = MagicMock()
    existing = existing_version()

    changed, msg, result = update_image_version(client, make_module(), existing)

    assert (changed, result) == (False, existing)
    assert "already matches" in msg
    mock_wait.assert_not_called()
    client.update_image_version.assert_not_called()


@patch(f"{SAGEMAKER}.get_image_version")
@patch(f"{SAGEMAKER}.wait_for_image_version_created")
def test_update_creating_no_diff_waits_to_confirm_readiness_and_rereads(mock_wait, mock_get):
    client = MagicMock()
    ready = existing_version("CREATED")
    mock_get.return_value = ready

    changed, msg, result = update_image_version(client, make_module(), existing_version("CREATING"))

    assert (changed, result) == (False, ready)
    mock_wait.assert_called_once_with(client, mock_wait.call_args.args[1], "img", 3)
    client.update_image_version.assert_not_called()


@patch(f"{SAGEMAKER}.get_image_version")
@patch(f"{SAGEMAKER}.wait_for_image_version_created")
def test_update_creating_no_diff_without_wait_returns_the_version_as_is(mock_wait, mock_get):
    client = MagicMock()
    existing = existing_version("CREATING")

    changed, _msg, result = update_image_version(client, make_module(wait=False), existing)

    assert (changed, result) == (False, existing)
    mock_wait.assert_not_called()
    mock_get.assert_not_called()


@patch(f"{SAGEMAKER}.get_image_version")
@patch(f"{SAGEMAKER}.wait_for_image_version_created")
def test_update_creating_no_diff_in_check_mode_does_not_wait(mock_wait, mock_get):
    changed = update_image_version(MagicMock(), make_module(check_mode=True), existing_version("CREATING"))[0]

    assert changed is False
    mock_wait.assert_not_called()


@patch(f"{SAGEMAKER}.get_image_version")
@patch(f"{SAGEMAKER}.wait_for_image_version_created")
def test_update_creating_with_diff_waits_then_updates(mock_wait, mock_get):
    client = MagicMock()
    order = MagicMock()
    order.attach_mock(mock_wait, "wait")
    order.attach_mock(client.update_image_version, "update")
    updated = existing_version(ReleaseNotes="new")
    mock_get.return_value = updated

    changed, msg, result = update_image_version(client, make_module(release_notes="new"), existing_version("CREATING"))

    assert (changed, result) == (True, updated)
    assert "updated successfully" in msg
    assert [call[0] for call in order.mock_calls] == ["wait", "update"]
    client.update_image_version.assert_called_once_with(aws_retry=True, ImageName="img", Version=3, ReleaseNotes="new")


@patch(f"{SAGEMAKER}.get_image_version")
@patch(f"{SAGEMAKER}.wait_for_image_version_created")
def test_update_creating_with_diff_and_no_wait_updates_without_waiting(mock_wait, mock_get):
    client = MagicMock()
    module = make_module(wait=False, release_notes="new")
    mock_get.return_value = existing_version("CREATING", ReleaseNotes="new")

    changed = update_image_version(client, module, existing_version("CREATING"))[0]

    assert changed is True
    client.update_image_version.assert_called_once_with(aws_retry=True, ImageName="img", Version=3, ReleaseNotes="new")
    mock_wait.assert_not_called()
    module.fail_json.assert_not_called()


@patch(f"{SAGEMAKER}.get_image_version")
@patch(f"{SAGEMAKER}.wait_for_image_version_created")
def test_update_with_diff_in_check_mode_changes_nothing(mock_wait, mock_get):
    client = MagicMock()
    module = make_module(check_mode=True, release_notes="new")

    changed, msg = update_image_version(client, module, existing_version("CREATING"))[:2]

    assert changed is True
    assert msg.startswith("Check mode: would have updated")
    client.update_image_version.assert_not_called()
    mock_wait.assert_not_called()


@patch(f"{SAGEMAKER}.get_image_version")
@patch(f"{SAGEMAKER}.wait_for_image_version_created")
def test_update_created_sends_alias_changes_and_does_not_wait(mock_wait, mock_get):
    client = MagicMock()
    module = make_module(aliases=["b", "c"])
    mock_get.return_value = existing_version(Aliases=["b", "c"])

    changed = update_image_version(client, module, existing_version(Aliases=["a", "b"]))[0]

    assert changed is True
    client.update_image_version.assert_called_once_with(
        aws_retry=True, ImageName="img", Version=3, AliasesToAdd=["c"], AliasesToDelete=["a"]
    )
    mock_wait.assert_not_called()


# --------------------------------------------------------------------------------------
# delete_image_version
# --------------------------------------------------------------------------------------
@patch(f"{SAGEMAKER}.wait_for_image_version_deletion")
def test_delete_missing_version_is_unchanged(mock_wait):
    client = MagicMock()

    changed, msg = delete_image_version(client, make_module(), None)

    assert changed is False
    assert "does not exist" in msg
    client.delete_image_version.assert_not_called()


@patch(f"{SAGEMAKER}.wait_for_image_version_deletion")
def test_delete_in_progress_waits_and_is_unchanged(mock_wait):
    client = MagicMock()

    changed, msg = delete_image_version(client, make_module(), existing_version("DELETING"))

    assert changed is False
    assert "already being deleted" in msg
    mock_wait.assert_called_once()
    client.delete_image_version.assert_not_called()


@patch(f"{SAGEMAKER}.wait_for_image_version_deletion")
def test_delete_in_progress_does_not_wait_in_check_mode(mock_wait):
    changed, msg = delete_image_version(MagicMock(), make_module(check_mode=True), existing_version("DELETING"))

    assert changed is False
    mock_wait.assert_not_called()


@patch(f"{SAGEMAKER}.wait_for_image_version_deletion")
def test_delete_check_mode_changes_nothing(mock_wait):
    client = MagicMock()

    changed, msg = delete_image_version(client, make_module(check_mode=True), existing_version())

    assert changed is True
    assert msg.startswith("Check mode: would have deleted")
    client.delete_image_version.assert_not_called()
    mock_wait.assert_not_called()


@patch(f"{SAGEMAKER}.wait_for_image_version_deletion")
def test_delete_created_version_deletes_and_waits(mock_wait):
    client = MagicMock()
    module = make_module(wait_timeout=90)

    changed, msg = delete_image_version(client, module, existing_version())

    assert changed is True
    assert "deleted successfully" in msg
    client.delete_image_version.assert_called_once_with(ImageName="img", Version=3, aws_retry=True)
    mock_wait.assert_called_once_with(client, module)
    module.warn.assert_not_called()


@patch(f"{SAGEMAKER}.wait_for_image_version_deletion")
@patch(f"{SAGEMAKER}.wait_for_image_version_created")
def test_delete_creating_waits_for_creation_then_deletes(mock_created, mock_deleted):
    client = MagicMock()
    module = make_module()
    order = MagicMock()
    order.attach_mock(mock_created, "created")
    order.attach_mock(client.delete_image_version, "delete")

    changed, msg = delete_image_version(client, module, existing_version("CREATING"))

    assert changed is True
    assert "deleted successfully" in msg
    assert [c[0] for c in order.mock_calls] == ["created", "delete"]
    mock_created.assert_called_once_with(client, module, "img", 3)
    mock_deleted.assert_called_once()


@patch(f"{SAGEMAKER}.wait_for_image_version_deletion")
@patch(f"{SAGEMAKER}.wait_for_image_version_created")
def test_delete_creating_without_wait_fails_early(mock_created, mock_deleted):
    client = MagicMock()

    with pytest.raises(FailJson):
        delete_image_version(client, make_module(wait=False), existing_version("CREATING"))

    client.delete_image_version.assert_not_called()
    mock_created.assert_not_called()


@patch(f"{SAGEMAKER}.wait_for_image_version_deletion")
@patch(f"{SAGEMAKER}.wait_for_image_version_created")
def test_delete_creating_without_wait_explains_how_to_proceed(mock_created, mock_deleted):
    module = make_module(wait=False)

    with pytest.raises(FailJson):
        delete_image_version(MagicMock(), module, existing_version("CREATING"))

    message = module.fail_json.call_args.kwargs["msg"]
    assert "still being created" in message
    assert "wait=true" in message


@pytest.mark.parametrize("wait", [True, False])
@patch(f"{SAGEMAKER}.wait_for_image_version_created")
def test_delete_creating_in_check_mode_never_waits_or_deletes(mock_created, wait):
    client = MagicMock()
    module = make_module(check_mode=True, wait=wait)

    if wait:
        changed, msg = delete_image_version(client, module, existing_version("CREATING"))
        assert changed is True
        assert msg.startswith("Check mode: would have deleted")
    else:
        with pytest.raises(FailJson):
            delete_image_version(client, module, existing_version("CREATING"))

    mock_created.assert_not_called()
    client.delete_image_version.assert_not_called()


@patch(f"{SAGEMAKER}.wait_for_image_version_deletion")
def test_delete_vanished_between_describe_and_delete_is_unchanged(mock_wait):
    client = MagicMock()
    client.delete_image_version.side_effect = not_found("DeleteImageVersion")

    changed, msg = delete_image_version(client, make_module(), existing_version())

    assert changed is False
    assert "does not exist" in msg
    mock_wait.assert_not_called()


@patch(f"{SAGEMAKER}.wait_for_image_version_deletion")
def test_delete_other_api_errors_propagate(mock_wait):
    client = MagicMock()
    client.delete_image_version.side_effect = ClientError(
        {"Error": {"Code": "ResourceInUse", "Message": "busy"}}, "DeleteImageVersion"
    )

    with pytest.raises(ClientError):
        delete_image_version(client, make_module(), existing_version())


@pytest.mark.parametrize("status", ["CREATE_FAILED", "DELETE_FAILED"])
@patch(f"{SAGEMAKER}.wait_for_image_version_deletion")
def test_delete_failed_versions_are_deleted(mock_wait, status):
    client = MagicMock()
    module = make_module()

    changed = delete_image_version(client, module, existing_version(status, FailureReason="boom"))[0]

    assert changed is True
    client.delete_image_version.assert_called_once()
    mock_wait.assert_called_once()
    if status == "DELETE_FAILED":
        module.warn.assert_called_once()
        assert "boom" in module.warn.call_args.args[0]
    else:
        module.warn.assert_not_called()


# --------------------------------------------------------------------------------------
# create_image_version
# --------------------------------------------------------------------------------------
def test_create_check_mode_does_not_call_the_api():
    client = MagicMock()

    changed, msg, version = create_image_version(client, make_module(check_mode=True, version=None))

    assert (changed, version) == (True, None)
    assert msg.startswith("Check mode: would have created")
    client.create_image_version.assert_not_called()


@patch(f"{SAGEMAKER}.wait_for_image_version_created")
def test_create_parses_the_version_from_the_arn_and_waits(mock_wait):
    client = MagicMock()
    client.create_image_version.return_value = {
        "ImageVersionArn": "arn:aws:sagemaker:eu-north-1:123456789012:image-version/img/7"
    }
    module = make_module(
        version=None, base_image=BASE_IMAGE, aliases=["latest"], ml_framework="TensorFlow 1.1", horovod=False
    )

    changed, msg, version = create_image_version(client, module)

    assert (changed, version) == (True, 7)
    client.create_image_version.assert_called_once_with(
        aws_retry=True,
        ImageName="img",
        BaseImage=BASE_IMAGE,
        Aliases=["latest"],
        MLFramework="TensorFlow 1.1",
        Horovod=False,
    )
    mock_wait.assert_called_once_with(client, module, "img", 7)


# --------------------------------------------------------------------------------------
# wait_for_image_version_created
# --------------------------------------------------------------------------------------
def test_wait_created_is_skipped_when_wait_is_false():
    client = MagicMock()

    wait_for_image_version_created(client, make_module(wait=False), "img", 3)

    client.get_waiter.assert_not_called()


@pytest.mark.parametrize("wait_timeout,delay,attempts", [(600, 60, 10), (30, 30, 1), (0, 1, 1)])
def test_wait_created_derives_delay_and_attempts_from_the_timeout(wait_timeout, delay, attempts):
    client = MagicMock()

    wait_for_image_version_created(client, make_module(wait_timeout=wait_timeout), "img", 3)

    client.get_waiter.assert_called_once_with("image_version_created")
    client.get_waiter.return_value.wait.assert_called_once_with(
        ImageName="img", Version=3, WaiterConfig={"Delay": delay, "MaxAttempts": attempts}
    )


@patch(f"{SAGEMAKER}.describe_image_version")
def test_wait_created_failure_reports_the_failure_reason(mock_describe):
    client = MagicMock()
    client.get_waiter.return_value.wait.side_effect = WaiterError("ImageVersionCreated", "failed", {})
    mock_describe.return_value = {"FailureReason": "image pull failed"}
    module = make_module()

    with pytest.raises(FailJson):
        wait_for_image_version_created(client, module, "img", 3)

    assert "image pull failed" in module.fail_json.call_args.kwargs["msg"]


# --------------------------------------------------------------------------------------
# describe / find
# --------------------------------------------------------------------------------------
def test_describe_image_version_only_sends_supplied_arguments():
    client = MagicMock()
    client.describe_image_version.return_value = {"Version": 3}

    assert describe_image_version(client, "img", version=3) == {"Version": 3}
    client.describe_image_version.assert_called_once_with(ImageName="img", Version=3)


def test_describe_image_version_returns_none_when_missing():
    client = MagicMock()
    client.describe_image_version.side_effect = not_found("DescribeImageVersion")

    assert describe_image_version(client, "img", version=3) is None


@patch(f"{SAGEMAKER}.list_image_version_aliases", return_value=["latest"])
def test_find_by_version_returns_a_list_with_aliases(mock_aliases):
    client = MagicMock()
    client.describe_image_version.return_value = {"Version": 3}

    assert find_image_versions(client, "img", version=3) == [{"Version": 3, "Aliases": ["latest"]}]


@patch(f"{SAGEMAKER}.list_image_versions")
@patch(f"{SAGEMAKER}.list_image_version_aliases", return_value=[])
def test_find_by_version_ignores_list_params(mock_aliases, mock_list):
    client = MagicMock()
    client.describe_image_version.return_value = {"Version": 3}

    find_image_versions(client, "img", version=3, SortBy="VERSION", SortOrder="DESCENDING")

    mock_list.assert_not_called()
    client.describe_image_version.assert_called_once_with(ImageName="img", Version=3)


def test_find_missing_version_or_image_returns_an_empty_list():
    client = MagicMock()
    client.describe_image_version.side_effect = not_found("DescribeImageVersion")

    assert find_image_versions(client, "img", version=3) == []
    assert find_image_versions(client, "img", alias="latest") == []


# --------------------------------------------------------------------------------------
# Horovod: UpdateImageVersion resets it to false whenever the call omits it
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("existing_horovod", [True, False])
@patch(f"{SAGEMAKER}.get_image_version")
def test_update_keeps_the_existing_horovod_value_when_changing_something_else(mock_get, existing_horovod):
    client = MagicMock()
    module = make_module(release_notes="new")
    mock_get.return_value = existing_version()

    update_image_version(client, module, existing_version(Horovod=existing_horovod))

    client.update_image_version.assert_called_once_with(
        aws_retry=True, ImageName="img", Version=3, ReleaseNotes="new", Horovod=existing_horovod
    )


@patch(f"{SAGEMAKER}.get_image_version")
def test_update_keeps_the_existing_horovod_value_for_an_alias_only_change(mock_get):
    client = MagicMock()
    module = make_module(aliases=["x"])
    mock_get.return_value = existing_version()

    update_image_version(client, module, existing_version(Horovod=True))

    client.update_image_version.assert_called_once_with(
        aws_retry=True, ImageName="img", Version=3, AliasesToAdd=["x"], Horovod=True
    )


@patch(f"{SAGEMAKER}.get_image_version")
def test_update_uses_the_requested_horovod_value(mock_get):
    client = MagicMock()
    module = make_module(horovod=False)
    mock_get.return_value = existing_version()

    update_image_version(client, module, existing_version(Horovod=True))

    client.update_image_version.assert_called_once_with(aws_retry=True, ImageName="img", Version=3, Horovod=False)


@patch(f"{SAGEMAKER}.get_image_version")
def test_update_does_not_invent_horovod_when_the_version_has_none(mock_get):
    client = MagicMock()
    module = make_module(release_notes="new")
    mock_get.return_value = existing_version()

    update_image_version(client, module, existing_version())

    assert "Horovod" not in client.update_image_version.call_args.kwargs
