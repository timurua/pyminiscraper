from bs4 import BeautifulSoup
from urllib.parse import urlparse
from .url import make_absolute_url
from typing import List, Set
from bs4.element import Tag

EXCLUDED_EXTENSIONS = (
    '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
    '.pdf', '.zip', '.tar', '.gz', '.mp3', '.mp4', '.avi', '.mov',
    '.wmv', '.wav', '.flv', '.swf', '.exe', '.dmg', '.iso',
    # Add other non-HTML extensions as needed
)

class HtmlContent:
    def __init__(self, canonical_url: str, outgoing_urls: list[str], visible_text: str, sitemap_urls: list[str] | None,  rss_urls: list[str] | None, robots_content: list[str]| None)-> None:
        self.canonical_url = canonical_url
        self.outgoing_urls = outgoing_urls
        self.visible_text = visible_text
        self.sitemap_urls = sitemap_urls
        self.rss_urls = rss_urls
        self.robots_content = robots_content

class HtmlScraperProcessor:
    def __init__(self, url: str, html: str, soup: BeautifulSoup) -> None:
        self.url = url
        self.html = html
        self.soup = soup

    @staticmethod
    def is_excluded_url(href: str) -> bool:
        """Determine if a URL should be excluded based on its scheme or file extension."""
        # Exclude empty hrefs
        href = href.strip()
        if not href:
            return True
        
        # Exclude JavaScript links, mailto links, and fragments
        if href.startswith(('javascript:', 'mailto:', '#')):
            return True
        
        # Exclude URLs with unwanted file extensions
        parsed_href = urlparse(href)
        path = parsed_href.path.lower()
        if any(path.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
            return True
        return False

    def extract(self) -> HtmlContent:
        # Determine the canonical URL
        canonical_link = self.soup.find('link', rel='canonical')
        canonical_url = self.url
        if isinstance(canonical_link, Tag) and canonical_link.get('href'):
            canonical_url = make_absolute_url(self.url, canonical_link.get('href'))
            
        # Extract robots.txt URL from metadata
        robots_meta = self.soup.find('meta', attrs={'name': 'robots'})
        robots_content = None
        if isinstance(robots_meta, Tag):
            content = robots_meta.get('content')
            if isinstance(content, str):
                robots_content = content.split()
            robots_content = None
            
        # Extract sitemap URL from metadata
        sitemap_links = self.soup.find_all('link', rel='sitemap')
        sitemap_urls: List[str] = []
        for sitemap_link in sitemap_links:
            if sitemap_link and sitemap_link.get('href'):
                sitemap_urls.append(make_absolute_url(self.url, sitemap_link['href']))

        # Extract sitemap URL from metadata
        rss_links = self.soup.find_all('link', rel='alternate', type="application/rss+xml")
        rss_urls: List[str] = []
        for rss_link in rss_links:
            if rss_link and rss_link.get('href'):
                rss_urls.append(make_absolute_url(self.url, rss_link['href']))                

        # Extract outgoing URLs
        outgoing_urls: Set[str] = set()
        for a_tag in self.soup.find_all('a', href=True):
            href = a_tag['href']
            if self.is_excluded_url(href):
                continue
            absolute_href = make_absolute_url(self.url, href)
            outgoing_urls.add(absolute_href)

        # Remove images from the soup to exclude them from the text
        for img in self.soup.find_all('img'):
            img.decompose()

        # Extract text content with simple formatting
        text_content = self.soup.get_text(separator='\n', strip=True)
        
        return HtmlContent(
            canonical_url=canonical_url, 
            outgoing_urls=list(outgoing_urls),
            visible_text=text_content, 
            sitemap_urls=sitemap_urls, 
            rss_urls=rss_urls, 
            robots_content=robots_content)
