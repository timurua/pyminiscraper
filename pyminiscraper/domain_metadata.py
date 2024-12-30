from .robots import RobotFileParser
from .sitemap import SitemapParser
from .model import ScraperWebPage

class DomainMetadata:
    def __init__(self, robots: RobotFileParser, sitemaps: dict[str, SitemapParser], home_page: ScraperWebPage) -> None:
        self.robots = robots
        self.sitemaps = sitemaps
        self.home_page = home_page

