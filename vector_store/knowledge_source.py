# TODO (@abhikdps): Remove this file once the Igloo API keys
# are aquired and rename the knowledge_source_igloo.py file to knowledge_source.py
import pathlib
import time
import logging
from typing import Any
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from constants import SOURCE_RESPOSITORY_PATH

logger = logging.getLogger(__name__)


class SourceScraper:
    def __init__(self, base_url: str = "https://source.redhat.com/"):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.base_url = base_url

        self.driver.get(self.base_url)
        print("\n Please log in manually and press ENTER here once done...")
        input()
        print(" Login confirmed. Proceeding with scraping.")

    def fetch_all_pages(self, url_fragment: str, recursive: bool = False):
        url = self.base_url.rstrip("/") + url_fragment
        self.driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        pages = [soup]

        if recursive:
            children_links = soup.select("a[href^='/']")
            visited = set()

            for link in children_links:
                href = link.get("href")
                full_url = self.base_url.rstrip("/") + href
                if href and href.startswith("/") and full_url not in visited:
                    visited.add(full_url)
                    try:
                        self.driver.get(full_url)
                        time.sleep(2)
                        sub_soup = BeautifulSoup(self.driver.page_source, "html.parser")
                        pages.append(sub_soup)
                    except Exception as e:
                        logger.warning(f"Failed to visit {full_url}: {e}")

        return pages

    def extract_attachments(self, soup: BeautifulSoup):
        attachments = []
        links = soup.select("a")
        for link in links:
            href = link.get("href")
            if href and any(ext in href for ext in [".pdf", ".docx", ".xlsx"]):
                attachments.append(href)
        return attachments

    def save_page(self, soup: BeautifulSoup, path: pathlib.Path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(soup))

    def download_attachments(self, attachments: list[str], base_path: pathlib.Path):
        for link in attachments:
            file_name = link.split("/")[-1]
            full_path = base_path / file_name
            try:
                self.driver.get(
                    link
                    if link.startswith("http")
                    else self.base_url.rstrip("/") + link
                )
                with open(full_path, "wb") as f:
                    f.write(self.driver.page_source.encode("utf-8"))
            except Exception as e:
                logger.warning(f"Failed to download attachment {link}: {e}")

    def scrape(
        self,
        url_fragment: str,
        recursive: bool,
        attachments: bool,
        metadata: dict[str, Any],
    ):
        meta_lookup = {}
        pages = self.fetch_all_pages(url_fragment, recursive)

        for i, soup in enumerate(pages):
            title = soup.title.string if soup.title else f"page_{i}"
            safe_title = title.replace("/", "_").replace(" ", "_")[:50]
            page_path = (
                SOURCE_RESPOSITORY_PATH / url_fragment.strip("/") / f"{safe_title}.html"
            )
            page_path.parent.mkdir(parents=True, exist_ok=True)

            self.save_page(soup, page_path)
            file_metadata = metadata.copy()
            file_metadata["url"] = self.base_url.rstrip("/") + url_fragment

            if attachments:
                attachment_links = self.extract_attachments(soup)
                self.download_attachments(attachment_links, page_path.parent)

            meta_lookup[page_path] = file_metadata

        return meta_lookup


def fetchall(
    url_fragment: str,
    recursive: bool = False,
    attachments: bool = True,
    metadata: dict = {},
    **kwargs,
):
    scraper = SourceScraper()
    return scraper.scrape(url_fragment, recursive, attachments, metadata)
