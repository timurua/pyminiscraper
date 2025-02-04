from .config import ScraperCallback, ScraperContext
from typing import Optional, override
from .model import ScraperWebPage, ScraperUrl

class MemoryStore(ScraperCallback):
    def __init__(self, store: dict[str, ScraperWebPage]) -> None:
        self.store = store
        
    @override
    async def on_page(self, context: ScraperContext, request: ScraperUrl, response: ScraperWebPage) -> None:
        self.store[response.normalized_url] = response
        
    @override
    async def load_page_from_cache(self, normalized_url: str) -> Optional[ScraperWebPage]:
        return self.store.get(normalized_url)