import aiohttp
from typing import Optional
import logging
from .model import ScraperWebPage
from datetime import datetime

class HttpHtmlScraperError(Exception):
    pass

logger = logging.getLogger("scrape_html_http")

class HttpHtmlScraper:
    def __init__(self, client_session: aiohttp.ClientSession, timeout_seconds: int = 30):
        self.client_session = client_session
        self.timeout_seconds = timeout_seconds

    async def scrape(self, normalized_url: str) -> ScraperWebPage:
        try:
            async with self.client_session.get(normalized_url) as http_response:
                if not http_response.status == 200:
                    logger.error(f"Error fetching {normalized_url}: {http_response.status}")
                    raise HttpHtmlScraperError(f"Error fetching {normalized_url}: {http_response.status}")
                if not http_response.content_type.startswith('text/html'):
                    logger.warning(f"Skipping non-HTML content type {http_response.content_type} for {normalized_url}")
                    raise HttpHtmlScraperError(f"Non html content {normalized_url}: {http_response.status}")
                html_content = await http_response.text()
                page=ScraperWebPage(
                    status_code=http_response.status,
                    headers={str(k): str(v) for k, v in dict(http_response.headers).items()},
                    content=html_content.encode("utf-8") if html_content is not None else None,
                    content_type="text/html",
                    content_charset="utf-8",                    
                    url=normalized_url,
                    normalized_url=normalized_url,
                    requested_at=datetime.now(),
                )
                return page
        except Exception as e: 
            logger.info(f"Failed to fetch page: {normalized_url}")
            raise HttpHtmlScraperError(f"""Failed to fetch page: {normalized_url}""") from e
        


class HttpHtmlScraperFactory:
    def __init__(self, client_session: aiohttp.ClientSession):
        self.client_session = client_session

    async def close(self) -> None:
        await self.client_session.close()

    def new_scraper(self) -> HttpHtmlScraper:
        return HttpHtmlScraper(self.client_session)
