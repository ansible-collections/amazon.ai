# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
name: sagemaker_endpoint_url
author:
  - Domen Dobnikar (@domendobnikar)
short_description: Look up the invocation URL of a SageMaker endpoint
description:
  - Returns the HTTPS URL used to invoke a deployed Amazon SageMaker real-time endpoint, one URL for each endpoint name given.
  - The endpoint is described first, so a name that does not exist is reported according to O(on_missing).
options:
  _terms:
    description: The names of the SageMaker endpoints.
    required: true
    type: list
    elements: str
  on_missing:
    description:
      - Action to take if the endpoint does not exist.
      - V(error) will raise a fatal error when the endpoint is missing.
      - V(skip) will silently ignore the missing endpoint.
      - V(warn) will skip over the missing endpoint but issue a warning.
    default: error
    type: str
    choices: ["error", "skip", "warn"]
  on_denied:
    description:
      - Action to take if access to the endpoint is denied.
      - V(error) will raise a fatal error when access to the endpoint is denied.
      - V(skip) will silently ignore the denied endpoint.
      - V(warn) will skip over the denied endpoint but issue a warning.
    default: error
    type: str
    choices: ["error", "skip", "warn"]
notes:
  - Required IAM actions include sagemaker:DescribeEndpoint.
seealso:
  - module: amazon.ai.sagemaker_endpoint
  - module: amazon.ai.sagemaker_endpoint_info
extends_documentation_fragment:
  - amazon.ai.boto3
  - amazon.ai.common.plugins
  - amazon.ai.region.plugins
"""

EXAMPLES = r"""
- name: Look up the invocation URL of an endpoint
  ansible.builtin.debug:
    msg: "{{ lookup('amazon.ai.sagemaker_endpoint_url', 'my-endpoint', region='us-east-1') }}"

- name: Look up several endpoints, skipping any that do not exist
  ansible.builtin.set_fact:
    endpoint_urls: "{{ query('amazon.ai.sagemaker_endpoint_url', 'endpoint-a', 'endpoint-b', on_missing='skip') }}"
"""

RETURN = r"""
_raw:
  description:
    - The invocation URL of each SageMaker endpoint found, in the order the names were given.
  type: list
  elements: str
  sample:
    - "https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/my-endpoint/invocations"
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_endpoint

from ansible_collections.amazon.aws.plugins.plugin_utils.lookup import AWSLookupBase
from ansible_collections.amazon.aws.plugins.plugin_utils.lookup import LookupErrorHandler
from ansible_collections.amazon.aws.plugins.plugin_utils.lookup import LookupResourceNotFoundError


class LookupModule(AWSLookupBase):
    _SERVICE = "sagemaker"

    def run(self, terms, variables, **kwargs) -> List[str]:
        super().run(terms, variables, **kwargs)

        runtime_url = self._runtime_url()
        results = []
        for term in terms:
            endpoint = self._describe_endpoint(term)
            if endpoint is None:
                continue
            results.append(f"{runtime_url}/endpoints/{endpoint['EndpointName']}/invocations")
        return results

    def _runtime_url(self) -> str:
        # endpoint=None drops any endpoint_url override, so botocore resolves the regional
        # SageMaker Runtime host (honouring partition and FIPS settings). No API call is made.
        return self.client("sagemaker-runtime", endpoint=None).meta.endpoint_url.rstrip("/")

    @LookupErrorHandler.handle_lookup_errors("SageMaker endpoint")
    def _describe_endpoint(self, term) -> Optional[Dict[str, Any]]:
        endpoint = describe_endpoint(self.aws_client, term)
        if endpoint is None:
            raise LookupResourceNotFoundError(
                term,
                error_template="Failed to find SageMaker endpoint {term}",
                warn_template="Skipping, did not find SageMaker endpoint {term}",
            )
        return endpoint
