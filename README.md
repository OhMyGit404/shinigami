# Shinigami 🍎

**Shinigami** is a CLI-based Content Discovery Engine that aggregates anime metadata from multiple websites. It uses **Playwright** for high-performance async scraping and **Typer** + **Rich** for a beautiful terminal interface.

##  Features

- **Multi-Provider Support**: Easily modifiable JSON recipes to add new sources.
- **Async Concurrency**: Scrape 5+ sites simultaneously.
- **Human Emulation**: Rotates User-Agents and adds random delays to avoid detection.
- **Rich UI**: Tables, status spinners, and colored output.

![Shinigami Demo](assets/demo.svg)

##  How It Works

Shinigami acts as a metasearch engine for anime:
1. **Aggregates** query results from multiple providers (defined in JSON).
2. **Emulates** a real user browser using `playwright` to bypass bot protections.
3. **Parses** the HTML using CSS selectors to extract titles, episodes, and links.
4. **Displays** the data in a sorted, interactive terminal table.

##  Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/shinigami.git
   cd shinigami
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Browsers**
   ```bash
   playwright install
   ```

## 🛠 Usage

### 1. List Available Providers
See which websites Shinigami is currently configured to scrape.
![List Demo](assets/list_demo.svg)
```bash
python -m shinigami.cli.main list-providers
```

### 2. Search for Anime
Search across all providers simultaneously. The results are sorted and displayed in a unified table.
![Search Demo](assets/search_demo.svg)
```bash
python -m shinigami.cli.main search "One Piece"
```

### 3. Debug a Provider
If a provider isn't working, debug it individually to see the raw data it returns.
![Debug Demo](assets/debug_demo.svg)
```bash
python -m shinigami.cli.main debug "LiveChart" --query "Naruto"
```

### 4. Create Your Own Provider (Wizard)
Use the interactive wizard to generate a new recipe without writing JSON manually.
```bash
python -m shinigami.cli.main wizard
```

## 🧩 Included Providers

Shinigami comes with a "Starter Pack" of providers (thanks to YarrList):
- **LiveChart** (Metadata)
- **MyAnimeList** (Metadata)
- **HiAnime** (Streaming)
- **GogoAnime** (Streaming)

## 🧩 Adding Providers Manually

Create a new JSON file in `shinigami/providers/`. Example:

```json
{
  "name": "MyAnimeSite",
  "search_url": "https://site.com/search?q={query}",
  "selectors": {
    "container": ".item",
    "title": ".title",
    "episode": ".ep-num",
    "link": "a"
  }
}
```

##  License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** - see the [LICENSE](LICENSE) file for details.

### Dual Licensing
**Shinigami** is available under a dual license:
- **AGPLv3** for open-source projects and personal use.
- **propietary/Commercial License** for businesses using it in closed-source applications.

Contact us for commercial licensing inquiries.
