from .store import ScraperStore, ScraperStoreFactory
from typing import Optional
from .model import ScraperWebPage
import os
import json
from dateutil import parser
from .url import normalized_url_hash

class FileStoreFactory(ScraperStoreFactory):
    def __init__(self, directory: str):
        self.directory = directory

    def new_store(self) -> ScraperStore:
        return FileStore(self.directory)

class FileStore(ScraperStore):
    def __init__(self, directory: str):
        self.directory = directory
        
    async def store_page(self, response: ScraperWebPage) -> None:
        normalized_url = response.normalized_url
        safe_filename = self.safe_filename(normalized_url)
        filepath = os.path.join(self.directory, f"{safe_filename}.json")

        os.makedirs(self.directory, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.model_dump_json(response))

    def model_dump_json(self, page: ScraperWebPage) -> str:
        return json.dumps({
            'url': page.url,
            'normalized_url': page.normalized_url,
            'normalized_url_hash': page.normalized_url_hash,
            'status_code': page.status_code,
            'headers': page.headers,
            'content': page.content.decode('utf-8') if page.content else None,
            'content_type': page.content_type,
            'content_charset': page.content_charset,
            'headless_browser': page.headless_browser,
            'metadata_title': page.metadata_title,
            'metadata_description': page.metadata_description,
            'metadata_image_url': page.metadata_image_url,
            'metadata_published_at': page.metadata_published_at.isoformat() if page.metadata_published_at else None,
            'canonical_url': page.canonical_url,
            'outgoing_urls': page.outgoing_urls,
            'visible_text': page.visible_text,
            'sitemap_urls': page.sitemap_urls,
            'robots_content': page.robots_content,
            'text_chunks': page.text_chunks,
        })

    async def load_page(self, normalized_url: str) -> Optional[ScraperWebPage]:
        safe_filename = self.safe_filename(normalized_url)
        filepath = os.path.join(self.directory, f"{safe_filename}.json")

        if not os.path.exists(filepath):
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return self.model_load_json(f.read())
        
    def safe_filename(self, normalized_url: str) -> str:
        hash = normalized_url_hash(normalized_url)
        safe_normalized_url = normalized_url.replace('/', '_').replace(':', '_')
        return f"{safe_normalized_url[:64]}_{hash}"
        
    def model_load_json(self, data: str) -> ScraperWebPage:
        d = json.loads(data)
        return ScraperWebPage(
            url=d['url'],
            normalized_url=d['normalized_url'],
            status_code=d['status_code'],
            headers=d['headers'],
            content=d['content'].encode('utf-8') if d['content'] else None,
            content_type=d['content_type'],
            content_charset=d['content_charset'],
            headless_browser=d['headless_browser'],
            metadata_title=d['metadata_title'],
            metadata_description=d['metadata_description'],
            metadata_image_url=d['metadata_image_url'],
            metadata_published_at=parser.parse(d['metadata_published_at']) if d['metadata_published_at'] else None,
            canonical_url=d['canonical_url'],
            outgoing_urls=d['outgoing_urls'],
            visible_text=d['visible_text'],
            sitemap_urls=d['sitemap_urls'],
            robots_content=d['robots_content'],
            text_chunks=d['text_chunks'],
        )