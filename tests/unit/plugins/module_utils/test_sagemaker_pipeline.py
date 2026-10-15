#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from io import BytesIO
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import create_pipeline
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import delete_pipeline
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_pipeline
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import get_pipeline_definition_from_s3
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_pipelines
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import pipeline_properties_to_update
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import reconcile_pipeline_tags
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import update_pipeline
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import wait_for_pipeline_status
from ansible_collections.amazon.ai.plugins.module_utils.utils import parse_json
from ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline import _ensure_absent
from ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline import _ensure_present
from ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline_info import main as pipeline_info_main
from botocore.exceptions import ClientError


def test_create_validation_reports_missing_role():
    module = MagicMock()
    module.params = {
        "pipeline_name": "pipeline",
        "pipeline_definition": '{"Version":"2020-12-01","Steps":[]}',
        "pipeline_definition_s3_location": None,
        "role_arn": None,
    }
    module.fail_json.side_effect = RuntimeError("module failure")

    with pytest.raises(RuntimeError, match="module failure"):
        _ensure_present(MagicMock(), module, None)

    module.fail_json.assert_called_once_with(msg="role_arn is required when creating a pipeline.")


def test_create_check_mode_does_not_initialize_s3_client():
    module = MagicMock()
    module.params = {
        "pipeline_name": "pipeline",
        "pipeline_definition": None,
        "pipeline_definition_s3_location": {"bucket": "bucket", "object_key": "definition.json"},
        "role_arn": "arn:aws:iam::123456789012:role/SageMakerPipelineRole",
        "wait": True,
    }
    module.check_mode = True

    changed, result = _ensure_present(MagicMock(), module, None)

    assert changed is True
    assert result["msg"].startswith("Check mode: would have created pipeline")
    assert result["pipeline"] == {}
    module.client.assert_not_called()


def test_present_check_mode_always_returns_pipeline_tags(monkeypatch):
    module = MagicMock()
    module.params = {
        "pipeline_name": "pipeline",
        "pipeline_definition": None,
        "pipeline_definition_s3_location": None,
        "tags": None,
    }
    module.check_mode = True
    existing = {"PipelineArn": "pipeline-arn", "PipelineName": "pipeline"}
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline.pipeline_properties_to_update",
        lambda *args, **kwargs: {},
    )
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline.update_pipeline",
        lambda *args, **kwargs: (False, "No updates needed for pipeline pipeline.", None),
    )
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline.reconcile_pipeline_tags",
        lambda *args, **kwargs: (False, ""),
    )
    list_tags = MagicMock(return_value={})
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline.list_tags",
        list_tags,
    )
    client = MagicMock()

    changed, result = _ensure_present(client, module, existing)

    assert changed is False
    assert result["pipeline"]["tags"] == {}
    list_tags.assert_called_once_with(client, "pipeline-arn")


def test_describe_pipeline_returns_none_when_missing():
    client = MagicMock()
    client.describe_pipeline.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFound", "Message": "missing"}},
        "DescribePipeline",
    )

    assert describe_pipeline(client, "missing") is None
    client.describe_pipeline.assert_called_once_with(PipelineName="missing")


def test_describe_pipeline_requests_specific_version():
    client = MagicMock()
    client.describe_pipeline.return_value = {
        "PipelineName": "pipeline",
        "PipelineDefinition": '{"Version":"2020-12-01","Steps":[]}',
        "PipelineVersionDescription": "first version",
    }

    assert describe_pipeline(client, "pipeline", pipeline_version_id=3) == {
        "PipelineName": "pipeline",
        "PipelineDefinition": '{"Version":"2020-12-01","Steps":[]}',
        "PipelineVersionDescription": "first version",
    }
    client.describe_pipeline.assert_called_once_with(PipelineName="pipeline", PipelineVersionId=3)


