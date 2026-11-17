#!/usr/bin/env python3
"""Maintain indexes for the bundled OKF knowledge (requires PyYAML).

This is a producer check for Datapack Smith, not a general OKF validator.
Agents consume the Markdown directly; the Minecraft harness needs no PyYAML.
"""

from __future__ import annotations

import argparse
import datetime
import re
from pathlib import Path
from typing import Any, Iterator

import yaml


DOCS = Path(__file__).resolve().parents[1] / "docs"
RESERVED = {"index.md", "log.md"}
DIRECTORY_DESCRIPTIONS = {
    "versions": "正式リリースの完全一致プロファイルとdata pack format。",
    "snapshots": "明示指定時に使う開発バージョンの完全一致プロファイル。",
    "reference": "データ種別ごとの配置、field、値型、参照関係。",
    "json-parameters": "JSON family別の値の意味とバージョン境界。",
}


class UniqueKeyLoader(yaml.SafeLoader):
    """Catch accidental metadata overwrites during producer maintenance."""


def unique_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode) -> dict:
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in mapping:
            raise ValueError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node)
    return mapping


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def read_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"{path}: missing YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ValueError(f"{path}: unclosed YAML frontmatter") from error
    try:
        metadata = yaml.load("\n".join(lines[1:end]), Loader=UniqueKeyLoader)
    except (yaml.YAMLError, ValueError, TypeError) as error:
        raise ValueError(f"{path}: invalid YAML: {error}") from error
    if not isinstance(metadata, dict):
        raise ValueError(f"{path}: frontmatter must be a mapping")
    return metadata, "\n".join(lines[end + 1:])


def markdown_prose(text: str) -> str:
    """Ignore fenced examples when checking actual links and citations."""
    lines = []
    fence = None
    for line in text.splitlines():
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if match:
            marker = match[1]
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            lines.append("")
        else:
            lines.append(line if fence is None else "")
    return "\n".join(lines)


def markdown_links(text: str) -> Iterator[tuple[str, str]]:
    text = markdown_prose(text)
    for match in re.finditer(r"(?<!!)\[([^\]\n]+)\]\(", text):
        depth = 1
        end = match.end()
        while end < len(text) and text[end] != "\n":
            char = text[end]
            if char == "\\":
                end += 2
                continue
            depth += (char == "(") - (char == ")")
            if depth == 0:
                yield match[1], text[match.end():end].strip().removeprefix("<").removesuffix(">")
                break
            end += 1


def timestamp(value: Any) -> datetime.datetime:
    if isinstance(value, str):
        value = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime.datetime) or value.utcoffset() is None:
        raise ValueError("timestamps require an ISO 8601 datetime with UTC offset")
    return value


def validate_optional_metadata(metadata: dict[str, Any]) -> None:
    if "status" in metadata and metadata["status"] not in {"draft", "stable", "deprecated"}:
        raise ValueError("invalid lifecycle status")
    if "stale_after" in metadata:
        timestamp(metadata["stale_after"])
    events = []
    if "generated" in metadata:
        events.append(metadata["generated"])
    if "verified" in metadata:
        verified = metadata["verified"]
        # OKF §5.2: a bare mapping is one event, not a different trust model.
        events.extend(verified if isinstance(verified, list) else [verified])
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("by"), str):
            raise ValueError("generated/verified events require an actor")
        if not re.fullmatch(r"(?:human:|process:)[^\s]+|[^\s/]+/[^\s]+", event["by"]):
            raise ValueError("invalid actor convention")
        if "at" in event:
            timestamp(event["at"])
        elif event is not metadata.get("generated"):
            raise ValueError("verified events require a datetime")


