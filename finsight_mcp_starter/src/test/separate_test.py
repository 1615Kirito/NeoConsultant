from finsight_mcp.mcp_client import local_mcp_tools
import asyncio


async def main():

    async with local_mcp_tools() as tools:

        result = await tools.call(
            "get_recent_news",
            {
                "ticker": "AAPL",
            },
        )

        print(result)


asyncio.run(main())