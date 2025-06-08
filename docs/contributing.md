# Contributing to `fabric-mcp`

Thank you for your interest in improving `fabric-mcp`, a Model Context Protocol
server for Fabric AI. Every contribution matters. This guide outlines how to
get started, follow development practices, and submit effective changes.

## Getting Started

### Prerequisites

Ensure the following tools are installed:

* **Python** (>= 3.11)
* **Git**
* **uv** (for dependency and environment management)

Install `uv` using one of the following methods:

```bash
pip install uv
# or
curl -LsSf https://astral.sh/uv/install.sh | sh
# or (macOS)
brew install uv
# or (Windows)
scoop install uv
# or (Linux)
snap install astral-uv
```

Refer to [Astral's documentation][astral-uv-docs] for details.

### Cloning the Repository

```bash
git clone https://github.com/ksylvan/fabric-mcp.git
cd fabric-mcp
```

### Setting Up the Environment

Use `make` to configure the development environment:

```bash
make bootstrap
```

This command uses `uv sync --dev` to install all dependencies into `.venv`, and also configures pre-commit hooks.

## Development Workflow

### Core Tools

| Tool    | Purpose                | Command                     | Config           |
| ------- | ---------------------- | --------------------------- | ---------------- |
| uv      | Environment management | `make bootstrap`            | `pyproject.toml` |
| ruff    | Linting & formatting   | `make format` / `make lint` | `.ruff.toml`     |
| isort   | Import sorting         | Part of `make format`       | `pyproject.toml` |
| pylint  | Linting                | Part of `make lint`         | `.pylintrc`      |
| pyright | Type checking          | Part of `make lint`         | `pyproject.toml` |
| pytest  | Testing                | `make test`                 | `pyproject.toml` |

### Running the Server

```bash
uv run fabric-mcp --help
uv run fabric-mcp --stdio
```

### Common Make Commands

```bash
make format        # Code formatting and import sorting
make lint          # Linting and type checks
make test          # Lint and run all tests
make coverage      # Run tests with coverage enforcement (90%)
make coverage-html # Generate HTML coverage report
make coverage-show # Open HTML coverage in browser
make dev           # Start FastMCP dev server with MCP inspector
make mcp-inspector # Start standalone MCP inspector
make build         # Build the project
make clean         # Remove build/test artifacts
make vulture       # Run the vulture tool (check for dead code)
```

## Code Style and Quality

You are required to follow the guidelines enforced by the linting and CI/CD scripts.

### Formatting

Run `make format` before committing to apply:

* `ruff format`
* `isort`

### Linting

Run `make lint` to:

* Check formatting (`ruff format --check`)
* Lint (`ruff check`, `pylint`)
* Type check (`pyright`)

### Type Checking

Strict type checking via `pyright` ensures reliability and is mandatory on this project.

Run it via `make lint`.

## Testing

### Guidelines

* Use `pytest`
* Place tests in `tests/` (in the `unit/` and `integration/` subdirectories)
* File naming: `test_*.py` or `*_test.py`
* Function names: prefix with `test_`
* Follow AAA pattern: Arrange, Act, Assert
* Use `pytest.raises`, `@pytest.fixture`, and `@pytest.mark.parametrize` as needed

### Running Tests

```bash
make test
```

To run a specific test:

```bash
uv run pytest tests/path/to/test_file.py::test_func
```

### Code Coverage

```bash
make coverage         # Check if coverage >= 90%
make coverage-html    # Generate HTML report
make coverage-show    # Open HTML report
```

## Commit Guidelines

We follow [Conventional Commits][conventional-commits]:

```plaintext
type(scope?): description
```

Examples:

* `feat(api): add session timeout handling`
* `fix(cli): correct argument parsing logic`
* `docs: update contributing guidelines`

Use `!` to mark breaking changes:

* `refactor!: remove deprecated config flags`

Common types:

| Type     | Purpose                          |
| -------- | -------------------------------- |
| feat     | New feature                      |
| fix      | Bug fix                          |
| docs     | Documentation only               |
| style    | Formatting (no logic changes)    |
| refactor | Refactoring (no behavior change) |
| test     | Adding or updating tests         |
| build    | Build system changes             |
| ci       | CI configuration                 |
| chore    | Other changes                    |
| revert   | Revert previous commit           |

## Submitting Changes

1. Create a feature branch:

    ```bash
    git checkout main
    git pull
    git checkout -b feat/my-new-feature
    ```

2. Ensure all checks pass:

    ```bash
    make format
    make lint
    make test
    ```

3. Push and create a PR targeting `develop` (a branch against `main` will be auto-rejected)

## Using the MCP Inspector

There are two ways to use the MCP Inspector:

### Option 1: Using the FastMCP Dev Server (Recommended for Development)

```bash
make dev
```

Then browse to <http://127.0.0.1:6274> and Connect.

### Option 2: Using the Standalone MCP Inspector

```bash
make mcp-inspector
```

This starts the standalone MCP inspector. You'll need to run `fabric-mcp` in a separate terminal with the appropriate transport (http or sse) and connect to it through the inspector interface.

See the [FastMCP documentation][fastmcp-dev] about using the MCP inspector
for more information.

## Configuration Files

* `pyproject.toml`: tool settings (`uv`, `ruff`, `isort`, `pytest`, `pyright`)
* `.ruff.toml`: Ruff linting configuration (overrides `pyproject.toml` if both exist)
* `.pylintrc`: Pylint settings (if present)

## Reporting Issues

Before opening an issue:

* Search existing issues.
* Include relevant logs, commands, and versions.

To request a feature:

* Describe the motivation and use case.

## Need Help?

Read the [detailed guide to contributing][detailed] and it might answer your question.

Open an issue or discussion on GitHub.

---

Thanks for contributing!

[astral-uv-docs]: https://astral.sh/docs/uv/
[conventional-commits]: https://www.conventionalcommits.org/
[detailed]: ./contributing-detailed.md
[fastmcp-dev]: https://gofastmcp.com/deployment/cli#dev
