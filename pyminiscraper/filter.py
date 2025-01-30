from urllib.parse import urlparse
from .config import ScraperDomainConfig, ScraperDomainConfigMode, ScraperAllowedDomains
import re
from .robots import robots_txt_pattern_compile
from .url import normalize_url

class DomainFilter:
    def __init__(self, domain_config: ScraperDomainConfig, urls: list[str] = [])-> None:
        self.forbidden_domains = domain_config.forbidden_domains
        self.allowed_domains: set[str]|None = set()        
        if domain_config.allowance == ScraperDomainConfigMode.DIREVE_FROM_URLS:
            for url in urls:
                self.allowed_domains.add(urlparse(url).netloc)
        elif domain_config.allowance == ScraperDomainConfigMode.ALLOW_ALL:
            self.allowed_domains = None
        elif isinstance(domain_config.allowance, ScraperAllowedDomains):
            for domain in domain_config.allowance.domains:
                self.allowed_domains.add(domain)
        else:
            raise ValueError("Unsupported domain config mode")
                
        if domain_config.forbidden_domains:
            self.forbidden_domains = domain_config.forbidden_domains
                
    def is_allowed(self, url: str)-> bool:
        url = normalize_url(url)
        domain = urlparse(url).netloc
        if self.forbidden_domains:
            for forbidden_domain in self.forbidden_domains:
                if domain.endswith(forbidden_domain):
                    return False
                
        if self.allowed_domains is None or len(self.allowed_domains) == 0:
            return True
        
        for allowed_domain in self.allowed_domains:
            if domain.endswith(allowed_domain):
                return True
        
        return False
    
class PathFilter:
    def __init__(self, path_filters: list[str], default_value: bool = True)-> None:
        self.path_filter_patterns: list[re.Pattern] = []
        self.default_value = default_value
        for path_filter in path_filters:
            self.path_filter_patterns.append(robots_txt_pattern_compile(path_filter))
            
    def is_passing(self, url: str)-> bool:
        if not self.path_filter_patterns:
            return self.default_value
        
        path = urlparse(url).path
        if not path.startswith('/'):
            path = "/" + path
                    
        for path_filter_pattern in self.path_filter_patterns:
            if path_filter_pattern.fullmatch(path):
                return True
        return False
        