import pytest
from pyminiscraper.url import make_absolute_url
from urllib.parse import urlparse

def test_make_absolute_url_with_absolute_url():
    base_url = "http://example.com/path/"
    relative_url = "http://other.com/test.html"
    result = make_absolute_url(base_url, relative_url)
    assert result == "http://other.com/test.html"

def test_make_absolute_url_with_relative_url():
    base_url = "http://example.com/path/"
    relative_url = "test.html"
    result = make_absolute_url(base_url, relative_url)
    assert result == "http://example.com/path/test.html"

def test_make_absolute_url_with_parent_directory():
    base_url = "http://example.com/path/subpath/"
    relative_url = "../test.html"
    result = make_absolute_url(base_url, relative_url)
    assert result == "http://example.com/path/test.html"

def test_make_absolute_url_with_root_relative():
    base_url = "http://example.com/path/"
    relative_url = "/test.html"
    result = make_absolute_url(base_url, relative_url)
    assert result == "http://example.com/test.html"

def test_make_absolute_url_with_empty_relative():
    base_url = "http://example.com/path/"
    relative_url = ""
    result = make_absolute_url(base_url, relative_url)
    assert result == "http://example.com/path/"

def test_make_absolute_url_preserves_query_params():
    base_url = "http://example.com/path/"
    relative_url = "test.html?param=value"
    result = make_absolute_url(base_url, relative_url)
    assert result == "http://example.com/path/test.html?param=value"