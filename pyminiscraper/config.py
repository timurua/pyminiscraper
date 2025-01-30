from abc import ABC, abstractmethod
from .model import ScraperUrl, ScraperWebPage
from .store import ScraperStoreFactory
import logging
from enum import Enum

logger = logging.getLogger("config")

class ScraperCallbackError(Exception):
    pass

class ScraperLoggingCallback(ABC):
    @abstractmethod
    async def on_log(self, text: str) -> None:
        pass    
    
class ScraperAugmentCallback(ABC):
    @abstractmethod
    async def on_web_page(self, url: ScraperUrl, page: ScraperWebPage) -> None:
        pass
    
    
class ScraperDomainConfigMode(Enum):
    ALLOW_ALL = "allow_all"
    DIREVE_FROM_URLS = "derive_from_seed_urls"
        
class ScraperAllowedDomains:
    def __init__(self, *, domains: list[str] = []):
        self.domains = domains
    
class ScraperDomainConfig:
    def __init__(self, *,
                forbidden_domains: list[str] = [],
                allowance: ScraperDomainConfigMode|ScraperAllowedDomains = ScraperDomainConfigMode.DIREVE_FROM_URLS):        
        self.forbidden_domains = forbidden_domains
        self.allowance = allowance
        
class ScraperConfig:
    def __init__(self, *, 
                seed_urls: list[ScraperUrl],
                include_path_patterns: list[str] = [],
                exclude_path_patterns: list[str] = [],
                max_parallel_requests: int = 16,
                use_headless_browser: bool = False,
                request_timeout_seconds: int = 30,
                follow_web_page_links: bool = False,
                follow_sitemap_links: bool = True,
                follow_feed_links: bool = True,
                max_requested_urls: int = 64 * 1024,
                max_back_to_back_errors: int = 128,
                scraper_store_factory: ScraperStoreFactory,
                log_callback: ScraperLoggingCallback | None = None,
                augment_callback: ScraperAugmentCallback | None = None,
                max_depth: int = 16,
                crawl_delay_seconds: int = 1,
                domain_config: ScraperDomainConfig = ScraperDomainConfig(
                    allowance=ScraperDomainConfigMode.DIREVE_FROM_URLS
                ),
                
                user_agent: str = 'pyminiscraper',):
        self.seed_urls = seed_urls
        self.include_path_patterns = include_path_patterns
        self.exclude_path_patterns = exclude_path_patterns
        self.max_parallel_requests = max_parallel_requests
        self.use_headless_browser = use_headless_browser
        self.request_timeout_seconds = request_timeout_seconds
        self.follow_web_page_links = follow_web_page_links
        self.follow_feed_links = follow_feed_links
        self.follow_sitemap_links = follow_sitemap_links
        self.max_requested_urls = max_requested_urls
        self.store_factory = scraper_store_factory
        self.log_callback = log_callback
        self.augment_callback = augment_callback
        self.max_depth = max_depth
        self.crawl_delay_seconds = crawl_delay_seconds
        self.user_agent = user_agent
        self.max_back_to_back_errors = max_back_to_back_errors
        self.domain_config = domain_config

    async def log(self, text: str) -> None:
        logger.info(text)
        if self.log_callback:
            await self.log_callback.on_log(text)
