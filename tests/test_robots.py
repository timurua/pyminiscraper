import pytest
from pyminiscraper.robots import Robot, RuleLine, Entry, AccessRule
import aiohttp
import asyncio
from pyminiscraper.robots import Robot, AccessRule, RobotsError, robots_txt_pattern_compile, robots_txt_path_match
from aioresponses import aioresponses
import re

def test_robot_file_parser_initialization():
    parser = Robot()
    assert parser.entries == []
    assert parser.sitemap_urls == set([])
    assert parser.default_entry is None
    assert parser.access_rule == AccessRule.ALLOW_ALL

def test_robot_file_parser_can_fetch_disallow_all():
    parser = Robot()
    parser.access_rule = AccessRule.DISALLOW_ALL
    assert parser.can_fetch("*", "/") is False

def test_robot_file_parser_can_fetch_allow_all():
    parser = Robot()
    parser.access_rule = AccessRule.ALLOW_ALL
    assert parser.can_fetch("*", "/") is True


def test_rule_line_initialization():
    rule = RuleLine("/path", True)
    assert rule.path == "/path"
    assert rule.allowance is True

def test_rule_line_applies_to():
    rule = RuleLine("/path", True)
    assert rule.applies_to("/path") is True
    assert rule.applies_to("/other") is False

def test_entry_initialization():
    entry = Entry()
    assert entry.useragents == []
    assert entry.rulelines == []
    assert entry.delay is None
    assert entry.req_rate is None

def test_entry_applies_to():
    entry = Entry()
    entry.useragents.append("test-agent")
    assert entry.applies_to("test-agent") is True
    assert entry.applies_to("other-agent") is False

def test_entry_allowance():
    entry = Entry()
    entry.rulelines.append(RuleLine("/path", True))
    assert entry.allowance("/path") is True
    assert entry.allowance("/other") is True
    entry.rulelines.append(RuleLine("/other", False))
    assert entry.allowance("/other") is False

def test_robot_file_parser_parse_empty_lines():
    parser = Robot()
    lines = """
    User-agent: *
    
    Disallow: /private

    Allow: /public
    
    Crawl-delay: 10
    
    Request-rate: 1/5
    
    Sitemap: http://example.com/sitemap.xml

    User-agent: test-agent
    
    Disallow: /test
    """
    parser.parse(lines)

    assert len(parser.entries) == 1
    assert parser.default_entry is not None
    assert parser.default_entry.useragents == ["*"]
    assert parser.default_entry.rulelines[0].path == "/private"
    assert parser.default_entry.rulelines[0].allowance is False
    assert parser.default_entry.rulelines[1].path == "/public"
    assert parser.default_entry.rulelines[1].allowance is True
    assert parser.default_entry.delay == 10
    assert parser.default_entry.req_rate is not None
    assert parser.default_entry.req_rate.requests == 1
    assert parser.default_entry.req_rate.seconds == 5
    assert parser.sitemap_urls == set(["http://example.com/sitemap.xml"])

    assert parser.entries[0].useragents == ["test-agent"]
    assert parser.entries[0].rulelines[0].path == "/test"
    assert parser.entries[0].rulelines[0].allowance is False

def test_robot_file_parser_parse_comments():
    parser = Robot()
    content = """
    # This is a comment
    User-agent: *
    Disallow: /private # This is another comment
    Allow: /public
    Crawl-delay: 10
    Request-rate: 1/5
    Invalid-line
    Sitemap: http://example.com/sitemap.xml

    User-agent: test-agent
    Disallow: /test
    """
    parser.parse(content)

    assert len(parser.entries) == 1
    assert parser.default_entry is not None
    assert parser.default_entry.useragents == ["*"]
    assert parser.default_entry.rulelines[0].path == "/private"
    assert parser.default_entry.rulelines[0].allowance is False
    assert parser.default_entry.rulelines[1].path == "/public"
    assert parser.default_entry.rulelines[1].allowance is True
    assert parser.default_entry.delay == 10
    assert parser.default_entry.req_rate is not None
    assert parser.default_entry.req_rate.requests == 1
    assert parser.default_entry.req_rate.seconds == 5
    assert parser.sitemap_urls == set(["http://example.com/sitemap.xml"])

    assert parser.entries[0].useragents == ["test-agent"]
    assert parser.entries[0].rulelines[0].path == "/test"
    assert parser.entries[0].rulelines[0].allowance is False

    assert parser.can_fetch("test-agent", "/") is True
    assert parser.can_fetch("test-agent", "/other") is True
    assert parser.can_fetch("test-agent", "/") is True

    assert parser.can_fetch("unknown-agent", "/test") is True
    assert parser.can_fetch("unknown-agent", "/other") is True

@pytest.mark.asyncio
async def test_download_and_parse_disallow_all():
    with aioresponses() as m:
        m.get("http://example.com/robots.txt", status=403, body="")
        async with aiohttp.ClientSession() as session:
            parser = await Robot.download_and_parse("http://example.com/robots.txt", session)
            assert parser.access_rule == AccessRule.DISALLOW_ALL

@pytest.mark.asyncio
async def test_download_and_parse_allow_all():
    with aioresponses() as m:
        m.get("http://example.com/robots.txt", status=404, body="")
        async with aiohttp.ClientSession() as session:
            parser = await Robot.download_and_parse("http://example.com/robots.txt", session)
            assert parser.access_rule == AccessRule.ALLOW_ALL

