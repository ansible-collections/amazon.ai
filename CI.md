# Continuous Integration (CI)

## AWS Upstream Testing

GitHub Actions are used to run the CI for the amazon.ai collection. The workflows used for the CI can be found [here](https://github.com/ansible-collections/amazon.ai/tree/main/.github/workflows). These workflows include jobs to run the unit tests, sanity tests, linters, and changelog checks.

The collection uses reusable workflows from [ansible-network/github_actions](https://github.com/ansible-network/github_actions) for standardized testing.

To learn more about the testing strategy, see [this proposal](https://github.com/ansible-collections/cloud-content-handbook/blob/main/Proposals/core_collection_dependency.md).

### PR Testing Workflows

The following tests run on every pull request to `main` or `stable-*` branches:

| Job | Description | Python Versions | ansible-core Versions |
| --- | ----------- | --------------- | --------------------- |
| Changelog | Checks for the presence of changelog fragments | 3.12 | devel |
| Linters | Runs `black`, `isort`, `flake8`, `flynt`, and `ansible-lint` via tox | 3.10 | devel |
| Sanity | Runs ansible sanity checks | See compatibility table below | devel, milestone, stable-2.17, stable-2.18, stable-2.19, stable-2.20 |
| Unit tests | Executes unit test cases | See compatibility table below | devel, milestone, stable-2.17, stable-2.18, stable-2.19, stable-2.20 |
| Integration tests | Executes integration test suites (requires protected environment approval) | 3.12 | milestone |

### Python Version Compatibility by ansible-core Version

These are defined by the GitHub Actions workflow exclusions in [sanity.yml](/.github/workflows/sanity.yml) and [units.yml](/.github/workflows/units.yml).

**Note:** The [/tox.ini](/tox.ini) file's `envlist` is currently outdated (only defines ansible 2.17-2.18 with Python 3.10-3.13) and does not reflect the actual CI matrix shown below. The authoritative source is the GitHub Actions workflow files.

| ansible-core Version | Sanity Tests | Unit Tests |
| -------------------- | ------------ | ---------- |
| devel | 3.12, 3.13, 3.14 | 3.12, 3.13, 3.14 |
| milestone | 3.12, 3.13, 3.14 | 3.12, 3.13, 3.14 |
| stable-2.20 | 3.12, 3.13, 3.14 | 3.12, 3.13, 3.14 |
| stable-2.19 | 3.11, 3.12, 3.13 | 3.11, 3.12, 3.13, 3.14 |
| stable-2.18 | 3.11, 3.12, 3.13 | 3.11, 3.12, 3.13, 3.14 |
| stable-2.17 | 3.10, 3.11, 3.12 | 3.10, 3.11, 3.12, 3.14 |

*Note: Unit tests intentionally include Python 3.14 for stable-2.17, stable-2.18, and stable-2.19 even though sanity tests do not. This forward-compatibility testing helps identify issues early.*

### Integration Testing

Integration tests require AWS credentials and run against real AWS services. Unlike the amazon.aws collection (which uses Zuul for integration testing), amazon.ai uses GitHub Actions with a protected environment.

The integration workflow:
- Uses `pull_request_target` trigger for security
- Requires manual approval via GitHub's "protected environment" feature
- Uses Python 3.12 with ansible-core milestone version
- Automatically splits tests across 2 parallel jobs for faster execution
- Sets up AWS credentials via ansible-network/github_actions AWS test provider

To run integration tests locally:
```bash
# Configure AWS credentials first
aws configure set aws_access_key_id     <your-access-key>
aws configure set aws_secret_access_key <your-secret-key>
aws configure set region                <aws-region>

# Run all integration tests
ansible-test integration

# Run specific test target
ansible-test integration bedrock_agent
```

### Linters

The linters job runs multiple code quality checks via tox labels:
- `black-lint`: Python code formatting check (120 char line length)
- `isort-lint`: Import sorting check
- `flake8-lint`: Python style guide enforcement
- `flynt-lint`: F-string formatting check
- `ansible-lint`: Ansible-specific linting

To run linters locally:
```bash
# Run all linters
tox -e black-lint,isort-lint,flake8-lint,flynt-lint,ansible-lint

# Auto-fix formatting issues
tox -e black
tox -e isort
```
