#!/usr/bin/env bash

set -euo pipefail

CURRENT_BRANCH="$(git branch --show-current)"

if [ -z "$CURRENT_BRANCH" ]; then
  echo "Error: could not detect current branch."
  exit 1
fi

if [ "$CURRENT_BRANCH" = "main" ]; then
  echo "Error: do not open a PR from main."
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: GitHub CLI (gh) is not installed."
  echo "Install it first and authenticate with: gh auth login"
  exit 1
fi

echo "Current branch: $CURRENT_BRANCH"
echo

read -rp "PR title: " PR_TITLE
echo
read -rp "Base branch [main]: " BASE_BRANCH
BASE_BRANCH="${BASE_BRANCH:-main}"

echo
echo "Pushing branch to origin..."
git push -u origin "$CURRENT_BRANCH"

echo
echo "Creating pull request..."
gh pr create \
  --base "$BASE_BRANCH" \
  --head "$CURRENT_BRANCH" \
  --title "$PR_TITLE" \
  --fill

echo
echo "Pull request created successfully."