def test_list_pipelines_returns_paginated_summaries():
    client = MagicMock()
    client.get_paginator.return_value.paginate.return_value.build_full_result.return_value = {
        "PipelineSummaries": [{"PipelineName": "pipeline-a"}, {"PipelineName": "pipeline-b"}]
    }

    assert list_pipelines(client, PipelineNamePrefix="pipeline") == [
        {"PipelineName": "pipeline-a"},
        {"PipelineName": "pipeline-b"},
    ]
    client.get_paginator.assert_called_once_with("list_pipelines")
    client.get_paginator.return_value.paginate.assert_called_once_with(PipelineNamePrefix="pipeline")


def test_list_pipelines_limits_total_items():
    client = MagicMock()
    client.get_paginator.return_value.paginate.return_value.build_full_result.return_value = {
        "PipelineSummaries": [{"PipelineName": "pipeline-a"}]
    }

    assert list_pipelines(client, max_items=1) == [{"PipelineName": "pipeline-a"}]
    client.get_paginator.return_value.paginate.assert_called_once_with(PaginationConfig={"MaxItems": 1})


def test_get_pipeline_definition_from_s3_reads_and_closes_body():
    client = MagicMock()
    body = BytesIO(b'{"Steps": []}')
    client.get_object.return_value = {"Body": body}
    module = MagicMock()

    result = get_pipeline_definition_from_s3(
        client,
        {"Bucket": "pipeline-bucket", "ObjectKey": "definition.json", "VersionId": "v1"},
        module,
    )

    assert result == {"Steps": []}
    assert body.closed
    client.get_object.assert_called_once_with(
        Bucket="pipeline-bucket",
        Key="definition.json",
        VersionId="v1",
    )


def test_pipeline_properties_to_update_compares_inline_definitions_structurally():
    module = MagicMock()
    module.params = {
        "pipeline_definition": '{"Steps": [{"Name": "step"}]}',
        "pipeline_definition_s3_location": None,
        "role_arn": None,
        "pipeline_display_name": None,
        "pipeline_description": None,
        "parallelism_configuration": None,
    }
    existing = {"PipelineDefinition": '{ "Steps" : [{"Name":"step"}] }'}

    assert pipeline_properties_to_update(existing, module) == {}


def test_pipeline_properties_to_update_handles_missing_existing_s3_definition(monkeypatch):
    module = MagicMock()
    module.params = {
        "pipeline_definition": None,
        "pipeline_definition_s3_location": {"bucket": "bucket", "object_key": "definition.json"},
        "role_arn": None,
        "pipeline_display_name": None,
        "pipeline_description": None,
        "parallelism_configuration": None,
    }
    s3_client = MagicMock()
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.module_utils.sagemaker.get_pipeline_definition_from_s3",
        lambda *args, **kwargs: {"Steps": []},
    )

    assert pipeline_properties_to_update({}, module, s3_client=s3_client) == {
        "PipelineDefinitionS3Location": {"Bucket": "bucket", "ObjectKey": "definition.json"}
    }


def test_pipeline_properties_to_update_includes_only_different_properties():
    module = MagicMock()
    module.params = {
        "pipeline_definition": None,
        "pipeline_definition_s3_location": None,
        "role_arn": "arn:aws:iam::123456789012:role/pipeline",
        "pipeline_display_name": "updated",
        "pipeline_description": None,
        "parallelism_configuration": {"max_parallel_execution_steps": 2},
    }
    existing = {
        "RoleArn": "arn:aws:iam::123456789012:role/pipeline",
        "PipelineDisplayName": "original",
        "ParallelismConfiguration": {"MaxParallelExecutionSteps": 1},
    }

    assert pipeline_properties_to_update(existing, module) == {
        "PipelineDisplayName": "updated",
        "ParallelismConfiguration": {"MaxParallelExecutionSteps": 2},
    }


