# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import Any
from typing import Dict
from typing import List

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


def get_model_details(client, model_id: str) -> Dict[str, Any]:
    """
    Retrieves detailed information about a specific foundation model using the
    Bedrock `get_foundation_model` API.

    Args:
        client (boto3.client): A Boto3 Bedrock client.
        model_id (str): The identifier of the foundation model to retrieve.

    Returns:
        Dict[str, Any]: A dictionary containing the model details, with keys converted
                        to snake_case. Returns an empty dictionary if no details are found.
    """
    response = client.get_foundation_model(modelIdentifier=model_id)
    return camel_dict_to_snake_dict(response.get("modelDetails", {}))


def list_models_with_filters(module: AnsibleAWSModule, client) -> List[Dict[str, Any]]:
    """
    Retrieves a list of foundation models using the Bedrock `list_foundation_models` API,
    optionally filtering by provider, customization type, output modality, or inference type.

    Args:
        module (AnsibleAWSModule): The Ansible AWS module instance containing user parameters.
        client (boto3.client): A Boto3 Bedrock client.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing model summaries,
                              with keys converted to snake_case. Returns an empty list if no models are found.
    """
    params: Dict[str, Any] = {}

    if module.params.get("by_provider"):
        params["byProvider"] = module.params["by_provider"]

    if module.params.get("by_customization_type"):
        params["byCustomizationType"] = module.params["by_customization_type"]

    if module.params.get("by_output_modality"):
        params["byOutputModality"] = module.params["by_output_modality"]

    if module.params.get("by_inference_type"):
        params["byInferenceType"] = module.params["by_inference_type"]

    response = client.list_foundation_models(**params)
    return [camel_dict_to_snake_dict(model) for model in response.get("modelSummaries", [])]
