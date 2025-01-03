from typing import Dict
from dataclasses import dataclass
from datetime import datetime
from .hash import generate_url_safe_id
from .url import normalize_url, normalized_url_hash as do_normalized_url_hash

class ScraperUrl:
    def __init__(self, url: str, *, no_cache: bool = False, max_depth: int = 16):
        self.url = url
        self.normalized_url = normalize_url(url)
        self.no_cache = no_cache
        self.max_depth = max_depth

    @staticmethod
    def create_terminal():
        return ScraperUrl("", max_depth = -1)

    def is_terminal(self):
        return self.max_depth < 0

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

    headless_browser: bool = False

    metadata_title: str | None = None
    metadata_description: str | None = None
    metadata_image_url: str | None = None
    metadata_published_at: datetime | None = None

    canonical_url: str | None = None
    outgoing_urls: list[str] | None = None
    visible_text: str | None = None
    sitemap_urls: list[str] | None = None
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
                robots_content: list[str] | None = None,
                text_chunks: list[str] | None = None,
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
        self.robots_content = robots_content
        self.text_chunks = text_chunks


        