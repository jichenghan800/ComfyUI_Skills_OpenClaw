from __future__ import annotations

import re
from collections.abc import Mapping

_FRIENDLY_FIELDS = {
    "seed",
    "steps",
    "cfg",
    "width",
    "height",
    "batch_size",
    "filename_prefix",
    "sampler_name",
    "scheduler",
    "denoise",
    "aspect_ratio",
    "size",
    "num",
}


def _normalize_identifier(value: object) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower())
    return normalized.strip("_")


def _normalize_text(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").strip().lower()).strip()


def suggest_parameter_alias(param_key: str, param_info: Mapping[str, object]) -> str | None:
    key_id = _normalize_identifier(param_key)
    field_id = _normalize_identifier(param_info.get("field", ""))
    text_blob = " ".join(
        part for part in (_normalize_text(param_key), _normalize_text(param_info.get("description", ""))) if part
    )

    if field_id in {"text", "prompt"} or key_id.startswith("prompt"):
        if "negative" in text_blob:
            return "negative_prompt"
        return "prompt"

    if field_id in _FRIENDLY_FIELDS:
        return field_id

    if key_id in _FRIENDLY_FIELDS:
        return key_id

    return None


def build_unique_parameter_alias_map(parameters: Mapping[str, Mapping[str, object]]) -> dict[str, str]:
    suggestions: dict[str, str] = {}
    alias_counts: dict[str, int] = {}
    raw_keys = set(parameters.keys())

    for param_key, param_info in parameters.items():
        alias = suggest_parameter_alias(param_key, param_info)
        if not alias:
            continue
        suggestions[param_key] = alias
        alias_counts[alias] = alias_counts.get(alias, 0) + 1

    alias_map: dict[str, str] = {}
    for param_key, alias in suggestions.items():
        if alias_counts.get(alias) != 1:
            continue
        if alias in raw_keys and alias != param_key:
            continue
        alias_map[alias] = param_key

    return alias_map


def get_display_parameter_name(param_key: str, parameters: Mapping[str, Mapping[str, object]]) -> str:
    alias_map = build_unique_parameter_alias_map(parameters)
    for alias, target_key in alias_map.items():
        if target_key == param_key:
            return alias
    return param_key

