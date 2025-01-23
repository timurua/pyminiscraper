from .html import HtmlScraperProcessor
from .metadata import PageMetadataExtractor
from bs4 import BeautifulSoup
from .model import ScraperWebPage
from .text import chunk_text


def extract_metadata(web_page: ScraperWebPage) -> ScraperWebPage:
    if not web_page.content:
        return web_page
    
    html_charset = web_page.content_charset if web_page.content_charset else 'utf-8'
    content = web_page.content.decode(html_charset) 
    soup = BeautifulSoup(content, 'html.parser')

    metadata = PageMetadataExtractor(web_page.normalized_url, content=content, soup=soup).get_all_metadata()
    web_page.metadata_title = metadata.title
    web_page.metadata_description = metadata.description
    web_page.metadata_image_url = metadata.image_url
    web_page.metadata_published_at = metadata.published_at

    html_content = HtmlScraperProcessor(web_page.normalized_url, content, soup).extract()
    web_page.visible_text = html_content.visible_text
    web_page.canonical_url = html_content.canonical_url
    web_page.outgoing_urls = html_content.outgoing_urls
    web_page.sitemap_urls = html_content.sitemap_urls
    web_page.robots_content = html_content.robots_content

    web_page.text_chunks = chunk_text(web_page.visible_text)
    return web_page