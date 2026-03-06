"""Cross-cutting validation that all template references resolve to real MCP primitives.

Ensures every tool name, resource URI, and format placeholder referenced in
template .md files corresponds to a registered MCP tool, resource, or template.
"""

import asyncio
import importlib.resources
import re

import ynab_mcp.server  # noqa: F401  # Side-effect: registers all MCP handlers
from ynab_mcp.app import mcp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_async(coro):
    """Run an async coroutine synchronously for test introspection.

    Returns:
        The result of the coroutine.
    """
    return asyncio.run(coro)


def _get_registered_tool_names() -> set[str]:
    """Return set of all registered MCP tool names.

    Uses mcp.list_tools() async API (FastMCP public method).
    """
    tools = _run_async(mcp.list_tools())
    return {t.name for t in tools}


def _get_registered_resource_uris() -> set[str]:
    """Return set of all registered MCP static resource URIs.

    Uses mcp.list_resources() async API.
    """
    resources = _run_async(mcp.list_resources())
    return {str(r.uri) for r in resources}


def _get_registered_resource_template_uris() -> set[str]:
    """Return set of all registered MCP resource template URI patterns.

    Uses mcp.list_resource_templates() async API.
    """
    templates = _run_async(mcp.list_resource_templates())
    return {t.uri_template for t in templates}


def _load_all_template_files() -> dict[str, str]:
    """Load all .md template files from the templates package.

    Returns:
        Dict mapping ``subpackage/filename`` to file content.
    """
    templates: dict[str, str] = {}
    for subpackage in ("prompts", "analysis", "workflows"):
        pkg = importlib.resources.files(f"ynab_mcp.templates.{subpackage}")
        for item in pkg.iterdir():
            if hasattr(item, "name") and item.name.endswith(".md"):
                templates[f"{subpackage}/{item.name}"] = item.read_text(
                    encoding="utf-8"
                )
    return templates


# Regex patterns for extracting references from templates
# Matches backtick-quoted tool names like `manage_budgets`
_TOOL_REF_RE = re.compile(r"`(manage_\w+|clear_cache)`")
# Matches ynab:// URIs (with or without {budget_id} placeholder)
_RESOURCE_REF_RE = re.compile(r"`(ynab://[^`]+)`")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestToolReferences:
    """Every tool name referenced in templates is a real registered MCP tool."""

    def test_all_tool_references_exist(self):
        registered_tools = _get_registered_tool_names()
        all_templates = _load_all_template_files()

        missing: list[str] = []
        for filename, content in all_templates.items():
            refs = _TOOL_REF_RE.findall(content)
            missing.extend(
                f"{filename}: `{tool_name}`"
                for tool_name in refs
                if tool_name not in registered_tools
            )

        assert not missing, (
            "Template files reference unregistered tools:\n"
            + "\n".join(f"  - {m}" for m in missing)
        )

    def test_at_least_one_tool_reference_found(self):
        """Sanity check: templates should reference at least some tools."""
        all_templates = _load_all_template_files()
        total_refs = sum(
            len(_TOOL_REF_RE.findall(content)) for content in all_templates.values()
        )
        assert total_refs > 0, "No tool references found in any template"


class TestResourceReferences:
    """Every ynab:// URI in templates matches a registered resource."""

    def test_all_resource_references_exist(self):
        static_uris = _get_registered_resource_uris()
        template_uris = _get_registered_resource_template_uris()
        all_templates = _load_all_template_files()

        missing: list[str] = []
        for filename, content in all_templates.items():
            refs = _RESOURCE_REF_RE.findall(content)
            for uri in refs:
                # Normalize {budget_id} placeholder for comparison
                normalized = uri.replace("{budget_id}", "TEST_ID")
                # Check static resources first
                if uri in static_uris:
                    continue
                # Check against resource templates
                matched = any(
                    normalized == tmpl_uri.replace("{budget_id}", "TEST_ID")
                    for tmpl_uri in template_uris
                )
                if not matched:
                    missing.append(f"{filename}: `{uri}`")

        assert not missing, (
            "Template files reference unregistered resources:\n"
            + "\n".join(f"  - {m}" for m in missing)
        )

    def test_at_least_one_resource_reference_found(self):
        """Sanity check: templates should reference at least some resources."""
        all_templates = _load_all_template_files()
        total_refs = sum(
            len(_RESOURCE_REF_RE.findall(content)) for content in all_templates.values()
        )
        assert total_refs > 0, "No resource references found in any template"


class TestTemplateFormatSafety:
    """All templates format cleanly with standard placeholders."""

    def test_all_templates_format_cleanly(self):
        all_templates = _load_all_template_files()
        errors: list[str] = []

        for filename, content in all_templates.items():
            try:
                content.format(budget_id="test-id", month="2026-01")
            except (KeyError, ValueError, IndexError) as exc:
                errors.append(f"{filename}: {type(exc).__name__}: {exc}")

        assert not errors, "Template files have format issues:\n" + "\n".join(
            f"  - {e}" for e in errors
        )


class TestPromptCount:
    """The expected number of prompts are registered with the MCP server."""

    def test_prompt_count(self):
        """At least 15 prompts registered (3 base + 6 analysis + 6 workflows)."""
        prompts = _run_async(mcp.list_prompts())
        assert len(prompts) >= 15, (
            f"Expected at least 15 prompts, got {len(prompts)}: "
            f"{[p.name for p in prompts]}"
        )
