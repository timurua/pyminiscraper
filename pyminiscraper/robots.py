import collections
import urllib.parse
import urllib.request
from typing import List, Optional, Union
from enum import Enum
import aiohttp
import logging
import asyncio
from .url import normalize_url
import re

logger = logging.getLogger("robots")

RequestRate = collections.namedtuple("RequestRate", "requests seconds")

class RobotsError(Exception):
    pass

class ParseState(Enum):
    NONE = 0
    USER_AGENT = 1
    RULES = 2

class AccessRule(Enum):
    ALLOW_ALL = 1
    DISALLOW_ALL = 2
    DEFAULT = 3

class Robot:
    def __init__(self)-> None:
        self.entries: List[Entry] = []
        self.sitemap_urls: set[str] = set()
        self.default_entry: Optional[Entry] = None
        self.access_rule: AccessRule = AccessRule.ALLOW_ALL

    @classmethod
    async def download_and_parse(cls, normalized_url: str, client_session: aiohttp.ClientSession, timeout_seconds: int = 30) -> "Robot":
        try:
            async with client_session.get(normalized_url, timeout=aiohttp.ClientTimeout(total=timeout_seconds)) as http_response:
                robots = cls()
                if http_response.status in (401, 403):
                    robots.access_rule = AccessRule.DISALLOW_ALL
                elif http_response.status >= 400 and http_response.status < 500:
                    robots.access_rule = AccessRule.ALLOW_ALL
                else:
                    content = await http_response.text()
                    robots.parse(content)
                return robots
        except Exception as e:
            logger.error(f"Error fetching {normalized_url}: {e}")
            raise RobotsError(f"""Failed to fetch robots.txt from {normalized_url}""") from e                    
        
    def _add_entry(self, entry: 'Entry') -> None:
        if "*" in entry.useragents:
            if self.default_entry is None:
                self.default_entry = entry
        else:
            self.entries.append(entry)

    def parse(self, content: str) -> None:
        lines = content.splitlines()
        state = ParseState.NONE
        entry = Entry()

        for line_text in lines:
            i = line_text.find('#')
            if i >= 0:
                line_text = line_text[:i]
            line_text = line_text.strip()
            if not line_text:
                continue
            line = line_text.split(':', 1)
            if len(line) != 2:
                logger.warning(f"Skipping invalid line in robots.txt: {line}")
                continue

            line[0] = line[0].strip().lower()
            line[1] = urllib.parse.unquote(line[1].strip())
            if line[0] == "user-agent":
                if state == ParseState.RULES:
                    self._add_entry(entry)
                    entry = Entry()
                entry.useragents.append(line[1])
                state = ParseState.USER_AGENT
            elif line[0] == "disallow":
                if state != ParseState.NONE:
                    entry.rulelines.append(RuleLine(line[1], False))
                    state = ParseState.RULES
            elif line[0] == "allow":
                if state != ParseState.NONE:
                    entry.rulelines.append(RuleLine(line[1], True))
                    state = ParseState.RULES
            elif line[0] == "crawl-delay":
                if state != ParseState.NONE:
                    if line[1].strip().isdigit():
                        entry.delay = int(line[1])
                    state = ParseState.RULES
            elif line[0] == "request-rate":
                if state != ParseState.NONE:
                    numbers = line[1].split('/')
                    if (len(numbers) == 2 and numbers[0].strip().isdigit()
                            and numbers[1].strip().isdigit()):
                        entry.req_rate = RequestRate(int(numbers[0]), int(numbers[1]))
                    state = ParseState.RULES
            elif line[0] == "sitemap":
                self.sitemap_urls.add(line[1])
        if state == ParseState.RULES:
            self._add_entry(entry)

    def can_fetch(self, useragent: str, url: str) -> bool:
        if self.access_rule == AccessRule.DISALLOW_ALL:
            return False
        if self.access_rule == AccessRule.ALLOW_ALL:
            return True

        parsed_url = urllib.parse.urlparse(urllib.parse.unquote(url))
        url = urllib.parse.urlunparse(('', '', parsed_url.path,
                                       parsed_url.params, parsed_url.query, parsed_url.fragment))
        url = urllib.parse.quote(url)
        if not url:
            url = "/"
        for entry in self.entries:
            if entry.applies_to(useragent):
                return entry.allowance(url)
        if self.default_entry:
            return self.default_entry.allowance(url)
        return True

    def crawl_delay(self, useragent: str) -> Optional[int]:
        for entry in self.entries:
            if entry.applies_to(useragent):
                return entry.delay
        if self.default_entry:
            return self.default_entry.delay
        return None

    def request_rate(self, useragent: str) -> Optional[RequestRate]:
        for entry in self.entries:
            if entry.applies_to(useragent):
                return entry.req_rate
        if self.default_entry:
            return self.default_entry.req_rate
        return None

    def site_maps(self) -> Optional[set[str]]:
        return self.sitemap_urls

    def __str__(self) -> str:
        entries = self.entries
        if self.default_entry is not None:
            entries = entries + [self.default_entry]
        return '\n\n'.join(map(str, entries))


