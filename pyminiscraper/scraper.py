import asyncio
from typing import Optional, Dict
import logging
from urllib.parse import urlparse, urljoin
from .scrape_html_http import HttpHtmlScraperFactory
from .scrape_html_browser import BrowserHtmlScraperFactory
from .model import ScraperWebPage, ScraperUrl
import sys
from .store import ScraperStore, ScraperStoreFactory
from .url_normalize import normalize_url
from abc import ABC, abstractmethod
from .model import ScraperUrl
from .domain_filter import DomainFilter
from .extract import extract_metadata
from .stats import DomainStats, ScraperStats, analyze_url_groups
from .domain_metadata import DomainMetadata
from .sitemap import SitemapParser
from .robots import RobotFileParser

logger = logging.getLogger("scraper")

class ScraperCallback(ABC):
    @abstractmethod
    def on_log(self, text: str) -> None:
        pass

class InMemoryScraperStore(ScraperStore):
    def __init__(self):
        self.responses = {}

    async def store_page(self, response: ScraperWebPage) -> None:
        self.responses[response.normalized_url] = response

    async def load_page(self, normalized_url: str) -> Optional[ScraperWebPage]:
        return self.responses.get(normalized_url)


class ScraperConfig:
    def __init__(self, *, scraper_urls: list[ScraperUrl],
                max_parallel_requests: int = 16,
                use_headless_browser: bool = False,
                timeout_seconds: int = 30,
                max_requested_urls: int = 64 * 1024,
                max_queue_size: int = 1024 * 1024,
                scraper_store_factory: ScraperStoreFactory | None = None,
                allow_l2_domains: bool = True,
                scraper_callback: ScraperCallback | None = None,
                user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/115.0.0.0 Safari/537.36',):
        self.scraper_urls = scraper_urls
        self.max_parallel_requests = max_parallel_requests
        self.domain_filter = DomainFilter(allow_l2_domains, [url.url for url in scraper_urls])
        self.max_queue_size = max_queue_size
        self.use_headless_browser = use_headless_browser
        self.timeout_seconds = timeout_seconds
        self.max_requested_urls = max_requested_urls
        self.scraper_store_factory = scraper_store_factory
        self.scraper_callback = scraper_callback
        self.user_agent = user_agent

    def log(self, text: str) -> None:
        logger.info(text)
        if self.scraper_callback:
            self.scraper_callback.on_log(text)


class ScraperLoopResult:
    def __init__(self, completed_url_count: int):
        self.completed_urls_count = completed_url_count


class Scraper:
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.domain_metadata: Dict[str, asyncio.Task[DomainMetadata]] = {}
        self.initiated_urls: set[str] = set()
        self.completed_urls: set[str] = set()
        self.initiated_urls_count = 0
        self.requested_urls_count = 0
        self.completed_urls_count = 0
        self.url_queue: asyncio.Queue[ScraperUrl] = asyncio.Queue(
            maxsize=config.max_queue_size)
        self.http_html_scraper_factory = HttpHtmlScraperFactory(user_agent=config.user_agent)
        self.browser_html_scraper_factory = BrowserHtmlScraperFactory() if self.config.use_headless_browser else None
        
    async def run(self) -> ScraperStats:
        for scraper_url in self.config.scraper_urls:
            await self.queue_if_allowed(scraper_url)

        tasks = []
        for i in range(self.config.max_parallel_requests):
            task = asyncio.create_task(self.scrape_loop(f"Scraper-{i}"))
            tasks.append(task)
        
        await asyncio.gather(*tasks)

        domain_stats = analyze_url_groups(list(self.completed_urls), min_pages_per_sub_path=5)
        return ScraperStats(
            initiated_urls_count=self.initiated_urls_count,
            requested_urls_count=self.requested_urls_count,
            completed_urls_count=self.completed_urls_count,
            domain_stats=domain_stats
        )        

    async def close(self):
        if self.http_html_scraper_factory:
            await self.http_html_scraper_factory.close()
        if self.browser_html_scraper_factory:
            await self.browser_html_scraper_factory.close()

    async def extract_metadata_and_save(self, scraper_store: ScraperStore, page: ScraperWebPage) -> ScraperWebPage:
        self.completed_urls.add(page.normalized_url)
        page = extract_metadata(page)
        if scraper_store:
            await scraper_store.store_page(page)
        return page


    async def scrape_loop(self, name: str) -> ScraperLoopResult:
        loop_completed_urls_count = 0
        scraper_store = self.config.scraper_store_factory.new_store() if self.config.scraper_store_factory else None
        while True:
            logger.info(
                f"waiting - looper: {name} i:c={self.initiated_urls_count}:{self.completed_urls_count} URLs")
            scraper_url = await self.url_queue.get()
            if scraper_url.is_terminal():
                logger.info(
                    f"terminating - looper: {name} i:c={self.initiated_urls_count}:{self.completed_urls_count} URLs")
                break

            if self.requested_urls_count >= self.config.max_requested_urls:
                logger.info(
                    f"terminating - max requested urls reached - {name} i:c={self.initiated_urls_count}:{self.completed_urls_count}")
                break

            logger.info(
                f"initiating - {name} i:c={self.initiated_urls_count}:{self.completed_urls_count} url: {scraper_url.normalized_url}")
            
            self.config.log("Scraping URL: " + scraper_url.normalized_url)

            page = None
            if (not scraper_url.no_cache) and scraper_store:
                logger.info(
                    f"loading from store - {name} i:c={self.initiated_urls_count}:{self.completed_urls_count} url: {scraper_url.normalized_url}")
                page = await scraper_store.load_page(scraper_url.normalized_url)
                # re-extracting metadata
                if page:
                    page = extract_metadata(page)

            domain_metadata = await self.get_domain_metadata(scraper_store, scraper_url)
            
            if not domain_metadata.robots.can_fetch(self.config.user_agent, scraper_url.normalized_url):
                logger.info(
                    f"url not allowed for scraping - skipping i:c={self.initiated_urls_count}:{self.completed_urls_count} - url: {scraper_url.normalized_url}")
                self.completed_urls_count += 1
                continue


            self.requested_urls_count += 1
            if page is None:
                if self.config.use_headless_browser and self.browser_html_scraper_factory:
                    page = await self.browser_html_scraper_factory.new_scraper().scrape(scraper_url.normalized_url)
                else:
                    page = await self.http_html_scraper_factory.new_scraper().scrape(scraper_url.normalized_url)
            
            if page is not None:
                page = await self.extract_metadata_and_save(scraper_store, page)

            self.completed_urls_count += 1
            loop_completed_urls_count += 1
            logger.info(
                f"completed - {name} i:c={self.initiated_urls_count}:{self.completed_urls_count} url: {scraper_url.normalized_url}, i:c={self.initiated_urls_count}:{self.completed_urls_count}")

            if page is None or page.outgoing_urls is None or len(page.outgoing_urls) == 0 or scraper_url.max_depth <= 0:
                await self.terminate_all_loops_if_needed()
                continue

            for outgoing_url in page.outgoing_urls:
                outgoing_scraper_url = ScraperUrl(
                    outgoing_url, no_cache=False, max_depth=scraper_url.max_depth-1)
                await self.queue_if_allowed(outgoing_scraper_url)

            self.terminate_all_loops_if_needed()

        return ScraperLoopResult(loop_completed_urls_count)
    
    async def get_domain_metadata(self, scraper_store: ScraperStore, scraper_url: ScraperUrl) -> DomainMetadata:
        normalized_url_parsed = urlparse(scraper_url.normalized_url)
        domain_metadata_task = self.domain_metadata.get(normalized_url_parsed.netloc)
        if domain_metadata_task is not None:
            return await domain_metadata_task
        
        domain_url = f"{normalized_url_parsed.scheme}://{normalized_url_parsed.netloc}"
        logger.info(f"downloading domain metadata {domain_url}")
        domain_metadata_task = asyncio.create_task(self.download_domain_metadata(scraper_store, domain_url))
        self.domain_metadata[normalized_url_parsed.netloc] = domain_metadata_task
        return await domain_metadata_task

    
    async def download_domain_metadata(self, scraper_store: ScraperStore, domain_url: str) -> DomainMetadata:
        home_page_url=urljoin(domain_url, "/")
        logger.info(f"downloading home page {home_page_url}")
        home_page = await self.http_html_scraper_factory.new_scraper().scrape(home_page_url)
        home_page = await self.extract_metadata_and_save(scraper_store, home_page)

        robots_url = urljoin(domain_url, "/robots.txt")
        try:
            logger.info(f"downloading robots.txt {robots_url}")
            robot = await RobotFileParser.download_and_parse(robots_url, self.http_html_scraper_factory.client_session)
        except Exception as e:
            logger.error(f"Error fetching sitemap {robots_url}: {e}")
            robot = RobotFileParser()
        
        sitemaps: dict[str, SitemapParser] = {}
        for sitemap_normalized_url in robot.sitemap_normalized_urls:
            try:
                logger.info(f"downloading sitemap {sitemap_normalized_url}")
                sitemap = await SitemapParser.download_and_parse(sitemap_normalized_url, self.http_html_scraper_factory.client_session)
                sitemaps[sitemap_normalized_url] = sitemap
            except Exception as e:
                logger.error(f"Error fetching sitemap {sitemap_normalized_url}: {e}")
        
        return DomainMetadata(
            robots=robot,
            sitemaps=sitemaps,
            home_page=home_page
        )

    async def queue_if_allowed(self, outgoing_scraper_url: ScraperUrl) -> None:
        if outgoing_scraper_url.normalized_url in self.initiated_urls:
            return
        if not self.is_domain_allowed(outgoing_scraper_url.normalized_url):
            logger.info(f"skipping url i:c={self.initiated_urls_count}:{
                        self.completed_urls_count} - url: {outgoing_scraper_url.normalized_url}")
            return
                
        logger.info(f"queueing url i:c={self.initiated_urls_count}:{
                    self.completed_urls_count} - url: {outgoing_scraper_url.normalized_url}")
        self.initiated_urls_count += 1
        self.initiated_urls.add(outgoing_scraper_url.normalized_url)
        await self.url_queue.put(outgoing_scraper_url)
    

    def is_domain_allowed(self, normalized_url: str) -> bool:
        return self.config.domain_filter.is_allowed(normalized_url)

    async def terminate_all_loops_if_needed(self):
        if self.completed_urls_count < self.initiated_urls_count:
            return
        logger.info(
            f"terminating all loops - i:c={self.initiated_urls_count}:{self.completed_urls_count}")
        await self.terminate_all_loops();
        
    async def terminate_all_loops(self):
        for i in range(self.config.max_parallel_requests):
            await self.url_queue.put(ScraperUrl.create_terminal())

    async def stop(self) -> None:
        for i in range(self.config.max_parallel_requests):
            await self.url_queue.put(ScraperUrl.create_terminal())
    
