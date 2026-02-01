# Shinigami 🍎

**Shinigami** is a CLI-based Content Discovery Engine that aggregates anime metadata from multiple websites. It uses **Playwright** for high-performance async scraping and **Typer** + **Rich** for a beautiful terminal interface.

##  Features

- **Multi-Provider Support**: Easily modifiable JSON recipes to add new sources.
- **Async Concurrency**: Scrape 5+ sites simultaneously.
- **Human Emulation**: Rotates User-Agents and adds random delays to avoid detection.
- **Rich UI**: Tables, status spinners, and colored output.

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

##  Usage

### Search for Anime
Search across all configured providers:
```bash
python -m shinigami.cli.main search "One Piece"
```

### List Providers
See which JSON recipes are currently loaded:
```bash
python -m shinigami.cli.main list-providers
```

### Debug a Provider
Test a specific provider and see the raw output:
```bash
python -m shinigami.cli.main debug "LiveChart" --query "Naruto"
```

##  Adding Providers

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
