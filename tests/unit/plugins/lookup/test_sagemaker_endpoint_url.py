# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for the sagemaker_endpoint_url lookup plugin."""

from unittest.mock import MagicMock
from unittest.mock import patch

import botocore.exceptions
import pytest
from ansible_collections.amazon.ai.plugins.lookup.sagemaker_endpoint_url import LookupModule

from ansible.errors import AnsibleLookupError

MOD = "ansible_collections.amazon.ai.plugins.lookup.sagemaker_endpoint_url"
ENDPOINT_NAME = "my-endpoint"
RUNTIME_URL = "https://runtime.sagemaker.us-east-1.amazonaws.com"


def _client_error(code, message="error"):
    return botocore.exceptions.ClientError({"Error": {"Code": code, "Message": message}}, "DescribeEndpoint")


@pytest.fixture(name="lookup_plugin")
def fixture_lookup_plugin():
    lookup = LookupModule()
    lookup.params = {}

    def _get_option(option):
        return lookup.params.get(option)

    lookup.get_option = MagicMock(side_effect=_get_option)
    lookup.client = MagicMock()
    lookup._cached_client = MagicMock()
    lookup.warn = MagicMock()
    return lookup


class TestRuntimeUrl:
    @pytest.mark.parametrize(
        "endpoint_url",
        [
            "https://runtime.sagemaker.us-east-1.amazonaws.com",
            "https://runtime.sagemaker.us-east-1.amazonaws.com/",
        ],
    )
    def test_returns_runtime_endpoint_without_trailing_slash(self, lookup_plugin, endpoint_url):
        lookup_plugin.client.return_value.meta.endpoint_url = endpoint_url

        result = lookup_plugin._runtime_url()

        assert result == "https://runtime.sagemaker.us-east-1.amazonaws.com"

    def test_builds_runtime_client_without_endpoint_override(self, lookup_plugin):
        lookup_plugin.client.return_value.meta.endpoint_url = (
            "https://runtime-fips.sagemaker.us-gov-west-1.amazonaws.com"
        )

        result = lookup_plugin._runtime_url()

        lookup_plugin.client.assert_called_once_with("sagemaker-runtime", endpoint=None)
        assert result == "https://runtime-fips.sagemaker.us-gov-west-1.amazonaws.com"
        lookup_plugin._cached_client.describe_endpoint.assert_not_called()


class TestDescribeEndpoint:
    @patch(f"{MOD}.describe_endpoint")
    def test_returns_endpoint_when_found(self, m_describe, lookup_plugin):
        endpoint = {"EndpointName": ENDPOINT_NAME, "EndpointStatus": "InService"}
        m_describe.return_value = endpoint

        result = lookup_plugin._describe_endpoint(ENDPOINT_NAME)

        assert result == endpoint
        m_describe.assert_called_once_with(lookup_plugin._cached_client, ENDPOINT_NAME)
        lookup_plugin.warn.assert_not_called()

    @pytest.mark.parametrize("on_missing", [None, "error"])
    @patch(f"{MOD}.describe_endpoint", return_value=None)
    def test_missing_endpoint_raises_on_error(self, _m_describe, lookup_plugin, on_missing):
        lookup_plugin.params = {"on_missing": on_missing}

        with pytest.raises(AnsibleLookupError, match=f"^Failed to find SageMaker endpoint {ENDPOINT_NAME}$"):
            lookup_plugin._describe_endpoint(ENDPOINT_NAME)

    @patch(f"{MOD}.describe_endpoint", return_value=None)
    def test_missing_endpoint_warns_on_warn(self, _m_describe, lookup_plugin):
        lookup_plugin.params = {"on_missing": "warn"}

        result = lookup_plugin._describe_endpoint(ENDPOINT_NAME)

        assert result is None
        lookup_plugin.warn.assert_called_once_with(f"Skipping, did not find SageMaker endpoint {ENDPOINT_NAME}")

    @patch(f"{MOD}.describe_endpoint", return_value=None)
    def test_missing_endpoint_skipped_silently_on_skip(self, _m_describe, lookup_plugin):
        lookup_plugin.params = {"on_missing": "skip"}

        result = lookup_plugin._describe_endpoint(ENDPOINT_NAME)

        assert result is None
        lookup_plugin.warn.assert_not_called()

    @patch(f"{MOD}.describe_endpoint")
    def test_access_denied_raises_on_error(self, m_describe, lookup_plugin):
        m_describe.side_effect = _client_error("AccessDeniedException")
        lookup_plugin.params = {"on_denied": "error"}

        with pytest.raises(AnsibleLookupError, match=f"Failed to access SageMaker endpoint {ENDPOINT_NAME}"):
            lookup_plugin._describe_endpoint(ENDPOINT_NAME)

    @patch(f"{MOD}.describe_endpoint")
    def test_access_denied_warns_on_warn(self, m_describe, lookup_plugin):
        m_describe.side_effect = _client_error("AccessDeniedException")
        lookup_plugin.params = {"on_denied": "warn"}

        result = lookup_plugin._describe_endpoint(ENDPOINT_NAME)

        assert result is None
        lookup_plugin.warn.assert_called_once_with(f"Skipping, access denied for SageMaker endpoint {ENDPOINT_NAME}")

    @patch(f"{MOD}.describe_endpoint")
    def test_access_denied_skipped_silently_on_skip(self, m_describe, lookup_plugin):
        m_describe.side_effect = _client_error("AccessDeniedException")
        lookup_plugin.params = {"on_denied": "skip"}

        result = lookup_plugin._describe_endpoint(ENDPOINT_NAME)

        assert result is None
        lookup_plugin.warn.assert_not_called()

    @patch(f"{MOD}.describe_endpoint")
    def test_access_denied_ignores_on_missing(self, m_describe, lookup_plugin):
        m_describe.side_effect = _client_error("AccessDeniedException")
        lookup_plugin.params = {"on_missing": "skip", "on_denied": "error"}

        with pytest.raises(AnsibleLookupError, match="AccessDenied"):
            lookup_plugin._describe_endpoint(ENDPOINT_NAME)

    @pytest.mark.parametrize("on_missing", ["error", "warn", "skip"])
    @patch(f"{MOD}.describe_endpoint")
    def test_other_client_error_always_raises(self, m_describe, lookup_plugin, on_missing):
        m_describe.side_effect = _client_error("ValidationException", "Something else went wrong")
        lookup_plugin.params = {"on_missing": on_missing, "on_denied": "skip"}

        with pytest.raises(AnsibleLookupError, match="Failed to retrieve SageMaker endpoint"):
            lookup_plugin._describe_endpoint(ENDPOINT_NAME)

    @patch(f"{MOD}.describe_endpoint")
    def test_botocore_error_raises(self, m_describe, lookup_plugin):
        m_describe.side_effect = botocore.exceptions.EndpointConnectionError(endpoint_url="https://example")

        with pytest.raises(AnsibleLookupError, match="Failed to retrieve SageMaker endpoint"):
            lookup_plugin._describe_endpoint(ENDPOINT_NAME)


