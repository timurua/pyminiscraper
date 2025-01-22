from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
import xml.etree.ElementTree as ET
import aiohttp
import logging
from .rss import RssError, RssParser
from .atom import AtomParser, AtomLink

logger = logging.getLogger("feed")

class FeedError(Exception):
    pass

@dataclass
class Item:
    title: Optional[str]
    link: Optional[str]
    description: Optional[str]
    pub_date: Optional[datetime]


@dataclass
class Feed:
    items: List[Item]


class FeedParser:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        
    def from_rss(self, xml_content_bytes: bytes) -> Feed:
        rss_parser = RssParser(self.session)
        rss_feed = rss_parser.parse(xml_content_bytes)
        items = []
        for rss_item in rss_feed.items:
            items.append(Item(
                title=rss_item.title,
                link=rss_item.link,
                description=rss_item.description,
                pub_date=rss_item.pub_date
            ))
        return Feed(items=items)
    
    def from_atom(self, xml_content_bytes: bytes) -> Feed:
        atom_parser = AtomParser()
        atom_feed = atom_parser.parse(xml_content_bytes)
        items = []
        for atom_entry in atom_feed.entries:
            items.append(Item(
                title=atom_entry.title,
                link=self._get_link(atom_entry.links) if atom_entry.links else None,
                description=atom_entry.content,
                pub_date=atom_entry.published
            ))
        return Feed(items=items)
    
    def _get_link(self, links: list[AtomLink]|None) -> Optional[str]:
        if links:
            for link in links:
                if link.type == 'text/html':
                    return link.href
        return None
        
    
    @classmethod
    async def download_and_parse(cls, normalized_url: str, session: aiohttp.ClientSession) -> Feed:
        try:
            async with session.get(normalized_url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to download rss {normalized_url} status: {response.status}")
                
                content_type = response.content_type
                if not content_type:
                    raise ValueError(f"Failed to identify content for {normalized_url}")
                
                if 'rss' in content_type:
                    return cls(session).from_rss(await response.read())
                elif 'xml' in content_type:
                    return cls(session).from_atom(await response.read())                
                else:
                    raise ValueError(f"Unknown content {content_type} for {normalized_url}")
                
        except Exception as e:
            logger.error(f"Error fetching {normalized_url}: {e}")
            raise RssError(f"""Failed to fetch rss from {normalized_url}""") from e                    
