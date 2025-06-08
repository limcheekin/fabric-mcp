# Contributing to `fabric-mcp`

- [Contributing to `fabric-mcp`](#contributing-to-fabric-mcp)
  - [Introduction](#introduction)
    - [Welcome and Project Overview](#welcome-and-project-overview)
    - [Importance of these Guidelines](#importance-of-these-guidelines)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Cloning the Repository](#cloning-the-repository)
    - [Setting up the Development Environment](#setting-up-the-development-environment)
  - [Development Workflow](#development-workflow)
    - [Core Tools Overview](#core-tools-overview)
    - [Running the Project](#running-the-project)
    - [Common `make` Commands](#common-make-commands)
  - [Code Style and Quality Standards](#code-style-and-quality-standards)
    - [Formatting](#formatting)
    - [Linting](#linting)
    - [Type Checking](#type-checking)
  - [Testing](#testing)
    - [Writing Tests](#writing-tests)
    - [Running Tests](#running-tests)
    - [Code Coverage](#code-coverage)
    - [Using the MCP Inspector](#using-the-mcp-inspector)
      - [Option 1: FastMCP Dev Server (Recommended for Development)](#option-1-fastmcp-dev-server-recommended-for-development)
      - [Option 2: Standalone MCP Inspector](#option-2-standalone-mcp-inspector)
  - [Commit Message Guidelines](#commit-message-guidelines)
    - [Conventional Commits Standard](#conventional-commits-standard)
    - [Importance of Clear Messages](#importance-of-clear-messages)
    - [Table: Common Conventional Commit Types](#table-common-conventional-commit-types)
    - [Breaking Changes](#breaking-changes)
  - [Submitting Changes](#submitting-changes)
    - [Branching Strategy](#branching-strategy)
    - [Creating a Pull Request (PR)](#creating-a-pull-request-pr)
    - [PR Validation Process](#pr-validation-process)
  - [Understanding Project Configuration (`pyproject.toml` and `.ruff.toml`)](#understanding-project-configuration-pyprojecttoml-and-rufftoml)
    - [Role of `pyproject.toml`](#role-of-pyprojecttoml)
    - [Ruff Configuration (`.ruff.toml` or `pyproject.toml`)](#ruff-configuration-rufftoml-or-pyprojecttoml)
    - [Key Sections in `pyproject.toml`](#key-sections-in-pyprojecttoml)
  - [Reporting Bugs and Suggesting Enhancements](#reporting-bugs-and-suggesting-enhancements)
    - [Before Submitting an Issue](#before-submitting-an-issue)
    - [Reporting a Bug](#reporting-a-bug)
    - [Suggesting an Enhancement](#suggesting-an-enhancement)
  - [Questions or Need Help?](#questions-or-need-help)

## Introduction

### Welcome and Project Overview

Welcome to the `fabric-mcp` project! We are thrilled that you are interested in contributing. `fabric-mcp` aims to provide a Model Context Protocol server for Fabric AI.
Every contribution, regardless of its size, is highly valued and plays a crucial role in the growth and improvement of the project. This is a merit-based and results-focused engineering project.

### Importance of these Guidelines

This document provides a set of guidelines for contributing to `fabric-mcp`. Adhering to these guidelines helps ensure a smooth, consistent, and effective collaboration process for everyone involved. Following these practices helps maintain code quality, ensures consistency across the codebase, and makes the review process more straightforward and efficient for maintainers and contributors alike.

## Getting Started

This section will guide new contributors through the process of setting up their local development environment for `fabric-mcp`.

### Prerequisites

Before you begin, ensure you have the following software installed on your system:

- **Python:** `fabric-mcp` requires Python (as specified in `pyproject.toml`, e.g., `>=3.11`).
- **Git:** For version control and interacting with the GitHub repository.
- **`uv` (Python Package Installer and Manager):**
  - The `fabric-mcp` project uses `uv` for managing Python dependencies and virtual environments. `uv` is chosen for its significant speed improvements and efficient handling of these tasks.
  - If you do not have `uv` installed, you can install it via several methods:
    - Using `pip`:

    ```bash
    pip install uv
    ```

    - Using `curl` (Linux/macOS):

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    - Using Homebrew (macOS):

    ```bash
    brew install uv
    ```

    - Using Scoop (Windows):

    ```bash
    scoop install uv
    ```

    - Using Snap (Linux distributions that support Snap):

    ```bash
    snap install astral-uv
    ```

  Refer to the official Astral `uv` [documentation][astral-uv-docs] for additional information.

### Cloning the Repository

To get a local copy of the project, clone the `fabric-mcp` repository from GitHub:

```bash
git clone https://github.com/ksylvan/fabric-mcp.git
cd fabric-mcp
```

### Setting up the Development Environment

The `fabric-mcp` project uses a `Makefile` to streamline the setup process. To create the virtual environment and install all necessary dependencies (including development dependencies), simply run:

```bash
make bootstrap
```

This command executes `uv sync --dev` which sets up the `.venv` virtual environment and installs all packages defined in `pyproject.toml`. This single command ensures your development environment is correctly configured.

We also install pre-commit hooks at this step to prevent direct commits into `develop` and `main`. All fixes
and feature work will be done on branches in your fork.

## Development Workflow

This section describes the common tasks and tools used during the development of `fabric-mcp`.

### Core Tools Overview

Contributors will primarily interact with the following tools, largely configured via `pyproject.toml` and/or dedicated configuration files like `.ruff.toml`:

| Tool | Primary Purpose | Key Command(s) (via `make` or `uv run`) | Configured In |
| :--- | :--- | :--- | :--- |
| `uv` | Env/Package manager, Task Runner | `make bootstrap`, `uv run <task>` | `pyproject.toml` |
| `ruff` | Linting & Formatting | `make format`, `make lint` | `pyproject.toml`, `.ruff.toml` |
| `isort` | Import Sorting | `make format` (`uv run isort .`) | `pyproject.toml` (often via `ruff` or standalone) |
| `pylint` | Linting (additional checks) | `make lint` (`uv run pylint`) | `pyproject.toml` (or `.pylintrc`) |
| `pytest` | Automated Testing | `make test` (`uv run pytest`) | `pyproject.toml` |
| `pyright` | Static Type Checking | `make lint` (`uv run pyright`) | `pyproject.toml` |
| `vulture` | Check for dead code, unused variables/functions | `make vulture` (`uv run vulture`) | `pyproject.toml` |

This table offers a consolidated summary, helping contributors quickly identify the main tools, their functions, common commands, and their configuration sources.

### Running the Project

To run the `fabric-mcp` server locally, use the following command:

```plaintext
$ uv run fabric-mcp -help
usage: fabric-mcp [-h] [--version] [--stdio] [-l {debug,info,warning,error,critical}]

A Model Context Protocol server for Fabric AI.

options:
  -h, --help            show this help message and exit
  --version             Show the version number and exit.
  --stdio               Run the server in stdio mode (default).
  -l {debug,info,warning,error,critical}, --log-level {debug,info,warning,error,critical}
                        Set the logging level (default: info)
```

For example, to run the server with default settings:

```bash
uv run fabric-mcp
```

### Common `make` Commands

The `Makefile` provides convenient shortcuts for common development tasks. Below are key commands from the `Makefile`:

| `make` command | Description | Underlying `uv run` / other commands (from Makefile) |
| :--- | :--- | :--- |
| `make bootstrap` | Sets up the development environment and installs all dependencies. | `uv sync --dev` |
| `make format` | Formats the codebase using Ruff and sorts imports using isort. | `uv run ruff format.`<br>`uv run isort .` |
| `make lint` | Runs format checks, Ruff linter, Pylint, and Pyright type checker. | `uv run ruff format --check .`<br>`uv run ruff check .`<br>`uv run pylint --fail-on=W0718 fabric_mcp tests`<br>`uv run pyright fabric_mcp tests` |
| `make test` | Runs linters (including type checks) and then the automated test suite. | `make lint`<br>`uv run pytest -v` |
| `make coverage` | Runs tests and reports code coverage, failing if below threshold. | `uv run pytest --cov=fabric_mcp -ra -q --cov-report=term-missing --cov-fail-under=90` |
| `make coverage-html` | Runs tests and generates an HTML code coverage report. | `uv run pytest --cov=fabric_mcp --cov-report=html:coverage_html --cov-fail-under=90` |
| `make coverage-show` | Opens the HTML coverage report in the browser. | `open coverage_html/index.html \|\| xdg-open coverage_html/index.html \|\| start coverage_html/index.html` |
| `make dev` | Starts the FastMCP dev server with MCP inspector for interactive testing. | `pnpm install @modelcontextprotocol/inspector`<br>`uv run fastmcp dev src/fabric_mcp/server_stdio.py` |
| `make mcp-inspector` | Starts the standalone MCP inspector for connecting to running servers. | `pnpm dlx @modelcontextprotocol/inspector` |
| `make build` | Builds the package. | `uv run hatch build` |
| `make clean` | Removes temporary build, test, and environment artifacts. | `rm -rf .venv && rm -rf dist` |
| `make tag` | Tags the current git HEAD with the semantic version. | `git tag v$(VERSION)` (where VERSION is from `uv run hatch version`) |

## Code Style and Quality Standards

Maintaining a consistent code style and high code quality is required for the `fabric-mcp` project.

### Formatting

Consistent code formatting improves readability and reduces cognitive load.

- **Tools:** `ruff format` and `isort`
  - `fabric-mcp` uses `ruff format` for general code formatting, configured to be compatible with the `black` style.
  - `isort` is used specifically for organizing imports.
- **Configuration:**
  - `ruff`'s formatting rules are configured within `pyproject.toml` and/or a `.ruff.toml` file. If both exist in the same directory, `.ruff.toml` takes precedence over `pyproject.toml` for Ruff's settings. Key enforced rules typically include line length (e.g., 100 characters) and quote style.
  - `isort` is configured in `pyproject.toml` (usually under `[tool.isort]` or `[tool.ruff.lint.isort]` if managed by Ruff).
- **How to Run:**
  - To format your code and sort imports, run the following command from the project root:

    ```bash
    make format
    ```

    This command executes `uv run ruff format.` and `uv run isort.`. It is required to run this command before committing any changes.

### Linting

Linting helps identify potential errors, stylistic issues, and anti-patterns.

- **Tools:** `ruff check` and `pylint`
  - `fabric-mcp` employs `ruff check` for a wide range of linting tasks, leveraging its speed and comprehensive rule set
  - `pylint` is used for additional, deeper static analysis.
- **Configuration:**
  - `ruff`'s linting behavior is defined in `pyproject.toml` and/or `.ruff.toml` (with `.ruff.toml` taking precedence). This includes selected rule sets (e.g., `flake8-bugbear`, `pylint` equivalents) and any ignored rules.
  - `pylint` is typically configured via `pyproject.toml` or a dedicated `.pylintrc` file. The `Makefile` shows it's run with `--fail-on=W0718`.
- **How to Run:**
  - To check your code for formatting consistency, linting issues (with Ruff and Pylint), and perform type checking (with Pyright), run:

    ```bash
    make lint
    ```

    This command executes `uv run ruff format --check.`, `uv run ruff check.`, `uv run pylint --fail-on=W0718 fabric_mcp tests`, and `uv run pyright fabric_mcp tests`.

    NOTE: Contributors **must** run this and resolve any reported issues before submitting pull requests.

### Type Checking

Static type checking helps catch type-related errors early, improving code reliability and maintainability.

- **Tool:** `pyright`
  - `fabric-mcp` uses `pyright` for static type analysis.
- **Configuration:**
  - `pyright` is configured in `pyproject.toml` under the `[tool.pyright]` section.
  - `fabric-mcp` enforces strict type checking. Refer to the `[tool.pyright]` section in `pyproject.toml` for the exact set of enforced rules.
- **How to Run:**
  - Type checking is performed as part of the linting process. Run:

    ```bash
    make lint
    ```

    This command includes the execution of `uv run pyright fabric_mcp tests`. All type errors must be resolved before submitting a pull request.

## Testing

Ensuring that code is thoroughly tested is vital for the stability, reliability, and maintainability of `fabric-mcp`.

### Writing Tests

All new features and bug fixes should be accompanied by tests.

- **Framework:** `pytest`
  - `fabric-mcp` uses `pytest` as its testing framework.
- **Test File Location and Naming:**
  - Test files should be located in the `tests/` directory.
  - Test files must follow the naming convention `test_*.py` or `*_test.py`.
  - Test functions or methods within these files must be prefixed with `test_`.
- **Best Practices:**
  - **Test One Feature at a Time:** Each test should focus on a single, specific aspect.
  - **Clear and Descriptive Naming:** Names should clearly describe what is being tested.
  - **Arrange, Act, Assert (AAA):** Structure tests clearly.
  - **Mock External Dependencies:** Isolate code under test. `pytest-mock` or `unittest.mock` can be used.
  - **Test for Expected Exceptions:** Use `pytest.raises`.
  - **Keep Tests DRY with Fixtures and Parametrization:** Use `@pytest.fixture` for reusable setup and `@pytest.mark.parametrize` for running tests with multiple inputs.

### Running Tests

Execute tests regularly during development.

- **Command to Run All Tests (includes linting and type checking):**

    ```bash
    make test
    ```

    This command first runs `make lint` (which includes `ruff format --check.`, `ruff check.`, `pylint...`, and `pyright...`), and then executes `uv run pytest -v`.
- **Running Specific Tests (without full linting beforehand):**
  - To run specific `pytest` tests directly:
    - `uv run pytest tests/module/test_specific_file.py`
    - `uv run pytest tests/module/test_specific_file.py::test_particular_function`
    - `uv run pytest -k "keyword_expression"`
    - `uv run pytest -m "marker"`

### Code Coverage

Code coverage analysis helps identify parts of the codebase not exercised by the test suite.

- **Importance:** High coverage is a useful metric for test thoroughness.
- **Tool:** `pytest-cov` (integrated with `pytest`).
- **Expected Coverage Threshold:**
  - `fabric-mcp` aims for a minimum code coverage of 90%.
  - Pull requests that decrease coverage below this threshold or fail to meet it for new code may be blocked.
- **How to Generate and View the Coverage Report:**
  - To run tests and generate a coverage report (including checking the threshold):

    ```bash
    make coverage
    ```

    This command runs `uv run pytest --cov=fabric_mcp -ra -q --cov-report=term-missing --cov-fail-under=90`.
- To generate an HTML report for detailed viewing:

    ```bash
    make coverage-html
    ```

    Then open the report using:

    ```bash
    # OS-agnostic - this will work on a modern macOS, Linux, or Windows host.
    make coverage-show
    ```

    The HTML report can be found at `coverage_html/index.html`.

### Using the MCP Inspector

The MCP Inspector is an interactive developer tool for testing and debugging MCP (Model Context Protocol) servers.
There are two ways to use the MCP Inspector with `fabric-mcp`:

#### Option 1: FastMCP Dev Server (Recommended for Development)

The FastMCP library provides a CLI tool for running our FastMCP-based servers and accessing the
MCP inspector in an integrated development environment.

```bash
make dev
```

This runs the following commands:

```bash
pnpm install @modelcontextprotocol/inspector
uv run fastmcp dev src/fabric_mcp/server_stdio.py
```

After running `make dev` you can browse to <http://127.0.0.1:6274> and Connect.

#### Option 2: Standalone MCP Inspector

For more advanced testing scenarios or when you need to connect to a separately running `fabric-mcp` server:

```bash
make mcp-inspector
```

This starts the standalone MCP inspector using:

```bash
pnpm dlx @modelcontextprotocol/inspector
```

When using this option, you'll need to:

1. Start `fabric-mcp` in a separate terminal with the appropriate transport (http or sse)
2. Connect to the running server through the inspector interface

See the [FastMCP documentation][fastmcp-dev] about using the MCP inspector
for more information.

## Commit Message Guidelines

Clear, consistent, and informative commit messages are crucial.

### Conventional Commits Standard

`fabric-mcp` adheres to the [**Conventional Commits**][conventional-commits] specification.

- **Structure:**

    ```plaintext
    <type>[optional scope]: <description>

    [optional body]

    [optional footer(s)]
    ```

- **Key Components:**

  - **`type`:** (e.g., `feat`, `fix`, `docs`). Must be lowercase.
  - **`scope` (optional):** (e.g., `(api)`, `(cli)`).
  - **`description`:** Concise summary in imperative mood, lowercase, no period.
  - **`body` (optional):** Detailed explanation.
  - **`footer(s)` (optional):** Issue references (e.g., `Closes #123`), breaking changes.

### Importance of Clear Messages

- Improved Readability.
- Better Collaboration.
- Automated Changelogs.
- Automated Versioning (SemVer).

### Table: Common Conventional Commit Types

| Type | Description | Corresponds to SemVer |
| :--- | :--- | :--- |
| `feat` | A new feature | MINOR |
| `fix` | A bug fix | PATCH |
| `docs` | Documentation only changes | None |
| `style` | Code style changes (formatting, linting) | None |
| `refactor` | Code change that neither fixes a bug nor adds a feature | None / PATCH |
| `perf` | A code change that improves performance | PATCH |
| `test` | Adding missing tests or correcting existing tests | None |
| `build` | Changes affecting build system or external dependencies | PATCH |
| `ci` | Changes to CI configuration files and scripts | None |
| `chore` | Other changes not modifying `src` or `test` files | None |
| `revert` | Reverts a previous commit | PATCH |

### Breaking Changes

- Append `!` after `type` or `scope`: `feat(auth)!: remove deprecated endpoint`.
- and include `BREAKING CHANGE:` in the footer.
- Results in a MAJOR version bump.

## Submitting Changes

Process for contributing code via Pull Requests (PRs).

### Branching Strategy

- **Feature Branches:** Create from `main` (or the primary development branch).

    ```bash
    git checkout main
    git pull upstream main
    git checkout -b feature/my-new-widget
    ```

- **Naming Conventions:** `feature/<description>`, `fix/<issue>-<description>`, `docs/<area>`.

### Creating a Pull Request (PR)

- **Before Submitting, Ensure:**
    1. Code formatted: `make format`.
    2. Linters and type checks pass: `make lint`.
    3. All tests pass: `make test`. (This includes `make lint` implicitly).
    4. Coverage maintained/improved: `make coverage`.
    5. Clear, compliant commit messages.
    6. Branch is up-to-date with the target branch (rebase preferred).

        ```bash
        git fetch upstream
        git rebase upstream/main
        ```

- **PR Title and Description:**
  - **PR Title:** Follow Conventional Commits format.
  - **PR Description:** Explain what, why, and how to test. Link relevant issues.

### PR Validation Process

- **Automated Checks (GitHub Actions):**
  - Triggered on PR submission.
  - Checks typically include:
    - Formatting & Linting: `make lint` (which runs `ruff format --check`, `ruff check`, `pylint`, and `pyright`).
    - Tests: `make test` (which also runs `make lint` first).
    - Coverage: `make coverage`.
    - Build: `make build`.
  - All checks must pass.
- **Code Review:**
  - Maintainers will review your code.
  - Be responsive to feedback and engage constructively.

## Understanding Project Configuration (`pyproject.toml` and `.ruff.toml`)

The `pyproject.toml` file is central to the project's structure and tooling. Ruff may also use a `.ruff.toml` file.

### Role of `pyproject.toml`

It's the standard configuration file for:

- Project metadata (name, version, etc.).
- Dependencies (runtime and development/optional).
- Build system requirements.
- Configuration for `uv`, `isort`, `pytest`, `pyright`, `pylint`, and potentially `ruff`.

### Ruff Configuration (`.ruff.toml` or `pyproject.toml`)

Ruff can be configured via `pyproject.toml` (under `[tool.ruff]`), a dedicated `ruff.toml`, or `.ruff.toml`. If multiple configuration files are present in the same directory, `.ruff.toml` takes precedence over `ruff.toml`, which in turn takes precedence over `pyproject.toml` for Ruff's settings.

### Key Sections in `pyproject.toml`

- **`[project]`**: Core metadata (name, version, `requires-python`, `dependencies`).
- **`[tool.uv.dev-dependencies]`**: Development dependencies (as used by `make bootstrap` via `uv sync --dev`).
- **`[tool.ruff]`**: Configuration for `ruff` linter and formatter (if not in a separate `.ruff.toml` or `ruff.toml`).
  - `[tool.ruff.lint]`
  - `[tool.ruff.format]`
  - `[tool.ruff.lint.isort]` (if isort is managed via ruff)
- **`[tool.isort]`**: Configuration for `isort` (if configured standalone).
- **`[tool.pytest.ini_options]`**: `pytest` configuration.
- **`[tool.pyright]`**: `pyright` type checker configuration.
- **`[tool.pylint]`**: `pylint` configuration (often ``, etc.).
- **`[build-system]`**: Build backend and requirements (e.g., `hatchling`).

## Reporting Bugs and Suggesting Enhancements

Use the GitHub Issue tracker for `fabric-mcp`.

### Before Submitting an Issue

1. **Search Existing Issues.**
2. **Use the Latest Version.**
3. **Gather Information.**

### Reporting a Bug

Include:

- Clear Title.
- Steps to Reproduce.
- Expected Behavior.
- Actual Behavior (error messages, tracebacks).
- Environment Details (`fabric-mcp` version, Python version, OS).

### Suggesting an Enhancement

Include:

- Clear Title.
- Detailed Explanation (value, use cases, problem solved).
- Potential Implementation (Optional).

## Questions or Need Help?

- **Primary Channel:** GitHub Issue tracker for `fabric-mcp`.

Thank you for your interest in contributing to `fabric-mcp`!

[astral-uv-docs]: https://github.com/astral-sh/uv#readme
[conventional-commits]: https://www.conventionalcommits.org/en/v1.0.0/#summary
[fastmcp-dev]: https://gofastmcp.com/deployment/cli#dev
