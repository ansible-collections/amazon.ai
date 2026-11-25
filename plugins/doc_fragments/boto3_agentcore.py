# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment:
    def __init__(self):
        requirements = """
options: {}
requirements:
  - python >= 3.9
  - boto3 >= 1.39.7
  - botocore >= 1.39.7
"""

        self.DOCUMENTATION = requirements
        self.MODULES = requirements
