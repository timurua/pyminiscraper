import pytest
from datetime import datetime
from pyminiscraper.sitemap import Sitemap, PageUrl, SitemapUrl, ChangeFrequency
import aiohttp
from aioresponses import aioresponses
from pyminiscraper.sitemap import Sitemap, ChangeFrequency, SitemapError

def test_parse_urlset():
    xml_content = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>http://example.com/</loc>
            <lastmod>2023-10-01T12:00:00Z</lastmod>
            <changefreq>daily</changefreq>
            <priority>0.8</priority>
        </url>
    </urlset>
    """
    parser = Sitemap()
    parser.parse(xml_content)
    
    assert len(parser.page_urls) == 1
    page_url = parser.page_urls[0]
    assert page_url.loc == "http://example.com/"
    assert page_url.lastmod == datetime.fromisoformat("2023-10-01T12:00:00+00:00")
    assert page_url.changefreq == ChangeFrequency.DAILY
    assert page_url.priority == 0.8

def test_parse_sitemapindex():
    xml_content = """
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <sitemap>
            <loc>http://example.com/sitemap1.xml</loc>
            <lastmod>2023-10-01T12:00:00Z</lastmod>
        </sitemap>
    </sitemapindex>
    """
    parser = Sitemap()
    parser.parse(xml_content)
    
    assert len(parser.sitemap_urls) == 1
    sitemap_url = parser.sitemap_urls[0]
    assert sitemap_url.loc == "http://example.com/sitemap1.xml"
    assert sitemap_url.lastmod == datetime.fromisoformat("2023-10-01T12:00:00+00:00")

def test_parse_invalid_format():
    xml_content = """
    <invalidtag>
    </invalidtag>
    """
    parser = Sitemap()
    with pytest.raises(ValueError, match="Unsupported XML format"):
        parser.parse(xml_content)

@pytest.mark.asyncio
async def test_download_and_parse_success():
    url = "http://example.com/sitemap.xml"
    xml_content = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>http://example.com/</loc>
            <lastmod>2023-10-01T12:00:00Z</lastmod>
            <changefreq>daily</changefreq>
            <priority>0.8</priority>
        </url>
    </urlset>
    """
    
    with aioresponses() as m:
        m.get(url, status=200, body=xml_content)
        
        async with aiohttp.ClientSession() as session:
            parser = await Sitemap.download_and_parse(url, session)
            
            assert len(parser.page_urls) == 1
            page_url = parser.page_urls[0]
            assert page_url.loc == "http://example.com/"
            assert page_url.lastmod == datetime.fromisoformat("2023-10-01T12:00:00+00:00")
            assert page_url.changefreq == ChangeFrequency.DAILY
            assert page_url.priority == 0.8

@pytest.mark.asyncio
async def test_download_and_parse_failure():
    url = "http://example.com/sitemap.xml"
    
    with aioresponses() as m:
        m.get(url, status=404)
        
        async with aiohttp.ClientSession() as session:
            with pytest.raises(SitemapError):
                await Sitemap.download_and_parse(url, session)

@pytest.mark.asyncio
async def test_download_and_parse_client_error():
    url = "http://example.com/sitemap.xml"
    
    with aioresponses() as m:
        m.get(url, exception=aiohttp.ClientError("Connection error"))
        
        async with aiohttp.ClientSession() as session:
            with pytest.raises(SitemapError):
                await Sitemap.download_and_parse(url, session)
