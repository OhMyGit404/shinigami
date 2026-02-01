
import asyncio
import csv
import os
import aiofiles
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from shinigami.core.engine import ShinigamiEngine, BrowserManager

console = Console()
DATA_DIR = "data"
INPUT_FILE = "all_anime_titles.txt"
OUTPUT_FILE = os.path.join(DATA_DIR, "anime_dataset.csv")

async def hydrate():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # 1. Load Titles
    if not os.path.exists(INPUT_FILE):
        console.print(f"[red]Input file {INPUT_FILE} not found![/red]")
        return
    
    with open(INPUT_FILE, "r") as f:
        titles = [line.strip() for line in f if line.strip()]

    # 2. Check existing progress
    existing_data = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_data[row["Title"]] = row

    # 3. Setup Engine
    engine = ShinigamiEngine()
    engine.load_providers()
    # Prioritize MAL for metadata
    mal_provider = next((p for p in engine.providers if "myanimelist" in p.name.lower()), None)
    
    if not mal_provider:
        console.print("[red]MyAnimeList provider not found! Please ensure shinigami/providers/myanimelist.json exists.[/red]")
        return

    # 4. Processing Loop
    fieldnames = ["Title", "Source", "URL", "Episodes", "Score", "Type"]
    
    # We open in append mode if exists, else write header
    mode = "a" if os.path.exists(OUTPUT_FILE) else "w"
    
    async with BrowserManager() as manager:
        browser = await manager.get_browser()
        
        with open(OUTPUT_FILE, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if mode == "w":
                writer.writeheader()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.percentage:>3.0f}%"),
            ) as progress:
                task = progress.add_task("[cyan]Hydrating Dataset...", total=len(titles))
                
                for title in titles:
                    if title in existing_data:
                        progress.update(task, advance=1)
                        continue
                    
                    progress.update(task, description=f"Searching: {title}")
                    
                    try:
                        # Search only MAL for metadata precision
                        results = await engine._scrape_provider(browser, mal_provider, title)
                        
                        best_match = results[0] if results else None
                        
                        row = {
                            "Title": title,
                            "Source": best_match.source if best_match else "N/A",
                            "URL": best_match.url if best_match else "N/A",
                            "Episodes": best_match.meta.get("episodes", "N/A") if best_match else "N/A",
                            "Score": best_match.meta.get("score", "N/A") if best_match else "N/A",
                            "Type": best_match.type if best_match else "N/A"
                        }
                        
                        writer.writerow(row)
                        f.flush() # Ensure write to disk
                        
                    except Exception as e:
                        # Log error but continue
                        writer.writerow({"Title": title, "Source": "Error", "URL": str(e)})
                    
                    progress.update(task, advance=1)
                    # Gentle layout to avoid bans
                    await asyncio.sleep(1.0)

if __name__ == "__main__":
    asyncio.run(hydrate())
