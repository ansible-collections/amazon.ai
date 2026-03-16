# Continuous Integration (CI)

## Amazon AI Upstream Testing

GitHub Actions are used to run the CI for the amazon.ai collection. The workflows used for the CI can be found in the [.github/workflows](.github/workflows) directory.

### PR Testing Workflows

The following tests run on every pull request to `main` or `stable-*` branches:

| Job | Description | Python Versions | ansible-core Versions |
| --- | ----------- | --------------- | --------------------- |
| [Changelog](.github/workflows/changelog.yml) | Checks for the presence of changelog fragments | 3.12 | devel |
| [Linters](.github/workflows/linters.yml) | Runs `black`, `isort`, `flake8`, `flynt`, and `ansible-lint` via tox | 3.10 | N/A |
| [Sanity](.github/workflows/sanity.yml) | Runs ansible sanity checks | See compatibility table below | devel, milestone, stable-2.17, stable-2.18, stable-2.19, stable-2.20 |
| [Unit tests](.github/workflows/units.yml) | Executes unit test cases | See compatibility table below | devel, milestone, stable-2.17, stable-2.18, stable-2.19, stable-2.20 |
| [Integration](.github/workflows/integration.yml) | Executes integration test suites (requires protected environment approval) | 3.12 | milestone |

**Note:** Integration tests require live AWS services and use GitHub's protected environment feature for credential security.

### Python Version Compatibility by ansible-core Version

These are outlined in the GitHub Actions workflow exclusions in [sanity.yml](.github/workflows/sanity.yml) and [units.yml](.github/workflows/units.yml).

| ansible-core Version | Sanity Tests | Unit Tests |
| -------------------- | ------------ | ---------- |
| devel | 3.12, 3.13, 3.14 | 3.12, 3.13, 3.14 |
| milestone | 3.12, 3.13, 3.14 | 3.12, 3.13, 3.14 |
| stable-2.20 | 3.12, 3.13, 3.14 | 3.12, 3.13, 3.14 |
| stable-2.19 | 3.11, 3.12, 3.13 | 3.11, 3.12, 3.13, 3.14 |
| stable-2.18 | 3.11, 3.12, 3.13 | 3.11, 3.12, 3.13, 3.14 |
| stable-2.17 | 3.10, 3.11, 3.12 | 3.10, 3.11, 3.12, 3.14 |
