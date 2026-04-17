"""Loader de perfis de permissões por projeto.

O contrato atual esperado é:

{
  "activeProfile": "balanced",
  "profiles": {
    "safe": {
      "description": "...",
      "permissions": {
        "defaultMode": "bypassPermissions",
        "allow": ["Bash(ls *)", ...],
        "deny": ["Bash(rm *)", ...],
      },
    },
  },
}

"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping
import shlex


DEFAULT_PERMISSION_PROFILE_NAME = "balanced"
_PROFILE_FILE_CANDIDATES = (
    Path("permissions-profiles.jsonc"),
    Path("permissions-profiles.json"),
    Path("docs") / "permissions-profiles.jsonc",
    Path("docs") / "permissions-profiles.json",
)


def _normalize_name(value: Any) -> str:
    return str(value or "").strip().lower()


def _strip_jsonc_comments(payload: str) -> str:
    lines = []
    for raw_line in payload.splitlines():
        line = raw_line
        comment_pos = line.find("//")
        if comment_pos >= 0:
            line = line[:comment_pos]
        lines.append(line)
    return "\n".join(lines)


def _load_profile_payload(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonc":
        text = _strip_jsonc_comments(text)
    payload = json.loads(text)
    if not isinstance(payload, Mapping):
        raise ValueError(f"permissions profile file deve conter objeto JSON: {path}")
    return dict(payload)


def _normalize_rules(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _normalize_profiles(payload: Mapping[str, Any]) -> dict[str, Any]:
    raw_profiles = payload.get("profiles")
    if not isinstance(raw_profiles, Mapping):
        raw_profiles = {}

    profiles: dict[str, dict[str, Any]] = {}
    for profile_name, profile_payload in raw_profiles.items():
        if not isinstance(profile_payload, Mapping):
            continue
        permissions = profile_payload.get("permissions")
        if not isinstance(permissions, Mapping):
            permissions = {}

        normalized_profile = {
            "description": str(profile_payload.get("description", "")),
            "permissions": {
                "defaultMode": str(permissions.get("defaultMode", "bypassPermissions")),
                "allow": _normalize_rules(permissions.get("allow")),
                "deny": _normalize_rules(permissions.get("deny")),
            },
        }
        profiles[_normalize_name(profile_name)] = normalized_profile

    active_profile = str(payload.get("activeProfile") or DEFAULT_PERMISSION_PROFILE_NAME)
    normalized_active = _normalize_name(active_profile)
    if normalized_active and normalized_active not in profiles:
        normalized_active = DEFAULT_PERMISSION_PROFILE_NAME
    if normalized_active not in profiles and profiles:
        normalized_active = next(iter(profiles))

    return {
        "activeProfile": normalized_active or DEFAULT_PERMISSION_PROFILE_NAME,
        "profiles": profiles,
    }


def load_permission_profiles(
    workspace: Path | None = None,
    path: Path | str | None = None,
) -> dict[str, Any]:
    workspace_root = Path(workspace or Path.cwd())
    search_paths: list[Path] = []

    if path is not None:
        search_paths.append(Path(path))
    else:
        for candidate in _PROFILE_FILE_CANDIDATES:
            search_paths.append(workspace_root / candidate)

    for candidate in search_paths:
        payload = _load_profile_payload(candidate)
        if payload:
            return _normalize_profiles(payload)

    return {
        "activeProfile": DEFAULT_PERMISSION_PROFILE_NAME,
        "profiles": {},
    }


def active_permission_profile(
    payload: Mapping[str, Any] | None,
    requested_profile: str | None = None,
) -> str:
    payload_map = payload or {}
    profiles: dict[str, Any] = payload_map.get("profiles", {}) if isinstance(payload_map, Mapping) else {}
    if not isinstance(profiles, Mapping):
        profiles = {}

    candidate = _normalize_name(requested_profile)
    if not candidate:
        candidate = _normalize_name(payload_map.get("activeProfile") if isinstance(payload_map, Mapping) else "")
    if candidate and candidate in profiles:
        return candidate

    fallback = _normalize_name(DEFAULT_PERMISSION_PROFILE_NAME)
    if fallback in profiles:
        return fallback

    if profiles:
        return next(iter(profiles))

    return _normalize_name(DEFAULT_PERMISSION_PROFILE_NAME)


def _extract_shell_executable(rule: str) -> str | None:
    value = (rule or "").strip()
    if not (value.startswith("Bash(") and value.endswith(")")):
        return None
    inner = value[5:-1].strip()
    if not inner:
        return None
    try:
        tokens = shlex.split(inner)
    except ValueError:
        tokens = inner.split()
    if not tokens:
        return None
    return tokens[0].lower()


def resolve_shell_permissions(
    payload: Mapping[str, Any] | None,
    profile_name: str | None = None,
) -> tuple[list[str], list[str]]:
    profiles = payload.get("profiles", {}) if isinstance(payload, Mapping) else {}
    active = active_permission_profile(payload, requested_profile=profile_name)
    profile = {}
    if isinstance(profiles, Mapping):
        profile = profiles.get(active, {}) if isinstance(active, str) else {}
        if isinstance(profile, Mapping):
            profile = dict(profile)
        else:
            profile = {}

    permissions = profile.get("permissions", {}) if isinstance(profile, Mapping) else {}
    if not isinstance(permissions, Mapping):
        permissions = {}

    allowed_rules = _normalize_rules(permissions.get("allow"))
    denied_rules = _normalize_rules(permissions.get("deny"))

    allowed: set[str] = set()
    denied: set[str] = set()
    for rule in allowed_rules:
        executable = _extract_shell_executable(rule)
        if executable:
            allowed.add(executable)
    for rule in denied_rules:
        executable = _extract_shell_executable(rule)
        if executable:
            denied.add(executable)

    allowed.discard("")
    denied.discard("")

    return sorted(allowed), sorted(denied)

