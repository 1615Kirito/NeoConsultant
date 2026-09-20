import pytest

from finsight_mcp.agent.workflow import build_workflow
from finsight_mcp.mcp_client import local_mcp_tools
from finsight_mcp.llm import llm


@pytest.mark.asyncio
async def test_full_workflow_e2e():
    model = llm()

    async with local_mcp_tools() as tools:

        workflow = build_workflow(
            tools=tools,
            llm=model,
        )

        result = await workflow.ainvoke(
            {
                "ticker": "AAPL",
                "revision_count": 0,
                "max_revisions": 2,
            }
        )

    assert result is not None

    assert "final_report" in result

    assert result["final_report"] is not None

    print("\n========== FINAL REPORT ==========")
    print(
        result["final_report"].model_dump_json(
            indent=2
        )
    )