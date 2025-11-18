# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment:
    # Modules and Plugins can (currently) use the same fragment
    def __init__(self):
        # Minimum requirements for the collection
        requirements = """
options: {}
requirements:
  - python >= 3.9
  - boto3 >= 1.35.0
  - botocore >= 1.35.0
"""

        self.DOCUMENTATION = requirements
        self.MODULES = requirements