@pytest.mark.asyncio
async def test_download_and_parse_parse_content():
    with aioresponses() as m:
        m.get("http://example.com/robots.txt", status=200, body="""
            User-agent: *
            Disallow: /private
        """)
        async with aiohttp.ClientSession() as session:
            parser = await Robot.download_and_parse("http://example.com/robots.txt", session)
            assert parser.access_rule == AccessRule.ALLOW_ALL
            assert parser.default_entry is not None
            assert parser.default_entry.useragents == ["*"]
            assert parser.default_entry.rulelines[0].path == "/private"
            assert parser.default_entry.rulelines[0].allowance is False

@pytest.mark.asyncio
async def test_download_and_parse_client_error(caplog):
    with aioresponses() as m:
        m.get("http://example.com/robots.txt", exception=aiohttp.ClientError("Client error"))
        async with aiohttp.ClientSession() as session:
            with pytest.raises(RobotsError):
                await Robot.download_and_parse("http://example.com/robots.txt", session)
            
@pytest.mark.asyncio
async def test_download_and_parse_timeout_error(caplog):
    with aioresponses() as m:
        m.get("http://example.com/robots.txt", exception=asyncio.TimeoutError("Timeout error"))
        async with aiohttp.ClientSession() as session:
            with pytest.raises(RobotsError):
                await Robot.download_and_parse("http://example.com/robots.txt", session)

@pytest.mark.asyncio
async def test_download_and_parse_unicode_decode_error(caplog):
    with aioresponses() as m:
        m.get("http://example.com/robots.txt", status=200, body=b"\x80\x81")
        async with aiohttp.ClientSession() as session:
            with pytest.raises(RobotsError):
                await Robot.download_and_parse("http://example.com/robots.txt", session)
                
def test_robots_txt_pattern_compile():
    # Test basic pattern compilation
    assert str(robots_txt_pattern_compile("/test")) == "re.compile('/test.*')"
    assert str(robots_txt_pattern_compile("/test*")) == "re.compile('/test.*')"
    assert str(robots_txt_pattern_compile("/test$")) == "re.compile('/test$')"
    
    # Test dot escaping
    assert str(robots_txt_pattern_compile("/test.html")) == "re.compile('/test\\\\.html.*')"
    
    # Test without leading slash
    assert str(robots_txt_pattern_compile("test")) == "re.compile('/test.*')"

def test_robots_txt_path_match_exact():
    assert robots_txt_path_match("/test", "/test") is True
    assert robots_txt_path_match("/test", "/test2") is True
    assert robots_txt_path_match("/test$", "/test") is True
    assert robots_txt_path_match("/test$", "/test2") is False

def test_robots_txt_path_match_wildcards():
    assert robots_txt_path_match("/test*", "/test123") is True
    assert robots_txt_path_match("/test*page", "/test_mypage") is True
    assert robots_txt_path_match("/*/page", "/test/page") is True
    assert robots_txt_path_match("/*.html", "/file.html") is True
    assert robots_txt_path_match("/*.html$", "/file.html") is True
    assert robots_txt_path_match("/*.html$", "/file.htmlx") is False

def test_robots_txt_path_match_leading_slash():
    assert robots_txt_path_match("test", "test") is True
    
def test_robots_txt_pattern_compile_advanced():
    # Test advanced pattern compilation
    assert str(robots_txt_pattern_compile("/path/*/test")) == "re.compile('/path/.*/test.*')"
    assert str(robots_txt_pattern_compile("/file.txt$")) == "re.compile('/file\\\\.txt$')"
    assert str(robots_txt_pattern_compile("/*.php$")) == "re.compile('/.*\\\\.php$')"
    assert str(robots_txt_pattern_compile("/test/*.jpg")) == "re.compile('/test/.*\\\\.jpg.*')"

def test_robots_txt_path_match_advanced():
    # True assertions
    assert robots_txt_path_match("/path/*", "/path/to/file") is True
    assert robots_txt_path_match("/*.pdf", "/doc.pdf") is True 
    assert robots_txt_path_match("/assets/*", "/assets/images/logo.png") is True
    assert robots_txt_path_match("/*.min.js", "/jquery.min.js") is True
    assert robots_txt_path_match("/*/uploads/*", "/site/uploads/file.txt") is True
    
    # False assertions
    assert robots_txt_path_match("/private/*$", "/private/files/test") is True
    assert robots_txt_path_match("/*.jpg$", "/image.jpg.png") is False
    assert robots_txt_path_match("/admin/", "/administrator") is False
    assert robots_txt_path_match("/test/*.php", "/test2/file.php") is False
    assert robots_txt_path_match("/exact/path$", "/exact/path/subdir") is False

def test_robots_txt_path_match_edge_cases():
    # Empty and special paths
    assert robots_txt_path_match("/", "/") is True
    assert robots_txt_path_match("/*", "/any/path/here") is True
    assert robots_txt_path_match("/$", "/") is True
    assert robots_txt_path_match("/$", "/path") is False
    
    # Paths with dots and special characters
    assert robots_txt_path_match("/page.*/", "/page.php/") is True
    assert robots_txt_path_match("/test.*$", "/test") is False
    assert robots_txt_path_match("/*.download", "/file.download.txt") is True
    assert robots_txt_path_match("/download/*.html$", "/download/page.html") is True