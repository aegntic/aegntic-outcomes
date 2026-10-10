#!/usr/bin/env bash
# skill-route installer.
#
# Installs by symlink. Creates nothing inside the skill corpus. Safe to re-run.
#
#   ./install.sh              # symlink skill into the primary host roots
#   ./install.sh --link       # symlink bin/skill-route onto PATH (recommended)
#   ./install.sh --bundle     # vendor hand-authored deps into vendor/ (self-contained)
#   ./install.sh --doctor     # verify every routed-to skill resolves
#   ./install.sh --uninstall  # remove what this installer created, nothing else
#   ./install.sh --check      # report status, change nothing
#
# Default (no flags) links only. It never writes inside the skill corpus.
# --bundle writes to $HERE/vendor/, inside the plugin, never to a corpus root.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROUTE="$HERE/bin/skill-route"
SKILL_DIR="$HERE"

MARK=".skill-route-install"   # marker written next to each symlink we create

log() { printf '%s\n' "$*" >&2; }

host_roots() {
  # Primary skill roots only. Shared/external dirs listed in hermes config are
  # consumed by whatever owns them; symlinking into them spreads the install
  # beyond where it belongs.
  for d in "$HOME"/.agents/skills "$HOME"/.claude/skills "$HOME"/.hermes/skills; do
    [ -d "$d" ] && printf '%s\n' "$d"
  done
}

extra_roots() {
  # Read-only view of additional roots, used by --check only.
  local cfg="$HOME/.hermes/config.yaml"
  [ -f "$cfg" ] || return 0
  sed -n '/^skills:/,/^[a-z]/p' "$cfg" \
    | grep -oE '^ +- /[^ ]+' | sed 's/^ *- *//' | while read -r p; do
      [ -d "$p" ] && printf '%s\n' "$p"
    done
}

created=()
remember() { created+=("$1"); }

link_skill() {
  local root="$1"
  local target="$root/skill-route"
  if [ -e "$target" ] || [ -L "$target" ]; then
    if [ -L "$target" ] && [ "$(readlink -f "$target")" = "$(readlink -f "$SKILL_DIR")" ]; then
      log "  ok       $target (already linked)"
      return 0
    fi
    log "  SKIP     $target exists and is not ours — leaving alone"
    return 0
  fi
  ln -s "$SKILL_DIR" "$target"
  printf 'installed by skill-route %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$target/$MARK"
  log "  linked   $target -> $SKILL_DIR"
  remember "$target"
}

link_bin() {
  local dir="${1:-$HOME/.local/bin}"
  local target="$dir/skill-route"
  mkdir -p "$dir"

  if [ -e "$target" ] && [ ! -L "$target" ]; then
    log "  SKIP     $target exists (not a symlink) — leaving alone"
    return 0
  fi
  ln -sf "$ROUTE" "$target"
  log "  linked   $target -> $ROUTE"
  remember "$target"
}

uninstall() {
  local n=0
  while read -r t; do
    if [ -L "$t" ]; then
      rm -f "$t"; log "  removed  $t"; n=$((n+1))
    elif [ -d "$t" ] && [ -f "$t/$MARK" ]; then
      rm -f "$t/$MARK"; rm -rf "$t"; log "  removed  $t (marked)"; n=$((n+1))
    fi
  done < <(host_roots | while read -r r; do printf '%s\n' "$r/skill-route"; done
           printf '%s\n' "$HOME/.local/bin/skill-route")
  log "removed $n link(s). Nothing else touched."
}

check() {
  log "skill-route install status"
  local t
  while read -r t; do
    if [ -L "$t" ]; then log "  linked   $t"
    elif [ -e "$t" ]; then log "  present  $t (not ours)"
    else log "  absent   $t"; fi
  done < <(host_roots | while read -r r; do printf '%s\n' "$r/skill-route"; done
           printf '%s\n' "$HOME/.local/bin/skill-route")
  command -v skill-route >/dev/null && log "  on PATH  $(command -v skill-route)" \
    || log "  not on PATH — run with --link or add ~/.local/bin to PATH"
  log ""
  log "routing surface (read-only):"
  "$ROUTE" --index 2>/dev/null | sed -n '1,3p' | sed 's/^/  /' || true
}

case "${1:-}" in
  --uninstall) uninstall ;;
  --check)     check ;;
  --link)      link_bin ;;
  --bundle)    "$ROUTE" --bundle ;;
  --doctor)    exec "$ROUTE" --doctor ;;
  "")
    log "linking skill-route skill into:"
    while read -r r; do link_skill "$r"; done < <(host_roots)
    log ""
    log "run '$0 --link' to also put skill-route on PATH."
    ;;
  *) log "usage: $0 [--link|--uninstall|--check]"; exit 1 ;;
esac
