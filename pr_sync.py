#!/usr/bin/env python3
"""
PR Sync - Automatically update PR descriptions using Claude Code.

This tool:
1. Validates the repo is ShettyGaurav/Demo-PR-App (STRICTLY enforced)
2. Checks for an open PR on the current branch
3. Analyzes the diff using Claude Code
4. Updates the PR description with meaningful changes

Usage: python pr_sync.py [--dry-run]
"""

import subprocess
import sys
import re
import json
from pathlib import Path

# STRICT: Only this repo is allowed - hardcoded, not configurable
ALLOWED_REPO = "harsh1947-jain/Git_Agent"


def run_cmd(cmd: list[str], check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        if capture:
            print(f"Command failed: {' '.join(cmd)}")
            print(f"stderr: {e.stderr}")
        raise


def get_repo_name() -> str | None:
    """Extract owner/repo from git remote URL."""
    try:
        result = run_cmd(["git", "remote", "get-url", "origin"], check=False)
        if result.returncode != 0:
            return None

        url = result.stdout.strip()

        # Handle SSH: git@github.com:owner/repo.git
        ssh_match = re.search(r"github\.com[:/](.+?/.+?)(?:\.git)?$", url)
        if ssh_match:
            return ssh_match.group(1).rstrip(".git")

        # Handle HTTPS: https://github.com/owner/repo.git
        https_match = re.search(r"github\.com/(.+?/.+?)(?:\.git)?$", url)
        if https_match:
            return https_match.group(1).rstrip(".git")

        return None
    except Exception:
        return None


def validate_repo() -> bool:
    """STRICT: Only allow ShettyGaurav/Demo-PR-App."""
    repo = get_repo_name()
    if repo != ALLOWED_REPO:
        print(f"ERROR: This tool only works with {ALLOWED_REPO}")
        print(f"Current repo: {repo or 'unknown'}")
        print("Exiting without making any changes.")
        return False
    return True


def get_current_branch() -> str | None:
    """Get the current git branch name."""
    result = run_cmd(["git", "branch", "--show-current"], check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def get_open_pr(branch: str) -> dict | None:
    """Check if there's an open PR for the current branch."""
    result = run_cmd(
        ["gh", "pr", "view", branch, "--json", "number,title,body,baseRefName,url"],
        check=False
    )
    if result.returncode != 0:
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def get_diff(base_branch: str) -> str:
    """Get the diff between base branch and current HEAD."""
    result = run_cmd(["git", "diff", f"{base_branch}...HEAD"], check=False)
    return result.stdout if result.returncode == 0 else ""


def get_commit_messages(base_branch: str) -> str:
    """Get commit messages between base and HEAD."""
    result = run_cmd(
        ["git", "log", f"{base_branch}...HEAD", "--pretty=format:%s%n%b", "--reverse"],
        check=False
    )
    return result.stdout if result.returncode == 0 else ""


def is_meaningful_change(diff: str) -> bool:
    """
    Check if the diff contains meaningful changes.
    Skip: whitespace-only, comment-only, typo fixes in comments.
    """
    if not diff.strip():
        return False

    # Remove diff headers
    lines = diff.split('\n')
    meaningful_lines = []

    for line in lines:
        # Skip diff metadata
        if line.startswith(('diff --git', 'index ', '---', '+++', '@@')):
            continue
        # Skip empty lines in diff
        if line in ('+', '-', ' '):
            continue
        # Skip lines that are only whitespace changes
        if line.startswith(('+', '-')):
            content = line[1:].strip()
            # Skip empty content
            if not content:
                continue
            # Skip comment-only lines (common patterns)
            if content.startswith(('#', '//', '/*', '*', '"""', "'''")):
                continue
            meaningful_lines.append(line)

    # Any code change counts as meaningful
    return len(meaningful_lines) >= 1


def analyze_with_claude(diff: str, commit_messages: str, current_body: str) -> str | None:
    """Use Claude Code to analyze changes and generate PR description."""

    prompt = f"""Analyze this git diff and commit messages to generate a complete Pull Request description.

COMMIT MESSAGES:
{commit_messages or "(no commits)"}

DIFF:
{diff[:15000]}

TASK:
Generate a complete PR description that covers ALL changes in this PR.

OUTPUT FORMAT (return ONLY this, no extra text):

## Summary
[2-3 bullet points summarizing all changes]

## What Changed
- [file/component]: [what changed]
- [continue for all main changes]

## Why
[1-2 sentences on the purpose/motivation]

## Test Plan
- [ ] [how to test these changes]

---
*PR description auto-generated by pr-sync*"""

    try:
        # Use claude CLI with --print for non-interactive output
        result = subprocess.run(
            ["claude", "--print", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode != 0:
            print(f"Claude analysis failed: {result.stderr}")
            return None

        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("Claude analysis timed out")
        return None
    except FileNotFoundError:
        print("ERROR: 'claude' CLI not found. Make sure Claude Code is installed.")
        return None


def update_pr_description(pr_number: int, current_body: str, new_content: str, dry_run: bool = False) -> bool:
    """Update the PR description by replacing with new content."""

    # Replace entirely with new content
    updated_body = new_content

    if dry_run:
        print("\n=== DRY RUN - Would update PR with: ===")
        print(updated_body)
        print("=== END DRY RUN ===\n")
        return True

    # Use gh to update PR
    result = run_cmd(
        ["gh", "pr", "edit", str(pr_number), "--body", updated_body],
        check=False
    )

    return result.returncode == 0


def create_pr_with_description(branch: str, base_branch: str, diff: str, commit_messages: str, dry_run: bool = False) -> bool:
    """Create initial PR with AI-generated description."""

    prompt = f"""Generate a Pull Request description for these changes.

BRANCH: {branch}
BASE: {base_branch}

COMMIT MESSAGES:
{commit_messages or "(no commits)"}

DIFF:
{diff[:15000]}

OUTPUT FORMAT (return ONLY this, no extra text):

## Summary
[2-3 bullet points summarizing the changes]

## What Changed
- [file/component]: [what changed]
- [continue for main changes]

## Why
[1-2 sentences on the purpose/motivation]

## Test Plan
- [ ] [how to test these changes]

---
*PR description auto-generated by pr-sync*"""

    try:
        result = subprocess.run(
            ["claude", "--print", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            print(f"Claude failed to generate PR description: {result.stderr}")
            return False

        pr_body = result.stdout.strip()

        # Generate a title from the first commit message or branch name
        title = commit_messages.split('\n')[0][:70] if commit_messages else f"Feature: {branch}"

        if dry_run:
            print(f"\n=== DRY RUN - Would create PR: ===")
            print(f"Title: {title}")
            print(f"Body:\n{pr_body}")
            print("=== END DRY RUN ===\n")
            return True

        result = subprocess.run(
            ["gh", "pr", "create", "--title", title, "--body", pr_body, "--base", base_branch],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"Created PR: {result.stdout.strip()}")
            return True
        else:
            print(f"Failed to create PR: {result.stderr}")
            return False

    except Exception as e:
        print(f"Error creating PR: {e}")
        return False


def main():
    dry_run = "--dry-run" in sys.argv

    print("PR Sync - Updating PR description...")

    # STRICT repo validation
    if not validate_repo():
        sys.exit(1)

    print(f"Repo validated: {ALLOWED_REPO}")

    # Get current branch
    branch = get_current_branch()
    if not branch:
        print("ERROR: Could not determine current branch")
        sys.exit(1)

    if branch in ("main", "master"):
        print("On main/master branch - nothing to do")
        sys.exit(0)

    print(f"Branch: {branch}")

    # Check for open PR
    pr = get_open_pr(branch)

    # Determine base branch (default to main)
    base_branch = pr["baseRefName"] if pr else "main"

    # Get diff
    diff = get_diff(base_branch)
    if not diff:
        print("No diff found - nothing to update")
        sys.exit(0)

    # Check for meaningful changes
    if not is_meaningful_change(diff):
        print("No meaningful changes detected (whitespace/comments only) - skipping")
        sys.exit(0)

    print("Meaningful changes detected")

    # Get commit messages for context
    commit_messages = get_commit_messages(base_branch)

    if pr:
        # Update existing PR
        print(f"Found PR #{pr['number']}: {pr['title']}")
        print("Analyzing changes with Claude...")

        new_content = analyze_with_claude(diff, commit_messages, pr.get("body", ""))

        if not new_content:
            print("Failed to generate update content")
            sys.exit(1)

        if update_pr_description(pr["number"], pr.get("body", ""), new_content, dry_run):
            print(f"Successfully updated PR #{pr['number']}")
            print(f"View at: {pr['url']}")
        else:
            print("Failed to update PR")
            sys.exit(1)
    else:
        # Create new PR
        print("No open PR found for this branch")
        print("Creating new PR with generated description...")

        if create_pr_with_description(branch, base_branch, diff, commit_messages, dry_run):
            print("PR created successfully")
        else:
            print("Failed to create PR")
            sys.exit(1)


if __name__ == "__main__":
    main()
