import asyncclick as click
import asyncio
import pathlib
import logging
import sys
from .scraper import Scraper, ScraperConfig, ScraperUrl, ScraperUrlType
from .store_file import FileStoreFactory
from .config import ScraperDomainConfig, ScraperDomainConfigMode

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
            seed_urls=[
                ScraperUrl(
                    "https://feeds.feedburner.com/PythonInsider", type= ScraperUrlType.FEED)
            ],
            max_parallel_requests=5,
            domain_config=ScraperDomainConfig(
                allowance=ScraperDomainConfigMode.ALLOW_ALL
            ),
            use_headless_browser=True,
            request_timeout_seconds=30,
            crawl_delay_seconds=1,
            follow_web_page_links=False,
            scraper_store_factory=FileStoreFactory(storage_dir.absolute().as_posix()),
        ),
    )
    await scraper.run()

def cli():
    """Wrapper function to run async command"""
    return asyncio.run(main())

if __name__ == '__main__':
    cli()