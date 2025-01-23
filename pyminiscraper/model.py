from typing import Dict
from dataclasses import dataclass
from datetime import datetime
from .url import normalize_url, normalized_url_hash as do_normalized_url_hash
from enum import Enum

class ScraperUrlType(Enum):
    HTML = 0
    SITEMAP = 1
    FEED = 2
    TERMINATE_LOOP = -1
    

class ScrapeUrlMetadata:
    def __init__(self, title: str | None, description: str | None, published_at: datetime | None, image_url: str | None):   
        self.title = title
        self.description = description
        self.published_at = published_at
        self.image_url = image_url

class ScraperUrl:
    def __init__(self, url: str, *, max_depth: int = 16, type: ScraperUrlType = ScraperUrlType.HTML, high_priority: bool = False, metadata: ScrapeUrlMetadata | None = None):
        self.url = url
        self.normalized_url = normalize_url(url)
        self.max_depth = max_depth
        self.type = type
        self.high_priority = high_priority
        self.metadata = metadata

    @staticmethod
    def create_terminal():
        return ScraperUrl("", type=ScraperUrlType.TERMINATE_LOOP)

    def is_terminal(self):
        return self.type == ScraperUrlType.TERMINATE_LOOP

@dataclass
class ScraperWebPage:
    """Container for HTTP response data"""
    status_code: int
    url: str
    normalized_url: str
    normalized_url_hash: str
    headers: Dict[str, str] | None
    content: bytes | None
    content_type: str | None
    content_charset: str | None = None
    requested_at: datetime | None = None

    headless_browser: bool = False

    metadata_title: str | None = None
    metadata_description: str | None = None
    metadata_image_url: str | None = None
    metadata_published_at: datetime | None = None

    canonical_url: str | None = None
    outgoing_urls: list[str] | None = None
    visible_text: str | None = None
    sitemap_urls: list[str] | None = None
    feed_urls: list[str] | None = None
    robots_content: list[str] | None = None
    text_chunks: list[str] | None = None

    def __init__(self, 
                status_code: int,
                url: str,
                normalized_url: str,
                headers: Dict[str, str] | None,
                content: bytes | None,
                content_type: str | None = None,
                content_charset: str | None = None,
                headless_browser: bool = False,
                metadata_title: str | None = None,
                metadata_description: str | None = None,
                metadata_image_url: str | None = None,
                metadata_published_at: datetime | None = None,
                canonical_url: str | None = None,
                outgoing_urls: list[str] | None = None,
                visible_text: str | None = None,
                sitemap_urls: list[str] | None = None,
                rss_urls: list[str] | None = None,
                robots_content: list[str] | None = None,
                text_chunks: list[str] | None = None,
                requested_at: datetime | None = None
                ):
        self.status_code = status_code
        self.url = url
        self.normalized_url = normalized_url
        self.normalized_url_hash = do_normalized_url_hash(normalized_url)
        self.headers = headers
        self.content = content 
        self.content_type = content_type
        self.content_charset = content_charset
        self.headless_browser = headless_browser
        self.metadata_title = metadata_title
        self.metadata_description = metadata_description
        self.metadata_image_url = metadata_image_url
        self.metadata_published_at = metadata_published_at
        self.canonical_url = canonical_url
        self.outgoing_urls = outgoing_urls
        self.visible_text = visible_text
        self.sitemap_urls = sitemap_urls
        self.feed_urls = rss_urls
        self.robots_content = robots_content
        self.text_chunks = text_chunks
        self.requested_at = requested_at


        