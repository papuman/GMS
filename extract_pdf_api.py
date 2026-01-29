#!/usr/bin/env python3
"""
Extract API endpoints from TiloPay SDK PDF documentation
"""
import pdfplumber
from pathlib import Path
import re

pdf_path = Path('/Users/papuman/Documents/My Projects/GMS/docs/TiloPayAccess/docs/sdk-documentation.pdf')
output_path = Path('/Users/papuman/Documents/My Projects/GMS/docs/TiloPayAccess/docs/api-endpoints-extracted.md')

print(f"Extracting API endpoints from: {pdf_path}")
print(f"Output will be saved to: {output_path}\n")

markdown = []
markdown.append("# TiloPay API Endpoints\n")
markdown.append("**Extracted from:** SDK Documentation PDF\n\n")
markdown.append("---\n\n")

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}\n")

    full_text = []

    for i, page in enumerate(pdf.pages, 1):
        print(f"Processing page {i}/{len(pdf.pages)}...")
        text = page.extract_text()
        if text:
            full_text.append(f"\n## Page {i}\n\n")
            full_text.append(text)
            full_text.append("\n")

    # Combine all text
    content = '\n'.join(full_text)

    # Save full extracted text first
    raw_output = output_path.parent / 'sdk-documentation-full-text.md'
    raw_output.write_text(content, encoding='utf-8')
    print(f"\n✓ Saved full text extraction to: {raw_output}")

    # Now parse for API-specific information
    print("\nParsing for API endpoints and parameters...")

    # Look for common patterns
    patterns = {
        'urls': r'https?://[^\s<>"\'\)]+',
        'endpoints': r'/api/[^\s<>"\'\)]+',
        'methods': r'\b(GET|POST|PUT|DELETE|PATCH)\b',
        'headers': r'(Authorization|Content-Type|Accept|X-[A-Za-z-]+)\s*:',
        'params': r'(api[_-]?key|api[_-]?user|api[_-]?password|token|auth)',
    }

    findings = {
        'URLs': set(),
        'Endpoints': set(),
        'HTTP Methods': set(),
        'Headers': set(),
        'Parameters': set(),
    }

    # Extract URLs
    for match in re.finditer(patterns['urls'], content, re.IGNORECASE):
        findings['URLs'].add(match.group(0))

    # Extract endpoints
    for match in re.finditer(patterns['endpoints'], content, re.IGNORECASE):
        findings['Endpoints'].add(match.group(0))

    # Extract methods
    for match in re.finditer(patterns['methods'], content):
        findings['HTTP Methods'].add(match.group(0))

    # Extract headers
    for match in re.finditer(patterns['headers'], content):
        findings['Headers'].add(match.group(0))

    # Extract parameters
    for match in re.finditer(patterns['params'], content, re.IGNORECASE):
        findings['Parameters'].add(match.group(0))

    # Build structured markdown
    markdown.append("## Discovered API Information\n\n")

    for category, items in findings.items():
        if items:
            markdown.append(f"### {category}\n\n")
            for item in sorted(items):
                markdown.append(f"- `{item}`\n")
            markdown.append("\n")

    # Look for structured sections
    markdown.append("## Document Sections\n\n")

    # Find all headings (lines in ALL CAPS or with specific patterns)
    lines = content.split('\n')
    current_section = None
    section_content = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line looks like a heading
        if (len(line) < 100 and
            (line.isupper() or
             re.match(r'^[\d\.]+\s+[A-Z]', line) or
             re.match(r'^[A-Z][A-Za-z\s]+:$', line))):

            if current_section:
                # Save previous section
                if current_section not in section_content:
                    section_content[current_section] = []
            current_section = line
            if current_section not in section_content:
                section_content[current_section] = []
        elif current_section:
            section_content[current_section].append(line)

    # Output sections
    for section, content_lines in section_content.items():
        if content_lines:
            markdown.append(f"### {section}\n\n")
            # Take first 10 lines of each section
            for line in content_lines[:10]:
                if line.strip():
                    markdown.append(f"{line}\n")
            if len(content_lines) > 10:
                markdown.append(f"\n*[{len(content_lines) - 10} more lines...]*\n")
            markdown.append("\n")

    # Save markdown
    output_path.write_text(''.join(markdown), encoding='utf-8')
    print(f"✓ Saved API endpoints markdown to: {output_path}")

    print("\n" + "="*60)
    print("Summary:")
    print("="*60)
    for category, items in findings.items():
        print(f"{category}: {len(items)} found")
    print(f"Sections: {len(section_content)} found")
    print("="*60)

print("\n✓ Extraction complete!")
