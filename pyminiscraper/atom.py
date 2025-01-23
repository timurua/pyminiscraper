from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import asyncio
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from io import BytesIO

@dataclass
class AtomAuthor:
    name: Optional[str] = None
    email: Optional[str] = None
    uri: Optional[str] = None

@dataclass
class AtomLink:
    href: Optional[str] = None
    rel: Optional[str] = None
    type: Optional[str] = None
    title: Optional[str] = None

@dataclass
class AtomEntry:
    id: Optional[str] = None
    title: Optional[str] = None
    updated: Optional[datetime] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    published: Optional[datetime] = None
    authors: Optional[list[AtomAuthor]] = None
    links: Optional[list[AtomLink]] = None
    categories: Optional[list[str]] = None

    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        if self.links is None:
            self.links = []
        if self.categories is None:
            self.categories = []

@dataclass
class AtomFeed:
    id: str|None
    title: str|None
    updated: datetime|None
    authors: list[AtomAuthor]
    entries: list[AtomEntry]
    links: list[AtomLink]|None = None
    subtitle: Optional[str] = None
    
    def __post_init__(self):
        if self.links is None:
            self.links = []

class AtomParser:
    def __init__(self):
        self.ns = {
            'atom': 'http://www.w3.org/2005/Atom'
        }

    def parse(self, content: bytes) -> AtomFeed:
        root = ET.parse(BytesIO(content)).getroot()        
        
        # Parse feed metadata
        feed_id = self._get_text(root, './/atom:id')
        feed_title = self._get_text(root, './/atom:title')
        feed_updated = self._parse_datetime(self._get_text(root, './/atom:updated'))
        feed_subtitle = self._get_text(root, './/atom:subtitle')
        
        # Parse feed authors
        feed_authors = self._parse_authors(root)
        
        # Parse feed links
        feed_links = self._parse_links(root)
        
        # Parse entries
        entries = self._parse_entries(root)
        
        return AtomFeed(
            id=feed_id,
            title=feed_title,
            updated=feed_updated,
            subtitle=feed_subtitle,
            authors=feed_authors,
            links=feed_links,
            entries=entries
        )
    
    def _parse_authors(self, element: ET.Element) -> List[AtomAuthor]:
        """Parse author elements into AtomAuthor objects."""
        authors = []
        for author_elem in element.findall('.//atom:author', self.ns):
            name = self._get_text(author_elem, 'atom:name')
            email = self._get_text(author_elem, 'atom:email')
            uri = self._get_text(author_elem, 'atom:uri')
            authors.append(AtomAuthor(name=name, email=email, uri=uri))
        return authors
    
    def _parse_links(self, element: ET.Element) -> List[AtomLink]:
        """Parse link elements into AtomLink objects."""
        links = []
        for link_elem in element.findall('.//atom:link', self.ns):
            href = link_elem.get('href')
            rel = link_elem.get('rel')
            type_ = link_elem.get('type')
            title = link_elem.get('title')
            links.append(AtomLink(href=href, rel=rel, type=type_, title=title))
        return links
    
    def _parse_entries(self, root: ET.Element) -> List[AtomEntry]:
        """Parse entry elements into AtomEntry objects."""
        entries = []
        for entry_elem in root.findall('.//atom:entry', self.ns):
            entry_id = self._get_text(entry_elem, 'atom:id')
            entry_title = self._get_text(entry_elem, 'atom:title')
            entry_updated = self._parse_datetime(self._get_text(entry_elem, 'atom:updated'))
            entry_published = self._parse_datetime(self._get_text(entry_elem, 'atom:published'))
            entry_content = self._get_text(entry_elem, 'atom:content')
            entry_summary = self._get_text(entry_elem, 'atom:summary')
            
            # Parse entry-specific authors and links
            entry_authors = self._parse_authors(entry_elem)
            entry_links = self._parse_links(entry_elem)
            
            # Parse categories
            categories = [
                term for term in [
                cat.get('term') 
                for cat in entry_elem.findall('atom:category', self.ns)] if term is not None
            ]                        

            
            entries.append(
                AtomEntry(
                    id=entry_id,
                    title=entry_title,
                    updated=entry_updated,
                    published=entry_published,
                    content=entry_content,
                    summary=entry_summary,
                    authors=entry_authors,
                    links=entry_links,
                    categories=categories
                )
            )
        return entries
    
    def _get_text(self, element: ET.Element, xpath: str) -> Optional[str]:
        """Helper method to get text content from an element using xpath."""
        elem = element.find(xpath, self.ns)
        return elem.text if elem is not None else None
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string into datetime object."""
        if not dt_str:
            return None
        try:
            return parsedate_to_datetime(dt_str)
        except (TypeError, ValueError):
            return None

