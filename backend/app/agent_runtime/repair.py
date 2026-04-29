"""Repair: wraps tool_repair for the agent to call."""

from app.agent_runtime.tool_registry import tool_repair


def repair_content_pack(
    content_pack: dict, validation_errors: list[str] | None = None
) -> tuple[dict | None, str | None]:
    """
    Repair a content pack deterministically.

    Args:
        content_pack: The content pack to repair.
        validation_errors: Optional list of validation error messages.

    Returns:
        (repaired_content_pack, error_message)
    """
    return tool_repair({"content_pack": content_pack})
