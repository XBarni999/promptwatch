from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Answer, Suite, TestCase

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal environments
    yaml = None


def load_suite(path: str | Path) -> Suite:
    data = _load_mapping(path)
    cases = [
        TestCase(
            id=str(item["id"]),
            input=str(item.get("input", "")),
            expected=dict(item.get("expected", {})),
        )
        for item in data.get("cases", [])
    ]
    return Suite(name=str(data.get("name", Path(path).stem)), cases=cases)


def load_answers(path: str | Path) -> dict[str, Answer]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        items = raw.get("answers", [])
    else:
        items = raw

    answers: dict[str, Answer] = {}
    for item in items:
        case_id = str(item["case_id"])
        answers[case_id] = Answer(
            case_id=case_id,
            output=str(item.get("output", "")),
            citations=[str(citation) for citation in item.get("citations", [])],
            metadata=dict(item.get("metadata", {})),
        )
    return answers


def _load_mapping(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".json":
        data = json.loads(text)
    elif yaml is None:
        data = _parse_simple_yaml(text)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{source} must contain a mapping at the top level")
    return data


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    lines = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))
    value, index = _parse_block(lines, 0, 0)
    if index != len(lines):
        raise ValueError("Could not parse the entire YAML document")
    if not isinstance(value, dict):
        raise ValueError("Simple YAML fallback only supports top-level mappings")
    return value


def _parse_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    if lines[index][1].startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_dict(lines, index, indent)


def _parse_dict(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while index < len(lines):
        line_indent, content = lines[index]
        if line_indent < indent or content.startswith("- "):
            break
        if line_indent > indent:
            raise ValueError(f"Unexpected indentation near: {content}")
        key, raw_value = _split_key_value(content)
        index += 1
        if raw_value == "":
            value, index = _parse_block(lines, index, indent + 2)
        else:
            value = _parse_scalar(raw_value)
        result[key] = value
    return result, index


def _parse_list(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    while index < len(lines):
        line_indent, content = lines[index]
        if line_indent < indent or not content.startswith("- "):
            break
        if line_indent > indent:
            raise ValueError(f"Unexpected indentation near: {content}")

        item = content[2:].strip()
        index += 1
        if ":" in item:
            key, raw_value = _split_key_value(item)
            entry: dict[str, Any] = {}
            if raw_value == "":
                value, index = _parse_block(lines, index, indent + 2)
            else:
                value = _parse_scalar(raw_value)
            entry[key] = value
            if index < len(lines) and lines[index][0] == indent + 2 and not lines[index][1].startswith("- "):
                extra, index = _parse_dict(lines, index, indent + 2)
                entry.update(extra)
            result.append(entry)
        else:
            result.append(_parse_scalar(item))
    return result, index


def _split_key_value(content: str) -> tuple[str, str]:
    if ":" not in content:
        raise ValueError(f"Expected key/value pair near: {content}")
    key, value = content.split(":", 1)
    return key.strip(), value.strip()


def _parse_scalar(value: str) -> Any:
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value.isdigit():
        return int(value)
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value
