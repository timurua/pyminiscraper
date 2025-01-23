# pyminiscraper

## Introduction

`pyminiscraper` is a lightweight Python library designed for easy web scraping. It provides a simple interface to extract data from web pages with minimal setup. Whether you are a beginner or an advanced user, `pyminiscraper` offers the flexibility to handle various scraping tasks efficiently.

## Features

| Feature | Implemented |
|---------|------------|
| Basic Web Page scraping | ✅ |
| Extremely scalable async scraping | ✅ |
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

## Use Cases

### Downloading only sitemap referenced web pages

Here is a basic example of how to use `pyminiscraper` to scrape 

```python

scraper = Scraper(
    ScraperConfig(
        seed_urls=[
            ScraperUrl(
                "https://www.anthropic.com/", max_depth=2, ScraperUrlType.HTML)
        ],
        follow_sitemap_links=True,
        follow_web_page_links=False,
        follow_feed_links=False,
        scraper_store_factory=FileStoreFactory(storage_dir),
    ),
)
await scraper.run()

```

### Scraping pages referenced in Atom/RSS Feeds

Here is a basic example of how to use `pyminiscraper` to scrape 

```python
scraper = Scraper(
    ScraperConfig(
        seed_urls=[
            ScraperUrl(
                "https://feeds.feedburner.com/PythonInsider", type= ScraperUrlType.FEED)
        ],
        follow_sitemap_links=False,
        follow_web_page_links=False,
        follow_feed_links=True,
        scraper_store_factory=FileStoreFactory(storage_dir),
    ),
)
await scraper.run()
```

### Full web site capture/spidering using all possible sources of references Sitemaps/Atom/RSS/links on Web Pages

Here is a basic example of how to use `pyminiscraper` to scrape 

```python
scraper = Scraper(
    ScraperConfig(
        seed_urls=[
            ScraperUrl(
                "https://www.anthropic.com/", type= ScraperUrlType.FEED)
        ],
        follow_sitemap_links=True,
        follow_web_page_links=True,
        follow_feed_links=True,
        scraper_store_factory=FileStoreFactory(storage_dir),
    ),
)
await scraper.run()
```

### High volume scraping

Here is a basic example of how to use `pyminiscraper` to scrape 

```python
async def scrape_site(url: str)
    scraper = Scraper(
        ScraperConfig(
            seed_urls=[
                ScraperUrl(
                    url, type= ScraperUrlType.FEED)
            ],
            follow_sitemap_links=True,
            follow_web_page_links=True,
            follow_feed_links=True,
            scraper_store_factory=FileStoreFactory(storage_dir),
        ),
    )
    await scraper.run()

sites = [
            "https://example1.com", 
            "https://example2.com", 
            "https://example3.com"
        ]
tasks = [scrape_site(url) for url in sites]
await asyncio.gather(*tasks)
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
