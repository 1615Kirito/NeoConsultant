from __future__ import annotations

import json
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


class MCPToolClient:
    def __init__(self, session: ClientSession):
        self.session = session

    async def call(self, name: str, arguments: dict) -> dict:
        result = await self.session.call_tool(name, arguments)

        if result.structuredContent is not None:
            return result.structuredContent

        for content in result.content:
            if isinstance(content, types.TextContent):
                try:
                    return json.loads(content.text)
                except json.JSONDecodeError:
                    return {"text": content.text}

        raise RuntimeError(
            f"MCP tool {name!r} returned no parseable content."
        )


@asynccontextmanager
async def local_mcp_tools() -> AsyncIterator[MCPToolClient]:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "finsight_mcp.mcp_server"],
        env=os.environ.copy(),
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield MCPToolClient(session)