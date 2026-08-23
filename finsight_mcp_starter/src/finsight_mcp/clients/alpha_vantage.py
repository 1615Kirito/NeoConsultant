# Alpha Vantage Data Fetching Client

from datetime import datetime, timezone

import httpx

from finsight_mcp.schemas import (
    NewsBundle,
    NewsItem,
    PriceHistory,
    PricePoint,
)

# Settings
from finsight_mcp.config import Settings


class AlphaVantageError(RuntimeError):
    pass


class AlphaVantageClient:
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(
        self,
        settings: Settings,
    ):
        self.settings = settings

    async def _get(
        self,
        params: dict,
    ) -> dict:
        """
        Send request to Alpha Vantage API.
        """

        request_params = {
            **params,
            "apikey": self.settings.alpha_vantage_api_key,
        }

        async with httpx.AsyncClient(
            timeout=30.0,
        ) as client:
            response = await client.get(
                self.BASE_URL,
                params=request_params,
            )

            response.raise_for_status()

        data = response.json()

        # Alpha Vantage often returns errors inside a 200 response
        if "Error Message" in data:
            raise AlphaVantageError(
                data["Error Message"]
            )

        if "Information" in data:
            raise AlphaVantageError(
                data["Information"]
            )

        if "Note" in data:
            raise AlphaVantageError(
                data["Note"]
            )

        return data

    async def get_price_history(
        self,
        ticker: str,
    ) -> PriceHistory:

        ticker = ticker.upper()

        data = await self._get(
            {
                "function": "TIME_SERIES_DAILY",
                "symbol": ticker,
                "outputsize": "compact",
            }
        )

        raw_series = data.get(
            "Time Series (Daily)"
        )

        if not raw_series:
            raise AlphaVantageError(
                f"No price history returned for {ticker}"
            )

        prices = []

        for date_str, values in raw_series.items():
            prices.append(
                PricePoint(
                    date=date_str,
                    open=float(values["1. open"]),
                    high=float(values["2. high"]),
                    low=float(values["3. low"]),
                    close=float(values["4. close"]),
                    volume=int(values["5. volume"]),
                )
            )

        prices.sort(
            key=lambda p: p.date
        )

        return PriceHistory(
            ticker=ticker,
            prices=prices,
            source_id=f"alpha_vantage:{ticker}:daily",
            source_url=self.BASE_URL,
            date_time=datetime.now(timezone.utc),
        )

    async def get_recent_news(
        self,
        ticker: str,
    ) -> NewsBundle:

        ticker = ticker.upper()

        data = await self._get(
            {
                "function": "NEWS_SENTIMENT",
                "tickers": ticker,
                "limit": 20,
            }
        )

        raw_articles = data.get(
            "feed",
            [],
        )

        articles = []

        for item in raw_articles:

            sentiment_score = None

            ticker_sentiment = item.get(
                "ticker_sentiment",
                [],
            )

            for sentiment in ticker_sentiment:
                if sentiment.get("ticker") == ticker:
                    score = sentiment.get(
                        "ticker_sentiment_score"
                    )

                    if score is not None:
                        sentiment_score = float(score)

                    break

            published_at = item.get(
                "time_published",
                "",
            )

            publication_date = None

            if published_at:
                try:
                    publication_date = datetime.strptime(
                        published_at,
                        "%Y%m%dT%H%M%S",
                    ).date()
                except ValueError:
                    publication_date = None

            articles.append(
                NewsItem(
                    title=item.get(
                        "title",
                        "",
                    ),
                    summary=item.get(
                        "summary",
                        "",
                    ),
                    source_id=(
                        f"alpha_vantage_news:"
                        f"{ticker}:"
                        f"{published_at}"
                    ),
                    source_url=item.get(
                        "url",
                        "",
                    ),
                    published_at=published_at,
                    publication_date=publication_date,
                    sentiment_score=sentiment_score,
                )
            )

        return NewsBundle(
            ticker=ticker,
            articles=articles,
        )