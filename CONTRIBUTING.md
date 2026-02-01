# Contributing to Shinigami

We welcome contributions! Whether you want to add a new provider recipe, fix a bug, or improve the CLI, here's how you can help.

## Getting Started

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally.
3. **Create a new branch** for your feature or fix.

## Adding a New Provider

The easiest way to contribute is to add a new "Recipe".
1. Look at `shinigami/providers/example.json`.
2. Find an anime site you want to scrape.
3. Create a new `.json` file in `shinigami/providers/` with the correct CSS selectors.
4. Test it using `python -m shinigami.cli.main debug "YourProviderName"`.

## Development Guidelines

- Use **Python 3.10+**.
- Use **Type Hints** for all functions.
- Format code with **Black** or standard PEP8.
- Ensure your changes don't break existing functionality.

## Pull Requests

1. Push your branch to GitHub.
2. Open a Pull Request against the `main` branch.
3. Describe your changes and what you tested.

Thank you for contributing! 🍎
