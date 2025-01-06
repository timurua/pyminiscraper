from .robots import Robot
from .model import ScraperWebPage

class DomainMetadata:
    def __init__(self, domain_url: str, robots: Robot, home_page: ScraperWebPage|None = None) -> None:
        self.domain_url = domain_url
        self.robots = robots

