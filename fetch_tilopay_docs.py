#!/usr/bin/env python3
"""
TiloPay Documentation Scraper
Fetches all official TiloPay documentation and converts to markdown format
"""

import os
import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
import time
import re

class TiloPayDocScraper:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.visited_urls = set()

    def fetch_url(self, url, retries=3):
        """Fetch URL with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def html_to_markdown(self, html_content, base_url=""):
        """Convert HTML to Markdown"""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove scripts, styles, and nav elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()

        markdown = []

        # Extract main content
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        if not main_content:
            main_content = soup

        for element in main_content.descendants:
            if element.name == 'h1':
                markdown.append(f"\n# {element.get_text(strip=True)}\n")
            elif element.name == 'h2':
                markdown.append(f"\n## {element.get_text(strip=True)}\n")
            elif element.name == 'h3':
                markdown.append(f"\n### {element.get_text(strip=True)}\n")
            elif element.name == 'h4':
                markdown.append(f"\n#### {element.get_text(strip=True)}\n")
            elif element.name == 'h5':
                markdown.append(f"\n##### {element.get_text(strip=True)}\n")
            elif element.name == 'h6':
                markdown.append(f"\n###### {element.get_text(strip=True)}\n")
            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text:
                    markdown.append(f"{text}\n")
            elif element.name == 'a':
                text = element.get_text(strip=True)
                href = element.get('href', '')
                if href and text:
                    full_url = urljoin(base_url, href)
                    markdown.append(f"[{text}]({full_url})")
            elif element.name == 'li':
                text = element.get_text(strip=True)
                if text and element.parent.name in ['ul', 'ol']:
                    prefix = '-' if element.parent.name == 'ul' else '1.'
                    markdown.append(f"{prefix} {text}\n")
            elif element.name == 'code':
                text = element.get_text(strip=True)
                if text:
                    markdown.append(f"`{text}`")
            elif element.name == 'pre':
                text = element.get_text(strip=True)
                if text:
                    markdown.append(f"\n```\n{text}\n```\n")

        return '\n'.join(markdown)

    def fetch_postman_api_docs(self):
        """Fetch Postman API documentation"""
        print("Fetching Postman API documentation...")
        url = "https://documenter.getpostman.com/view/12758640/TVKA5KUT"

        try:
            # Try to get the JSON version
            json_url = f"{url}?format=json"
            response = self.fetch_url(json_url)

            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                markdown = self.postman_json_to_markdown(data)
            else:
                # Fall back to HTML scraping
                response = self.fetch_url(url)
                markdown = self.html_to_markdown(response.text, url)

            output_file = self.output_dir / "api-reference.md"
            output_file.write_text(markdown, encoding='utf-8')
            print(f"✓ Saved API reference to {output_file}")

        except Exception as e:
            print(f"✗ Error fetching Postman docs: {e}")

    def postman_json_to_markdown(self, data):
        """Convert Postman JSON to Markdown"""
        markdown = []

        if isinstance(data, dict):
            collection = data.get('collection', data)

            # Collection info
            info = collection.get('info', {})
            markdown.append(f"# {info.get('name', 'TiloPay API')}\n")
            markdown.append(f"{info.get('description', '')}\n")

            # Items (endpoints)
            items = collection.get('item', [])
            for item in items:
                markdown.extend(self.parse_postman_item(item))

        return '\n'.join(markdown)

    def parse_postman_item(self, item, level=2):
        """Parse Postman collection item"""
        markdown = []
        header = '#' * level

        if 'name' in item:
            markdown.append(f"\n{header} {item['name']}\n")

        if 'description' in item:
            markdown.append(f"{item['description']}\n")

        # Request details
        if 'request' in item:
            request = item['request']
            method = request.get('method', 'GET')
            url = request.get('url', {})

            if isinstance(url, dict):
                raw_url = url.get('raw', '')
            else:
                raw_url = url

            markdown.append(f"**Endpoint:** `{method} {raw_url}`\n")

            # Headers
            headers = request.get('header', [])
            if headers:
                markdown.append("\n**Headers:**\n")
                for header in headers:
                    markdown.append(f"- `{header.get('key')}`: `{header.get('value')}`\n")

            # Body
            body = request.get('body', {})
            if body:
                mode = body.get('mode', '')
                if mode == 'raw':
                    markdown.append(f"\n**Request Body:**\n```json\n{body.get('raw', '')}\n```\n")

        # Response examples
        if 'response' in item:
            for response in item['response']:
                markdown.append(f"\n**Example Response:** {response.get('name', 'Response')}\n")
                markdown.append(f"```json\n{response.get('body', '')}\n```\n")

        # Nested items
        if 'item' in item:
            for subitem in item['item']:
                markdown.extend(self.parse_postman_item(subitem, level + 1))

        return markdown

    def fetch_sdk_pdf(self):
        """Fetch SDK PDF documentation"""
        print("Fetching SDK PDF documentation...")
        url = "https://app.tilopay.com/sdk/documentation.pdf"

        try:
            response = self.fetch_url(url)
            pdf_file = self.output_dir / "sdk-documentation.pdf"
            pdf_file.write_bytes(response.content)
            print(f"✓ Saved SDK PDF to {pdf_file}")

            # Create a note about PDF conversion
            note_file = self.output_dir / "sdk-documentation-note.md"
            note_file.write_text(
                f"# TiloPay SDK Documentation\n\n"
                f"The official SDK documentation is available as a PDF: `sdk-documentation.pdf`\n\n"
                f"Source: {url}\n\n"
                f"To view the full documentation, please open the PDF file.\n",
                encoding='utf-8'
            )
            print(f"✓ Created note at {note_file}")

        except Exception as e:
            print(f"✗ Error fetching SDK PDF: {e}")

    def fetch_documentation_page(self, url, filename):
        """Fetch a documentation page and save as markdown"""
        print(f"Fetching {url}...")

        try:
            response = self.fetch_url(url)
            markdown = self.html_to_markdown(response.text, url)

            output_file = self.output_dir / filename
            output_file.write_text(
                f"# Documentation\n\nSource: {url}\n\n{markdown}",
                encoding='utf-8'
            )
            print(f"✓ Saved to {output_file}")

        except Exception as e:
            print(f"✗ Error fetching {url}: {e}")

    def fetch_all_documentation(self):
        """Fetch all TiloPay documentation"""
        print("\n" + "="*60)
        print("TiloPay Documentation Scraper")
        print("="*60 + "\n")

        # Core documentation
        self.fetch_postman_api_docs()
        self.fetch_sdk_pdf()

        # Main documentation pages
        docs_to_fetch = [
            ("https://tilopay.com/documentacion", "main-documentation.md"),
            ("https://tilopay.com/documentacion/sdk", "sdk-features.md"),
            ("https://tilopay.com/developers", "developer-registration.md"),
            ("https://tilopay.com/preguntas-frecuentes", "faq.md"),
        ]

        for url, filename in docs_to_fetch:
            self.fetch_documentation_page(url, filename)
            time.sleep(1)  # Be nice to the server

        # Create index
        self.create_index()

        print("\n" + "="*60)
        print("Documentation fetch complete!")
        print(f"All files saved to: {self.output_dir}")
        print("="*60 + "\n")

    def create_index(self):
        """Create an index of all documentation"""
        index_content = [
            "# TiloPay Documentation Index\n",
            "This directory contains the complete TiloPay documentation fetched from official sources.\n",
            "\n## Contents\n",
        ]

        for file in sorted(self.output_dir.glob("*.md")):
            if file.name != "index.md":
                index_content.append(f"- [{file.stem}](./{file.name})\n")

        for file in sorted(self.output_dir.glob("*.pdf")):
            index_content.append(f"- [{file.stem}](./{file.name}) (PDF)\n")

        index_content.append("\n## Official Sources\n")
        index_content.append("- [TiloPay Documentation](https://tilopay.com/documentacion)\n")
        index_content.append("- [Postman API Reference](https://documenter.getpostman.com/view/12758640/TVKA5KUT)\n")
        index_content.append("- [SDK Documentation PDF](https://app.tilopay.com/sdk/documentation.pdf)\n")
        index_content.append("- [Developer Portal](https://tilopay.com/developers)\n")
        index_content.append("\n## Support\n")
        index_content.append("- Email: soporte@tilopay.com\n")
        index_content.append("- Developer Support: https://cst.support.tilopay.com/servicedesk/customer/portal/21\n")

        index_file = self.output_dir / "index.md"
        index_file.write_text(''.join(index_content), encoding='utf-8')
        print(f"✓ Created index at {index_file}")


def main():
    output_dir = "/Users/papuman/Documents/My Projects/GMS/docs/TiloPayAccess/docs"
    scraper = TiloPayDocScraper(output_dir)
    scraper.fetch_all_documentation()


if __name__ == "__main__":
    main()
