# Indirect Node Counts in Ansible Collections

## Overview

In the context of Ansible automation, **indirect node counts** refer to the practice of verifying capacity or availability **by analyzing the output of Ansible modules that interact with external systems**, rather than directly querying the nodes themselves. This approach is especially useful in complex, public cloud, or on-premises environments.

This file explains:
- What indirect node counts are
- Why they are required
- What they enable
- Their value

## What Are Indirect Node Counts?

Standard node counting relies on Ansible connecting to a host. However, in cloud or API-driven automation, the "managed nodes" are often manipulated via a centralized API (like AWS) rather than direct connections.

**Indirect node counts** solve this by inspecting the **return values (JSON payload)** of specific Ansible modules.

For example:
1. A playbook runs `amazon.ai.bedrock_agent_info` to gather facts about your AI/ML environment.
2. The module queries the AWS Bedrock API and returns a list of agents.
3. The controller applies a specific filter (defined in `extensions/audit/event_query.yml`) to that output to count how many unique nodes were automated.

This process is **passive**: it derives counts from the automation that is already running, without initiating separate API requests.

## Why Are They Required?

Directly connecting to every node:
- Is **inefficient** in large-scale environments
- May be **prohibited** due to security, network segmentation, or policy
- **Doesn't scale** across multiple clusters or providers
- Often leads to **incomplete or stale data**

Using indirect node counts via cloud APIs:
- Enables **centralized insight** into resource usage
- Works well in **managed or disconnected environments**
- Allows **non-invasive** assessment (e.g., read-only API access)

## What Does It Do?

In practical terms, using indirect node counts in an Ansible collection:
- Enables **guardrails** to verify what you are automating
- Reduces operational risk and improves **predictability** of automation workflows

## Why This Is a Good Practice

| Benefit | Description |
|--------|-------------|
| Scalable | Works across many clusters and environments |
| Secure | Limits direct access to sensitive nodes |
| Efficient | Avoids per-node polling, uses cached or aggregated data |
| Integrated | Leverages our existing Certified and Validated collections |
| Reliable | Provides consistent data source for automation decisions |

## Supported Resources for Amazon AI/ML Services

The following table details the AWS AI/ML resources currently supported by the NodeQuery logic within the **amazon.ai** collection. To ensure consistent reporting across different services, this extension maps service-specific attributes to a set of **Canonical Facts**.

**What are Canonical Facts?**
Canonical Facts are standardized fields (like `id`, `name`, `tags`, and `status`) that provide a uniform way to identify and assess resources, regardless of the underlying AWS service.

All taxonomy values conform to the Ansible Normalized Resource Taxonomy v1.0 (lowercase snake_case).

The table below details how AWS AI/ML resources are mapped to these canonical facts.

| Category | AWS Resource | Ansible Module | `device_type` | `infra_bucket` | Canonical Fact Mapping |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AI/ML** | **Bedrock Agent** | `bedrock_agent_info` | `ai_agent` | `machine_learning` | `.agent_id` → **id**<br>`.agent_name` → **name**<br>`.tags` → **tags**<br>`.agent_status` → **status** |
| **AI/ML** | **Bedrock Agent Alias** | `bedrock_agent_alias_info` | `ai_agent` | `machine_learning` | `.agent_alias_id` → **id**<br>`.agent_alias_name` → **name**<br>`.tags` → **tags**<br>`.agent_alias_status` → **status** |
| **AI/ML** | **Bedrock Agent Action Group** | `bedrock_agent_action_group_info` | `ai_agent` | `machine_learning` | `.action_group_id` → **id**<br>`.action_group_name` → **name**<br>`.tags` → **tags**<br>`.action_group_state` → **status** |
| **AI/ML** | **Bedrock Foundation Model** | `bedrock_foundation_models_info` | `ai_model` | `machine_learning` | `.model_id` → **id**<br>`.model_name` → **name**<br>`.tags` → **tags** |
| **Observability** | **DevOps Guru Resource Collection** | `devopsguru_resource_collection_info` | `monitoring` | `monitoring` | static **id** and **name** |

## Excluded Modules

- `bedrock_agent` / `bedrock_agent_alias` / `bedrock_agent_action_group` — mutating modules; their `_info` counterparts capture the resources
- `bedrock_invoke_agent` / `bedrock_invoke_model` — invocation modules that run inference, not resource lifecycle
- `devopsguru_resource_collection` — mutating module; `_info` counterpart captures the resource
- `devopsguru_insight_info` — read-only insight queries, not resource management

## Testing and Validation

Reliability is ensured through integration testing. The **extensions/audit/event_query.yml** file is explicitly tested in this collection to verify that the node counting logic works as expected against the supported resources.

### How to Run Integration Tests Locally

To validate the node counting logic yourself, you can run any integration test target prefixed with **node_query_**.

#### Prerequisites

The indirect node counts integration tests have additional dependencies, specifically the `jq` Python bindings. Please run `pip install -r tests/integration/requirements.txt` to ensure all requirements are installed.

#### Command

**Example: Running the Bedrock Node Query Test**

```bash
ansible-test integration node_query_bedrock --no-temp-workdir
```

**Example: Running the DevOps Guru Node Query Test**

```bash
ansible-test integration node_query_devopsguru --no-temp-workdir
```

**Important: The `--no-temp-workdir` Flag**

When running these tests locally, you must include the `--no-temp-workdir` flag.

- **The Problem**: The tests rely on a local helper role, **setup_node_query**, to prepare the environment. Standard **ansible-test** behavior creates a temporary, isolated testing directory that does not automatically copy this helper role (as it is not a production dependency listed in **meta/main.yml**).

- **The Solution**: The `--no-temp-workdir` flag forces **ansible-test** to run in the current directory context, ensuring the test suite can access the **setup_node_query** role.