@patch(f"{MOD}.AWSLookupBase.run")
class TestRun:
    @pytest.fixture(name="run_plugin")
    def fixture_run_plugin(self, lookup_plugin):
        lookup_plugin._runtime_url = MagicMock(return_value=RUNTIME_URL)
        lookup_plugin._describe_endpoint = MagicMock(side_effect=lambda term: {"EndpointName": term})
        return lookup_plugin

    def test_passes_arguments_to_base_run(self, m_base_run, run_plugin):
        variables = {"some_var": "value"}

        run_plugin.run([ENDPOINT_NAME], variables, region="us-east-1", on_missing="skip")

        m_base_run.assert_called_once_with([ENDPOINT_NAME], variables, region="us-east-1", on_missing="skip")

    def test_returns_invocation_url_per_term_in_order(self, _m_base_run, run_plugin):
        result = run_plugin.run(["endpoint-b", "endpoint-a"], {})

        assert result == [
            f"{RUNTIME_URL}/endpoints/endpoint-b/invocations",
            f"{RUNTIME_URL}/endpoints/endpoint-a/invocations",
        ]
        assert [c.args for c in run_plugin._describe_endpoint.call_args_list] == [("endpoint-b",), ("endpoint-a",)]

    def test_resolves_runtime_url_once_for_all_terms(self, _m_base_run, run_plugin):
        run_plugin.run(["endpoint-a", "endpoint-b", "endpoint-c"], {})

        run_plugin._runtime_url.assert_called_once_with()

    def test_url_uses_endpoint_name_from_describe_response(self, _m_base_run, run_plugin):
        run_plugin._describe_endpoint.side_effect = None
        run_plugin._describe_endpoint.return_value = {"EndpointName": "My-Endpoint"}

        result = run_plugin.run(["my-endpoint"], {})

        assert result == [f"{RUNTIME_URL}/endpoints/My-Endpoint/invocations"]

    def test_skips_terms_that_resolve_to_none(self, _m_base_run, run_plugin):
        run_plugin._describe_endpoint.side_effect = [None, {"EndpointName": "endpoint-b"}, None]

        result = run_plugin.run(["endpoint-a", "endpoint-b", "endpoint-c"], {})

        assert result == [f"{RUNTIME_URL}/endpoints/endpoint-b/invocations"]

    def test_returns_empty_list_when_nothing_found(self, _m_base_run, run_plugin):
        run_plugin._describe_endpoint.side_effect = None
        run_plugin._describe_endpoint.return_value = None

        result = run_plugin.run(["endpoint-a", "endpoint-b"], {})

        assert result == []

    def test_returns_empty_list_for_no_terms(self, _m_base_run, run_plugin):
        result = run_plugin.run([], {})

        assert result == []
        run_plugin._describe_endpoint.assert_not_called()

    def test_propagates_lookup_error(self, _m_base_run, run_plugin):
        run_plugin._describe_endpoint.side_effect = AnsibleLookupError("Failed to find SageMaker endpoint missing")

        with pytest.raises(AnsibleLookupError, match="Failed to find SageMaker endpoint missing"):
            run_plugin.run(["missing", ENDPOINT_NAME], {})

    @patch(f"{MOD}.describe_endpoint")
    def test_skips_missing_endpoint_end_to_end(self, m_describe, _m_base_run, lookup_plugin):
        lookup_plugin.client.return_value.meta.endpoint_url = f"{RUNTIME_URL}/"
        lookup_plugin.params = {"on_missing": "warn"}
        m_describe.side_effect = [None, {"EndpointName": ENDPOINT_NAME}]

        result = lookup_plugin.run(["missing", ENDPOINT_NAME], {})

        assert result == [f"{RUNTIME_URL}/endpoints/{ENDPOINT_NAME}/invocations"]
        lookup_plugin.warn.assert_called_once_with("Skipping, did not find SageMaker endpoint missing")
