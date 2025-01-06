# pyminiscraper

## Introduction

`pyminiscraper` is a lightweight Python library designed for easy web scraping. It provides a simple interface to extract data from web pages with minimal setup. Whether you are a beginner or an advanced user, `pyminiscraper` offers the flexibility to handle various scraping tasks efficiently.

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
        only_sitemaps=False,
        scraper_store_factory=FileStoreFactory(storage_dir.absolute().as_posix()),
    ),
)
await scraper.run()

```

## Advanced Configuration Options

`pyminiscraper` also provides advanced configuration options to handle more complex scraping scenarios. Below are some of the options you can configure:

### Custom Headers

You can set custom headers to mimic a real browser request:

```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

scraper = Scraper('https://example.com', headers=headers)
```

### Handling Pagination

To scrape data from multiple pages, you can use the pagination feature:

```python
scraper = Scraper('https://example.com/page/{}')

for page in range(1, 6):
    data = scraper.extract({
        'title': 'h1',
        'description': 'meta[name="description"]::attr(content)'
    }, page=page)
    print(data)
```

### Using Proxies

If you need to use a proxy to avoid IP blocking, you can configure it as follows:

```python
proxies = {
    'http': 'http://10.10.1.10:3128',
    'https': 'http://10.10.1.10:1080',
}

scraper = Scraper('https://example.com', proxies=proxies)
```

### Error Handling

You can handle errors gracefully using the built-in error handling mechanism:

```python

storage_dir.mkdir(parents=True, exist_ok=True)

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
        only_sitemaps=False,
        scraper_store_factory=FileStoreFactory(storage_dir.absolute().as_posix()),
    ),
)
await scraper.run()

```

### Scraper Configuration

You can configure the scraper using the `ScraperConfig` class to handle various advanced settings:

```python
from pyminiscraper import ScraperConfig, ScraperUrl, ScraperStoreFactory, ScraperCallback

config = ScraperConfig(
    scraper_urls=[ScraperUrl('https://example.com')],
    max_parallel_requests=16,
    use_headless_browser=False,
    timeout_seconds=30,
    only_sitemaps=True,
    max_requested_urls=64 * 1024,
    max_back_to_back_errors=128,
    scraper_store_factory=ScraperStoreFactory(),
    allow_l2_domains=True,
    scraper_callback=None,
    max_depth=16,
    max_requests_per_hour=60*60*10,
    rerequest_after_hours=24,
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
)
```

With these advanced options, `pyminiscraper` allows you to customize your scraping tasks to fit your specific needs.
