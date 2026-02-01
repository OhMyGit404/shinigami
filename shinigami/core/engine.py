import asyncio
import json
import random
import glob
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright, Browser, Page, Playwright

# --- Models ---

class SearchResult(BaseModel):
    title: str
    source: str
    url: str
    rank: int = 0
    # Flexible fields
    type: str = "streaming" # streaming, metadata, download
    meta: Dict[str, Any] = Field(default_factory=dict) # score, status, image_url
    payload: Optional[str] = None # magnet link, embed url, etc
    
    # Backwards compatibility helper (optional, can be removed if strictly migrating)
    @property
    def episodes(self) -> Optional[str]:
        return str(self.meta.get("episodes")) if self.meta.get("episodes") else None

class ProviderRecipe(BaseModel):
    name: str
    search_url: str
    selectors: Dict[str, str]
    infinite_scroll: bool = False

# --- Core Mechanics ---

class BrowserManager:
    """
    Singleton-like manager for the Playwright browser instance.
    Ensures we don't spawn multiple browsers and handles cleanup.
    """
    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._lock = asyncio.Lock()

    async def get_browser(self) -> Browser:
        async with self._lock:
            if not self._browser:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(headless=True)
            return self._browser

    async def close(self):
        async with self._lock:
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

    async def __aenter__(self):
        await self.get_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

# --- Engine ---

class ShinigamiEngine:
    def __init__(self, providers_dir: str = "shinigami/providers"):
        self.providers_dir = providers_dir
        self.providers: List[ProviderRecipe] = []
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]

    def load_providers(self):
        """Loads all JSON provider recipes from the providers directory."""
        self.providers = []
        pattern = os.path.join(self.providers_dir, "*.json")
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    provider = ProviderRecipe(**data)
                    self.providers.append(provider)
            except Exception as e:
                print(f"Failed to load provider {file_path}: {e}")
        return self.providers

    async def _scrape_provider(self, browser: Browser, provider: ProviderRecipe, query: str) -> List[SearchResult]:
        """Scrapes a single provider for the given query."""
        results = []
        
        # Guard clause for new users who might select invalid text selectors
        # We need to be careful with context creation
        try:
            page = await browser.new_page(
                user_agent=random.choice(self.user_agents)
            )
        except Exception as e:
            # Browser might be closed?
            return []

        try:
            url = provider.search_url.replace("{query}", query)
            await page.goto(url, wait_until="domcontentloaded", timeout=15000) # 15s timeout
            
            # Random delay for human emulation
            await page.wait_for_timeout(random.randint(500, 1500))

            if provider.infinite_scroll:
                # Basic scroll implementation
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000)

            # Wait for container if specified, else generic wait
            container_sel = provider.selectors.get("container")
            if not container_sel:
                return []

            try:
                await page.wait_for_selector(container_sel, timeout=5000)
            except:
                pass
            
            elements = await page.query_selector_all(container_sel)
            
            for index, el in enumerate(elements):
                try:
                    title_sel = provider.selectors.get("title")
                    link_sel = provider.selectors.get("link")
                    ep_sel = provider.selectors.get("episode")
                    
                    title = await el.eval_on_selector(title_sel, "e => e.innerText") if title_sel else "Unknown"
                    
                    # Handle relative links
                    if link_sel:
                        href = await el.eval_on_selector(link_sel, "e => e.getAttribute('href')")
                        if href and not href.startswith("http"):
                             from urllib.parse import urljoin
                             link = urljoin(url, href)
                        else:
                            link = href
                    else:
                        link = ""

                    episodes = await el.eval_on_selector(ep_sel, "e => e.innerText") if ep_sel else None
                    
                    # Determine type and metadata
                    meta = {}
                    if episodes:
                        meta["episodes"] = episodes.strip()
                    
                    # Basic heuristic for type
                    result_type = "streaming"
                    if "myanimelist" in provider.name.lower() or "livechart" in provider.name.lower():
                        result_type = "metadata"

                    results.append(SearchResult(
                        title=title.strip(),
                        source=provider.name,
                        url=link,
                        rank=index + 1,
                        type=result_type,
                        meta=meta
                    ))
                except Exception as e:
                    continue
                    
        except Exception as e:
            pass
        finally:
            await page.close()
            
        return results

    async def search(self, query: str) -> List[SearchResult]:
        """Concurrently searches all loaded providers using BrowserManager."""
        async with BrowserManager() as manager:
            browser = await manager.get_browser()
            tasks = [self._scrape_provider(browser, provider, query) for provider in self.providers]
            all_results = await asyncio.gather(*tasks)
            
            # Flatten list
            flat_results = [item for sublist in all_results for item in sublist]
            return flat_results

    async def validate_selector(self, search_url: str, query: str, selector: str) -> List[str]:
        """
        Validates a CSS selector by running it against a real browser.
        Returns a list of text content found (up to 5 items).
        """
        results = []
        if not selector:
            return []
            
        async with BrowserManager() as manager:
            browser = await manager.get_browser()
            page = await browser.new_page(
                user_agent=random.choice(self.user_agents)
            )
            try:
                url = search_url.replace("{query}", query)
                await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                except:
                    return ["Error: Timeout waiting for selector"]

                elements = await page.query_selector_all(selector)
                if not elements:
                    return []
                
                # Extract text from first 5
                for i, el in enumerate(elements[:5]):
                    text = await el.text_content()
                    if text:
                        results.append(text.strip())
            except Exception as e:
                return [f"Error: {str(e)}"]
            finally:
                await page.close()
                
        return results

