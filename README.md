# pyminiscraper

## Introduction

`pyminiscraper` is a lightweight Python library designed for easy web scraping. It provides a simple interface to extract data from web pages with minimal setup. Whether you are a beginner or an advanced user, `pyminiscraper` offers the flexibility to handle various scraping tasks efficiently.

## Features

| Feature | Implemented |
|---------|------------|
| Basic Web Page scraping | ✅ |
| Web Page spidering | ✅ |
| Parallel requests | ✅ |
| Headless browser support | ✅ |
| Robots parsing | ✅ |
| Sitemap parsing | ✅ |
| RSS parsing | ✅ |
| Atom parsing | ✅ |
| Open Graph parsing | ✅ |
| Rate limiting | ✅ |
| Error handling | ✅ |
| Depth control | ✅ |
| Custom user agent | ✅ |
| File storage | ✅ |
| Custom callbacks | ✅ |
| Domain restrictions | ✅ |
| Request timeout | ✅ |
| Page caching | ✅ |


## Simplest Use Case

Here is a basic example of how to use `pyminiscraper` to scrape data from a web page:

```python
from pyminiscraper.scraper import Scraper
from pyminiscraper.config import ScraperConfig

storage_dir.mkdir(parents=True, exist_ok=True)
click.echo(f"Storage directory set to: {storage_dir}")

scraper = Scraper(
    ScraperConfig(
        scraper_urls=[
            ScraperUrl(
                "https://www.anthropic.com/news", max_depth=2)
        ],
        max_parallel_requests=16,
        use_headless_browser=False,
        timeout_seconds=30,
        max_requests_per_hour=6*60,
        scraper_store_factory=FileStoreFactory(storage_dir.absolute().as_posix()),
    ),
)
await scraper.run()

```

## Advanced Configuration Options

Configuration for web scraping behavior.

Parameters:
- max_parallel_requests (int): Maximum number of concurrent scraping requests
- max_requested_urls (int): Maximum total number of URLs to request before stopping
- max_depth (int): Maximum depth for recursively following links (0 means only scrape seed URLs)
- max_back_to_back_errors (int): Number of consecutive errors before terminating scraper
- crawl_delay_seconds (float): Minimum delay between requests to same domain
- request_timeout_seconds (float): Request timeout in seconds
- user_agent (str): User agent string to use in requests
- store_factory: Factory for creating storage backend
- seed_urls (List[ScraperUrl]): Initial URLs to start scraping from
- use_headless_browser (bool): Whether to use headless browser for JavaScript rendering
- follow_web_page_links (bool): Whether to follow links found in web pages
- follow_sitemap_links (bool): Whether to follow links found in sitemaps
- follow_feed_links (bool): Whether to follow links found in RSS/Atom feeds
- domain_config (DomainConfig): Configuration for allowed/blocked domains
- log (Callable): Logging function to use

The scraper will:
- Start with seed URLs and scrape them according to configuration
- Follow links up to max_depth if follow_web_page_links is True
- Follow sitemap.xml links if follow_sitemap_links is True 
- Follow RSS/Atom feed links if follow_feed_links is True
- Respect robots.txt and crawl delay settings
- Store results using provided store_factory
- Stop when max_requested_urls is reached or max_back_to_back_errors occurs