def read_concept(
    path: Path, *, producer: bool = True, root: Path | None = None
) -> dict[str, Any]:
    metadata, body = read_frontmatter(path)
    # Only type is universally required. Other requirements below belong to
    # this producer, not to the OKF §11 conformance definition.
    required = ("type", "title", "description") if producer else ("type",)
    for key in required:
        value = metadata.get(key)
        if not isinstance(value, str) or not value.strip() or (producer and "\n" in value):
            constraint = "non-empty single-line string" if producer else "non-empty string"
            raise ValueError(f"{path}: {key} must be a {constraint}")
    if not producer:
        return metadata
    tags = metadata.get("tags")
    if not isinstance(tags, list) or not tags or any(
        not isinstance(tag, str) or not tag.strip() for tag in tags
    ):
        raise ValueError(f"{path}: tags must be a non-empty string list")
    sources = metadata.get("sources", [])
    if not isinstance(sources, list) or any(
        not isinstance(source, dict)
        or not isinstance(source.get("resource"), str)
        or not source["resource"].strip()
        for source in sources
    ):
        raise ValueError(f"{path}: sources entries must have a resource string")
    source_ids = [source["id"] for source in sources if "id" in source]
    if any(not isinstance(key, str) or not key.strip() for key in source_ids):
        raise ValueError(f"{path}: source ids must be non-empty strings")
    if len(source_ids) != len(set(source_ids)):
        raise ValueError(f"{path}: duplicate source ids")
    prose = re.sub(r"(`+).*?\1", "", markdown_prose(body))
    definitions = re.findall(r"^\[\^([^\]]+)\]:", prose, re.MULTILINE)
    without_definitions = re.sub(r"^\[\^[^\]]+\]:.*$", "", prose, flags=re.MULTILINE)
    references = set(re.findall(r"\[\^([^\]]+)\]", without_definitions))
    if len(definitions) != len(set(definitions)):
        raise ValueError(f"{path}: duplicate footnote definitions")
    if references - set(definitions) or references - set(source_ids):
        raise ValueError(f"{path}: footnotes must resolve to definitions and sources[].id")
    if set(definitions) - references:
        raise ValueError(f"{path}: unused footnote definitions")
    # A valid id is insufficient if its footnote points at another source.
    # Compare the actual targets so reordering/swapping citations cannot pass.
    sources_by_id = {source["id"]: source for source in sources if "id" in source}
    bundle_root = root if root is not None else DOCS

    def resolved_resource(resource: str) -> str:
        if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", resource):
            return resource
        target, separator, fragment = resource.partition("#")
        base = bundle_root if target.startswith("/") else path.parent
        return str((base / target.lstrip("/")).resolve()) + separator + fragment

    for key, definition in re.findall(r"^\[\^([^\]]+)\]: (.+)$", body, re.MULTILINE):
        if key not in references:
            continue
        targets = list(markdown_links(definition))
        resource = sources_by_id[key]["resource"]
        if targets and resolved_resource(targets[0][1]) != resolved_resource(resource):
            raise ValueError(f"{path}: footnote {key} points at a different resource than sources[].id")
    resources = {source["resource"] for source in sources}
    missing = {url for _, url in markdown_links(body) if url.startswith(("https://", "http://"))} - resources
    if missing:
        raise ValueError(f"{path}: external references missing from sources: {', '.join(sorted(missing))}")
    try:
        validate_optional_metadata(metadata)
    except (ValueError, TypeError) as error:
        raise ValueError(f"{path}: {error}") from error
    return metadata


