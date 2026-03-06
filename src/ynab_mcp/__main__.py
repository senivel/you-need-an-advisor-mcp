"""Entry point for ``python -m ynab_mcp`` and ``uvx ynab-mcp``."""

from ynab_mcp.server import mcp


def main() -> None:
    """Run the YNAB MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
