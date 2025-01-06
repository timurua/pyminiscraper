import asyncio
from typing import Dict
import logging
from urllib.parse import urlparse
from .url import make_absolute_url
from .scrape_html_http import HttpHtmlScraperFactory
from .scrape_html_browser import BrowserHtmlScraperFactory
from .model import ScraperWebPage, ScraperUrl, ScraperUrlType
from .store import ScraperStore, ScraperStoreFactory
from .url import normalize_url
from abc import ABC, abstractmethod
from .model import ScraperUrl
from .domain_filter import DomainFilter
from .extract import extract_metadata
from .stats import ScraperStats, analyze_url_groups
from .domain_metadata import DomainMetadata
from .sitemap import Sitemap
from .robots import Robot
from aiolimiter import AsyncLimiter
from .deque import AsyncDeque
from .config import ScraperConfig
from datetime import datetime

logger = logging.getLogger("scraper")

class ScraperError(Exception):
    pass

class ScraperLoopResult:
    def __init__(self, completed_url_count: int):
        self.completed_urls_count = completed_url_count


class Scraper:
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.domain_metadata: Dict[str, asyncio.Task[DomainMetadata]] = {}
        self.queued_urls: set[str] = set()
        self.requested_urls_count = 0
        self.success_urls_count = 0
        self.skipped_urls_count = 0
        self.error_urls_count = 0
        self.url_queue: AsyncDeque[ScraperUrl] = AsyncDeque()
        self.http_html_scraper_factory = HttpHtmlScraperFactory(user_agent=config.user_agent)
        self.browser_html_scraper_factory = BrowserHtmlScraperFactory() if self.config.use_headless_browser else None
        self.request_rate_limiter = AsyncLimiter(self.config.max_requests_per_hour, float(60*60))
        self.back_to_back_errors = 0
        self.sitemaps: dict[str, Sitemap] = {}

    async def run(self) -> ScraperStats:
        for scraper_url in self.config.scraper_urls:
            await self.queue_scraper_url(scraper_url)

        tasks = []
        for i in range(self.config.max_parallel_requests):
            task = asyncio.create_task(self.scrape_loop(f"Scraper-{i}"))
            tasks.append(task)
        
        await asyncio.gather(*tasks)

        domain_stats = analyze_url_groups(list(self.queued_urls), min_pages_per_sub_path=5)
        await self.close()       
        return ScraperStats(
            queued_urls_count=len(self.queued_urls),
            requested_urls_count=self.requested_urls_count,
            success_urls_count=self.success_urls_count,
            error_urls_count=self.error_urls_count,
            skipped_urls_count=self.skipped_urls_count,
            domain_stats=domain_stats
        )         

    async def close(self):
        if self.http_html_scraper_factory:
            await self.http_html_scraper_factory.close()
        if self.browser_html_scraper_factory:
            await self.browser_html_scraper_factory.close()

    async def extract_metadata_and_save(self, scraper_store: ScraperStore, page: ScraperWebPage) -> ScraperWebPage:
        page = extract_metadata(page)
        if scraper_store:
            await scraper_store.store_page(page)
        return page


    async def scrape_loop(self, looper_name: str) -> ScraperLoopResult:
        loop_completed_urls_count = 0
        scraper_store = self.config.scraper_store_factory.new_store()
        while True:
            scraper_url = await self.url_queue.popright()
            if scraper_url.is_terminal() or self.was_max_requests_achieved():
                logger.info(
                    f"terminating - {self.looper_context(looper_name)} URLs")
                break
            
            self.config.log(f"scraping url - {self.looper_context(looper_name)} - {self.url_context(scraper_url)}")

            domain_metadata = await self.get_domain_metadata(scraper_url)
            
            if not domain_metadata.robots.can_fetch(self.config.user_agent, scraper_url.normalized_url):
                logger.info(
                    f"url not allowed for scraping - {self.looper_context(looper_name)} - {self.url_context(scraper_url)}")
                self.skipped_urls_count += 1
                continue

            self.requested_urls_count += 1
            await self.request_rate_limiter.acquire()
            try:
                if scraper_url.type == ScraperUrlType.HTML:
                    page = await self.load_or_download_page(scraper_store=scraper_store, scraper_url=scraper_url)
                    await self.enqueu_page_urls(scraper_url, page)
                elif scraper_url.type == ScraperUrlType.SITEMAP:
                    sitemap = await self.download_sitemap(scraper_url.normalized_url)
                    await self.enqueue_sitemap_urls(sitemap)
                self.success_urls_count += 1    
            except Exception as e:
                self.config.log(f"exception while retriving url - {self.looper_context(looper_name)} - {self.url_context(scraper_url)}")
                self.error_urls_count += 1

            await self.terminate_all_loops_if_needed(looper_name)

        return ScraperLoopResult(loop_completed_urls_count)
    
    async def download_sitemap(self, normalized_url: str) -> Sitemap:
        sitemap = await Sitemap.download_and_parse(normalized_url, self.http_html_scraper_factory.client_session)
        self.sitemaps[normalized_url] = sitemap
        return sitemap
    
    async def enqueue_sitemap_urls(self, sitemap: Sitemap, only_page = False) -> None:
        for page_url in sitemap.page_urls:
            await self.queue_scraper_url(ScraperUrl(page_url.loc, no_cache=True, max_depth=self.config.max_depth, type=ScraperUrlType.HTML))
        if not only_page:
            for sitemap_url in sitemap.sitemap_urls:
                await self.queue_scraper_url(ScraperUrl(sitemap_url.loc, no_cache=True, max_depth=self.config.max_depth, type=ScraperUrlType.SITEMAP))        

    def looper_context(self, looper_name: str)->str:
        return f"{looper_name} q:r:c:e:s={len(self.queued_urls)}:{self.requested_urls_count}:{self.success_urls_count}:{self.error_urls_count}:{self.skipped_urls_count}"
    
    def url_context(self, scraper_url: ScraperUrl)->str:
        return f"type={scraper_url.type} {scraper_url.normalized_url}"

    def was_max_requests_achieved(self) -> bool:
        return self.requested_urls_count >= self.config.max_requested_urls

    
    async def load_or_download_page(self, scraper_store: ScraperStore, scraper_url: ScraperUrl)-> ScraperWebPage:
        page = None
        if (not scraper_url.no_cache) and scraper_store:
            page = await scraper_store.load_page(scraper_url.normalized_url)
            if page is not None:
                logger.info(f'page was loaded from store {self.url_context(scraper_url)}')
                if page.requested_at and (datetime.now() - page.requested_at).total_seconds() < self.config.rerequest_after_hours * 60 * 60:
                    return page
        
        try:
            if self.config.use_headless_browser and self.browser_html_scraper_factory:
                page = await self.browser_html_scraper_factory.new_scraper().scrape(scraper_url.normalized_url)
            else:
                page = await self.http_html_scraper_factory.new_scraper().scrape(scraper_url.normalized_url)
            self.back_to_back_errors = 0
            page = await self.extract_metadata_and_save(scraper_store, page)
            page.requested_at = datetime.now()
            return page

        except Exception as e:
            logger.warning(f"Failed to fetch page {self.url_context(scraper_url)}")
            self.back_to_back_errors += 1
            if self.back_to_back_errors >= self.config.max_back_to_back_errors:
                logger.error(f"Terminating due to maximum back to back errors reached")
                await self.stop()
            raise ScraperError(f"Failed to fetch page {self.url_context(scraper_url)}") from e
    
    async def enqueu_page_urls(self, url: ScraperUrl, page: ScraperWebPage)-> None:
        for sitemap_url in page.sitemap_urls or []:
            await self.queue_scraper_url(ScraperUrl(sitemap_url, no_cache=True, max_depth=self.config.max_depth, type=ScraperUrlType.SITEMAP))

        if not self.config.only_sitemaps:
            for outgoing_url in page.outgoing_urls or []:
                outgoing_scraper_url = ScraperUrl(
                    outgoing_url, no_cache=False, max_depth=url.max_depth-1, type=ScraperUrlType.HTML)
                await self.queue_scraper_url(outgoing_scraper_url)

        

    
    async def get_domain_metadata(self, scraper_url: ScraperUrl) -> DomainMetadata:
        normalized_url_parsed = urlparse(scraper_url.normalized_url)
        domain_metadata_task = self.domain_metadata.get(normalized_url_parsed.netloc)
        if domain_metadata_task is not None:
            return await domain_metadata_task
        
        domain_url = f"{normalized_url_parsed.scheme}://{normalized_url_parsed.netloc}"
        logger.info(f"downloading domain metadata {domain_url}")
        domain_metadata_task = asyncio.create_task(self.download_domain_metadata(domain_url))
        self.domain_metadata[normalized_url_parsed.netloc] = domain_metadata_task
        return await domain_metadata_task

    
    async def download_domain_metadata(self, domain_url: str) -> DomainMetadata:
        robots_url = make_absolute_url(domain_url, "/robots.txt")
        try:
            logger.info(f"downloading robots.txt {robots_url}")
            robot = await Robot.download_and_parse(robots_url, self.http_html_scraper_factory.client_session)
        except Exception as e:
            logger.error(f"Error fetching sitemap {robots_url}: {e}")
            robot = Robot()

        for sitemap_url in robot.sitemap_urls:
            await self.queue_scraper_url(ScraperUrl(sitemap_url, no_cache=True, max_depth=self.config.max_depth, type=ScraperUrlType.SITEMAP))                
        
        return DomainMetadata(
            robots=robot,
            domain_url=domain_url)
    
    async def queue_sitemap_urls(self, sitemap: Sitemap)-> None:
        for page_url in sitemap.page_urls:
            await self.queue_scraper_url(ScraperUrl(page_url.loc, no_cache=True, max_depth=self.config.max_depth, type=ScraperUrlType.HTML, high_priority=True))
        for page_url in sitemap.sitemap_urls:
            await self.queue_scraper_url(ScraperUrl(page_url.loc, no_cache=True, max_depth=self.config.max_depth, type=ScraperUrlType.SITEMAP))                

    async def queue_scraper_url(self, outgoing_scraper_url: ScraperUrl) -> None:
        if outgoing_scraper_url.normalized_url in self.queued_urls:
            return
        if not self.is_domain_allowed(outgoing_scraper_url.normalized_url):
            logger.info(f"skipping url before queueing - {self.looper_context('')} - {self.url_context(outgoing_scraper_url)}")
            return
                
        logger.info(f"queueing - {self.looper_context('')} - url: {self.url_context(outgoing_scraper_url)}")
        self.queued_urls.add(outgoing_scraper_url.normalized_url)
        if outgoing_scraper_url.type == ScraperUrlType.SITEMAP or outgoing_scraper_url.type == ScraperUrlType.TERMINATE_LOOP or outgoing_scraper_url.high_priority:
            await self.url_queue.appendright(outgoing_scraper_url) 
        else:
            await self.url_queue.appendleft(outgoing_scraper_url)
    

    def is_domain_allowed(self, normalized_url: str) -> bool:
        return self.config.domain_filter.is_allowed(normalized_url)

    async def terminate_all_loops_if_needed(self, name: str) -> None:   
        if (self.success_urls_count+self.error_urls_count+self.skipped_urls_count) < len(self.queued_urls):
            return
        logger.info(
            f"terminating all loops - {self.looper_context(name)}")
        await self.stop()
        
    async def stop(self):
        for _ in range(self.config.max_parallel_requests):
            await self.url_queue.appendright(ScraperUrl.create_terminal())

    
