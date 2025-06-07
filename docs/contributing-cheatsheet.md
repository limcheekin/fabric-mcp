# Contributing to `fabric-mcp` (Micro Summary)

## For Developers

```bash
# One-time setup (new contributor)

git clone https://github.com/ksylvan/fabric-mcp.git
cd fabric-mcp
make bootstrap  # ← Installs deps AND pre-commit hooks automatically

# Daily workflow

git checkout develop
git checkout -b feature/my-change

# make changes

# Run tests and ensure coverage targets met
# (testing also runs linters and the "vulture" tool)
make test
make coverage

git commit -m "feat: my changes"  # ← Hooks run, ensure good practices
git push -u origin feature/my-change
```

Submit your PR with `develop` as its base. Your change must pass all automated tests and meet coverage targets.

## Using the MCP Inspector

```bash
make dev
```

Then browse to <http://127.0.0.1:6274> and Connect.

You can also test the http streaming and sse transports by using:

```bash
make mcp-inspector
```

This launches the bare MCP inspector (and does not start `fabric-mcp` with the `stdio` transport)

## Release workflow (for maintainers)

After a PR is merged:

```bash
git checkout develop
git pull
make merge  # ← Safe, confirmed merge to main
```

## For more details

Read the [Contributing guidelines](./contributing.md) and the
[detailed guide to Contributing](./contributing-detailed.md).
