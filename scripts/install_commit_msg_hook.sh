#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
hook_path="$repo_root/.git/hooks/commit-msg"

cat > "$hook_path" <<'EOF'
#!/usr/bin/env bash

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
message_file="$1"

if [[ -x "$repo_root/.venv/Scripts/conventional-pre-commit.exe" ]]; then
    if command -v wslpath >/dev/null 2>&1; then
        message_file="$(wslpath -w "$message_file")"
    fi
    exec "$repo_root/.venv/Scripts/conventional-pre-commit.exe" "$message_file"
fi

if [[ -x "$repo_root/.venv/bin/conventional-pre-commit" ]]; then
    exec "$repo_root/.venv/bin/conventional-pre-commit" "$message_file"
fi

if command -v conventional-pre-commit >/dev/null 2>&1; then
    exec conventional-pre-commit "$message_file"
fi

echo "conventional-pre-commit not found. Install dependencies with 'pip install -r reqs.txt'." >&2
exit 1
EOF

chmod +x "$hook_path"
echo "Installed commit-msg hook at $hook_path"
