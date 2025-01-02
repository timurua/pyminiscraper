import asyncclick as click
import asyncio
import pathlib
import logging
import sys
from .scraper import Scraper, ScraperConfig, ScraperUrl
from .store_memory import MemoryStoreFactory
from .scrape_html_browser import BrowserHtmlScraperFactory
from .scrape_html_http import HttpHtmlScraperFactory

@click.command()
@click.argument('storage_dir', type=click.Path(file_okay=False, dir_okay=True, path_type=pathlib.Path))
async def main(storage_dir: pathlib.Path):
    logging.basicConfig(
        # Set the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        level=logging.INFO,
        # Define the log format
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),  # Log to standard output
        ]
    )
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
            max_queue_size=1024*1024,
            timeout_seconds=30,
            scraper_store_factory=MemoryStoreFactory(),
        ),
    )
    await scraper.run()

def cli():
    """Wrapper function to run async command"""
    return asyncio.run(main())

if __name__ == '__main__':
    cli()