def test_wait_for_pipeline_status_checks_expected_properties_structurally():
    client = MagicMock()
    client.describe_pipeline.return_value = {
        "PipelineStatus": "Active",
        "PipelineDescription": "ready",
        "PipelineDefinition": '{"Steps": [{"Name": "step"}]}',
    }
    module = MagicMock()
    module.params = {"wait_timeout": 1}

    wait_for_pipeline_status(
        client,
        module,
        "example-pipeline",
        expected_properties={
            "PipelineDescription": "ready",
            "PipelineDefinition": {"Steps": [{"Name": "step"}]},
        },
    )

    client.describe_pipeline.assert_called_once_with(PipelineName="example-pipeline")
    module.fail_json.assert_not_called()


def test_wait_for_pipeline_status_describes_requested_version():
    client = MagicMock()
    client.describe_pipeline.return_value = {"PipelineStatus": "Active"}
    module = MagicMock()
    module.params = {"wait_timeout": 1}

    wait_for_pipeline_status(client, module, "example-pipeline", pipeline_version_id=3)

    client.describe_pipeline.assert_called_once_with(PipelineName="example-pipeline", PipelineVersionId=3)


def test_wait_for_pipeline_status_retries_until_expected_properties_are_visible():
    client = MagicMock()
    client.describe_pipeline.side_effect = [
        {"PipelineStatus": "Active", "PipelineDescription": "old"},
        {"PipelineStatus": "Active", "PipelineDescription": "new"},
    ]
    module = MagicMock()
    module.params = {"wait_timeout": 1}

    with patch("ansible_collections.amazon.ai.plugins.module_utils.sagemaker.time.sleep"):
        wait_for_pipeline_status(
            client,
            module,
            "example-pipeline",
            expected_properties={"PipelineDescription": "new"},
        )

    assert client.describe_pipeline.call_count == 2
    module.fail_json.assert_not_called()


def test_wait_for_pipeline_deletion_accepts_resource_not_found():
    client = MagicMock()
    client.describe_pipeline.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFound", "Message": "missing"}},
        "DescribePipeline",
    )
    module = MagicMock()
    module.params = {"wait_timeout": 1}

    wait_for_pipeline_status(client, module, "example-pipeline", deleted=True)

    module.fail_json.assert_not_called()


def test_wait_for_pipeline_status_fails_when_expected_properties_timeout():
    client = MagicMock()
    client.describe_pipeline.return_value = {"PipelineStatus": "Active", "PipelineDescription": "old"}
    module = MagicMock()
    module.params = {"wait_timeout": 1}
    module.fail_json.side_effect = RuntimeError("wait failed")

    with (
        patch(
            "ansible_collections.amazon.ai.plugins.module_utils.sagemaker.time.monotonic",
            side_effect=[0, 2],
        ),
        pytest.raises(RuntimeError, match="wait failed"),
    ):
        wait_for_pipeline_status(
            client,
            module,
            "example-pipeline",
            expected_properties={"PipelineDescription": "new"},
        )

    module.fail_json.assert_called_once()


@pytest.mark.parametrize(
    "extra_properties",
    [
        {},
        {"PipelineDescription": "updated"},
        {"PipelineDisplayName": "updated"},
        {"RoleArn": "arn:aws:iam::123456789012:role/updated"},
        {"PipelineDefinition": '{"Version":"2020-12-01","Steps":[]}'},
    ],
)
def test_update_pipeline_adds_existing_role_only_for_parallelism_only_updates(monkeypatch, extra_properties):
    client = MagicMock()
    client.update_pipeline.return_value = {"PipelineVersionId": 3}
    module = MagicMock()
    module.check_mode = False
    module.params = {
        "pipeline_name": "pipeline",
        "wait": True,
        "parallelism_configuration": {"max_parallel_execution_steps": 2},
    }
    waiter = MagicMock()
    monkeypatch.setattr("ansible_collections.amazon.ai.plugins.module_utils.sagemaker.wait_for_pipeline_status", waiter)

    properties_to_update = {
        "ParallelismConfiguration": {"MaxParallelExecutionSteps": 2},
        **extra_properties,
    }
    original_properties = dict(properties_to_update)
    assert update_pipeline(
        client,
        module,
        properties_to_update,
        {"RoleArn": "arn:aws:iam::123456789012:role/pipeline"},
    ) == (True, "Pipeline pipeline updated successfully.", 3)

    expected_properties = dict(properties_to_update)
    if not extra_properties:
        expected_properties["RoleArn"] = "arn:aws:iam::123456789012:role/pipeline"
    client.update_pipeline.assert_called_once_with(
        PipelineName="pipeline",
        **expected_properties,
    )
    assert properties_to_update == original_properties
    waiter.assert_called_once_with(
        client,
        module,
        "pipeline",
        expected_properties={"ParallelismConfiguration": {"MaxParallelExecutionSteps": 2}},
        pipeline_version_id=3,
    )


