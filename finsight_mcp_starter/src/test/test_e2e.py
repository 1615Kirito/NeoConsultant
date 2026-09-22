import pytest

from finsight_mcp.agent.workflow import build_workflow
from finsight_mcp.mcp_client import local_mcp_tools
from finsight_mcp.llm import llm


import json
from pathlib import Path
from datetime import datetime


def save_report(report, ticker: str):
    output_dir = Path("reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = output_dir / f"{ticker}_{timestamp}.json"

    if hasattr(report, "model_dump"):
        data = report.model_dump(mode="json")
    else:
        data = report

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    return json_path


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

    report_final = result["final_report"]

    path = save_report(report_final, "AAPL")

    print(f"\nReport saved to: {path}")