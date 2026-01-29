#!/usr/bin/env python3
"""
Aggressively fetch Postman API documentation using multiple methods
"""
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
import time

output_dir = Path('/Users/papuman/Documents/My Projects/GMS/docs/TiloPayAccess/docs')
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

print("Attempting to fetch Postman API documentation with multiple methods...\n")

# Method 1: Try to get the page with full headers
print("Method 1: Fetching Postman page with browser-like headers...")
url = "https://documenter.getpostman.com/view/12758640/TVKA5KUT"

try:
    response = session.get(url, timeout=30)

    # Save the HTML
    html_file = output_dir / 'postman-api-full.html'
    html_file.write_text(response.text, encoding='utf-8')
    print(f"✓ Saved HTML ({len(response.text)} bytes)")

    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract all text content
    markdown = ["# TiloPay Postman API Documentation\n\n"]
    markdown.append(f"Source: {url}\n\n")

    # Try to find the main content
    # Postman uses specific classes for their documentation
    content_sections = soup.find_all(['div', 'section'], class_=lambda x: x and any(
        keyword in str(x).lower() for keyword in ['content', 'documentation', 'request', 'response', 'endpoint']
    ))

    if content_sections:
        print(f"Found {len(content_sections)} content sections")
        for section in content_sections:
            text = section.get_text(separator='\n', strip=True)
            if text and len(text) > 50:
                markdown.append(f"\n{text}\n\n")

    # If that didn't work, extract ALL visible text
    if len(''.join(markdown)) < 2000:
        print("Extracting all visible text...")

        # Remove scripts and styles
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()

        # Get body text
        body = soup.find('body')
        if body:
            # Extract headings and content
            for elem in body.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'code', 'li']):
                text = elem.get_text(strip=True)
                if text and len(text) > 10:
                    if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        level = int(elem.name[1])
                        markdown.append(f"\n{'#' * level} {text}\n\n")
                    elif elem.name == 'pre' or elem.name == 'code':
                        markdown.append(f"\n```\n{text}\n```\n\n")
                    elif elem.name == 'li':
                        markdown.append(f"- {text}\n")
                    else:
                        markdown.append(f"{text}\n\n")

    # Save markdown
    md_file = output_dir / 'postman-api-extracted.md'
    content = ''.join(markdown)
    md_file.write_text(content, encoding='utf-8')
    print(f"✓ Saved markdown ({len(content)} bytes)")

    # Try to extract any JSON data embedded in the page
    print("\nSearching for embedded JSON data...")
    scripts = soup.find_all('script')
    for script in scripts:
        script_text = script.string
        if script_text and ('collection' in script_text.lower() or 'api' in script_text.lower()):
            # Try to find JSON objects
            import re
            json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', script_text)
            for i, match in enumerate(json_matches[:5]):  # Check first 5 matches
                try:
                    data = json.loads(match)
                    if isinstance(data, dict) and len(data) > 3:
                        json_file = output_dir / f'postman-data-{i}.json'
                        json_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
                        print(f"✓ Found JSON data: {json_file.name}")
                except:
                    pass

except Exception as e:
    print(f"✗ Error: {e}")

# Method 2: Try alternative Postman URLs
print("\nMethod 2: Trying alternative Postman URLs...")
alt_urls = [
    "https://www.postman.com/tilopay",
    "https://www.postman.com/collections/12758640-TVKA5KUT",
]

for alt_url in alt_urls:
    try:
        print(f"Trying: {alt_url}")
        response = session.get(alt_url, timeout=20)
        if response.status_code == 200:
            filename = alt_url.split('/')[-1] + '.html'
            (output_dir / filename).write_text(response.text, encoding='utf-8')
            print(f"✓ Saved {filename}")
    except Exception as e:
        print(f"✗ Failed: {e}")

print("\n✓ Postman documentation fetch complete!")
print(f"\nFiles saved to: {output_dir}")
