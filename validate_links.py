#!/usr/bin/env python3
"""
Validate internal links in markdown documentation.
Checks if linked files exist and reports broken links.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Base directory
DOCS_DIR = Path("/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/docs")
REPO_ROOT = Path("/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS")

# Results
broken_links = []
checked_links = 0
files_with_issues = defaultdict(list)

def extract_markdown_links(content, file_path):
    """Extract all markdown links from content."""
    # Pattern matches [text](url) and [text](url "title")
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    links = []

    for match in re.finditer(pattern, content):
        link_text = match.group(1)
        link_url = match.group(2)

        # Remove optional title from URL
        link_url = link_url.split('"')[0].split("'")[0].strip()

        # Skip external links (http, https, mailto)
        if link_url.startswith(('http://', 'https://', 'mailto:', '#')):
            continue

        links.append({
            'text': link_text,
            'url': link_url,
            'line': content[:match.start()].count('\n') + 1
        })

    return links

def resolve_link_path(source_file, link_url):
    """Resolve relative link to absolute path."""
    source_dir = source_file.parent

    # Remove anchor if present
    link_path = link_url.split('#')[0]

    if not link_path:  # Just an anchor link
        return None

    # Resolve relative path
    if link_path.startswith('/'):
        # Absolute from repo root
        target = REPO_ROOT / link_path.lstrip('/')
    else:
        # Relative to source file
        target = (source_dir / link_path).resolve()

    return target

def check_file_exists(file_path):
    """Check if file exists."""
    if file_path is None:
        return True  # Anchor-only links are OK if we're not validating anchors

    return file_path.exists()

def validate_markdown_file(md_file):
    """Validate all links in a markdown file."""
    global checked_links

    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading {md_file}: {e}")
        return

    links = extract_markdown_links(content, md_file)

    for link in links:
        checked_links += 1
        target_path = resolve_link_path(md_file, link['url'])

        if not check_file_exists(target_path):
            broken_links.append({
                'source': md_file,
                'target': link['url'],
                'target_resolved': target_path,
                'text': link['text'],
                'line': link['line']
            })
            files_with_issues[str(md_file)].append({
                'url': link['url'],
                'line': link['line'],
                'text': link['text']
            })

def main():
    """Main validation function."""
    print("🔍 Validating markdown links in documentation...\n")

    # Find all markdown files
    md_files = list(DOCS_DIR.rglob("*.md"))

    # Also check root-level docs
    root_md_files = [f for f in REPO_ROOT.glob("*.md") if f.is_file()]

    all_files = md_files + root_md_files

    print(f"Found {len(all_files)} markdown files to check\n")

    # Validate each file
    for md_file in sorted(all_files):
        validate_markdown_file(md_file)

    # Report results
    print("=" * 80)
    print(f"\n📊 VALIDATION RESULTS\n")
    print(f"Total markdown files checked: {len(all_files)}")
    print(f"Total links checked: {checked_links}")
    print(f"Broken links found: {len(broken_links)}")
    print(f"Files with issues: {len(files_with_issues)}")

    if broken_links:
        print("\n" + "=" * 80)
        print("❌ BROKEN LINKS FOUND:\n")

        for source_file, issues in sorted(files_with_issues.items()):
            # Make path relative for readability
            try:
                rel_path = Path(source_file).relative_to(REPO_ROOT)
            except:
                rel_path = source_file

            print(f"\n📄 {rel_path}")
            print(f"   {len(issues)} broken link(s):")

            for issue in issues:
                print(f"   Line {issue['line']}: [{issue['text']}]({issue['url']})")

        print("\n" + "=" * 80)
        print(f"\n❌ Validation FAILED: {len(broken_links)} broken links\n")
        return 1
    else:
        print("\n" + "=" * 80)
        print("\n✅ Validation PASSED: All links are valid!\n")
        return 0

if __name__ == "__main__":
    exit(main())
