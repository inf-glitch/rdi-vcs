#!/usr/bin/env bash
# Uninstaller for rdi-vcs — reverses install.sh (Miniforge, symlink, ~/.env.sh, shell rc PATH).

set -euo pipefail

DRY_RUN=0
ASSUME_YES=0
REMOVE_RC_BACKUPS=0
INSTALL_DIR_ARG=""

usage() {
  cat <<'EOF'
Usage: uninstall.sh [options]

Removes the rdi-vcs Miniforge install, launcher symlink, the whole ~/.env.sh file,
and the PATH line added to shell rc files by install.sh.

Options:
  --install-dir PATH   Use this clone directory (overrides ~/.env.sh and env)
  --dry-run            Print actions only; do not remove anything
  -y, --yes            Do not prompt for confirmation
  --remove-rc-backups  Remove ~/.bashrc.pre-rdi-vcs and ~/.zshrc.pre-rdi-vcs if present
  -h, --help           Show this help

Install directory resolution (first match wins):
  1. --install-dir
  2. RDI_VCS_INSTALLATION environment variable
  3. RDI_VCS_INSTALLATION from ~/.env.sh
  4. Current directory if it contains miniforge3/ or rdi-vcs.sh
EOF
}

die() {
  echo "uninstall.sh: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-dir)
      [[ $# -ge 2 ]] || die "--install-dir requires a path"
      INSTALL_DIR_ARG="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -y|--yes)
      ASSUME_YES=1
      shift
      ;;
    --remove-rc-backups)
      REMOVE_RC_BACKUPS=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown option: $1 (use --help)"
      ;;
  esac
done

rm_rf() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] rm -rf -- $*"
  else
    rm -rf -- "$@"
  fi
}

rm_f() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] rm -f -- $*"
  else
    rm -f -- "$@"
  fi
}

# Returns 0 and prints value if found
rdi_vcs_installation_from_env_sh() {
  local f="${HOME}/.env.sh"
  [[ -f "$f" ]] || return 1
  local line val
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" =~ ^export[[:space:]]+RDI_VCS_INSTALLATION=(.*)$ ]]; then
      val="${BASH_REMATCH[1]}"
      val="${val#\"}"
      val="${val%\"}"
      val="${val#\'}"
      val="${val%\'}"
      val="${val%%[[:space:]]*}"
      printf '%s\n' "$val"
      return 0
    fi
  done <"$f"
  return 1
}

resolve_install_dir() {
  local dir=""
  if [[ -n "$INSTALL_DIR_ARG" ]]; then
    dir="$INSTALL_DIR_ARG"
  elif [[ -n "${RDI_VCS_INSTALLATION:-}" ]]; then
    dir="$RDI_VCS_INSTALLATION"
  else
    dir="$(rdi_vcs_installation_from_env_sh || true)"
    if [[ -z "$dir" ]]; then
      if [[ -d "${PWD}/miniforge3" ]] || [[ -f "${PWD}/rdi-vcs.sh" ]]; then
        dir="$PWD"
      fi
    fi
  fi
  if [[ -z "$dir" ]]; then
    die "could not resolve install directory. Use --install-dir /path/to/rdi-vcs or set RDI_VCS_INSTALLATION."
  fi
  # Normalize to absolute path
  if [[ -d "$dir" ]]; then
    (cd "$dir" && pwd)
  else
    die "install directory does not exist or is not a directory: $dir"
  fi
}

is_rdi_path_line() {
  local line="${1%$'\r'}"
  [[ "$line" == 'export PATH=$PATH:~/.local/' ]] || [[ "$line" == 'export PATH=$PATH:~/.local' ]]
}

filter_rc_file() {
  local path="$1"
  [[ -f "$path" ]] || return 0
  local tmp out=0
  tmp="$(mktemp)"
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    if is_rdi_path_line "$line"; then
      echo "  removing PATH line from $(basename "$path")"
      out=1
      continue
    fi
    printf '%s\n' "$line" >>"$tmp"
  done <"$path"
  if [[ "$out" -eq 1 ]]; then
    if [[ "$DRY_RUN" -eq 1 ]]; then
      echo "[dry-run] would rewrite $path (PATH line removed)"
      rm -f "$tmp"
    else
      mv "$tmp" "$path"
    fi
  else
    rm -f "$tmp"
  fi
}

remove_env_sh() {
  local f="${HOME}/.env.sh"
  [[ -f "$f" ]] || { echo "  (~/.env.sh not present — skipping)"; return 0; }
  echo "  rm -f ~/.env.sh"
  rm_f "$f"
}

INSTALL_DIR="$(resolve_install_dir)"
MINIFORGE_SH="Miniforge3-$(uname)-$(uname -m).sh"
MINIFORGE_SH_PATH="${INSTALL_DIR}/${MINIFORGE_SH}"

echo "rdi-vcs uninstall"
echo "  install directory: $INSTALL_DIR"
echo ""

if [[ "$DRY_RUN" -eq 0 ]] && [[ "$ASSUME_YES" -eq 0 ]]; then
  if [[ ! -t 0 ]]; then
    die "stdin is not a terminal; use -y or --yes to confirm uninstall"
  fi
  read -r -p "Proceed with removal? [y/N] " reply
  case "$reply" in
    y|Y|yes|YES) ;;
    *) echo "Aborted."; exit 1 ;;
  esac
fi

echo "Removing Miniforge tree and installer script..."
if [[ -d "${INSTALL_DIR}/miniforge3" ]]; then
  echo "  rm -rf ${INSTALL_DIR}/miniforge3"
  rm_rf "${INSTALL_DIR}/miniforge3"
else
  echo "  (no miniforge3 directory — skipping)"
fi

if [[ -f "$MINIFORGE_SH_PATH" ]]; then
  echo "  rm -f ${MINIFORGE_SH_PATH}"
  rm_f "$MINIFORGE_SH_PATH"
else
  echo "  (no ${MINIFORGE_SH} — skipping)"
fi

echo "Removing launcher symlink ~/.local/rdi-vcs ..."
if [[ -L "${HOME}/.local/rdi-vcs" ]] || [[ -f "${HOME}/.local/rdi-vcs" ]]; then
  rm_f "${HOME}/.local/rdi-vcs"
else
  echo "  (not present — skipping)"
fi

echo "Removing ~/.env.sh ..."
remove_env_sh

echo "Removing rdi-vcs PATH snippet from ~/.bashrc and ~/.zshrc (if present) ..."
filter_rc_file "${HOME}/.bashrc"
filter_rc_file "${HOME}/.zshrc"

if [[ "$REMOVE_RC_BACKUPS" -eq 1 ]]; then
  echo "Removing installer shell rc backups (--remove-rc-backups) ..."
  for b in "${HOME}/.bashrc.pre-rdi-vcs" "${HOME}/.zshrc.pre-rdi-vcs"; do
    if [[ -f "$b" ]]; then
      rm_f "$b"
    else
      echo "  (not present: $b)"
    fi
  done
fi

echo ""
echo "Done."
