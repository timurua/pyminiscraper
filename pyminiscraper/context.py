import aiohttp
from typing import AsyncGenerator, Any, override
from .model import ScraperUrl, ScraperWebPage
from .config import ScraperContext


class ScraperContextImpl(ScraperContext):
    def __init__(self, client_session: aiohttp.ClientSession):
        self.client_session = client_session
        self.should_prevent_default_queuing = False
        self.queued_urls: list[ScraperUrl] = []

    @override
    async def do_request(self, url: str) -> AsyncGenerator[aiohttp.ClientResponse, Any]:
        async with self.client_session.get(url) as http_response:
            yield http_response
            
    @override
    async def equeue_url(self, url: ScraperUrl) -> None:
        self.queued_urls.append(url)        
    
    @override    
    def prevent_default_queuing(self) -> None:
        self.should_prevent_default_queuing = True
    
class ScraperRequestContext:
    def __init__(self, context: ScraperContext, url: ScraperUrl, response: ScraperWebPage):
        self.context = context
        self.url = url
        self.response = response
        
        