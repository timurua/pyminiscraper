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

### Scraper URLs

- **Parameter**: `scraper_urls: list[ScraperUrl]`
- **Description**: A list of `ScraperUrl` objects that define the URLs to be scraped and their respective configurations.
- **Example**:
    ```python
    scraper_urls=[
            ScraperUrl("https://www.example.com", max_depth=2)
    ]
    ```

### Max Parallel Requests

- **Parameter**: `max_parallel_requests: int = 16`
- **Description**: The maximum number of parallel requests that the scraper can make.
- **Example**:
    ```python
    max_parallel_requests=16
    ```

### Use Headless Browser

- **Parameter**: `use_headless_browser: bool = False`
- **Description**: Whether to use a headless browser for scraping.
- **Example**:
    ```python
    use_headless_browser=False
    ```

### Timeout Seconds

- **Parameter**: `timeout_seconds: int = 30`
- **Description**: The timeout duration in seconds for each request.
- **Example**:
    ```python
    timeout_seconds=30
    ```

### Only Sitemaps

- **Parameter**: `only_sitemaps: bool = True`
- **Description**: Whether to scrape only sitemap URLs.
- **Example**:
    ```python
    only_sitemaps=True
    ```

### Max Requested URLs

- **Parameter**: `max_requested_urls: int = 64 * 1024`
- **Description**: The maximum number of URLs that can be requested.
- **Example**:
    ```python
    max_requested_urls=64 * 1024
    ```

### Max Back-to-Back Errors

- **Parameter**: `max_back_to_back_errors: int = 128`
- **Description**: The maximum number of consecutive errors allowed before stopping the scraper.
- **Example**:
    ```python
    max_back_to_back_errors=128
    ```

### Scraper Store Factory

- **Parameter**: `scraper_store_factory: ScraperStoreFactory`
- **Description**: The factory used to create the storage for scraped data.
- **Example**:
    ```python
    scraper_store_factory=FileStoreFactory("/path/to/storage")
    ```

### Allow L2 Domains

- **Parameter**: `allow_l2_domains: bool = True`
- **Description**: Whether to allow scraping of second-level domains.
- **Example**:
    ```python
    allow_l2_domains=True
    ```

### Scraper Callback

- **Parameter**: `scraper_callback: ScraperCallback | None = None`
- **Description**: A callback function that is called after each scraping operation.
- **Example**:
    ```python
    scraper_callback=my_callback_function
    ```

### Max Depth

- **Parameter**: `max_depth: int = 16`
- **Description**: The maximum depth to follow links from the initial URL.
- **Example**:
    ```python
    max_depth=16
    ```

### Max Requests Per Hour

- **Parameter**: `max_requests_per_hour: float = 60*60*10`
- **Description**: The maximum number of requests allowed per hour.
- **Example**:
    ```python
    max_requests_per_hour=60*60*10
    ```

### Rerequest After Hours

- **Parameter**: `rerequest_after_hours: int = 24`
- **Description**: The number of hours to wait before re-requesting a URL.
- **Example**:
    ```python
    rerequest_after_hours=24
    ```

### No Page Store

- **Parameter**: `no_page_store: bool = False`
- **Description**: Whether to disable storing the scraped pages.
- **Example**:
    ```python
    no_page_store=False
    ```

### User Agent

- **Parameter**: `user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'`
- **Description**: The user agent string to use for requests.
- **Example**:
    ```python
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    ```