@pytest.mark.parametrize("check_mode, properties_to_update", [(True, {"ParallelismConfiguration": {}}), (False, {})])
def test_update_pipeline_does_not_call_aws_for_check_mode_or_no_changes(check_mode, properties_to_update):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = check_mode
    module.params = {"pipeline_name": "pipeline"}

    changed, msg, version_id = update_pipeline(client, module, properties_to_update, {})

    assert changed is check_mode
    assert msg.startswith("Check mode: would have " if check_mode else "No updates needed")
    assert version_id is None
    client.update_pipeline.assert_not_called()


def test_update_pipeline_without_wait_does_not_read_s3_or_poll(monkeypatch):
    client = MagicMock()
    client.update_pipeline.return_value = {"PipelineVersionId": 2}
    module = MagicMock()
    module.check_mode = False
    module.params = {"pipeline_name": "pipeline", "wait": False}
    s3_client = MagicMock()
    waiter = MagicMock()
    monkeypatch.setattr("ansible_collections.amazon.ai.plugins.module_utils.sagemaker.wait_for_pipeline_status", waiter)

    result = update_pipeline(client, module, {"PipelineDescription": "updated"}, {}, s3_client=s3_client)

    assert result == (True, "Pipeline pipeline updated successfully.", 2)
    client.update_pipeline.assert_called_once_with(PipelineName="pipeline", PipelineDescription="updated")
    s3_client.get_object.assert_not_called()
    waiter.assert_not_called()


@pytest.mark.parametrize("check_mode", [False, True])
def test_create_pipeline_converts_parameters_and_handles_check_mode(monkeypatch, check_mode):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = check_mode
    module.params = {
        "pipeline_name": "pipeline",
        "pipeline_definition": '{"Steps":[]}',
        "role_arn": "arn:aws:iam::123456789012:role/pipeline",
        "tags": {"MixedCase": "value"},
        "wait": True,
    }
    waiter = MagicMock()
    monkeypatch.setattr("ansible_collections.amazon.ai.plugins.module_utils.sagemaker.wait_for_pipeline_status", waiter)

    changed, msg = create_pipeline(client, module)

    assert changed
    if check_mode:
        assert msg.startswith("Check mode: would have ")
        client.create_pipeline.assert_not_called()
        waiter.assert_not_called()
    else:
        client.create_pipeline.assert_called_once_with(
            PipelineName="pipeline",
            PipelineDefinition='{"Steps":[]}',
            RoleArn=module.params["role_arn"],
            Tags=[{"Key": "MixedCase", "Value": "value"}],
        )
        waiter.assert_called_once_with(
            client,
            module,
            "pipeline",
            expected_properties={"PipelineDefinition": {"Steps": []}, "RoleArn": module.params["role_arn"]},
        )


@pytest.mark.parametrize("check_mode, wait", [(True, True), (False, True), (False, False)])
def test_delete_pipeline_handles_check_mode_and_wait(monkeypatch, check_mode, wait):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = check_mode
    module.params = {"pipeline_name": "pipeline", "wait": wait}
    waiter = MagicMock()
    monkeypatch.setattr("ansible_collections.amazon.ai.plugins.module_utils.sagemaker.wait_for_pipeline_status", waiter)

    changed, msg = delete_pipeline(client, module)

    assert changed
    assert msg.startswith("Check mode: would have " if check_mode else "Pipeline pipeline deleted successfully.")
    assert client.delete_pipeline.call_count == int(not check_mode)
    assert waiter.call_count == int(wait and not check_mode)
    if wait and not check_mode:
        waiter.assert_called_once_with(client, module, "pipeline", deleted=True)


