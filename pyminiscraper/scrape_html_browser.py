import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import concurrent.futures
import concurrent
from .model import ScraperWebPage
from typing import Callable, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import logging
import time

logger = logging.getLogger("broswer_html_scraper")

executor = concurrent.futures.ThreadPoolExecutor(max_workers=64)

class BrowserHtmlScraperError(Exception):
    pass


class BrowserHtmlScraperFactory:
    def __init__(self)-> None:
        self.drivers: list[webdriver.Chrome] = []

    async def close(self) -> None:
        loop = asyncio.get_event_loop()
        for driver in self.drivers:
            loop.run_in_executor(executor, driver.quit)
        self.drivers = []

    def new_scraper(self) -> 'BrowserHtmlScraper':
        return BrowserHtmlScraper(self._getDriver, self._returnDriver)

    def _getDriver(self) -> webdriver.Chrome:
        if len(self.drivers) == 0:
            chrome_options = Options()

            # Memory-related flags
            chrome_options.add_argument('--memory-model=low')
            chrome_options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
            chrome_options.add_argument('--disable-application-cache')
            # chrome_options.add_argument('--single-process')  # Run Chrome in a single process
            chrome_options.add_argument('--process-per-site')  # Use one process per site
            chrome_options.add_argument('--renderer-process-limit=2')  # Limit renderer processes

            # Disable features to reduce memory
            chrome_options.add_argument('--disable-extensions')  # Disable extensions
            chrome_options.add_argument('--disable-gpu')  # Disable GPU hardware acceleration
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-javascript')  # Only if you don't need JS
            chrome_options.add_argument('--disable-bundled-ppapi-flash')  # Disable Flash

            # Process and thread limits
            chrome_options.add_argument('--js-flags="--max-old-space-size=512"')  # Limit JS heap size
            chrome_options.add_argument('--initial-memory-in-mb=50')  # Initial memory allocation
            chrome_options.add_argument('--max-memory-in-mb=512')  # Maximum memory allocation

            # Performance optimization
            chrome_options.add_argument('--no-sandbox')  # Careful: security implications
            chrome_options.add_argument('--headless')  # Run in headless mode
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')  # Disable image loading
            chrome_options.add_argument('--blink-settings=imagesEnabled=false')  # Disable images
            driver = webdriver.Chrome(options=chrome_options)
            self.drivers.append(driver)

        return self.drivers.pop()

    def _returnDriver(self, driver: webdriver.Chrome) -> None:
        self.drivers.append(driver)


class BrowserHtmlScraper:
    def __init__(self, driver_get: Callable[[], webdriver.Chrome], driver_return: Callable[[webdriver.Chrome], None]):
        self.driver_get = driver_get
        self.driver_return = driver_return

    async def scrape(self, normalized_url: str) -> ScraperWebPage:
        loop = asyncio.get_event_loop()
        try:
            driver = self.driver_get()
            
            def get_driver_data()-> Tuple[str, str, str]:
                driver.get(normalized_url)
                # WebDriverWait(driver, 10).until(
                #     expected_conditions.presence_of_element_located(("tag name", "body"))
                # )
                time.sleep(5)
                elements = driver.find_elements(By.XPATH, "//*")
                def is_displayed(element):
                    try:
                        return element.is_displayed()
                    except:
                        return False
                    
                elements[:] = filter(lambda element: is_displayed(element), elements)
                visible_text = " ".join([element.text for element in elements])
                html = driver.page_source
                title = driver.title
                return html, visible_text, title
            
            data = await loop.run_in_executor(executor, get_driver_data)
            html = data[0]
            visible_text = data[1]
            title = data[2]

        except Exception as e: 
            logger.info(f"Failed to fetch page: {normalized_url}")
            raise BrowserHtmlScraperError(f"""Failed to fetch page: {normalized_url}""") from e                    
            
        finally:
            if driver:
                self.driver_return(driver)        
        
        page = ScraperWebPage(
            status_code=200,
            headers=None,
            metadata_title=title,
            content=html.encode("utf-8"),
            visible_text=visible_text,
            content_type="text/html",
            content_charset="utf-8",
            headless_browser=True,
            url=normalized_url,
            normalized_url=normalized_url,
        )
        return page
