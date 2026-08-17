# SEC EDGAR Data Fetching Client


import httpx

from finsight_mcp_starter.src.finsight_mcp.schemas import CompanyFactsSummary


class SECEdgarError(RuntimeError):
    pass


class SECEdgarClient:
    BASE_URL = "https://data.sec.gov"

    def __init__(
        self,
        settings: Settings,
    ):
        self.settings = settings

    @property
    def headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.settings.sec_user_agent,
            "Accept-Encoding": "gzip, deflate",
        }



async def get_cik(
    self,
    ticker: str,
) -> str:

    url = (
        "https://www.sec.gov/files/"
        "company_tickers.json"
    )

    async with httpx.AsyncClient(
        timeout=30.0,
        headers=self.headers,
    ) as client:

        response = await client.get(url)

        response.raise_for_status()

    data = response.json()

    ticker = ticker.upper()

    for company in data.values():

        if company["ticker"].upper() == ticker:

            cik = str(
                company["cik_str"]
            ).zfill(10)

            return cik

    raise SECEdgarError(
        f"Could not find CIK for {ticker}"
    )


async def get_company_facts_raw(
    self,
    cik: str,
) -> dict:

    url = (
        f"{self.BASE_URL}/api/xbrl/"
        f"companyfacts/CIK{cik}.json"
    )

    async with httpx.AsyncClient(
        timeout=30.0,
        headers=self.headers,
    ) as client:

        response = await client.get(url)

        response.raise_for_status()

    return response.json()


def _latest_usd_value(
    facts: dict,
    concept_names: list[str],
) -> float | None:

    us_gaap = facts.get(
        "facts",
        {}
    ).get(
        "us-gaap",
        {}
    )

    for concept_name in concept_names:

        concept = us_gaap.get(
            concept_name
        )

        if not concept:
            continue

        usd_values = (
            concept
            .get("units", {})
            .get("USD", [])
        )

        if not usd_values:
            continue

        candidates = [
            item
            for item in usd_values
            if item.get("form")
            in {"10-K", "10-Q"}
        ]

        if not candidates:
            continue

        latest = max(
            candidates,
            key=lambda x: x.get(
                "filed",
                ""
            ),
        )

        return float(
            latest["val"]
        )

    return None


async def get_company_facts(
    self,
    ticker: str,
) -> CompanyFactsSummary:

    ticker = ticker.upper()

    cik = await self.get_cik(
        ticker
    )

    data = await self.get_company_facts_raw(
        cik
    )

    revenue = _latest_usd_value(
        data,
        [
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Revenues",
        ],
    )

    net_income = _latest_usd_value(
        data,
        [
            "NetIncomeLoss",
        ],
    )

    assets = _latest_usd_value(
        data,
        [
            "Assets",
        ],
    )

    liabilities = _latest_usd_value(
        data,
        [
            "Liabilities",
        ],
    )

    source_url = (
        f"{self.BASE_URL}/api/xbrl/"
        f"companyfacts/CIK{cik}.json"
    )

    return CompanyFactsSummary(
        ticker=ticker,
        revenue=revenue,
        net_income=net_income,
        assets=assets,
        liabilities=liabilities,
        source_id=f"sec_edgar:{cik}:companyfacts",
        source_url=source_url,
    )