#!/usr/bin/env bash
set -euo pipefail

repo_root=""
dest_root=""
skill_name=""
publish_all="false"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/publish-to-codex.sh --skill <name>
  ./scripts/publish-to-codex.sh --all

Options:
  --skill <name>      Publish one skill
  --all               Publish all skills
  --repo-root <path>  Override repository root
  --dest-root <path>  Override Codex skill destination root
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill)
      skill_name="${2:-}"
      shift 2
      ;;
    --all)
      publish_all="true"
      shift
      ;;
    --repo-root)
      repo_root="${2:-}"
      shift 2
      ;;
    --dest-root)
      dest_root="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "$repo_root" ]]; then
  repo_root="$(cd "$script_dir/.." && pwd)"
fi
if [[ -z "$dest_root" ]]; then
  dest_root="$HOME/.codex/skills"
fi

skills_root="$repo_root/skills"
mkdir -p "$dest_root"

copy_dir_contents() {
  local src="$1"
  local dst="$2"
  [[ -d "$src" ]] || return 0
  mkdir -p "$dst"
  cp -R "$src"/. "$dst"/
}

publish_skill() {
  local skill_dir="$1"
  local skill
  skill="$(basename "$skill_dir")"
  local shared_dir="$skill_dir/shared"
  local codex_dir="$skill_dir/codex"
  local target_dir="$dest_root/$skill"
  local tmp_dir="$dest_root/.$skill.tmp"

  [[ -d "$shared_dir" ]] || { echo "Missing shared directory for $skill" >&2; exit 1; }
  [[ -d "$codex_dir" ]] || { echo "Missing codex adapter directory for $skill" >&2; exit 1; }

  rm -rf "$tmp_dir"
  mkdir -p "$tmp_dir"
  copy_dir_contents "$shared_dir" "$tmp_dir"
  copy_dir_contents "$codex_dir" "$tmp_dir"
  rm -rf "$target_dir"
  mv "$tmp_dir" "$target_dir"
  echo "Published $skill -> $target_dir"
}

find_skill_dirs() {
  find "$skills_root" -mindepth 1 -maxdepth 2 -type d | while IFS= read -r dir; do
    if [[ -d "$dir/shared" && -d "$dir/codex" ]]; then
      echo "$dir"
    fi
  done | sort
}

resolve_skill_dir() {
  local requested="$1"
  local direct="$skills_root/$requested"
  if [[ -d "$direct/shared" && -d "$direct/codex" ]]; then
    echo "$direct"
    return 0
  fi

  local matches=()
  while IFS= read -r match; do
    matches+=("$match")
  done < <(find "$skills_root" -mindepth 2 -maxdepth 2 -type d -name "$requested" | sort)

  if [[ "${#matches[@]}" -eq 1 ]]; then
    echo "${matches[0]}"
    return 0
  fi
  if [[ "${#matches[@]}" -gt 1 ]]; then
    echo "Multiple skills matched '$requested'; use a category-qualified path." >&2
    exit 1
  fi

  echo "Skill not found: $requested" >&2
  exit 1
}

if [[ "$publish_all" == "true" ]]; then
  while IFS= read -r skill_dir; do
    publish_skill "$skill_dir"
  done < <(find_skill_dirs)
elif [[ -n "$skill_name" ]]; then
  skill_dir="$(resolve_skill_dir "$skill_name")"
  publish_skill "$skill_dir"
else
  echo "Provide --skill <name> or --all" >&2
  usage >&2
  exit 1
fi

echo "Done. Restart Codex to reload installed skills."
