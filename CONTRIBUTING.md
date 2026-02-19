# Contributing to GOLIATH

Thanks for your interest in contributing to GOLIATH! This guide covers everything you need to get started.

## Getting Started

1. Fork the repository and clone your fork:

```bash
git clone https://github.com/your-username/GOLIATH.git
cd GOLIATH
```

2. Install in development mode:

```bash
pip install -e .
pip install pytest ruff
```

3. Run the tests to make sure everything works:

```bash
python -m pytest tests/ -v
```

## Development Workflow

1. Create a branch for your change:

```bash
git checkout -b my-feature
```

2. Make your changes and run checks:

```bash
ruff check src/ tests/
ruff format src/ tests/
python -m pytest tests/ -v
```

3. Commit and push:

```bash
git add <files>
git commit -m "Short description of the change"
git push origin my-feature
```

4. Open a pull request against `master`.

## Code Style

- **Formatter:** [Ruff](https://docs.astral.sh/ruff/) — run `ruff format src/ tests/` before committing.
- **Linter:** Ruff — run `ruff check src/ tests/` and fix any issues.
- CI enforces both lint and format checks on every push and PR.

## Adding a New Integration

1. Create a file in `src/goliath/integrations/` (e.g. `myservice.py`).
2. Follow the existing pattern:
   - Module docstring with setup instructions.
   - A client class (e.g. `MyServiceClient`) with credential validation in `__init__`.
   - Use `requests.Session()` for HTTP calls.
   - Auth tokens in `Authorization` headers (never in URLs or request bodies).
   - Internal `_get`, `_post`, etc. helper methods.
3. Register it in `src/goliath/config.py`:
   - Add environment variables for credentials.
   - Add an entry to the `INTEGRATIONS` dict.
4. Add tests in `tests/` using `unittest.mock` (no real API calls).
5. Update `README.md`:
   - Architecture tree.
   - Integration table.
   - Quick examples section.
   - Configuration reference.

## Adding a New Model Provider

1. Create a file in `src/goliath/models/` (e.g. `my_provider.py`).
2. Subclass `BaseProvider` from `goliath.models.base` and implement `run()`.
3. Register it in `config.py` under `MODEL_PROVIDERS`.
4. Add tests.

## Writing Tests

- All tests use `unittest.mock` to avoid real API calls.
- Use `@patch` to mock `config` and `requests` at the module level.
- Test categories:
  - **Credential validation** — missing keys raise `RuntimeError`.
  - **API calls** — verify URLs, headers, and payloads.
  - **Error handling** — file not found, invalid input, etc.
- Run the full suite before submitting: `python -m pytest tests/ -v`

## Project Structure

```
src/goliath/
  config.py            # API keys, plugin registry
  core/
    engine.py          # Task execution engine
    moderation.py      # Content moderation layer
  models/              # AI model providers
  integrations/        # Third-party service clients
  memory/              # Persistent memory system
  cli/                 # Interactive REPL
tests/                 # All test files
```

## Reporting Issues

- Use [GitHub Issues](https://github.com/zdevelops1/GOLIATH/issues) for bugs and feature requests.
- For security vulnerabilities, see [SECURITY.md](SECURITY.md).

## Code of Conduct

All contributors are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).
