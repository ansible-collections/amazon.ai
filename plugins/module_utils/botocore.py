# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Botocore version validation helpers shared by amazon.ai modules."""

from ansible_collections.amazon.ai.plugins.module_utils.modules import AnsibleAWSAIModule as AnsibleAWSModule


def validate_botocore_version(module: AnsibleAWSModule, minimum_version: str, message: str) -> None:
    """Fail with the supplied message when Botocore is below the required version."""
    if not module.botocore_at_least(minimum_version):
        module.fail_json(msg=message)


def validate_botocore_option(module: AnsibleAWSModule, option: str, minimum_version: str) -> None:
    """Validate a Botocore minimum only when the named module option is supplied."""
    if module.params.get(option) is not None:
        validate_botocore_version(
            module,
            minimum_version,
            f"The {option} option requires botocore >= {minimum_version}.",
        )
