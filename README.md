# Popcorn Meter

Popcorn Meter is a Python project built with Poetry. It includes a Streamlit UI and a layered package structure for application logic, infrastructure integrations, and tests.

## Project Structure

```bash
<root>
|-- popcorn_meter/              # main package
|   |-- __init__.py
|   |-- __main__.py             # launches the Streamlit app
|   |-- application/            # use cases and ports
|   |-- infrastructure/         # OMDb + SQLite adapters
|   `-- ui/                     # Streamlit frontend
|-- tests/                      # unit/integration/ui tests
|-- .github/workflows/          # CI/CD workflows
|-- pyproject.toml              # Poetry configuration
|-- requirements.txt            # Poetry bootstrap dependency
|-- release.config.mjs          # semantic-release config
`-- renovate.json               # dependency update automation
```

## Development

Install dependencies:

```bash
pip install -r requirements.txt
poetry install
```

Run tests:

```bash
poetry run poe test
```

Run static checks:

```bash
poetry run poe static-checks
```

Format code:

```bash
poetry run poe format
```

Run the app:

```bash
python -m popcorn_meter
```

or:

```bash
poetry run popcorn-meter
```

## CI/CD and Releases

- CI runs checks and tests on push and pull request via GitHub Actions.
- Releases are managed by semantic-release through `.github/workflows/deploy.yml`.
- Publish credentials are expected in repository secrets:
- `PYPI_USERNAME` (use `__token__`)
- `PYPI_PASSWORD` (PyPI API token)
- `RELEASE_TOKEN` (GitHub token for release automation)

## Dependency Updates

Renovate is configured via `renovate.json` to open and manage dependency update pull requests.
