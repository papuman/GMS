#!/usr/bin/env python3
"""
Enhanced TiloPay Documentation Scraper
Fetches comprehensive TiloPay documentation including integration guides
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

class EnhancedTiloPayScraper:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

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

    def clean_text(self, text):
        """Clean and normalize text"""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_content_from_html(self, soup, url):
        """Extract meaningful content from HTML"""
        markdown = []

        # Try to find main content area
        content_areas = [
            soup.find('main'),
            soup.find('article'),
            soup.find(class_=re.compile(r'content|documentation|docs|guide')),
            soup.find('body')
        ]

        main_content = None
        for area in content_areas:
            if area:
                main_content = area
                break

        if not main_content:
            return "No content found"

        # Process headings and paragraphs
        for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'pre', 'table']):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                text = self.clean_text(element.get_text())
                if text:
                    markdown.append(f"\n{'#' * level} {text}\n")

            elif element.name == 'p':
                text = self.clean_text(element.get_text())
                if text and len(text) > 3:
                    markdown.append(f"{text}\n")

            elif element.name in ['ul', 'ol']:
                for li in element.find_all('li', recursive=False):
                    text = self.clean_text(li.get_text())
                    if text:
                        prefix = '-' if element.name == 'ul' else '1.'
                        markdown.append(f"{prefix} {text}\n")

            elif element.name == 'pre':
                code = element.find('code')
                if code:
                    lang = ''
                    if 'class' in code.attrs:
                        classes = code['class']
                        for cls in classes:
                            if cls.startswith('language-'):
                                lang = cls.replace('language-', '')
                                break
                    text = code.get_text()
                    markdown.append(f"\n```{lang}\n{text}\n```\n")
                else:
                    text = element.get_text()
                    markdown.append(f"\n```\n{text}\n```\n")

            elif element.name == 'table':
                markdown.append("\n")
                # Process table headers
                headers = element.find_all('th')
                if headers:
                    header_text = " | ".join([self.clean_text(h.get_text()) for h in headers])
                    markdown.append(f"| {header_text} |\n")
                    markdown.append(f"| {' | '.join(['---'] * len(headers))} |\n")

                # Process table rows
                for row in element.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if cells and not all(c.name == 'th' for c in cells):
                        cell_text = " | ".join([self.clean_text(c.get_text()) for c in cells])
                        markdown.append(f"| {cell_text} |\n")
                markdown.append("\n")

        return '\n'.join(markdown)

    def fetch_postman_docs_html(self):
        """Fetch Postman documentation via HTML scraping"""
        print("Fetching Postman API documentation (HTML)...")
        url = "https://documenter.getpostman.com/view/12758640/TVKA5KUT"

        try:
            response = self.fetch_url(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            markdown = [f"# TiloPay API Reference\n\nSource: {url}\n\n"]

            # Extract all sections
            sections = soup.find_all(['section', 'div'], class_=re.compile(r'request|endpoint|method'))

            if not sections:
                # Fallback: extract all content
                markdown.append(self.extract_content_from_html(soup, url))
            else:
                for section in sections:
                    markdown.append(self.extract_content_from_html(section, url))

            output_file = self.output_dir / "api-reference.md"
            content = '\n'.join(markdown)

            if len(content) < 500:
                # If content is too short, use a more aggressive extraction
                markdown = [f"# TiloPay API Reference\n\nSource: {url}\n\n"]
                markdown.append(self.extract_content_from_html(soup, url))
                content = '\n'.join(markdown)

            output_file.write_text(content, encoding='utf-8')
            print(f"✓ Saved API reference to {output_file} ({len(content)} bytes)")

        except Exception as e:
            print(f"✗ Error fetching Postman docs: {e}")
            # Create a minimal file with links
            output_file = self.output_dir / "api-reference.md"
            output_file.write_text(
                f"# TiloPay API Reference\n\n"
                f"**Online Documentation:** {url}\n\n"
                f"**Note:** The API documentation is best viewed online at the Postman link above.\n\n"
                f"For detailed endpoint information, parameters, and examples, please visit the Postman documentation.\n",
                encoding='utf-8'
            )

    def fetch_platform_integrations(self):
        """Fetch platform-specific integration documentation"""
        print("\nFetching platform integration guides...")

        platforms = {
            "woocommerce": "https://woocommerce.com/document/tilopay-gateway/",
            "shopify": "https://tilopay.com/documentacion/shopify",
            "wix": "https://tilopay.com/documentacion/wix",
            "magento": "https://tilopay.com/documentacion/magento",
            "vtex": "https://tilopay.com/documentacion/vtex",
        }

        integrations_dir = self.output_dir / "integrations"
        integrations_dir.mkdir(exist_ok=True)

        for platform, url in platforms.items():
            try:
                print(f"  Fetching {platform} integration...")
                response = self.fetch_url(url)
                soup = BeautifulSoup(response.text, 'html.parser')

                markdown = [f"# TiloPay {platform.title()} Integration\n\nSource: {url}\n\n"]
                markdown.append(self.extract_content_from_html(soup, url))

                output_file = integrations_dir / f"{platform}.md"
                output_file.write_text('\n'.join(markdown), encoding='utf-8')
                print(f"  ✓ Saved {platform} integration")

                time.sleep(1)

            except Exception as e:
                print(f"  ✗ Error fetching {platform}: {e}")

    def fetch_payment_gateways(self):
        """Fetch payment gateway documentation"""
        print("\nFetching payment gateway documentation...")

        gateways = [
            ("yappy", "https://tilopay.com/documentacion/yappy"),
            ("powertanz", "https://tilopay.com/documentacion/powertanz"),
            ("cardinal", "https://tilopay.com/documentacion/cardinal"),
            ("credix", "https://tilopay.com/documentacion/credix"),
        ]

        gateways_dir = self.output_dir / "gateways"
        gateways_dir.mkdir(exist_ok=True)

        for gateway_name, url in gateways:
            try:
                print(f"  Fetching {gateway_name} gateway...")
                response = self.fetch_url(url)
                soup = BeautifulSoup(response.text, 'html.parser')

                markdown = [f"# TiloPay {gateway_name.title()} Gateway\n\nSource: {url}\n\n"]
                markdown.append(self.extract_content_from_html(soup, url))

                output_file = gateways_dir / f"{gateway_name}.md"
                output_file.write_text('\n'.join(markdown), encoding='utf-8')
                print(f"  ✓ Saved {gateway_name} gateway")

                time.sleep(1)

            except Exception as e:
                print(f"  ✗ Error fetching {gateway_name}: {e}")

    def create_comprehensive_index(self):
        """Create comprehensive index"""
        print("\nCreating comprehensive index...")

        index_content = [
            "# TiloPay Complete Documentation\n",
            "Comprehensive documentation fetched from official TiloPay sources.\n",
            f"\nLast updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            "\n## Quick Start\n",
            "- [Main Documentation](./main-documentation.md)\n",
            "- [API Reference](./api-reference.md)\n",
            "- [SDK Documentation PDF](./sdk-documentation.pdf)\n",
            "- [SDK Features](./sdk-features.md)\n",
            "- [Developer Registration](./developer-registration.md)\n",
            "- [FAQ](./faq.md)\n",
        ]

        # Add integration guides
        integrations_dir = self.output_dir / "integrations"
        if integrations_dir.exists():
            index_content.append("\n## Platform Integrations\n")
            for file in sorted(integrations_dir.glob("*.md")):
                index_content.append(f"- [{file.stem.title()}](./integrations/{file.name})\n")

        # Add gateway docs
        gateways_dir = self.output_dir / "gateways"
        if gateways_dir.exists():
            index_content.append("\n## Payment Gateways\n")
            for file in sorted(gateways_dir.glob("*.md")):
                index_content.append(f"- [{file.stem.title()}](./gateways/{file.name})\n")

        index_content.append("\n## Official Resources\n")
        index_content.append("- **Main Site**: https://tilopay.com\n")
        index_content.append("- **Documentation Portal**: https://tilopay.com/documentacion\n")
        index_content.append("- **Postman API**: https://documenter.getpostman.com/view/12758640/TVKA5KUT\n")
        index_content.append("- **SDK Documentation**: https://app.tilopay.com/sdk/documentation.pdf\n")
        index_content.append("- **Developer Portal**: https://tilopay.com/developers\n")
        index_content.append("- **Support Portal**: https://cst.support.tilopay.com/servicedesk/customer/portal/21\n")

        index_content.append("\n## Support Contacts\n")
        index_content.append("- **Email**: soporte@tilopay.com\n")
        index_content.append("- **Sales**: https://tilopay.com/contacto-ventas\n")

        index_content.append("\n## API Credentials (from your config)\n")
        index_content.append("Stored separately in `../API.md`\n")

        index_file = self.output_dir / "README.md"
        index_file.write_text(''.join(index_content), encoding='utf-8')
        print(f"✓ Created comprehensive index at {index_file}")

    def run(self):
        """Run the complete scraper"""
        print("\n" + "="*70)
        print("Enhanced TiloPay Documentation Scraper")
        print("="*70 + "\n")

        self.fetch_postman_docs_html()
        self.fetch_platform_integrations()
        self.fetch_payment_gateways()
        self.create_comprehensive_index()

        print("\n" + "="*70)
        print("Enhanced documentation fetch complete!")
        print(f"All files saved to: {self.output_dir}")
        print("="*70 + "\n")


def main():
    output_dir = "/Users/papuman/Documents/My Projects/GMS/docs/TiloPayAccess/docs"
    scraper = EnhancedTiloPayScraper(output_dir)
    scraper.run()


if __name__ == "__main__":
    main()
