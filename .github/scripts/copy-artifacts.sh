#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

# Copy mapping artifacts to the companion artifacts repository
# Usage: copy-artifacts.sh <date> <token>

set -euo pipefail

DATE="${1:?Usage: copy-artifacts.sh <date> <token>}"
TOKEN="${2:?Usage: copy-artifacts.sh <date> <token>}"
OWNER="${GITHUB_REPOSITORY_OWNER:-modeseven-lfit}"
REPO="onap-release-mapping-artifacts"

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

echo "Cloning ${OWNER}/${REPO}..."
git clone --depth 1 \
  "https://x-access-token:${TOKEN}@github.com/${OWNER}/${REPO}.git" \
  "${WORKDIR}/repo"

DEST="${WORKDIR}/repo/data/artifacts/${DATE}"
mkdir -p "$DEST"

# Copy manifest files
if [ -d "manifest" ]; then
  cp -a manifest/. "$DEST/"
fi

# Copy metadata files
if [ -d "metadata" ]; then
  cp -a metadata/. "$DEST/"
fi

# Generate a README for this date folder
cat > "${DEST}/README.md" << EOF
# ONAP Release Mapping — ${DATE}

Artifacts generated on ${DATE} by the
[onap-release-mapping-tool](https://github.com/${OWNER}/onap-release-mapping-tool).

## Files

| File | Description |
|------|-------------|
| \`manifest.json\` | Release manifest (primary artifact) |
| \`manifest.yaml\` | YAML format |
| \`manifest.csv\` | CSV format (repositories only) |
| \`manifest.md\` | Markdown report |
| \`metadata.json\` | Run provenance and metadata |
EOF

# Update the latest symlink
cd "${WORKDIR}/repo/data/artifacts"
rm -f latest
ln -s "$DATE" latest

# Commit and push
cd "${WORKDIR}/repo"
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git add -A
if git diff --cached --quiet; then
  echo "No changes to commit"
else
  git commit -m "Add mapping artifacts for ${DATE}"
  git push origin main
  echo "Artifacts pushed for ${DATE}"
fi
