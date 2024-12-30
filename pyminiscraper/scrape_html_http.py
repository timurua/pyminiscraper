import asyncio
import aiohttp
from typing import Optional
import logging
from .model import ScraperWebPage
from .model import ScraperUrl


logger = logging.getLogger("scrape_html_http")

class HttpHtmlScraper:
    def __init__(self, client_session: aiohttp.ClientSession, timeout_seconds: int = 30):
        self.client_session = client_session
        self.timeout_seconds = timeout_seconds

    async def scrape(self, url: ScraperUrl) -> Optional[ScraperWebPage]:
        try:
            async with self.client_session.get(url.normalized_url) as http_response:
                if not http_response.status == 200:
                    logger.error(f"Error fetching {url}: {http_response.status}")
                    return None
                if not http_response.content_type.startswith('text/html'):
                    logger.warning(f"Skipping non-HTML content type {http_response.content_type} for {url}")
                    return None
                html_content = await http_response.text()

                page=ScraperWebPage(
                    status_code=http_response.status,
                    headers={str(k): str(v) for k, v in dict(http_response.headers).items()},
                    content=html_content.encode("utf-8") if html_content is not None else None,
                    content_type="text/html",
                    content_charset="utf-8",                    
                    url=url.normalized_url,
                    normalized_url=url.normalized_url,
                )
                return page
                
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Error fetching {url}: {e}")
        except (aiohttp.ClientResponseError, aiohttp.ClientPayloadError) as e:
            logger.error(f"Error receiving response for {url}: {e}")
        except (UnicodeDecodeError) as e:            
            logger.error(f"Error decoding text for {url}: {e}")
            
        return None
        


class HttpHtmlScraperFactory:
    def __init__(self, *, timeout_seconds: int = 30, user_agent: str):
        self.client_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False),
            headers={
                'User-Agent': user_agent
            })
        self.timeout_seconds = timeout_seconds

    async def close(self) -> None:
        await self.client_session.close()

    def new_scraper(self) -> HttpHtmlScraper:
        return HttpHtmlScraper(self.client_session, self.timeout_seconds)
