from abc import ABC, abstractmethod
from .model import ScraperUrl
from .store import ScraperStoreFactory
from .domain_filter import DomainFilter
import logging

logger = logging.getLogger("config")

class ScraperCallback(ABC):
    @abstractmethod
    def on_log(self, text: str) -> None:
        pass

class ScraperConfig:
    def __init__(self, *, scraper_urls: list[ScraperUrl],
                max_parallel_requests: int = 16,
                use_headless_browser: bool = False,
                timeout_seconds: int = 30,
                only_sitemaps: bool = True,
                max_requested_urls: int = 64 * 1024,
                max_back_to_back_errors: int = 128,
                scraper_store_factory: ScraperStoreFactory,
                allow_l2_domains: bool = True,
                scraper_callback: ScraperCallback | None = None,
                max_depth: int = 16,
                max_requests_per_hour: float = 60*60*10,
                rerequest_after_hours: int = 24,
                no_page_store: bool = False,
                user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/115.0.0.0 Safari/537.36',):
        self.scraper_urls = scraper_urls
        self.max_parallel_requests = max_parallel_requests
        self.domain_filter = DomainFilter(allow_l2_domains, [url.url for url in scraper_urls])
        self.use_headless_browser = use_headless_browser
        self.timeout_seconds = timeout_seconds
        self.only_sitemaps = only_sitemaps
        self.max_requested_urls = max_requested_urls
        self.scraper_store_factory = scraper_store_factory
        self.scraper_callback = scraper_callback
        self.max_depth = max_depth
        self.max_requests_per_hour = max_requests_per_hour
        self.user_agent = user_agent
        self.max_back_to_back_errors = max_back_to_back_errors
        if no_page_store:
            self.rerequest_after_hours = 0
        else:
            self.rerequest_after_hours = rerequest_after_hours

    def log(self, text: str) -> None:
        logger.info(text)
        if self.scraper_callback:
            self.scraper_callback.on_log(text)
