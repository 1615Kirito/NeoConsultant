# test_real_sec_edgar.py

import pytest

from finsight_mcp.clients.sec_edgar import SECEdgarClient
from finsight_mcp.config import settings

@pytest.mark.asyncio
async def test_real_sec_edgar():
    client = SECEdgarClient(settings)

    result = await client.get_company_facts("AAPL")

    print("\n=== SEC EDGAR REAL DATA ===")
    print(result)

    assert result is not None