def validate_reserved(path: Path, root: Path, *, producer: bool = True) -> None:
    text = path.read_text(encoding="utf-8")
    if path.name == "index.md":
        if text.startswith("---\n"):
            metadata, _ = read_frontmatter(path)
            if path.parent != root or set(metadata) - {"okf_version"}:
                raise ValueError(f"{path}: only the bundle-root index may declare okf_version")
        if not re.search(r"^#{1,6} .+", text, re.MULTILINE):
            raise ValueError(f"{path}: index requires a section heading")
        return
    if text.startswith("---\n"):
        raise ValueError(f"{path}: log uses date-grouped Markdown without concept frontmatter")
    headings = re.findall(r"^## (.+)$", text, re.MULTILINE)
    try:
        if producer and not re.search(r"^# .+", text, re.MULTILINE):
            raise ValueError("log requires a title")
        if not headings or any(not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) for date in headings):
            raise ValueError("log requires ISO date headings")
        dates = [datetime.date.fromisoformat(date) for date in headings]
        if dates != sorted(dates, reverse=True) or (producer and len(dates) != len(set(dates))):
            raise ValueError("log dates must be newest first (and unique in this producer)")
        for group in re.split(r"^## .+$", text, flags=re.MULTILINE)[1:]:
            if not re.search(r"^[-*] .+", group, re.MULTILINE):
                raise ValueError("each log date requires a list of entries")
            if re.search(r"^[ \t]+[-*] ", group, re.MULTILINE):
                raise ValueError("log entries must be a flat list")
    except ValueError as error:
        raise ValueError(f"{path}: {error}") from error


def render_index(
    directory: Path, root: Path, concepts: dict[Path, dict[str, Any]]
) -> str:
    lines = []
    if directory == root:
        lines.extend(['---', 'okf_version: "0.2"', '---', ''])
    title = "Datapack Smith knowledge" if directory == root else directory.name
    lines.extend([f"# {title}", "", "<!-- tools/okf_index.py で生成。本文とmetadataの正本は各concept文書。 -->", ""])
    if (directory / "log.md").is_file():
        lines.extend(["## 更新履歴", "", "- [更新履歴](log.md) - この範囲のknowledge更新記録。", ""])
    children = sorted(
        child for child in directory.iterdir()
        if child.is_dir() and any(path.is_relative_to(child) for path in concepts)
    )
    if children:
        lines.extend(["## ディレクトリ", ""])
        for child in children:
            description = DIRECTORY_DESCRIPTIONS.get(child.name, f"{child.name}の文書。")
            lines.append(f"- [{child.name}]({child.name}/index.md) - {description}")
        lines.append("")
    entries = [(path, meta) for path, meta in concepts.items() if path.parent == directory]
    types = sorted({meta["type"] for _, meta in entries})
    for concept_type in types:
        lines.extend([f"## {concept_type}", ""])
        group = [(path, meta) for path, meta in entries if meta["type"] == concept_type]
        group.sort(key=lambda item: (str(item[1].get("release_date", "")), item[0].name))
        for path, meta in group:
            lines.append(f"- [{meta['title']}]({path.name}) - {meta['description']}")
        lines.append("")
    return "\n".join(lines)


def maintain_indexes(
    root: Path, *, write: bool = False, conformance_only: bool = False
) -> tuple[int, list[str]]:
    concepts = {}
    errors = []
    for path in sorted(root.rglob("*.md")):
        try:
            if path.name in RESERVED:
                validate_reserved(path, root, producer=not conformance_only)
            else:
                concepts[path] = read_concept(path, producer=not conformance_only, root=root)
        except ValueError as error:
            errors.append(str(error))
    if errors or conformance_only:
        return len(concepts), errors
    directories = {root}
    for path in concepts:
        directories.add(path.parent)
        directories.update(parent for parent in path.parents if parent.is_relative_to(root))
    for directory in sorted(directories):
        index = directory / "index.md"
        expected = render_index(directory, root, concepts)
        if write:
            index.write_text(expected, encoding="utf-8")
        elif not index.exists() or index.read_text(encoding="utf-8") != expected:
            errors.append(f"{index}: index missing or stale; run tools/okf_index.py --write")
    return len(concepts), errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="regenerate indexes; default: check only")
    mode.add_argument("--conformance-only", action="store_true", help="check OKF §11 without local producer requirements or index freshness")
    args = parser.parse_args()
    count, errors = maintain_indexes(DOCS, write=args.write, conformance_only=args.conformance_only)
    for error in errors:
        print(f"ERROR: {error}")
    if not errors:
        detail = "OKF conformance" if args.conformance_only else f"producer metadata; indexes {'written' if args.write else 'current'}"
        print(f"OK: {count} concepts; {detail}")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
