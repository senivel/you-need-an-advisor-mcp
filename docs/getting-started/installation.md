# Installation

## Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** -- Python package and project manager
- **YNAB Personal Access Token** -- Required for API authentication

## Get a YNAB Personal Access Token

1. Log in to [YNAB](https://app.ynab.com/)
2. Go to **Account Settings** > **Developer Settings** ([direct link](https://app.ynab.com/settings/developer))
3. Click **New Token** and follow the prompts
4. Copy the token -- you'll need it for configuration

!!! warning

    Keep your token secret. It provides full access to your YNAB account data.

## Install

=== "uvx (recommended)"

    Run directly without installing -- the simplest option:

    ```bash
    uvx --from you-need-an-advisor-mcp ynaa-mcp
    ```

    This downloads and runs the latest version in an isolated environment. No project setup needed.

=== "pip install"

    Install as a package:

    ```bash
    pip install you-need-an-advisor-mcp
    ```

    Or with uv:

    ```bash
    uv add you-need-an-advisor-mcp
    ```

=== "Development setup"

    Clone and install for development:

    ```bash
    git clone https://github.com/senivel/you-need-an-advisor-mcp.git
    cd you-need-an-advisor-mcp
    uv sync --group dev --group docs
    uv run pre-commit install
    ```

    See the [Contributing guide](../contributing/index.md) for full development setup details.

## Next steps

Head to the [Quickstart](quickstart.md) to configure your MCP client and start asking questions about your budget.
