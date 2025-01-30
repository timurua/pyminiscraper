import asyncio
from typing import Dict
import logging
from urllib.parse import urlparse
from .url import make_absolute_url
from .scrape_html_http import HttpHtmlScraperFactory
from .scrape_html_browser import BrowserHtmlScraperFactory
from .model import ScraperWebPage, ScraperUrl, ScraperUrlType, ScrapeUrlMetadata
from .store import ScraperStore
from .model import ScraperUrl
from .extract import extract_metadata, PageMetadataExtractor
from .stats import ScraperStats, analyze_url_groups
from .domain_metadata import DomainMetadata
from .sitemap import Sitemap
from .robots import Robot
from .deque import AsyncDeque
from .config import ScraperConfig, ScraperCallbackError
from datetime import datetime
from .ratelimiter import CrawlRateLimiter
import aiohttp
from .feed import FeedParser, Feed
from .filter import DomainFilter, PathFilter


logger = logging.getLogger("scraper")

class ScraperError(Exception):
    pass

class ScraperLoopResult:
    def __init__(self, completed_url_count: int):
        self.completed_urls_count = completed_url_count


class Scraper:
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.client_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False),
            headers={
                'User-Agent': config.user_agent
            },
            timeout = aiohttp.ClientTimeout(total=config.request_timeout_seconds))
        
        self.domain_metadata: Dict[str, asyncio.Task[DomainMetadata]] = {}
        self.queued_urls: set[str] = set()
        self.requested_urls_count = 0
        self.success_urls_count = 0
        self.skipped_urls_count = 0
        self.error_urls_count = 0
        self.url_queue: AsyncDeque[ScraperUrl] = AsyncDeque()
        self.http_html_scraper_factory = HttpHtmlScraperFactory(self.client_session)
        self.browser_html_scraper_factory = BrowserHtmlScraperFactory() if self.config.use_headless_browser else None
        self.request_rate_limiter = CrawlRateLimiter(self.config.crawl_delay_seconds)
        self.back_to_back_errors = 0
        self.sitemaps: dict[str, Sitemap] = {}
        self.feeds: dict[str, Feed] = {}
        self.domain_filter = DomainFilter(config.domain_config, [url.url for url in config.seed_urls])
        self.include_path_patterns = PathFilter(config.include_path_patterns, default_value=True)
        self.exclude_path_patterns = PathFilter(config.exclude_path_patterns, default_value=False)
        

    async def run(self) -> ScraperStats:
        for scraper_url in self.config.seed_urls:
            await self._queue_scraper_url(scraper_url, skip_path_filter=True)

        tasks = []
        for i in range(self.config.max_parallel_requests):
            task = asyncio.create_task(self._scrape_loop(f"Scraper-{i}"))
            tasks.append(task)
        
        await asyncio.gather(*tasks)

        domain_stats = analyze_url_groups(list(self.queued_urls), min_pages_per_sub_path=5)
        await self._close()       
        return ScraperStats(
            queued_urls_count=len(self.queued_urls),
            requested_urls_count=self.requested_urls_count,
            success_urls_count=self.success_urls_count,
            error_urls_count=self.error_urls_count,
            skipped_urls_count=self.skipped_urls_count,
            domain_stats=domain_stats
        )         

    async def _close(self):
        if self.http_html_scraper_factory:
            await self.http_html_scraper_factory.close()
        if self.browser_html_scraper_factory:
            await self.browser_html_scraper_factory.close()

    async def _extract_metadata_and_save(self, scraper_store: ScraperStore,  url: ScraperUrl, page: ScraperWebPage) -> ScraperWebPage:
        page = extract_metadata(page)        
        self._default_to_external_metadata(url, page)
        if scraper_store:
            try:
                await scraper_store.store_page(page)
            except Exception as e:
                raise ScraperCallbackError(f"Error storing page {self._url_context(url)}") from e                
        return page
    
    def _default_to_external_metadata(self, url: ScraperUrl, page: ScraperWebPage) -> None:
        if url.metadata:
            page.metadata_title = page.metadata_title or url.metadata.title
            page.metadata_description = page.metadata_description or url.metadata.description
            page.metadata_image_url = page.metadata_image_url or url.metadata.image_url
            page.metadata_published_at = page.metadata_published_at or url.metadata.published_at



    async def _scrape_loop(self, looper_name: str) -> ScraperLoopResult:
        loop_completed_urls_count = 0
        scraper_store = self.config.store_factory.new_store()
        while True:
            scraper_url = await self.url_queue.popright()
            if scraper_url.is_terminal() or self._was_max_requests_achieved():
                logger.info(f"terminating - {self._looper_context(looper_name)} URLs")
                break
            
            await self.config.log(f"scraping url - {self._looper_context(looper_name)} - {self._url_context(scraper_url)}")

            domain_metadata = await self._get_domain_metadata(scraper_url)
            
            if not domain_metadata.robots.can_fetch(self.config.user_agent, scraper_url.normalized_url):
                logger.info(
                    f"url not allowed for scraping - {self._looper_context(looper_name)} - {self._url_context(scraper_url)}")
                self.skipped_urls_count += 1
                continue

            self.requested_urls_count += 1
            await self.request_rate_limiter.acquire()
            try:
                if scraper_url.type == ScraperUrlType.HTML:
                    page = await self._load_or_download_page(scraper_store=scraper_store, url=scraper_url)
                    await self._enqueue_web_page_urls(scraper_url, page)
                elif scraper_url.type == ScraperUrlType.SITEMAP:
                    sitemap = await self._download_sitemap(scraper_url.normalized_url)
                    await self._enqueue_sitemap_urls(sitemap)
                elif scraper_url.type == ScraperUrlType.FEED:
                    rss = await self._download_feed(scraper_url.normalized_url)
                    await self._enqueue_feed_urls(rss)                    
                self.success_urls_count += 1
            except ScraperCallbackError as e:
                logger.error(f"callback error while retriving url - {self._looper_context(looper_name)} - {self._url_context(scraper_url)} {e}")
                raise e
            except Exception as e:
                await self.config.log(f"exception while retriving url - {self._looper_context(looper_name)} - {self._url_context(scraper_url)}")
                self.error_urls_count += 1

            await self._terminate_all_loops_if_needed(looper_name)

        return ScraperLoopResult(loop_completed_urls_count)
    
    async def _download_sitemap(self, normalized_url: str) -> Sitemap:
        sitemap = await Sitemap.download_and_parse(normalized_url, self.http_html_scraper_factory.client_session)
        self.sitemaps[normalized_url] = sitemap
        return sitemap
    
    async def _download_feed(self, normalized_url: str) -> Feed:
        feed = await FeedParser.download_and_parse(normalized_url, self.http_html_scraper_factory.client_session)
        self.feeds[normalized_url] = feed
        return feed
    
    async def _enqueue_sitemap_urls(self, sitemap: Sitemap) -> None:
        for page_url in sitemap.page_urls:
            await self._queue_scraper_url(
                ScraperUrl(page_url.loc, 
                           max_depth=self.config.max_depth, 
                           type=ScraperUrlType.HTML, 
                           metadata=ScrapeUrlMetadata(
                                 None, None, page_url.lastmod, None
                           )
                )
            )
        
        for sitemap_url in sitemap.sitemap_urls:
            await self._queue_scraper_url(
                ScraperUrl(sitemap_url.loc, max_depth=self.config.max_depth, type=ScraperUrlType.SITEMAP)
            )        
            
    async def _enqueue_feed_urls(self, rss: Feed) -> None:
        for item in rss.items:
            if item.link:
                metadata = ScrapeUrlMetadata(
                    item.title, item.description, item.pub_date, 
                    None if item.description is None else PageMetadataExtractor(item.link, item.description).get_image_url()
                )
                await self._queue_scraper_url(ScraperUrl(item.link, max_depth=self.config.max_depth, type=ScraperUrlType.HTML, metadata=metadata))

    def _looper_context(self, looper_name: str)->str:
        return f"{looper_name} queued={len(self.queued_urls)} requested={self.requested_urls_count} success={self.success_urls_count} error={self.error_urls_count} skipped={self.skipped_urls_count}"
    
    def _url_context(self, scraper_url: ScraperUrl)->str:
        return f"type={scraper_url.type} {scraper_url.normalized_url}"

    def _was_max_requests_achieved(self) -> bool:
        return self.requested_urls_count >= self.config.max_requested_urls

    
    async def _load_or_download_page(self, scraper_store: ScraperStore, url: ScraperUrl)-> ScraperWebPage:
        try:
            page = await scraper_store.load_page(url.normalized_url)        
        except Exception as e:
            raise ScraperCallbackError(f"Error loading page {self._url_context(url)}") from e                
        try:
            if self.config.use_headless_browser and self.browser_html_scraper_factory:
                page = await self.browser_html_scraper_factory.new_scraper().scrape(url.normalized_url)
            else:
                page = await self.http_html_scraper_factory.new_scraper().scrape(url.normalized_url)
            self.back_to_back_errors = 0            

        except Exception as e:
            logger.warning(f"Failed to fetch page {self._url_context(url)}")
            self.back_to_back_errors += 1
            if self.back_to_back_errors >= self.config.max_back_to_back_errors:
                logger.error(f"Terminating due to maximum back to back errors reached")
                await self.stop()
            raise ScraperError(f"Failed to fetch page {self._url_context(url)}") from e

        page = await self._extract_metadata_and_save(scraper_store, url, page)        
        page.requested_at = datetime.now()
        return page
    
    async def _enqueue_web_page_urls(self, url: ScraperUrl, page: ScraperWebPage)-> None:
        for sitemap_url in page.sitemap_urls or []:
            await self._queue_scraper_url(ScraperUrl(sitemap_url, max_depth=self.config.max_depth, type=ScraperUrlType.SITEMAP))

        if self.config.follow_web_page_links:
            await self._queue_scraper_urls(page.outgoing_urls or [], ScraperUrlType.HTML)            
                
        if self.config.follow_sitemap_links:
            await self._queue_scraper_urls(page.sitemap_urls or [], ScraperUrlType.SITEMAP)
                
        if self.config.follow_feed_links:
            await self._queue_scraper_urls(page.feed_urls or [], ScraperUrlType.FEED)

    
    async def _get_domain_metadata(self, scraper_url: ScraperUrl) -> DomainMetadata:
        normalized_url_parsed = urlparse(scraper_url.normalized_url)
        domain_metadata_task = self.domain_metadata.get(normalized_url_parsed.netloc)
        if domain_metadata_task is not None:
            return await domain_metadata_task
        
        domain_url = f"{normalized_url_parsed.scheme}://{normalized_url_parsed.netloc}"
        logger.info(f"downloading domain metadata {domain_url}")
        domain_metadata_task = asyncio.create_task(self._download_domain_metadata(domain_url))
        self.domain_metadata[normalized_url_parsed.netloc] = domain_metadata_task        
        domain_metadata = await domain_metadata_task
        self.request_rate_limiter.reset(domain_metadata.robots.crawl_delay(self.config.user_agent) or self.config.crawl_delay_seconds)
        return domain_metadata

    
    async def _download_domain_metadata(self, domain_url: str) -> DomainMetadata:
        robots_url = make_absolute_url(domain_url, "/robots.txt")
        try:
            logger.info(f"downloading robots.txt {robots_url}")
            robot = await Robot.download_and_parse(robots_url, self.http_html_scraper_factory.client_session)
        except Exception as e:
            logger.error(f"Error fetching sitemap {robots_url}: {e}")
            robot = Robot()
            
        self.request_rate_limiter.reset(
            robot.crawl_delay(self.config.user_agent) or self.config.crawl_delay_seconds
        )

        if self.config.follow_sitemap_links:
            await self._queue_scraper_urls(list(robot.sitemap_urls), ScraperUrlType.SITEMAP)
        
        return DomainMetadata(
            robots=robot,
            domain_url=domain_url)
    
    async def _queue_sitemap_urls(self, sitemap: Sitemap)-> None:
        for page_url in sitemap.page_urls:
            await self._queue_scraper_url(ScraperUrl(page_url.loc, max_depth=self.config.max_depth, type=ScraperUrlType.HTML, high_priority=True))
        for sitemap_url in sitemap.sitemap_urls:
            await self._queue_scraper_url(ScraperUrl(sitemap_url.loc, max_depth=self.config.max_depth, type=ScraperUrlType.SITEMAP))
            
    async def _queue_scraper_urls(self, urls: list[str], type: ScraperUrlType) -> None:
        for url in urls:
            await self._queue_scraper_url(ScraperUrl(url, max_depth=self.config.max_depth, type=type))

    async def _queue_scraper_url(self, scraper_url: ScraperUrl, skip_path_filter: bool = False) -> None:
        if scraper_url.normalized_url in self.queued_urls:
            return
        if not self._is_domain_allowed(scraper_url.normalized_url):
            logger.info(f"skipping url before queueing - domain not allowed - {self._looper_context('')} - {self._url_context(scraper_url)}")
            return
        
        if scraper_url.type == ScraperUrlType.HTML \
            and not skip_path_filter \
            and ( self.exclude_path_patterns.is_passing(scraper_url.normalized_url)
                or not self.include_path_patterns.is_passing(scraper_url.normalized_url)):
            logger.info(f"skipping url before queueing - path not allowed - {self._looper_context('')} - {self._url_context(scraper_url)}")
            return
                
        logger.info(f"queueing - {self._looper_context('')} - url: {self._url_context(scraper_url)}")
        self.queued_urls.add(scraper_url.normalized_url)
        if scraper_url.type == ScraperUrlType.FEED \
            or scraper_url.type == ScraperUrlType.SITEMAP\
            or scraper_url.type == ScraperUrlType.TERMINATE_LOOP \
            or scraper_url.high_priority:
            await self.url_queue.appendright(scraper_url) 
        else:
            await self.url_queue.appendleft(scraper_url)
    

    def _is_domain_allowed(self, normalized_url: str) -> bool:
        return self.domain_filter.is_allowed(normalized_url)

    async def _terminate_all_loops_if_needed(self, name: str) -> None:   
        if (self.success_urls_count+self.error_urls_count+self.skipped_urls_count) < len(self.queued_urls):
            return
        logger.info(
            f"terminating all loops - no more queued urls - {self._looper_context(name)}")
        await self.stop()
        
    async def stop(self):
        for _ in range(self.config.max_parallel_requests):
            await self.url_queue.appendright(ScraperUrl.create_terminal())

    
