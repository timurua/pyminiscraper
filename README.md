# pyminiscraper

## Introduction

`pyminiscraper` is a lightweight Python library designed for easy web scraping. It provides a simple interface to extract data from web pages with minimal setup. Whether you are a beginner or an advanced user, `pyminiscraper` offers the flexibility to handle various scraping tasks efficiently.

## Features

| Feature | Description |
|---------|------------|
| Basic Web Page scraping | Scrape HTML content from web pages |
| Async scraping | Extremely scalable asynchronous scraping |
| Web Page spidering | Follow and scrape links from web pages |
| Parallel requests | Configure number of concurrent requests |
| Headless browser support | JavaScript rendering support |
| Robots.txt parsing | Respect robots.txt rules |
| Sitemap parsing | Parse and follow sitemap.xml |
| RSS/Atom parsing | Parse and follow RSS/Atom feeds |
| Open Graph parsing | Extract Open Graph metadata |
| Rate limiting | Configurable per-domain rate limiting |
| Error handling | Robust error handling with retry logic |
| Depth control | Control recursion depth for link following |
| Custom user agent | Set custom User-Agent strings |
| File storage | Built-in file storage system |
| Custom callbacks | Define custom processing logic |
| Domain restrictions | Control allowed/blocked domains |
| Request timeout | Configurable request timeouts |
| Page caching | Cache and reuse downloaded pages |

## Installation

```bash
pip install pyminiscraper
```

## How does it work

```
┌───────────────────┐
│                   │
│  Initializing     │
│                   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│     Download      │
│     Robots.txt    │
│                   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│     Queue for     │
|    Configurable   |◀────┐
|      Parallel     |     |
|     Processing    |     |
└─────────┬─────────┘     |
          │               |
          ▼               |
┌───────────────────┐     |    ┌───────────────────┐
│        Scrape     │     |    │                   │
|      Web Pages,   |     |    │    Loading        │
│     RSS & Atom    │──── | ───│    Saving         │
│                   │     |    │    Web Pages      │    
└─────────┬─────────┘     |    └───────────────────┘ 
          │               |
          ▼               |
┌───────────────────┐     |
│      Discover     │     |   
│      Outgoing     |     |
|     Web Page      │─────┘
|  RSS/Atom feed    |
│      links        │
└───────────────────┘
```

## Basic Usage

### Downloading Sitemap-Referenced Pages

This example shows how to scrape only pages referenced in a sitemap:

```python
from pyminiscraper import Scraper, ScraperConfig, ScraperUrl, FileStore
from pyminiscraper.config import ScraperDomainConfig, ScraperDomainConfigMode

scraper = Scraper(
    ScraperConfig(
        seed_urls=[
            ScraperUrl("https://www.example.com/", max_depth=2)
        ],
        follow_sitemap_links=True,
        follow_web_page_links=False,
        follow_feed_links=False,
        callback=FileStore(storage_dir),
    ),
)
await scraper.run()
```

### Scraping RSS/Atom Feeds

Example of scraping content from RSS/Atom feeds:

```python
from pyminiscraper import Scraper, ScraperConfig, ScraperUrl, ScraperUrlType, FileStore

scraper = Scraper(
    ScraperConfig(
        seed_urls=[
            ScraperUrl(
                "https://feeds.feedburner.com/PythonInsider", 
                type=ScraperUrlType.FEED
            )
        ],
        follow_sitemap_links=False,
        follow_web_page_links=False,
        follow_feed_links=True,
        callback=FileStore(storage_dir),
    ),
)
await scraper.run()
```

### Full Website Crawling

Example of comprehensive website crawling using all available sources:

```python
scraper = Scraper(
    ScraperConfig(
        seed_urls=[
            ScraperUrl("https://www.example.com/")
        ],
        follow_sitemap_links=True,
        follow_web_page_links=True,
        follow_feed_links=True,
        callback=FileStore(storage_dir),
    ),
)
await scraper.run()
```

### Custom Processing with Callbacks

Example of custom processing using callbacks:

```python
from pyminiscraper.config import ScraperCallback, ScraperContext
from pyminiscraper.model import ScraperWebPage, ScraperUrl

class CustomCallback(ScraperCallback):
    async def on_web_page(self, context: ScraperContext, request: ScraperUrl, response: ScraperWebPage) -> None:
        # Custom processing logic here
        print(f"Processing {response.url}")
        print(f"Title: {response.metadata_title}")
        
    async def on_feed(self, context: ScraperContext, feed: Feed) -> None:
        # Custom feed processing
        for item in feed.items:
            print(f"Feed item: {item.title}")

scraper = Scraper(
    ScraperConfig(
        seed_urls=[ScraperUrl("https://example.com")],
        callback=CustomCallback(),
    )
)
await scraper.run()
```

## Configuration Options

Configuration for web scraping behavior.

Parameters:
- seed_urls (list[ScraperUrl]): Initial URLs to start scraping from
- callback (ScraperCallback): Callback for processing scraped content
- include_path_patterns (list[str]): URL paths to include (default: [])
- exclude_path_patterns (list[str]): URL paths to exclude (default: [])
- max_parallel_requests (int): Maximum concurrent requests (default: 16)
- use_headless_browser (bool): Use headless browser for JavaScript (default: False) 
- request_timeout_seconds (int): Request timeout in seconds (default: 30)
- follow_web_page_links (bool): Follow links in web pages (default: False)
- follow_sitemap_links (bool): Follow sitemap.xml links (default: True)
- follow_feed_links (bool): Follow RSS/Atom feed links (default: True)
- prevent_default_queuing (bool): Disable automatic URL queuing (default: False)
- max_requested_urls (int): Maximum total URLs to request (default: 65536)
- max_back_to_back_errors (int): Consecutive errors before stopping (default: 128)
- on_response_callback (ScraperResponseCallback): Optional response callback
- max_depth (int): Maximum recursion depth for links (default: 16)
- crawl_delay_seconds (int): Delay between requests per domain (default: 1)
- domain_config (ScraperDomainConfig): Allowed/blocked domains configuration
- user_agent (str): User agent string (default: 'pyminiscraper')
- referer (str): Referer header (default: "https://www.google.com")

### Domain Configuration

Control which domains are allowed or blocked:

```python
from pyminiscraper.config import ScraperDomainConfig, ScraperDomainConfigMode

# Allow only specific domains
config = ScraperDomainConfig(
    allowance=ScraperAllowedDomains(domains=["example.com", "api.example.com"]),
    forbidden_domains=["ads.example.com"]
)

# Allow all domains
config = ScraperDomainConfig(
    allowance=ScraperDomainConfigMode.ALLOW_ALL
)

# Allow only domains derived from seed URLs
config = ScraperDomainConfig(
    allowance=ScraperDomainConfigMode.DERIVE_FROM_SEED_URLS
)
```

## Error Handling

The scraper includes built-in error handling:

- Respects `max_back_to_back_errors` to stop after consecutive failures
- Retries failed requests with exponential backoff
- Logs errors for debugging
- Continues operation after non-fatal errors

## Performance Tips

1. Adjust `max_parallel_requests` based on your needs and server capacity
2. Use `crawl_delay_seconds` to control request rate
3. Enable `use_headless_browser` only when JavaScript rendering is required
4. Implement caching in your callback to avoid re-downloading pages
5. Use path patterns to filter URLs before downloading


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

