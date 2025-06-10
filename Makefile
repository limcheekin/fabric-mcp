# Makefile for
#

.PHONY: __default _check_unused bootstrap build clean coverage coverage-html \
	coverage-show dev format help lint mcp-inspector merge tag \
	test test-fast test-serial vulture

COVERAGE_FAIL_UNDER := 95
PACKAGE_PATH := src/fabric_mcp
TESTS_PATH := tests


# The node package manager could be npm, but why? pnpm is faster and more efficient
# This is only needed if you are using the fastmcp dev server.
NPM_PACKAGER := pnpm
NPX := $(NPM_PACKAGER) dlx
STDIO_SERVER_SRC_FOR_MCP_INSPECTOR := $(PACKAGE_PATH)/server_stdio.py

VERSION := $(shell uv run hatch version)

__default: help

_check_unused:
	uv run python tests/scripts/check_shared_utils

bootstrap:
	uv sync --dev
	uv run pre-commit autoupdate
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg

build:
	uv run hatch build

clean:
	rm -rf .venv dist node_modules
	find $(PACKAGE_PATH) -name "*.pyc" -delete
	find $(TESTS_PATH) -name "*.pyc" -delete

coverage:
	uv run pytest -n auto --cov=$(PACKAGE_PATH) \
		-ra -q \
		--cov-report=term-missing \
		--cov-fail-under=$(COVERAGE_FAIL_UNDER)

coverage-html:
	# This will generate an HTML coverage report.
	uv run pytest -n auto --cov=$(PACKAGE_PATH) \
		--cov-report=html:coverage_html \
		--cov-fail-under=$(COVERAGE_FAIL_UNDER)

coverage-show:
	# This will open the HTML coverage report in the default web browser.
	@echo "Opening coverage report in the browser..."
	@open coverage_html/index.html || xdg-open coverage_html/index.html || start coverage_html/index.html
	@echo "Done."

# See https://gofastmcp.com/deployment/cli#dev
dev:
	$(NPM_PACKAGER) install @modelcontextprotocol/inspector
	uv run fastmcp dev ${STDIO_SERVER_SRC_FOR_MCP_INSPECTOR}

format:
	uv run ruff format .
	uv run isort .

help:
	@echo "Makefile for fabric_mcp (Version $(VERSION))"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  bootstrap     Bootstrap the project"
	@echo "  build         Build the project"
	@echo "  clean         Clean up the project"
	@echo "  coverage      Run test coverage"
	@echo "  coverage-html Run tests and generate an HTML coverage report."
	@echo "  coverage-show Show the coverage report in the browser."
	@echo "  dev           Start the fastmcp dev server for MCP inspector"
	@echo "  format        Format the codebase"
	@echo "  help          Show this help message"
	@echo "  lint          Run linters"
	@echo "  merge         Merge develop into main branch (bypassing pre-commit hooks)"
	@echo "  mcp-inspector Start the MCP inspector server"
	@echo "  tag           Tag the current git HEAD with the semantic versioning name."
	@echo "  test          Run tests with parallel execution"
	@echo "  test-fast     Run tests with optimized parallel execution (skips linting)"
	@echo "  test-serial   Run tests serially (single-threaded)"
	@echo "  vulture       Run Vulture to check for dead code and unused imports"

lint: vulture
	uv run ruff format --check .
	uv run ruff check .
	uv run pylint --fail-on=W0718 $(PACKAGE_PATH) $(TESTS_PATH)
	uv run pyright $(PACKAGE_PATH) $(TESTS_PATH)

merge:
	@echo "This will merge develop into main and push to origin."
	@git diff-index --quiet HEAD -- || { echo "Error: Working directory not clean. Please commit or stash your changes before proceeding."; exit 1; }
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || { echo "Merge aborted."; exit 1; }
	@echo "Merging develop into main..."
	@current_branch=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$current_branch" != "develop" ]; then \
		echo "Error: You must be on the develop branch to run this command."; \
		echo "Current branch: $$current_branch"; \
		exit 1; \
	fi
	@echo "Ensuring develop is up to date..."
	git pull origin develop
	@echo "Switching to main..."
	git checkout main
	@echo "Pulling latest main..."
	git pull origin main
	@echo "Merging develop into main (bypassing pre-commit hooks)..."
	git merge develop --no-verify || { echo "Error: Merge failed. Please resolve conflicts and try again."; exit 1; }
	@echo "Pushing to main..."
	git push origin main
	@echo "Switching back to develop..."
	git checkout develop
	@echo "Merge completed successfully!"

mcp-inspector:
	@echo "Starting MCP inspector server..."
	@echo "Ensure you have the @modelcontextprotocol/inspector package installed."
	@echo "If not, run 'make dev' to install it."
	@echo "Start fabric-mcp in a different terminal window with the http transport."
	@echo ""
	$(NPX) @modelcontextprotocol/inspector

tag:
	git tag v$(VERSION)

test: lint test-fast

test-fast:
	uv run pytest -v -n auto

test-serial: lint
	uv run pytest -v

# Vulture - static analysis for dead code
# Also checks for unimported .py files in tests/shared/
vulture: _check_unused
	uv run vulture
