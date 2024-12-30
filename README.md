# pyminiscraper

## Introduction

`pyminiscraper` is a lightweight Python library designed for easy web scraping. It provides a simple interface to extract data from web pages with minimal setup. Whether you are a beginner or an advanced user, `pyminiscraper` offers the flexibility to handle various scraping tasks efficiently.

## Simplest Use Case

Here is a basic example of how to use `pyminiscraper` to scrape data from a web page:

```python
from pyminiscraper import Scraper

# Initialize the scraper with the target URL
scraper = Scraper('https://example.com')

# Extract data using CSS selectors
data = scraper.extract({
    'title': 'h1',
    'description': 'meta[name="description"]::attr(content)'
})

print(data)
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
try:
    scraper = Scraper('https://example.com')
    data = scraper.extract({
        'title': 'h1',
        'description': 'meta[name="description"]::attr(content)'
    })
except Exception as e:
    print(f"An error occurred: {e}")
```

With these advanced options, `pyminiscraper` allows you to customize your scraping tasks to fit your specific needs.