class RuleLine:
    def __init__(self, path: str, allowance: bool) -> None:
        if path == '' and not allowance:
            allowance = True
        path = urllib.parse.urlunparse(urllib.parse.urlparse(path))
        self.path: str = urllib.parse.quote(path)
        self.path_pattern = robots_txt_pattern_compile(self.path)
        self.allowance: bool = allowance

    def applies_to(self, filename: str) -> bool:
        if not filename.startswith('/'):
            filename = '/' + filename
        return bool(self.path_pattern.fullmatch(filename))
        
    def __str__(self) -> str:
        return ("Allow" if self.allowance else "Disallow") + ": " + self.path


class Entry:
    def __init__(self) -> None:
        self.useragents: List[str] = []
        self.rulelines: List[RuleLine] = []
        self.delay: Optional[int] = None
        self.req_rate: Optional[RequestRate] = None

    def __str__(self) -> str:
        ret = []
        for agent in self.useragents:
            ret.append(f"User-agent: {agent}")
        if self.delay is not None:
            ret.append(f"Crawl-delay: {self.delay}")
        if self.req_rate is not None:
            rate = self.req_rate
            ret.append(f"Request-rate: {rate.requests}/{rate.seconds}")
        ret.extend(map(str, self.rulelines))
        return '\n'.join(ret)

    def applies_to(self, useragent: str) -> bool:
        useragent = useragent.split("/")[0].lower()
        for agent in self.useragents:
            if agent == '*':
                return True
            agent = agent.lower()
            if agent in useragent:
                return True
        return False

    def allowance(self, filename: str) -> bool:        
        for line in self.rulelines:
            if line.applies_to(filename):
                return line.allowance
        return True
    
special_chars = set(['\\', '.', '+', '?', '|', '(', ')', '[', ']', '{', '}'])
    
def robots_txt_pattern_compile(path: str) -> re.Pattern:
    pattern = path
    if not pattern.startswith('/'):
        pattern = '/' + pattern       
        
    # pattern = re.escape(pattern).replace(r'\\*', '*').replace(r'\\$', '$')
    
    escaped_pattern = ''
    for pchar in pattern:
        if pchar in special_chars:
            escaped_pattern += "\\" + pchar
        else:
            escaped_pattern += pchar            
    pattern = escaped_pattern
    
    pattern = pattern.replace('*', '.*')
    if not pattern.endswith('$') and not pattern.endswith('.*'):
        pattern = pattern + '.*'   
        
    return re.compile(pattern)
    
def robots_txt_path_match(robots_path: str, url_path: str) -> bool:
    if not url_path.startswith('/'):
        url_path = '/' + url_path
        
    compiled_pattern = robots_txt_pattern_compile(robots_path)        
    return bool(compiled_pattern.fullmatch(url_path))
