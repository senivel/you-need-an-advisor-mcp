"""Cross-cutting validation that all template references resolve to real MCP primitives.

Ensures every tool name, resource URI, and format placeholder referenced in
template .md files corresponds to a registered MCP tool, resource, or template.
"""

import asyncio
import importlib
import importlib.resources
import re
import typing

import ynaa_mcp.server  # noqa: F401  # Side-effect: registers all MCP handlers
from ynaa_mcp.app import mcp


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
        pkg = importlib.resources.files(f"ynaa_mcp.templates.{subpackage}")
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
# Matches action="value" patterns (with or without tool name on same line)
_ACTION_VALUE_RE = re.compile(r'action="(\w+)"')


def _get_valid_actions_for_tool(tool_name: str) -> set[str]:
    """Return the set of valid Literal action values for a manage_* tool.

    Dynamically imports the tool module, introspects the function's ``action``
    parameter type hint, and extracts the ``Literal`` members.

    Args:
        tool_name: Registered MCP tool name (e.g. ``manage_categories``).

    Returns:
        Set of valid action strings, or empty set if tool has no action param.
    """
    # manage_budgets -> budgets, manage_scheduled_transactions -> scheduled
    parts = tool_name.split("_", 1)
    if len(parts) < 2:
        return set()
    # Map tool name to module: manage_scheduled_transactions -> scheduled
    module_suffix = parts[1]
    # The module name matches the last segment for multi-word tools
    # e.g. manage_scheduled_transactions -> ynaa_mcp.tools.scheduled
    module_name = f"ynaa_mcp.tools.{module_suffix}"
    try:
        mod = importlib.import_module(module_name)
    except ModuleNotFoundError:
        # Try stripping to first word: scheduled_transactions -> scheduled
        module_name = f"ynaa_mcp.tools.{module_suffix.split('_')[0]}"
        mod = importlib.import_module(module_name)
    func = getattr(mod, tool_name, None)
    if func is None:
        return set()
    hints = typing.get_type_hints(func)
    action_hint = hints.get("action")
    if action_hint is None:
        return set()
    args = typing.get_args(action_hint)
    return set(args)


def _extract_action_references(
    content: str,
) -> list[tuple[str, str]]:
    """Extract (tool_name, action_value) pairs from template content.

    Walks the content line by line, tracking the most recently seen
    ``manage_*`` tool name. When an ``action="..."`` pattern is found,
    it is paired with that tool name. This handles both inline references
    (tool and action on same line) and multi-line references (tool on a
    preceding line).

    Returns:
        List of (tool_name, action_value) tuples.
    """
    refs: list[tuple[str, str]] = []
    current_tool: str | None = None
    for line in content.splitlines():
        # Update current tool if a manage_* reference appears on this line
        tool_matches = _TOOL_REF_RE.findall(line)
        if tool_matches:
            # Use the last tool reference on the line (most proximate)
            last_manage = [t for t in tool_matches if t.startswith("manage_")]
            if last_manage:
                current_tool = last_manage[-1]
        # Check for action references on this line
        action_matches = _ACTION_VALUE_RE.findall(line)
        if action_matches and current_tool:
            refs.extend((current_tool, action) for action in action_matches)
    return refs


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


class TestActionReferences:
    """Every action="..." value in templates is a valid Literal for its tool."""

    def test_all_action_references_valid(self):
        all_templates = _load_all_template_files()

        # Build cache of valid actions per tool
        valid_actions_cache: dict[str, set[str]] = {}

        invalid: list[str] = []
        for filename, content in all_templates.items():
            refs = _extract_action_references(content)
            for tool_name, action_value in refs:
                if tool_name not in valid_actions_cache:
                    valid_actions_cache[tool_name] = _get_valid_actions_for_tool(
                        tool_name
                    )
                valid = valid_actions_cache[tool_name]
                if valid and action_value not in valid:
                    invalid.append(
                        f'{filename}: `{tool_name}` action="{action_value}"'
                        f" (valid: {sorted(valid)})"
                    )

        assert not invalid, (
            "Template files reference invalid action values:\n"
            + "\n".join(f"  - {i}" for i in invalid)
        )

    def test_at_least_one_action_reference_found(self):
        """Sanity check: templates should reference at least some actions."""
        all_templates = _load_all_template_files()
        total_refs = sum(
            len(_extract_action_references(content))
            for content in all_templates.values()
        )
        assert total_refs > 0, "No action references found in any template"


class TestPromptCount:
    """The expected number of prompts are registered with the MCP server."""

    def test_prompt_count(self):
        """At least 15 prompts registered (3 base + 6 analysis + 6 workflows)."""
        prompts = _run_async(mcp.list_prompts())
        assert len(prompts) >= 15, (
            f"Expected at least 15 prompts, got {len(prompts)}: "
            f"{[p.name for p in prompts]}"
        )
