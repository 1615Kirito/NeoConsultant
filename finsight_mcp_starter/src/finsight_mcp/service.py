from finsight_mcp.config import settings
from finsight_mcp.llm import llm
from finsight_mcp.mcp_client import local_mcp_tools
from finsight_mcp.agent.workflow import build_workflow


async def generate_report(
    ticker: str,
    days: int = 100,
    news_limit: int = 10,
):
    model = llm()

    async with local_mcp_tools() as tools:
        workflow = build_workflow(
            tools=tools,
            llm=model,
        )

        result = await workflow.ainvoke({
            "ticker": ticker.upper(),
            "days": days,
            "news_limit": news_limit,
        })

    return result["report"]