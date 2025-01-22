import asyncio
from typing import Optional

# improve rate limiter to compensate for irregular delay
class CrawlRateLimiter:
    def __init__(self, crawl_delay_seconds: float) -> None:
        self.crawl_delay_seconds: float = crawl_delay_seconds
        self.last_request_time: Optional[float] = None
        self._lock: asyncio.Lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request"""
        async with self._lock:
            current_time: float = asyncio.get_event_loop().time()
            
            if self.last_request_time is None:
                self.last_request_time = current_time
                return
            
            time_since_last_request: float = current_time - self.last_request_time
            if time_since_last_request < self.crawl_delay_seconds:
                wait_time: float = self.crawl_delay_seconds - time_since_last_request
                await asyncio.sleep(wait_time)
            
            self.last_request_time = asyncio.get_event_loop().time()

    def reset(self, craw_delay_seconds: float) -> None:
        """Reset the rate limiter state"""
        self.crawl_delay_seconds = craw_delay_seconds
        self.last_request_time = None
        
