import asyncclick as click
import asyncio
import pathlib
import logging
import sys
from .scraper import Scraper, ScraperConfig, ScraperUrl, ScraperUrlType
from .store_file import FileStore
from .config import ScraperDomainConfig, ScraperDomainConfigMode
from fake_useragent import UserAgent

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

    ua = UserAgent()


def cli():
    """Wrapper function to run async command"""
    return asyncio.run(main())

if __name__ == '__main__':
    cli()