#!/usr/bin/env bash

# Synchronize tyler-romero-skills across Codex, GitHub Copilot, and Claude Code.
# For each available CLI, update an existing installation or add the
# tyler-romero/skills marketplace and install the plugin when it is missing.
# Skip unavailable CLIs and exit nonzero if any installation or update fails.

set -u

plugin_name="tyler-romero-skills"
marketplace="tyler-romero-skills"
marketplace_source="tyler-romero/skills"
plugin_id="${plugin_name}@${marketplace}"
failures=0

skip() {
  printf '[%s] skipped: %s\n' "$1" "$2"
}

fail() {
  printf '[%s] update failed: %s\n' "$1" "${2:-command returned a nonzero status}" >&2
  failures=$((failures + 1))
}

json_contains() {
  python3 -c '
import json, sys

key, expected = sys.argv[1:]

def contains(value):
    if isinstance(value, dict):
        return value.get(key) == expected or any(contains(item) for item in value.values())
    if isinstance(value, list):
        return any(contains(item) for item in value)
    return False

print("yes" if contains(json.load(sys.stdin)) else "no")
' "$1" "$2"
}

sync_codex() {
  command -v codex >/dev/null 2>&1 || { skip Codex 'CLI not installed'; return; }
  command -v python3 >/dev/null 2>&1 || { fail Codex 'python3 is required'; return; }

  local installed is_installed marketplaces has_marketplace
  installed="$(codex plugin list --json 2>/dev/null)" || { fail Codex; return; }
  is_installed="$(json_contains pluginId "$plugin_id" <<<"$installed")" || { fail Codex; return; }
  if [[ "$is_installed" == yes ]]; then
    printf '[Codex] updating %s\n' "$plugin_id"
    if codex plugin marketplace upgrade "$marketplace" && codex plugin add "$plugin_id"; then
      printf '[Codex] updated\n'
    else
      fail Codex
    fi
    return
  fi

  marketplaces="$(codex plugin marketplace list --json 2>/dev/null)" || { fail Codex; return; }
  has_marketplace="$(json_contains name "$marketplace" <<<"$marketplaces")" || { fail Codex; return; }
  if [[ "$has_marketplace" == yes ]]; then
    codex plugin marketplace upgrade "$marketplace" || { fail Codex; return; }
  else
    codex plugin marketplace add "$marketplace_source" || { fail Codex; return; }
  fi

  printf '[Codex] installing %s\n' "$plugin_id"
  if codex plugin add "$plugin_id"; then
    printf '[Codex] installed\n'
  else
    fail Codex
  fi
}

sync_copilot() {
  command -v copilot >/dev/null 2>&1 || { skip Copilot 'CLI not installed'; return; }

  local installed marketplaces
  installed="$(copilot plugin list 2>/dev/null)" || { fail Copilot; return; }
  if printf '%s\n' "$installed" | grep -Fq "$plugin_id"; then
    printf '[Copilot] updating %s\n' "$plugin_id"
    if copilot plugin update "$plugin_id"; then
      printf '[Copilot] updated\n'
    else
      fail Copilot
    fi
    return
  fi

  marketplaces="$(copilot plugin marketplace list 2>/dev/null)" || { fail Copilot; return; }
  if printf '%s\n' "$marketplaces" | grep -Fq "$marketplace"; then
    copilot plugin marketplace update "$marketplace" || { fail Copilot; return; }
  else
    copilot plugin marketplace add "$marketplace_source" || { fail Copilot; return; }
  fi

  printf '[Copilot] installing %s\n' "$plugin_id"
  if copilot plugin install "$plugin_id"; then
    printf '[Copilot] installed\n'
  else
    fail Copilot
  fi
}

sync_claude() {
  command -v claude >/dev/null 2>&1 || { skip Claude 'CLI not installed'; return; }
  command -v python3 >/dev/null 2>&1 || { fail Claude 'python3 is required'; return; }

  local installed scope marketplaces has_marketplace
  installed="$(claude plugin list --json 2>/dev/null)" || { fail Claude; return; }
  scope="$(python3 -c '
import json, sys
plugins = json.load(sys.stdin)
print(next((plugin.get("scope", "") for plugin in plugins if plugin.get("id") == sys.argv[1]), ""))
' "$plugin_id" <<<"$installed")" || { fail Claude; return; }
  if [[ -z "$scope" ]]; then
    marketplaces="$(claude plugin marketplace list --json 2>/dev/null)" || { fail Claude; return; }
    has_marketplace="$(json_contains name "$marketplace" <<<"$marketplaces")" || { fail Claude; return; }
    if [[ "$has_marketplace" == yes ]]; then
      claude plugin marketplace update "$marketplace" || { fail Claude; return; }
    else
      claude plugin marketplace add "$marketplace_source" || { fail Claude; return; }
    fi

    printf '[Claude] installing %s at user scope\n' "$plugin_id"
    if claude plugin install --scope user "$plugin_id"; then
      printf '[Claude] installed; restart Claude Code to apply\n'
    else
      fail Claude
    fi
    return
  fi

  printf '[Claude] updating %s at %s scope\n' "$plugin_id" "$scope"
  if claude plugin update --scope "$scope" "$plugin_id"; then
    printf '[Claude] updated; restart Claude Code to apply\n'
  else
    fail Claude
  fi
}

sync_codex
sync_copilot
sync_claude

if ((failures > 0)); then
  printf 'Finished with %d failed update(s).\n' "$failures" >&2
  exit 1
fi

printf 'All available platforms are synced.\n'
