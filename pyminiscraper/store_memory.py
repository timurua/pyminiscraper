from .store import ScraperStore, ScraperStoreFactory
from typing import Optional
from .model import ScraperWebPage

class MemoryStoreFactory(ScraperStoreFactory):
    def __init__(self) -> None:
        self.store: dict[str, ScraperWebPage] = {}
    
    def new_store(self) -> ScraperStore:
        return MemoryStore(self.store)

class MemoryStore(ScraperStore):
    def __init__(self, store: dict[str, ScraperWebPage]) -> None:
        self.store = store
        
    async def store_page(self, response: ScraperWebPage) -> None:
        self.store[response.normalized_url] = response
        
    async def load_page(self, normalized_url: str) -> Optional[ScraperWebPage]:
        return self.store.get(normalized_url)