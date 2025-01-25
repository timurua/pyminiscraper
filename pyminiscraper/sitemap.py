from typing import List, Dict, Union, Optional
import aiohttp
from datetime import datetime
from enum import Enum
import logging

import xml.etree.ElementTree as ET

logger = logging.getLogger("sitemap")

class SitemapError(Exception):
    pass

class ChangeFrequency(Enum):
    ALWAYS = "always"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    NEVER = "never"

    @classmethod
    def from_str(cls, value: str) -> 'ChangeFrequency':
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid change frequency: {value}")

class SitemapUrl:
    def __init__(self, loc: str, lastmod: datetime | None) -> None:
        self.loc = loc
        self.lastmod = lastmod

class PageUrl:
    def __init__(self, loc: str, lastmod: datetime | None, changefreq: ChangeFrequency | None, priority: float | None) -> None:
        self.loc = loc
        self.lastmod = lastmod
        self.changefreq = changefreq
        self.priority = priority        

class Sitemap:
    def __init__(self) -> None:
        self.page_urls: List[PageUrl] = []
        self.sitemap_urls: List[SitemapUrl] = []

    def parse(self, xml_content: str) -> None:

        tree: ET.ElementTree = ET.ElementTree(ET.fromstring(xml_content))
        root: ET.Element = tree.getroot()

        if root.tag.endswith('urlset'):
            self.page_urls =self._parse_urlset(root)
        elif root.tag.endswith('sitemapindex'):
            self.sitemap_urls = self._parse_sitemapindex(root)
        else:
            raise ValueError("Unsupported XML format")

    def _parse_urlset(self, root: ET.Element) -> List[PageUrl]:
        urls = []
        namespace = {'ns': root.tag.split('}')[0].strip('{')}
        for url in root.findall('ns:url', namespace):
            loc_elem = url.find('ns:loc', namespace)
            if loc_elem is None or loc_elem.text is None:
                continue
            loc = loc_elem.text
            lastmod_elem = url.find('ns:lastmod', namespace)
            lastmod = lastmod_elem.text if lastmod_elem is not None else None
            lastmod_date = None
            if lastmod is not None:
                lastmod_date = datetime.fromisoformat(lastmod.replace('Z', '+00:00'))
            changefreq_elem = url.find('ns:changefreq', namespace)
            changefreq = ChangeFrequency.from_str(changefreq_elem.text) if changefreq_elem is not None and changefreq_elem.text is not None else None
            priority_elem = url.find('ns:priority', namespace)
            priority = float(priority_elem.text) if priority_elem is not None and priority_elem.text is not None else None
            urls.append(PageUrl(loc, lastmod_date, changefreq, priority))

        return urls

    def _parse_sitemapindex(self, root: ET.Element) -> List[SitemapUrl]:
        sitemaps = []
        namespace = {'ns': root.tag.split('}')[0].strip('{')}
        for sitemap in root.findall('ns:sitemap', namespace):
            loc_elem = sitemap.find('ns:loc', namespace)
            if loc_elem is None or loc_elem.text is None:
                continue
            loc = loc_elem.text
            lastmod_elem = sitemap.find('ns:lastmod', namespace)
            lastmod = lastmod_elem.text if lastmod_elem is not None else None
            lastmod_date = None
            if lastmod is not None:
                lastmod_date = datetime.fromisoformat(lastmod.replace('Z', '+00:00'))
            sitemaps.append(SitemapUrl(loc, lastmod_date))
        return sitemaps

    @classmethod
    async def download_and_parse(cls, normalized_url: str, session: aiohttp.ClientSession, timeout_seconds: int = 30) -> "Sitemap":
        """Downloads sitemap from URL and returns parsed result"""
        
        try:
            async with session.get(normalized_url, timeout=aiohttp.ClientTimeout(total=timeout_seconds)) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to download sitemap: {response.status}")
                content = await response.text()
                parser = cls()
                parser.parse(content)
                return parser
        except Exception as e:
            logger.error(f"Error fetching {normalized_url}: {e}")
            raise SitemapError(f"""Failed to fetch sitemap from {normalized_url}""") from e                    

