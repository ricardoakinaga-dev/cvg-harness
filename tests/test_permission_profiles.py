"""Testes para carregamento e resolução de perfis de permissão."""

from pathlib import Path

from cvg_harness.config import (
    active_permission_profile,
    load_permission_profiles,
    resolve_shell_permissions,
)


def test_load_permission_profiles_parses_jsonc_and_selects_active_profile(tmp_path: Path) -> None:
    profile_path = tmp_path / "permissions-profiles.jsonc"
    profile_path.write_text(
        """
        {
          // Perfil ativo por padrão.
          "activeProfile": "balanced",
          "profiles": {
            "safe": {
              "description": "seguro",
              "permissions": {
                "allow": ["Bash(echo *)", "Bash(ls)"],
                "deny": ["Bash(rm *)"]
              }
            },
            "balanced": {
              "description": "equilibrado",
              "permissions": {
                "allow": ["Bash(python *)", "Bash(npm *)", "Bash(echo *)"],
                "deny": ["Bash(rm -rf *)", "Bash(exec *)"]
              }
            }
          }
        }
        """
    )

    payload = load_permission_profiles(tmp_path)
    assert payload["activeProfile"] == "balanced"
    assert isinstance(payload.get("profiles"), dict)


def test_active_permission_profile_falls_back_to_balanced_when_missing(tmp_path: Path) -> None:
    payload = {
        "activeProfile": "aggressive",
        "profiles": {
            "safe": {"description": "x", "permissions": {"allow": [], "deny": []}},
            "balanced": {"description": "y", "permissions": {"allow": [], "deny": []}},
        },
    }

    assert active_permission_profile(payload, requested_profile="missing") == "balanced"


def test_resolve_shell_permissions_extracts_executables() -> None:
    payload = {
        "activeProfile": "safe",
        "profiles": {
            "safe": {
                "description": "safe",
                "permissions": {
                    "allow": ["Bash(python -m pytest *)", "Bash(git commit -m *)", "Bash(echo *)", "invalid"],
                    "deny": ["Bash(rm -rf *)", "Bash(reboot *)", "other"],
                },
            }
        },
    }

    allow, deny = resolve_shell_permissions(payload, profile_name="safe")
    assert allow == ["echo", "git", "python"]
    assert deny == ["reboot", "rm"]
