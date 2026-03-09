"""Entry point for ``python -m ynaa_mcp`` and ``uvx --from you-need-an-advisor-mcp ynaa-mcp``."""

from ynaa_mcp.server import mcp


def main() -> None:
    """Run the YNAB MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
