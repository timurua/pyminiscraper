from urllib.parse import urlparse
from .robots import Robot, AccessRule

class DomainFilter:
    def __init__(self, allow_l2_domains: bool, urls: list[str])-> None:
        self.domains: set[str] = set()
        self.allow_l2_domains = allow_l2_domains
        if allow_l2_domains:
            for url in urls:
                domain = urlparse(url).netloc
                l2domain = '.'.join(domain.split('.')[-2:])
                self.domains.add(l2domain)
        else:
            for url in urls:
                self.domains.add(urlparse(url).netloc)

    def is_allowed(self, url: str)-> bool:
        domain = urlparse(url).netloc
        if self.allow_l2_domains:
            l2domain = '.'.join(domain.split('.')[-2:])
            return l2domain in self.domains
        else:
            return domain in self.domains
        