# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Expose the AWS module class with amazon.ai user-agent metadata."""

from ansible_collections.amazon.ai.plugins.module_utils.common import AMAZON_AI_COLLECTION_NAME
from ansible_collections.amazon.ai.plugins.module_utils.common import AMAZON_AI_COLLECTION_VERSION

from ansible_collections.amazon.aws.plugins.module_utils.common import set_collection_info
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule as AmazonAWSModule


class AnsibleAWSModule(AmazonAWSModule):
    def __init__(self, **kwargs):
        super(AnsibleAWSModule, self).__init__(**kwargs)
        set_collection_info(
            collection_name=AMAZON_AI_COLLECTION_NAME,
            collection_version=AMAZON_AI_COLLECTION_VERSION,
        )
