import asyncclick as click
import asyncio
import pathlib
import logging
import sys

from pyminiscraper.feed import Feed
from .scraper import Scraper, ScraperConfig, ScraperUrl, ScraperUrlType
from .store_file import FileStore
from .config import ScraperDomainConfig, ScraperDomainConfigMode, ScraperCallback, ScraperContext, ScraperWebPage, ScraperUrl
from .model import ScrapeUrlMetadata
from typing import Optional, override

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
    
    store = FileStore(storage_dir.absolute().as_posix())
    
    class Callback(ScraperCallback):            
        @override
        async def on_web_page(self, context: ScraperContext, request: ScraperUrl, response: ScraperWebPage) -> None:
            await store.on_web_page(context, request, response)            
            
            if response.metadata_image_url:
                async with context.do_request(response.metadata_image_url) as http_response:
                    if http_response and http_response.status == 200:
                        image_data = await http_response.read()
                        content_type = http_response.headers.get('content-type', '')
                        ext = '.jpg' if 'jpeg' in content_type.lower() else '.png' if 'png' in content_type.lower() else '.jpg'
                        with open(storage_dir / f"{response.normalized_url_hash}{ext}", "wb") as f:
                            f.write(image_data)
                
            
        @override
        async def load_web_page_from_cache(self, normalized_url: str) -> Optional[ScraperWebPage]:
            return await store.load_web_page_from_cache(normalized_url)
        
        @override
        async def on_feed(self, context: ScraperContext, feed: Feed) -> None:
            for entry in feed.items:
                if not entry.link:
                    continue
                await context.equeue_url(ScraperUrl(entry.link, type=ScraperUrlType.HTML, max_depth=1, 
                        metadata=ScrapeUrlMetadata(entry.title, entry.description, entry.pub_date, None)))

    scraper = Scraper(
        ScraperConfig(
            seed_urls=[
                ScraperUrl(
                    "https://feeds.feedburner.com/PythonInsider", type= ScraperUrlType.FEED)
            ],
            max_parallel_requests=5,
            prevent_default_queuing=True,
            domain_config=ScraperDomainConfig(
                allowance=ScraperDomainConfigMode.ALLOW_ALL
            ),
            use_headless_browser=True,
            request_timeout_seconds=30,
            crawl_delay_seconds=1,
            follow_web_page_links=False,
            callback=Callback(),
        ),
    )
    await scraper.run()

def cli():
    """Wrapper function to run async command"""
    return asyncio.run(main())

if __name__ == '__main__':
    cli()