#!/usr/bin/env bash

set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: GitHub CLI (gh) is not installed."
  echo "Install it first and authenticate with: gh auth login"
  exit 1
fi

CURRENT_BRANCH="$(git branch --show-current)"

if [ "$CURRENT_BRANCH" = "main" ]; then
  echo "You are already on main."
else
  echo "Current branch: $CURRENT_BRANCH"
fi

echo
read -rp "PR number to merge: " PR_NUMBER

gh pr merge "$PR_NUMBER" --squash --delete-branch

echo
echo "Updating local main..."
git checkout main
git pull origin main

echo
echo "Done."