@pytest.mark.parametrize("check_mode", [False, True])
def test_already_deleting_pipeline_is_unchanged_and_check_mode_does_not_wait(monkeypatch, check_mode):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = check_mode
    module.params = {"pipeline_name": "pipeline", "wait": True}
    waiter = MagicMock()
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline.wait_for_pipeline_status", waiter
    )

    changed, result = _ensure_absent(client, module, {"PipelineStatus": "Deleting"})

    assert not changed
    assert "already being deleted" in result["msg"]
    client.delete_pipeline.assert_not_called()
    assert waiter.call_count == int(not check_mode)


def test_present_pipeline_fails_early_while_deleting():
    module = MagicMock()
    module.params = {"pipeline_name": "pipeline"}
    module.fail_json.side_effect = RuntimeError("module failure")
    client = MagicMock()

    with pytest.raises(RuntimeError, match="module failure"):
        _ensure_present(client, module, {"PipelineStatus": "Deleting"})

    assert "being deleted and cannot be updated" in module.fail_json.call_args.kwargs["msg"]
    client.update_pipeline.assert_not_called()


@pytest.mark.parametrize("content", [b"not JSON", b"\xff"])
def test_s3_definition_invalid_content_fails_and_closes_body(content):
    client = MagicMock()
    body = BytesIO(content)
    client.get_object.return_value = {"Body": body}
    module = MagicMock()
    module.fail_json.side_effect = RuntimeError("invalid content")

    with pytest.raises(RuntimeError, match="invalid content"):
        get_pipeline_definition_from_s3(client, {"Bucket": "pipeline-bucket", "ObjectKey": "definition.json"}, module)

    assert body.closed
    module.fail_json.assert_called_once()


@pytest.mark.parametrize("purge_tags", [False, True])
def test_reconcile_pipeline_tags_preserves_or_removes_unrequested_tags(monkeypatch, purge_tags):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = False
    module.params = {"pipeline_name": "pipeline", "tags": {"team": "ai"}, "purge_tags": purge_tags}
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.module_utils.sagemaker.list_tags",
        MagicMock(return_value={"suite": "pipeline"}),
    )

    changed, msg = reconcile_pipeline_tags(client, module, {"PipelineArn": "pipeline-arn"})

    assert changed
    assert "updated successfully" in msg
    client.add_tags.assert_called_once_with(ResourceArn="pipeline-arn", Tags=[{"Key": "team", "Value": "ai"}])
    assert client.delete_tags.call_count == int(purge_tags)
    if purge_tags:
        client.delete_tags.assert_called_once_with(ResourceArn="pipeline-arn", TagKeys=["suite"])


def test_reconcile_pipeline_tags_skips_reads_when_tags_omitted(monkeypatch):
    client = MagicMock()
    module = MagicMock()
    module.params = {"pipeline_name": "pipeline", "tags": None}
    list_tags_mock = MagicMock()
    monkeypatch.setattr("ansible_collections.amazon.ai.plugins.module_utils.sagemaker.list_tags", list_tags_mock)

    assert reconcile_pipeline_tags(client, module, {"PipelineArn": "pipeline-arn"}) == (False, "")
    list_tags_mock.assert_not_called()


@pytest.mark.parametrize("value", ["not JSON", None])
def test_parse_json_reports_invalid_input(value):
    module = MagicMock()
    module.fail_json.side_effect = RuntimeError("invalid input")

    with pytest.raises(RuntimeError, match="invalid input"):
        parse_json(value, module, "pipeline_definition")

    assert "pipeline_definition must contain valid JSON" in module.fail_json.call_args.kwargs["msg"]


