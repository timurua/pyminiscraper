import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from pyminiscraper.scraper import Scraper, ScraperError
from pyminiscraper.config import ScraperConfig
from pyminiscraper.model import ScraperUrl, ScraperUrlType, ScraperWebPage
from pyminiscraper.store import ScraperStoreFactory
from pyminiscraper.robots import Robot
from pyminiscraper.sitemap import Sitemap
from pyminiscraper.domain_metadata import DomainMetadata

@pytest.fixture
def scraper_config():
    config = ScraperConfig(
        user_agent="test-agent",
        max_requests_per_hour=1000,
        max_parallel_requests=5,
        max_requested_urls=100,
        use_headless_browser=False,
        scraper_urls=[ScraperUrl("http://example.com", type=ScraperUrlType.HTML)],
        scraper_store_factory=MagicMock(ScraperStoreFactory),
        rerequest_after_hours=24,
        max_back_to_back_errors=3,
        only_sitemaps=False,
        max_depth=3
    )
    return config

@pytest.fixture
def scraper(scraper_config):
    return Scraper(scraper_config)

@pytest.mark.asyncio
async def test_scraper_initialization(scraper):
    assert scraper.config.user_agent == "test-agent"
    assert scraper.requested_urls_count == 0
    assert scraper.success_urls_count == 0
    assert scraper.skipped_urls_count == 0
    assert scraper.error_urls_count == 0

@pytest.mark.asyncio
async def test_scraper_run(scraper):
    scraper.queue_scraper_url = AsyncMock()
    scraper.scrape_loop = AsyncMock()
    scraper.close = AsyncMock()
    scraper.config.scraper_urls = [ScraperUrl("http://example.com", type=ScraperUrlType.HTML)]

    await scraper.run()

    scraper.queue_scraper_url.assert_called_once()
    assert scraper.scrape_loop.call_count == scraper.config.max_parallel_requests
    scraper.close.assert_called_once()

@pytest.mark.asyncio
async def test_scraper_scrape_loop(scraper):
    scraper.url_queue.popright = AsyncMock(return_value=ScraperUrl("http://example.com", type=ScraperUrlType.HTML))
    scraper.get_domain_metadata = AsyncMock(return_value=DomainMetadata(robots=Robot()))
    scraper.load_or_download_page = AsyncMock(return_value=ScraperWebPage(url="http://example.com"))
    scraper.enqueu_page_urls = AsyncMock()
    scraper.was_max_requests_achieved = MagicMock(return_value=False)
    scraper.terminate_all_loops_if_needed = AsyncMock()

    result = await scraper.scrape_loop("Scraper-0")

    assert result.completed_urls_count == 0
    scraper.url_queue.popright.assert_called_once()
    scraper.get_domain_metadata.assert_called_once()
    scraper.load_or_download_page.assert_called_once()
    scraper.enqueu_page_urls.assert_called_once()
    scraper.terminate_all_loops_if_needed.assert_called_once()

@pytest.mark.asyncio
async def test_scraper_download_sitemap(scraper):
    sitemap = Sitemap(page_urls=[], sitemap_urls=[])
    Sitemap.download_and_parse = AsyncMock(return_value=sitemap)

    result = await scraper.download_sitemap("http://example.com/sitemap.xml")

    assert result == sitemap
    Sitemap.download_and_parse.assert_called_once_with("http://example.com/sitemap.xml", scraper.http_html_scraper_factory.client_session)

@pytest.mark.asyncio
async def test_scraper_enqueue_sitemap_urls(scraper):
    sitemap = Sitemap(page_urls=[ScraperUrl("http://example.com/page", type=ScraperUrlType.HTML)], sitemap_urls=[])
    scraper.queue_scraper_url = AsyncMock()

    await scraper.enqueue_sitemap_urls(sitemap)

    scraper.queue_scraper_url.assert_called_once_with(ScraperUrl("http://example.com/page", no_cache=True, max_depth=scraper.config.max_depth, type=ScraperUrlType.HTML))

@pytest.mark.asyncio
async def test_scraper_get_domain_metadata(scraper):
    scraper.download_domain_metadata = AsyncMock(return_value=DomainMetadata(robots=Robot()))
    scraper.domain_metadata = {}

    result = await scraper.get_domain_metadata(ScraperUrl("http://example.com", type=ScraperUrlType.HTML))

    assert isinstance(result, DomainMetadata)
    scraper.download_domain_metadata.assert_called_once()

@pytest.mark.asyncio
async def test_scraper_download_domain_metadata(scraper):
    Robot.download_and_parse = AsyncMock(return_value=Robot())
    scraper.queue_scraper_url = AsyncMock()

    result = await scraper.download_domain_metadata("http://example.com")

    assert isinstance(result, DomainMetadata)
    Robot.download_and_parse.assert_called_once_with("http://example.com/robots.txt", scraper.http_html_scraper_factory.client_session)
    scraper.queue_scraper_url.assert_not_called()

@pytest.mark.asyncio
async def test_scraper_queue_scraper_url(scraper):
    scraper.is_domain_allowed = MagicMock(return_value=True)
    scraper.url_queue.appendright = AsyncMock()
    scraper.url_queue.appendleft = AsyncMock()

    url = ScraperUrl("http://example.com", type=ScraperUrlType.HTML)
    await scraper.queue_scraper_url(url)

    scraper.url_queue.appendleft.assert_called_once_with(url)

@pytest.mark.asyncio
async def test_scraper_load_or_download_page(scraper):
    scraper_store = MagicMock()
    scraper_store.load_page = AsyncMock(return_value=None)
    scraper.http_html_scraper_factory.new_scraper = MagicMock(return_value=AsyncMock(scrape=AsyncMock(return_value=ScraperWebPage(url="http://example.com"))))
    scraper.extract_metadata_and_save = AsyncMock(return_value=ScraperWebPage(url="http://example.com"))

    result = await scraper.load_or_download_page(scraper_store, ScraperUrl("http://example.com", type=ScraperUrlType.HTML))

    assert isinstance(result, ScraperWebPage)
    scraper_store.load_page.assert_called_once()
    scraper.http_html_scraper_factory.new_scraper().scrape.assert_called_once()
    scraper.extract_metadata_and_save.assert_called_once()

@pytest.mark.asyncio
async def test_scraper_enqueu_page_urls(scraper):
    page = ScraperWebPage(url="http://example.com", sitemap_urls=["http://example.com/sitemap.xml"], outgoing_urls=["http://example.com/page"])
    scraper.queue_scraper_url = AsyncMock()

    await scraper.enqueu_page_urls(ScraperUrl("http://example.com", type=ScraperUrlType.HTML), page)

    assert scraper.queue_scraper_url.call_count == 2

@pytest.mark.asyncio
async def test_scraper_terminate_all_loops_if_needed(scraper):
    scraper.success_urls_count = 1
    scraper.error_urls_count = 1
    scraper.skipped_urls_count = 1
    scraper.queued_urls = {"http://example.com"}
    scraper.stop = AsyncMock()

    await scraper.terminate_all_loops_if_needed("Scraper-0")

    scraper.stop.assert_called_once()