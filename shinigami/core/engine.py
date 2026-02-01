import asyncio
import json
import random
import glob
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from playwright.async_api import async_playwright, Browser, Page

# --- Models ---

class SearchResult(BaseModel):
    title: str
    source: str
    episodes: Optional[str] = None
    url: str
    rank: int = 0

class ProviderRecipe(BaseModel):
    name: str
    search_url: str
    selectors: Dict[str, str]
    infinite_scroll: bool = False

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
        page = await browser.new_page(
            user_agent=random.choice(self.user_agents)
        )
        
        try:
            url = provider.search_url.replace("{query}", query)
            await page.goto(url, wait_until="domcontentloaded")
            
            # Random delay for human emulation
            await page.wait_for_timeout(random.randint(500, 1500))

            if provider.infinite_scroll:
                # Basic scroll implementation
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000)

            # Wait for container if specified, else generic wait
            container_sel = provider.selectors.get("container")
            if container_sel:
                try:
                    await page.wait_for_selector(container_sel, timeout=5000)
                except:
                    # If selector not found, might mean no results or different structure
                    pass
            
            # Extract data
            # We'll use evaluate to extract all at once for better performance/stability than loop elements in py
            # But for simplicity/readability with playwright elements:
            
            elements = await page.query_selector_all(provider.selectors.get("container", "body"))
            
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
                             # Simple join, rigorous would use urljoin
                             base = url.split("?")[0] # Very rough base extraction, ideally valid from recette
                             # Let's just assume we need to join with domain
                             from urllib.parse import urljoin
                             link = urljoin(url, href)
                        else:
                            link = href
                    else:
                        link = ""

                    episodes = await el.eval_on_selector(ep_sel, "e => e.innerText") if ep_sel else None
                    
                    results.append(SearchResult(
                        title=title.strip(),
                        source=provider.name,
                        episodes=episodes.strip() if episodes else None,
                        url=link,
                        rank=index + 1
                    ))
                except Exception as e:
                    # Skip incomplete items
                    continue
                    
        except Exception as e:
            # In a real app, use logging
            # print(f"Error scraping {provider.name}: {e}")
            pass
        finally:
            await page.close()
            
        return results

    async def search(self, query: str) -> List[SearchResult]:
        """Concurrently searches all loaded providers."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            tasks = [self._scrape_provider(browser, provider, query) for provider in self.providers]
            all_results = await asyncio.gather(*tasks)
            await browser.close()
            
            # Flatten list
            flat_results = [item for sublist in all_results for item in sublist]
            # Simple relevance sort (placeholder)
            return flat_results
