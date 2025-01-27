from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, urljoin
import re
from typing import List, Tuple
from re import Match
from .hash import generate_url_safe_id

def normalize_preserving_semantics(url: str) -> str:
    """
    Apply normalizations that preserve semantics:
    - Convert percent-encoded triplets to uppercase.
    - Convert scheme and host to lowercase.
    - Decode percent-encoded unreserved characters.
    - Remove dot-segments.
    - Convert empty path to "/".
    - Remove the default port.
    """
    # Parse the URL into components
    parsed_url = urlparse(url)
    scheme: str = parsed_url.scheme.lower()
    netloc: str = parsed_url.netloc.lower()

    # Remove default port (port 80 for http, 443 for https)
    hostname, sep, port = netloc.partition(':')
    if (scheme == 'http' and port == '80') or (scheme == 'https' and port == '443'):
        netloc = hostname

    # Unreserved characters as per RFC 3986
    unreserved_chars: str = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~'

    # Process the path
    path: str = parsed_url.path

    # Convert percent-encoded triplets to uppercase
    path = re.sub(r'%[0-9a-fA-F]{2}', lambda m: m.group(0).upper(), path)

    # Decode percent-encoded triplets of unreserved characters
    def decode_unreserved(match: Match) -> str:
        pct_encoded: str = match.group(0)
        char: str = chr(int(pct_encoded[1:], 16))
        return char if char in unreserved_chars else pct_encoded

    path = re.sub(r'%[0-9A-F]{2}', decode_unreserved, path)

    # Remove dot-segments
    path = remove_dot_segments(path)

    # Convert empty path to "/"
    if not path and netloc:
        path = '/'

    # Reconstruct the URL
    normalized_url: str = urlunparse((
        scheme,
        netloc,
        path,
        parsed_url.params,
        parsed_url.query,
        parsed_url.fragment
    ))
    return normalized_url

def remove_dot_segments(path: str) -> str:
    """Remove dot-segments from path as per RFC 3986 Section 5.2.4"""
    segments = path.split('/')
    output: list[str] = []
    for segment in segments:
        if segment == '..':
            if output:
                output.pop()
        elif segment != '.' and segment != '':
            output.append(segment)
    return '/' + '/'.join(output)

def normalize_usually_preserving_semantics(url: str) -> str:
    """
    Apply normalizations that usually preserve semantics:
    - Add a trailing "/" to a non-empty path if not present.
    """
    # First, apply normalizations that preserve semantics
    url = normalize_preserving_semantics(url)
    parsed_url = urlparse(url)
    path = parsed_url.path

    # Add trailing "/" to a non-empty path if not present
    # if path and not path.endswith('/'):
    #     path += '/'

    # Reconstruct the URL
    normalized_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        path,
        parsed_url.params,
        parsed_url.query,
        parsed_url.fragment
    ))
    return normalized_url

def normalize_changing_semantics(url: str) -> str:
    """
    Apply normalizations that change semantics:
    - Remove directory index.
    - Remove the fragment.
    - Remove duplicate slashes.
    - Remove "www" as the first domain label.
    - Sort the query parameters.
    - Remove the "?" when the query is empty.
    """
    # First, apply normalizations that usually preserve semantics
    url = normalize_usually_preserving_semantics(url)
    parsed_url = urlparse(url)
    scheme, netloc, path, params, query, fragment = parsed_url

    # Remove directory index
    directory_indexes: List[str] = ['index.html', 'index.htm', 'default.asp']
    for index in directory_indexes:
        if path.endswith(index):
            path = path[:-(len(index))]
            if not path.endswith('/'):
                path += '/'
            break

    # Remove the fragment
    fragment = ''

    # Remove duplicate slashes in path
    path = re.sub(r'//+', '/', path)

    # Remove "www" as the first domain label
    if netloc.startswith('www.'):
        netloc = netloc[4:]

    # Sort the query parameters
    if query:
        query_params: List[Tuple[str, str]] = parse_qsl(query, keep_blank_values=True)
        query_params.sort()
        query = urlencode(query_params, doseq=True)

    # Remove the "?" when the query is empty
    if not query:
        query = ''

    # Reconstruct the URL
    normalized_url: str = urlunparse((
        scheme,
        netloc,
        path,
        params,
        query,
        fragment
    ))
    return normalized_url

def normalize_url(url:str)->str:   
    return normalize_changing_semantics(url)

def normalized_url_hash(url:str)->str:
    normalized_url = normalize_url(url)
    return generate_url_safe_id(normalized_url)

def make_absolute_url(base_url, relative_url) -> str:
    # Check if relative_url is already absolute
    domain = urlparse(relative_url).netloc
    if domain:
        return relative_url
        
    return urljoin(base_url, relative_url)
