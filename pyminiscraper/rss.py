from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import aiohttp
from dateutil.parser import parse as parse_date
import logging
from io import BytesIO

logger = logging.getLogger("rss")

class RssError(Exception):
    pass

@dataclass
class RssItem:
    title: Optional[str]
    link: Optional[str]
    description: Optional[str]
    pub_date: Optional[datetime]
    guid: Optional[str]
    author: Optional[str]
    categories: List[str]
    
@dataclass
class RssFeed:
    title: Optional[str]
    link: Optional[str]
    description: Optional[str]
    language: Optional[str]
    last_build_date: Optional[datetime]
    items: List[RssItem]


class RssParser:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self._ns: Dict[str, str] = {}

    def parse(self, xml_content_bytes: bytes) -> RssFeed:
        try:
            class NamespaceCollector(ET.XMLParser):
                def __init__(self, ns_map):
                    super().__init__()
                    self._ns_map = ns_map

                def start_ns(self, prefix, uri):
                    self._ns_map[prefix] = uri

            self._ns = {}
            parser = NamespaceCollector(self._ns)
            root = ET.parse(BytesIO(xml_content_bytes), parser=parser).getroot()
            
            channel = root.find('.//channel', self._ns) or root
            if channel is None:
                raise RssError("No channel element found in RSS feed")

            return RssFeed(
                title=self._get_text(channel, 'title'),
                link=self._get_text(channel, 'link'),
                description=self._get_text(channel, 'description'),
                language=self._get_text(channel, 'language'),
                last_build_date=self._parse_date(self._get_text(channel, 'lastBuildDate')),
                items=self._parse_items(channel)
            )
        except ET.ParseError as e:
            raise RssError(f"Failed to parse RSS XML: {str(e)}")

    def _parse_items(self, channel: ET.Element) -> List[RssItem]:
        items = []
        for item in channel.findall('.//item', self._ns):
            items.append(RssItem(
                title=self._get_text(item, 'title'),
                link=self._get_text(item, 'link'),
                description=self._get_text(item, 'description'),
                pub_date=self._parse_date(self._get_text(item, 'pubDate')),
                guid=self._get_text(item, 'guid'),
                author=self._get_text(item, 'author') or self._get_text(item, 'creator'),
                categories=self._get_categories(item)
            ))
        return items

    def _get_text(self, element: ET.Element, tag: str) -> Optional[str]:
        for ns in [self._ns.get('dc', ''), self._ns.get('content', ''), '']:
            elem = element.find(f".//{ns}{tag}", self._ns)
            if elem is not None and elem.text:
                return elem.text.strip()
        return None

    def _get_categories(self, item: ET.Element) -> List[str]:
        categories = []
        for category in item.findall('.//category', self._ns):
            if category.text:
                categories.append(category.text.strip())
        return categories

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return parse_date(date_str)
        except (ValueError, TypeError):
            return None

    