@pytest.mark.parametrize(
    "pipeline, expected",
    [
        ({"PipelineName": "pipeline"}, {"changed": False, "pipelines": [{"pipeline_name": "pipeline"}]}),
        (None, {"changed": False, "pipelines": []}),
    ],
)
def test_pipeline_info_named_lookup_returns_pipeline_list(monkeypatch, pipeline, expected):
    module = MagicMock()
    module.params = {"pipeline_name": "pipeline", "pipeline_version_id": None}
    module.exit_json.side_effect = RuntimeError("module exit")
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline_info.AnsibleAWSModule",
        MagicMock(return_value=module),
    )
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline_info.describe_pipeline",
        MagicMock(return_value=pipeline),
    )

    with pytest.raises(RuntimeError, match="module exit"):
        pipeline_info_main()

    module.exit_json.assert_called_once_with(**expected)


def test_pipeline_info_describes_each_listed_pipeline(monkeypatch):
    module = MagicMock()
    module.params = {
        "pipeline_name": None,
        "pipeline_version_id": None,
        "pipeline_name_prefix": "pipeline",
        "sort_by": "Name",
        "sort_order": "Ascending",
        "max_items": 2,
    }
    module.exit_json.side_effect = RuntimeError("module exit")
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline_info.AnsibleAWSModule",
        MagicMock(return_value=module),
    )
    list_pipelines_mock = MagicMock(
        return_value=[
            {"PipelineName": "pipeline-one"},
            {"PipelineName": "pipeline-two"},
        ]
    )
    describe_pipeline_mock = MagicMock(
        side_effect=[
            {"PipelineName": "pipeline-one", "PipelineStatus": "Active", "PipelineDefinition": "{}"},
            None,
        ]
    )
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline_info.list_pipelines",
        list_pipelines_mock,
    )
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline_info.describe_pipeline",
        describe_pipeline_mock,
    )

    with pytest.raises(RuntimeError, match="module exit"):
        pipeline_info_main()

    list_pipelines_mock.assert_called_once_with(
        module.client.return_value,
        max_items=2,
        PipelineNamePrefix="pipeline",
        SortBy="Name",
        SortOrder="Ascending",
    )
    assert [call.args[1] for call in describe_pipeline_mock.call_args_list] == ["pipeline-one", "pipeline-two"]
    module.exit_json.assert_called_once_with(
        changed=False,
        pipelines=[
            {"pipeline_name": "pipeline-one", "pipeline_status": "Active", "pipeline_definition": "{}"},
        ],
    )


@pytest.mark.parametrize(
    "params, message",
    [
        ({"pipeline_name": "pipeline", "pipeline_version_id": 0}, "pipeline_version_id must be greater"),
        ({"max_items": 0}, "max_items must be greater than zero"),
        (
            {"pipeline_name_prefix": "pipeline", "sort_by": "CreationTime"},
            "sort_by must be Name when pipeline_name_prefix is supplied",
        ),
    ],
)
def test_pipeline_info_rejects_invalid_parameters_before_connecting(monkeypatch, params, message):
    module = MagicMock()
    module.params = params
    module.fail_json.side_effect = RuntimeError("invalid parameter")
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline_info.AnsibleAWSModule",
        MagicMock(return_value=module),
    )

    with pytest.raises(RuntimeError, match="invalid parameter"):
        pipeline_info_main()

    assert message in module.fail_json.call_args.kwargs["msg"]
    module.client.assert_not_called()


def test_pipeline_info_declares_pipeline_name_required_by_version_id(monkeypatch):
    module = MagicMock()
    module.params = {"pipeline_name": None, "pipeline_version_id": None}
    module.exit_json.side_effect = RuntimeError("module exit")
    ansible_module = MagicMock(return_value=module)
    monkeypatch.setattr(
        "ansible_collections.amazon.ai.plugins.modules.sagemaker_pipeline_info.AnsibleAWSModule",
        ansible_module,
    )

    with pytest.raises(RuntimeError, match="module exit"):
        pipeline_info_main()

    assert ansible_module.call_args.kwargs["required_by"] == {"pipeline_version_id": ["pipeline_name"]}
