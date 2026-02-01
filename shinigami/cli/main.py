import asyncio
import json
import os
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from shinigami.core.engine import ShinigamiEngine

app = typer.Typer(help="Shinigami - Content Discovery Engine")
console = Console()
engine = ShinigamiEngine()

@app.command()
def search(query: str):
    """
    Search for anime across all configured providers.
    """
    engine.load_providers()
    
    with console.status(f"[bold green]Searching for '{query}' across {len(engine.providers)} providers..."):
        results = asyncio.run(engine.search(query))
    
    if not results:
        console.print("[red]No results found.[/red]")
        return
        
    table = Table(title=f"Search Results for '{query}'")
    table.add_column("Rank", justify="center", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Episode", justify="right", style="green")
    table.add_column("Source", style="yellow")
    table.add_column("Link", style="blue")

    # Simple sorting by rank if available, otherwise just order of arrival
    # In a real app, you'd have a relevance scorer
    sorted_results = sorted(results, key=lambda x: x.rank)

    for res in sorted_results:
        table.add_row(
            str(res.rank),
            res.title,
            res.episodes or "N/A",
            res.source,
            res.url
        )

    console.print(table)

@app.command()
def list_providers():
    """
    List all currently loaded provider recipes.
    """
    providers = engine.load_providers()
    table = Table(title="Loaded Providers")
    table.add_column("Name", style="cyan")
    table.add_column("URL Template", style="magenta")
    table.add_column("Infinite Scroll", style="green")

    for p in providers:
        table.add_row(p.name, p.search_url, str(p.infinite_scroll))

    console.print(table)

@app.command()
def debug(provider_name: str, query: str = "One Piece"):
    """
    Debug a specific provider by running it directly and showing raw output.
    """
    engine.load_providers()
    target_provider = next((p for p in engine.providers if p.name.lower() == provider_name.lower()), None)
    
    if not target_provider:
        console.print(f"[red]Provider '{provider_name}' not found.[/red]")
        return

    console.print(f"[bold]Debugging provider:[/bold] {target_provider.name}")
    console.print(f"[bold]Query:[/bold] {query}")
    
    async def run_debug():
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            results = await engine._scrape_provider(browser, target_provider, query)
            await browser.close()
            return results

    try:
        results = asyncio.run(run_debug())
        console.print(Panel(json.dumps([r.dict() for r in results], indent=2), title="Raw JSON Output"))
    except Exception as e:
        console.print(f"[red]Error during debug:[/red] {e}")

@app.command()
def wizard():
    """
    (Interactive) Create a new provider recipe.
    """
    console.print(Panel("[bold cyan]Shinigami Recipe Wizard[/bold cyan]\nLet's create a new provider!", border_style="cyan"))

    name = typer.prompt("Provider Name (e.g. MyAnimeSite)")
    search_url = typer.prompt("Search URL (use {query} as placeholder)", default="https://example.com/search?q={query}")
    
    console.print("\n[bold]CSS Selectors[/bold]")
    container = typer.prompt("Container Selector (holds each result)", default=".item")
    title = typer.prompt("Title Selector", default=".title")
    episode = typer.prompt("Episode Selector (optional)", default=".ep", show_default=True)
    link = typer.prompt("Link Selector (usually 'a')", default="a")
    
    infinite = typer.confirm("Does this site use infinite scrolling?", default=False)

    recipe = {
        "name": name,
        "search_url": search_url,
        "selectors": {
            "container": container,
            "title": title,
            "episode": episode,
            "link": link
        },
        "infinite_scroll": infinite
    }

    # Clean empty optionals
    if not episode:
        del recipe["selectors"]["episode"]

    filename = name.lower().replace(" ", "") + ".json"
    path = os.path.join("shinigami", "providers", filename)
    
    try:
        with open(path, "w") as f:
            json.dump(recipe, f, indent=2)
        console.print(f"\n[bold green]Success![/bold green] Recipe saved to [underline]{path}[/underline]")
        console.print(f"Test it with: [yellow]shinigami debug \"{name}\"[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error saving file:[/bold red] {e}")

if __name__ == "__main__":
    app()
