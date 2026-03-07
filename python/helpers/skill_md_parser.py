"""Parse SKILL.md files: YAML frontmatter between --- markers + markdown body."""

from __future__ import annotations

from typing import Any

import yaml


def parse_skill_md(content: str) -> tuple[dict[str, Any], str]:
    """Parse a SKILL.md file into (frontmatter_dict, markdown_body).

    The file format is:
        ---
        key: value
        ...
        ---
        # Markdown body here

    Returns ``({}, "")`` for empty/None input and ``({}, content)`` when no
    frontmatter delimiters are found.
    """
    if not content:
        return {}, ""

    # Normalise line endings
    content = content.replace("\r\n", "\n")

    # Frontmatter must start at the very beginning of the file
    if not content.startswith("---"):
        return {}, content

    # Find the closing --- delimiter (skip the opening one)
    end_idx = content.find("\n---", 3)
    if end_idx == -1:
        # No closing delimiter – treat entire content as body
        return {}, content

    yaml_block = content[3:end_idx].strip()
    # Body starts after the closing --- and its newline
    body_start = end_idx + 4  # len("\n---")
    body = content[body_start:].lstrip("\n")

    frontmatter: dict[str, Any] = {}
    if yaml_block:
        try:
            parsed = yaml.safe_load(yaml_block)
            if isinstance(parsed, dict):
                frontmatter = parsed
        except yaml.YAMLError:
            # Malformed YAML – return empty frontmatter, full body
            return {}, content

    return frontmatter, body


def parse_skill_md_file(path: str) -> tuple[dict[str, Any], str]:
    """Convenience wrapper that reads a file then parses it."""
    with open(path, encoding="utf-8") as fh:
        return parse_skill_md(fh.read())
