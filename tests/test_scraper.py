import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pyminiscraper.scraper import Scraper, ScraperError
from pyminiscraper.config import ScraperConfig, ScraperDomainConfig, ScraperDomainConfigMode, ScraperAllowedDomains
from pyminiscraper.model import ScraperUrl, ScraperUrlType, ScraperWebPage
from pyminiscraper.store import ScraperStoreFactory
from pyminiscraper.robots import Robot
from pyminiscraper.sitemap import Sitemap
from pyminiscraper.domain_metadata import DomainMetadata
from pyminiscraper.feed import FeedParser, Feed

@pytest.fixture
def scraper_config():
    config = ScraperConfig(
        user_agent="test-agent",
        crawl_delay_seconds=1,
        max_parallel_requests=5,
        max_requested_urls=100,
        use_headless_browser=False,
        domain_config=ScraperDomainConfig(
            allowance=ScraperAllowedDomains(
                domains=["example.com"]                
            )
        ),
        
        seed_urls=[ScraperUrl("http://example.com", type=ScraperUrlType.HTML)],
        scraper_store_factory=MagicMock(ScraperStoreFactory),
        max_back_to_back_errors=3,
        follow_web_page_links=False,
        max_depth=3
    )
    return config

@pytest.mark.asyncio
async def test_scraper_initialization(scraper_config: ScraperConfig):
    scraper = Scraper(scraper_config)
    assert scraper.config.user_agent == "test-agent"
    assert scraper.requested_urls_count == 0
    assert scraper.success_urls_count == 0
    assert scraper.skipped_urls_count == 0
    assert scraper.error_urls_count == 0

@pytest.mark.asyncio
async def test_scraper_run(scraper_config: ScraperConfig):
    scraper = Scraper(scraper_config)
    with patch.object(scraper, '_scrape_loop', new_callable=AsyncMock) as mock_scrape_loop:
        mock_scrape_loop.return_value = None
        stats = await scraper.run()
        assert stats.queued_urls_count == 1
        assert stats.requested_urls_count == 0
        assert stats.success_urls_count == 0
        assert stats.error_urls_count == 0
        assert stats.skipped_urls_count == 0

@pytest.mark.asyncio
async def test_scraper_handle_error(scraper_config: ScraperConfig):
    scraper = Scraper(scraper_config)
    with patch.object(scraper, '_scrape_loop', new_callable=AsyncMock) as mock_scrape_loop:
        mock_scrape_loop.side_effect = ScraperError("Test error")
        with pytest.raises(ScraperError):
            await scraper.run()

@pytest.mark.asyncio
async def test_scraper_queue_scraper_url(scraper_config: ScraperConfig):
    scraper = Scraper(scraper_config)
    scraper_url = ScraperUrl("http://example.com/page", type=ScraperUrlType.HTML)
    await scraper._queue_scraper_url(scraper_url)
    assert scraper_url.normalized_url in scraper.queued_urls

@pytest.mark.asyncio
async def test_scraper_download_sitemap(scraper_config: ScraperConfig):
    scraper = Scraper(scraper_config)
    sitemap_url = "http://example.com/sitemap.xml"
    with patch.object(Sitemap, 'download_and_parse', new_callable=AsyncMock) as mock_download_and_parse:
        mock_download_and_parse.return_value = Sitemap()
        sitemap = await scraper._download_sitemap(sitemap_url)
        assert sitemap is not None
        assert sitemap_url in scraper.sitemaps

@pytest.mark.asyncio
async def test_scraper_download_feed(scraper_config: ScraperConfig):
    scraper = Scraper(scraper_config)
    feed_url = "http://example.com/feed.xml"
    with patch.object(FeedParser, 'download_and_parse', new_callable=AsyncMock) as mock_download_and_parse:
        mock_download_and_parse.return_value = Feed(items=[])
        feed = await scraper._download_feed(feed_url)
        assert feed is not None
        assert feed_url in scraper.feeds

