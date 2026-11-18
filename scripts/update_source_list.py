#!/usr/bin/env python3
"""Fill the site's Source code list from the "OGCR Architecture" Glossary Item on OBP-API.

The Glossary Item is the one place the repository list is kept: OBP-API serves it, and AI
agents read it through the OBP-MCP server. This script reads the item's "### Source code"
section, where each repository is one line:

    - [Name](https://link): what it does

and writes those repositories into docs/index.html, between the markers
<!-- source-list:start --> and <!-- source-list:end -->.

The Pages workflow runs it before each deploy. If OBP-API cannot be reached, or the section
is missing or empty, it changes nothing and exits with 1, so the site keeps the list that is
committed in the repository.

Usage:
  python3 scripts/update_source_list.py                       # read from OBP-API
  python3 scripts/update_source_list.py --markdown FILE       # read a local copy of the item
  OBP_HOST=http://localhost:8080 python3 scripts/update_source_list.py

Only the Python standard library is used, so there is nothing to install.
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

DEFAULT_HOST = "https://dcr.ogcr.tesobe.com"
GLOSSARY_TITLE = "OGCR Architecture"
INDEX = Path(__file__).resolve().parent.parent / "docs" / "index.html"
START = "<!-- source-list:start -->"
END = "<!-- source-list:end -->"

# One repository line: "- [Name](https://link): what it does".
REPO_LINE = re.compile(r"^\s*[-*]\s+\[(?P<name>[^\]]+)\]\((?P<url>https?://[^)\s]+)\)\s*(?::\s*(?P<about>.*\S))?\s*$")


def fail(message):
    """Say what went wrong, as a warning on GitHub Actions, and stop without changing anything."""
    prefix = "::warning::" if os.getenv("GITHUB_ACTIONS") else ""
    print(f"{prefix}Source code list not updated: {message}", file=sys.stderr)
    sys.exit(1)


def fetch_markdown(host):
    """The Markdown of the Glossary Item, from OBP-API's public glossary."""
    url = f"{host.rstrip('/')}/obp/v5.1.0/api/glossary"
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            body = json.load(response)
    except Exception as error:
        fail(f"could not read {url}: {error}")
    for item in body.get("glossary_items", []):
        if item.get("title") == GLOSSARY_TITLE:
            return item.get("description", {}).get("markdown", "")
    fail(f'{url} has no Glossary Item called "{GLOSSARY_TITLE}"')


def source_section(markdown):
    """The lines under the "Source code" heading, up to the next heading."""
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        if re.match(r"^#+\s+Source code\s*$", line, re.IGNORECASE):
            section = []
            for following in lines[index + 1:]:
                if re.match(r"^#+\s", following):
                    break
                section.append(following)
            return section
    fail('the Glossary Item has no "Source code" heading')


def repositories(markdown):
    """(name, url, about) for each repository line in the Source code section."""
    found = []
    for line in source_section(markdown):
        match = REPO_LINE.match(line)
        if match:
            found.append((match["name"].strip(), match["url"], (match["about"] or "").strip()))
    if not found:
        fail("the Source code section lists no repositories")
    # Every card on the site has a description, so a line without one is an item in the
    # old format, or a mistake. Keep the committed list rather than publish a worse one.
    undescribed = [name for name, _, about in found if not about]
    if undescribed:
        fail("these repositories have no description (write '- [Name](link): what it does'): " + ", ".join(undescribed))
    return found


def render(repos, indent):
    """The <li> items, escaped, one per line, at the markers' indentation."""
    items = []
    for name, url, about in repos:
        text = f"{html.escape(name, quote=False)}<span>{html.escape(about, quote=False)}</span>"
        items.append(f'{indent}<li><a href="{html.escape(url, quote=True)}">{text}</a></li>')
    return "\n".join(items)


def update_index(repos):
    """Replace what is between the markers in docs/index.html. True if the page changed."""
    page = INDEX.read_text(encoding="utf-8")
    pattern = re.compile(rf"(?P<indent>[ \t]*){re.escape(START)}\n.*?\n[ \t]*{re.escape(END)}", re.DOTALL)
    match = pattern.search(page)
    if not match:
        fail(f"{INDEX} has no {START} ... {END} markers")
    indent = match["indent"]
    block = f"{indent}{START}\n{render(repos, indent)}\n{indent}{END}"
    updated = page[:match.start()] + block + page[match.end():]
    if updated != page:
        INDEX.write_text(updated, encoding="utf-8")
    return updated != page


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--markdown", help="read the Glossary Item from this Markdown file instead of OBP-API")
    arguments = parser.parse_args()

    if arguments.markdown:
        markdown = Path(arguments.markdown).read_text(encoding="utf-8")
        source = arguments.markdown
    else:
        host = os.getenv("OBP_HOST", DEFAULT_HOST)
        markdown = fetch_markdown(host)
        source = f'the "{GLOSSARY_TITLE}" Glossary Item on {host}'

    repos = repositories(markdown)
    changed = update_index(repos)
    print(f"{len(repos)} repositories from {source}; docs/index.html {'updated' if changed else 'already up to date'}.")


if __name__ == "__main__":
    main()
