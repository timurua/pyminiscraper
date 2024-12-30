import requests
from urllib.parse import urljoin

class DomainMetadata:
    def __init__(self, home_page: str, sitemap: str, robots: str):
        self.home_page = home_page
        self.sitemap = sitemap
        self.robots = robots

class DomainMetadataScraper:
    def __init__(self, session: requests.Session, domain: str):
        self.session = session
        self.domain = domain

    def scrape(self):
        urls = {
            "home_page": urljoin(self.domain, "/"),
            "sitemap": urljoin(self.domain, "/sitemap.xml"),
            "robots": urljoin(self.domain, "/robots.txt")
        }

        results = {}
        for key, url in urls.items():
            try:
                response = self.session.get(url)
                response.raise_for_status()
                results[key] = response.text
            except requests.RequestException as e:
                results[key] = f"Error: {e}"

        return results