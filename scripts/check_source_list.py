#!/usr/bin/env python3
"""Check that the site's Components section and the "OGCR Architecture" Glossary Item list
the same repositories.

The Glossary Item on OBP-API is where the repository list is kept, so AI agents can read it
through the OBP-MCP server. The site describes each component by hand, with a link to its
repository. This script reads the item's "### Source code" section, where each repository
is one line:

    - [Name](https://link): what it does

and compares those links with the repository links (class "repo") in docs/index.html. It
changes nothing. It exits with 1 and names the differences when a repository is in one list
but not the other, or when it cannot read the Glossary Item.

Usage:
  python3 scripts/check_source_list.py                        # read the item from OBP-API
  python3 scripts/check_source_list.py --markdown FILE        # read a local copy of the item
  OBP_HOST=http://localhost:8080 python3 scripts/check_source_list.py

Only the Python standard library is used, so there is nothing to install.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

DEFAULT_HOST = "https://dcr.ogcr.tesobe.com"
GLOSSARY_TITLE = "OGCR Architecture"
INDEX = Path(__file__).resolve().parent.parent / "docs" / "index.html"

# One repository line in the Glossary Item: "- [Name](https://link)", then an optional ": what it does".
REPO_LINE = re.compile(r"^\s*[-*]\s+\[(?P<name>[^\]]+)\]\((?P<url>https?://[^)\s]+)\)")
# A repository link on the site: <a class="repo" href="...">.
REPO_LINK = re.compile(r'<a class="repo" href="(?P<url>[^"]+)"')


def warn(message):
    """Print a message, as a warning annotation when running on GitHub Actions."""
    prefix = "::warning::" if os.getenv("GITHUB_ACTIONS") else ""
    print(f"{prefix}{message}", file=sys.stderr)


def stop(message):
    warn(f"Repository check not run: {message}")
    sys.exit(1)


def fetch_markdown(host):
    """The Markdown of the Glossary Item, from OBP-API's public glossary."""
    url = f"{host.rstrip('/')}/obp/v5.1.0/api/glossary"
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            body = json.load(response)
    except Exception as error:
        stop(f"could not read {url}: {error}")
    for item in body.get("glossary_items", []):
        if item.get("title") == GLOSSARY_TITLE:
            return item.get("description", {}).get("markdown", "")
    stop(f'{url} has no Glossary Item called "{GLOSSARY_TITLE}"')


def glossary_repositories(markdown):
    """{link: name} for each repository line under the "Source code" heading."""
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        if re.match(r"^#+\s+Source code\s*$", line, re.IGNORECASE):
            found = {}
            for following in lines[index + 1:]:
                if re.match(r"^#+\s", following):
                    break
                match = REPO_LINE.match(following)
                if match:
                    found[normalise(match["url"])] = match["name"].strip()
            if not found:
                stop("the Source code section of the Glossary Item lists no repositories")
            return found
    stop('the Glossary Item has no "Source code" heading')


def normalise(url):
    """Compare links without a trailing slash or a .git ending."""
    return re.sub(r"(\.git)?/*$", "", url.strip())


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

    in_glossary = glossary_repositories(markdown)
    on_site = {normalise(match["url"]) for match in REPO_LINK.finditer(INDEX.read_text(encoding="utf-8"))}

    not_on_site = [f"{name} ({url})" for url, name in in_glossary.items() if url not in on_site]
    not_in_glossary = sorted(url for url in on_site if url not in in_glossary)
    if not_on_site:
        warn("In the Glossary Item but with no component on the site: " + ", ".join(not_on_site))
    if not_in_glossary:
        warn("On the site but not in the Glossary Item: " + ", ".join(not_in_glossary))
    if not_on_site or not_in_glossary:
        sys.exit(1)
    print(f"The site's components link to all {len(in_glossary)} repositories in {source}, and to no others.")


if __name__ == "__main__":
    main()
