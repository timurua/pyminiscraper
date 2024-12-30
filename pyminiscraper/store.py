from typing import Optional
from .model import ScraperWebPage
from abc import ABC, abstractmethod

class ScraperStore(ABC):
        @abstractmethod
        async def store_page(self, response: ScraperWebPage) -> None:
            pass

        @abstractmethod
        async def load_page(self, normalized_url: str) -> Optional[ScraperWebPage]:
            pass

class ScraperStoreFactory(ABC):
    @abstractmethod
    def new_store(self) -> ScraperStore:
        pass        

