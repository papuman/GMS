#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
import re

class TiloPayFetcher:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def fetch(self, url, timeout=30):
        for i in range(3):
            try:
                r = self.session.get(url, timeout=timeout)
                r.raise_for_status()
                return r
            except:
                if i < 2:
                    time.sleep(2)
        return None

    def html_to_md(self, html, url):
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()

        md = [f"# TiloPay Documentation\n\nSource: {url}\n\n"]

        main = soup.find('main') or soup.find('article') or soup.find('body')
        if not main:
            return "No content"

        for el in main.find_all(['h1','h2','h3','h4','h5','h6','p','ul','ol','pre','code','table']):
            try:
                if el.name in ['h1','h2','h3','h4','h5','h6']:
                    level = int(el.name[1])
                    text = re.sub(r'\s+', ' ', el.get_text()).strip()
                    if text:
                        md.append(f"\n{'#'*level} {text}\n")
                elif el.name == 'p':
                    text = re.sub(r'\s+', ' ', el.get_text()).strip()
                    if text:
                        md.append(f"{text}\n\n")
                elif el.name in ['ul','ol']:
                    for li in el.find_all('li', recursive=False):
                        text = re.sub(r'\s+', ' ', li.get_text()).strip()
                        if text:
                            md.append(f"- {text}\n")
                    md.append("\n")
                elif el.name == 'pre':
                    code = el.get_text()
                    md.append(f"\n```\n{code}\n```\n\n")
                elif el.name == 'code' and el.parent.name != 'pre':
                    text = el.get_text()
                    md.append(f"`{text}`")
            except:
                pass

        return ''.join(md)

    def save_pdf(self, url, filename):
        r = self.fetch(url)
        if r:
            (self.output_dir / filename).write_bytes(r.content)
            return True
        return False

    def save_page(self, url, filename):
        r = self.fetch(url)
        if r:
            md = self.html_to_md(r.text, url)
            (self.output_dir / filename).write_text(md, encoding='utf-8')
            return True
        return False

    def run(self):
        print("\nFetching TiloPay Documentation...\n")

        # PDFs
        print("Fetching PDFs...")
        self.save_pdf('https://app.tilopay.com/sdk/documentation.pdf', 'sdk-documentation.pdf')
        self.save_pdf('https://admin.tilopay.com/files/es_tilopay_payfac_user_guide.pdf', 'user-guide-spanish.pdf')

        # Main pages
        print("Fetching main documentation pages...")
        pages = [
            ('https://tilopay.com/documentacion', 'main-documentation.md'),
            ('https://tilopay.com/documentacion/sdk', 'sdk-features.md'),
            ('https://tilopay.com/developers', 'developer-registration.md'),
            ('https://tilopay.com/preguntas-frecuentes', 'faq.md'),
            ('https://documenter.getpostman.com/view/12758640/TVKA5KUT', 'api-reference.md'),
        ]

        for url, file in pages:
            print(f"  {file}...")
            self.save_page(url, file)
            time.sleep(1)

        # Platform integrations
        print("\nFetching platform integrations...")
        integrations_dir = self.output_dir / 'integrations'
        integrations_dir.mkdir(exist_ok=True)

        platforms = [
            ('https://woocommerce.com/document/tilopay-gateway/', 'woocommerce.md'),
            ('https://wordpress.org/plugins/tilopay/', 'wordpress.md'),
            ('https://help.vtex.com/en/docs/tutorials/setting-up-payments-with-tilopay', 'vtex.md'),
            ('https://apps.odoo.com/apps/modules/17.0/payment_tilopay', 'odoo.md'),
            ('https://support.bigcommerce.com/s/article/Connecting-with-Tilopay', 'bigcommerce.md'),
        ]

        for url, file in platforms:
            print(f"  {file}...")
            r = self.fetch(url)
            if r:
                md = self.html_to_md(r.text, url)
                (integrations_dir / file).write_text(md, encoding='utf-8')
            time.sleep(1)

        # Create index
        print("\nCreating index...")
        index = ["# TiloPay Complete Documentation\n\n"]
        index.append("## Core Documentation\n")
        for f in sorted(self.output_dir.glob("*.md")):
            index.append(f"- [{f.stem}](./{f.name})\n")
        index.append("\n## PDFs\n")
        for f in sorted(self.output_dir.glob("*.pdf")):
            index.append(f"- [{f.stem}](./{f.name})\n")
        if integrations_dir.exists():
            index.append("\n## Platform Integrations\n")
            for f in sorted(integrations_dir.glob("*.md")):
                index.append(f"- [{f.stem}](./integrations/{f.name})\n")

        index.append("\n## Official Links\n")
        index.append("- Main: https://tilopay.com\n")
        index.append("- Docs: https://tilopay.com/documentacion\n")
        index.append("- API: https://documenter.getpostman.com/view/12758640/TVKA5KUT\n")
        index.append("- SDK: https://app.tilopay.com/sdk/documentation.pdf\n")
        index.append("- Support: soporte@tilopay.com\n")

        (self.output_dir / 'README.md').write_text(''.join(index), encoding='utf-8')

        print(f"\nComplete! Files in: {self.output_dir}\n")

if __name__ == '__main__':
    fetcher = TiloPayFetcher('/Users/papuman/Documents/My Projects/GMS/docs/TiloPayAccess/docs')
    fetcher.run()
