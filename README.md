# Popcorn Meter

Popcorn Meter is a desktop/web movie recommendation application with a Streamlit GUI, developed in Python for a University Software Engineering project, built using Streamlit, Poetry, OMDb integration, and the template provided by the University course.

---

Discover movies, build your watchlist, track watched titles, and get personalized recommendations based on your preferences and activity.

The application combines:
- account-based preferences and history
- OMDb movie metadata
- explainable recommendation logic (genres, actors, ratings, plot signals, and feedback)

Popcorn Meter runs on Windows, Linux, and macOS.

A Streamlit Cloud demo is available at [`https://popcornmeter.streamlit.app/`](https://popcornmeter.streamlit.app/).

---

## To start the software application

This software project is tested with Python 3.10 and above. The recommended Python version is 3.12+.

1) Clone the repository locally:

```bash
git clone https://github.com/unibo-dtm-se-2324-POPCORNMETER/artifact.git
```

2) Go into the project directory:

```bash
cd artifact
```

3) Install the required dependencies:

```bash
pip install -r requirements.txt
poetry install
```

4) (Optional) configure local API secrets for app features:

Create `.streamlit/secrets.toml` with:

```toml
OMDB_API_KEY = "your_omdb_key"
TMDB_API_KEY = "your_tmdb_key"
```

5) Launch the application:

```bash
poetry run popcorn-meter
```

Or:

```bash
poetry run python -m popcorn_meter
```

## Development commands

Run tests:

```bash
poetry run poe test
```

Run coverage:

```bash
poetry run poe coverage
poetry run poe coverage-report
poetry run poe coverage-html
```

Run static checks:

```bash
poetry run poe static-checks
```

Format code:

```bash
poetry run poe format
```

## Further resources

[`Project documentation`](https://github.com/unibo-dtm-se-2324-POPCORNMETER/report)

[`TestPyPI page`](https://test.pypi.org/project/popcorn-meter/)

[`Ethar Ali (GitHub)`](https://github.com/EtharMAli)

[`Kosar Emazahery (GitHub)`](https://github.com/kosaremazahery)

[`Link to the project template`](https://github.com/unibo-dtm-se/template-python-project)

## Project structure

Overview:
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
|-- release.config.js          # semantic-release config
`-- renovate.json               # dependency update automation
```
