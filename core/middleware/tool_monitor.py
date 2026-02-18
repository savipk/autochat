"""
Tool call monitoring middleware for logging and observability.
"""

import logging
import time

from langchain.agents.middleware import wrap_tool_call

logger = logging.getLogger("autochat.tools")


@wrap_tool_call
async def tool_monitor_middleware(request, handler):
    """Logs tool calls with timing information."""
    tool_name = request.tool_call.get("name", "unknown")
    logger.info("Tool call started: %s", tool_name)
    start = time.monotonic()
    try:
        result = await handler(request)
        elapsed = time.monotonic() - start
        logger.info("Tool call completed: %s (%.2fs)", tool_name, elapsed)
        return result
    except Exception:
        elapsed = time.monotonic() - start
        logger.exception("Tool call failed: %s (%.2fs)", tool_name, elapsed)
        raise
