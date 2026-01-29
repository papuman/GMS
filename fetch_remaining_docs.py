#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
import json
import re

output_dir = Path('/Users/papuman/Documents/My Projects/GMS/docs/TiloPayAccess/docs')
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'})

def fetch(url, timeout=30):
    for i in range(3):
        try:
            r = session.get(url, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            print(f"  Attempt {i+1} failed: {e}")
            if i < 2:
                time.sleep(2)
    return None

print("\nFetching remaining TiloPay documentation...\n")

# Try to get Postman collection JSON directly
print("1. Attempting to fetch Postman API collection...")
postman_urls = [
    'https://www.postman.com/api-evangelist/workspace/tilopay/overview',
    'https://api.getpostman.com/collections/12758640-TVKA5KUT',
    'https://documenter.postman.com/json/view/12758640/TVKA5KUT',
]

for url in postman_urls:
    print(f"  Trying: {url}")
    r = fetch(url)
    if r and r.status_code == 200:
        try:
            data = r.json()
            (output_dir / 'api-postman-collection.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
            print(f"  ✓ Saved Postman collection JSON")
            break
        except:
            pass

# Fetch additional resources from tilopay.com
print("\n2. Fetching additional resources from tilopay.com...")
additional_pages = [
    ('https://tilopay.com/tilopay-checkout', 'checkout-overview.md'),
    ('https://tilopay.com/en/features/', 'features-list.md'),
    ('https://connect.tilopay.com', 'tilopay-connect.md'),
    ('https://tilopay.com/terminos-condiciones', 'terms-conditions.md'),
]

for url, filename in additional_pages:
    print(f"  Fetching {filename}...")
    r = fetch(url)
    if r:
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()

        md = [f"# TiloPay Documentation\n\nSource: {url}\n\n"]
        main = soup.find('main') or soup.find('article') or soup.find('body')
        if main:
            for el in main.find_all(['h1','h2','h3','h4','h5','h6','p','ul','ol','pre']):
                try:
                    if el.name in ['h1','h2','h3','h4','h5','h6']:
                        level = int(el.name[1])
                        text = re.sub(r'\s+', ' ', el.get_text()).strip()
                        if text:
                            md.append(f"\n{'#'*level} {text}\n")
                    elif el.name == 'p':
                        text = re.sub(r'\s+', ' ', el.get_text()).strip()
                        if text and len(text) > 10:
                            md.append(f"{text}\n\n")
                    elif el.name in ['ul','ol']:
                        for li in el.find_all('li', recursive=False):
                            text = re.sub(r'\s+', ' ', li.get_text()).strip()
                            if text:
                                md.append(f"- {text}\n")
                        md.append("\n")
                    elif el.name == 'pre':
                        md.append(f"\n```\n{el.get_text()}\n```\n\n")
                except:
                    pass

        (output_dir / 'additional' / filename).parent.mkdir(exist_ok=True)
        (output_dir / 'additional' / filename).write_text(''.join(md), encoding='utf-8')
        print(f"  ✓ Saved {filename}")
    time.sleep(1)

# Convert admin guide HTML to markdown
print("\n3. Converting admin guide to markdown...")
admin_html = output_dir / 'guides' / 'admin-guide.html'
if admin_html.exists():
    soup = BeautifulSoup(admin_html.read_text(encoding='utf-8'), 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
        tag.decompose()

    md = ["# TiloPay Admin Guide\n\nSource: https://app.tilopay.com/admin/guide/\n\n"]
    main = soup.find('main') or soup.find('body')
    if main:
        for el in main.find_all(['h1','h2','h3','h4','h5','h6','p','ul','ol','pre']):
            try:
                if el.name in ['h1','h2','h3','h4','h5','h6']:
                    level = int(el.name[1])
                    text = re.sub(r'\s+', ' ', el.get_text()).strip()
                    if text:
                        md.append(f"\n{'#'*level} {text}\n")
                elif el.name == 'p':
                    text = re.sub(r'\s+', ' ', el.get_text()).strip()
                    if text and len(text) > 10:
                        md.append(f"{text}\n\n")
                elif el.name in ['ul','ol']:
                    for li in el.find_all('li', recursive=False):
                        text = re.sub(r'\s+', ' ', li.get_text()).strip()
                        if text:
                            md.append(f"- {text}\n")
                    md.append("\n")
            except:
                pass

    (output_dir / 'guides' / 'admin-guide.md').write_text(''.join(md), encoding='utf-8')
    print("  ✓ Converted admin guide to markdown")

# Fetch WooCommerce documentation (the complete one)
print("\n4. Fetching complete WooCommerce documentation...")
r = fetch('https://woocommerce.com/document/tilopay-gateway/')
if r:
    soup = BeautifulSoup(r.text, 'html.parser')
    article = soup.find('article') or soup.find('main')
    if article:
        md = ["# TiloPay WooCommerce Gateway Documentation\n\nSource: https://woocommerce.com/document/tilopay-gateway/\n\n"]
        for el in article.find_all(['h1','h2','h3','h4','h5','h6','p','ul','ol','pre','code']):
            try:
                if el.name in ['h1','h2','h3','h4','h5','h6']:
                    level = int(el.name[1])
                    text = re.sub(r'\s+', ' ', el.get_text()).strip()
                    if text:
                        md.append(f"\n{'#'*level} {text}\n")
                elif el.name == 'p':
                    text = re.sub(r'\s+', ' ', el.get_text()).strip()
                    if text and len(text) > 10:
                        md.append(f"{text}\n\n")
                elif el.name in ['ul','ol']:
                    for li in el.find_all('li', recursive=False):
                        text = re.sub(r'\s+', ' ', li.get_text()).strip()
                        if text:
                            md.append(f"- {text}\n")
                    md.append("\n")
                elif el.name == 'pre':
                    md.append(f"\n```\n{el.get_text()}\n```\n\n")
            except:
                pass

        content = ''.join(md)
        if len(content) > 1000:  # Only save if we got good content
            (output_dir / 'integrations' / 'woocommerce-complete.md').write_text(content, encoding='utf-8')
            print("  ✓ Saved complete WooCommerce documentation")

# Try to fetch Shopify, Magento, etc. documentation from alternative sources
print("\n5. Fetching platform integrations from alternative sources...")
alt_integrations = [
    ('https://support.wix.com/en/article/connecting-tilopay-as-a-payment-provider', 'wix.md'),
    ('https://help.chargeautomation.com/en/articles/8525125-tilopay-chargeautomation', 'chargeautomation.md'),
]

for url, filename in alt_integrations:
    print(f"  Fetching {filename}...")
    r = fetch(url)
    if r:
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()

        md = [f"# TiloPay Integration - {filename.split('.')[0].title()}\n\nSource: {url}\n\n"]
        main = soup.find('main') or soup.find('article') or soup.find('body')
        if main:
            for el in main.find_all(['h1','h2','h3','h4','h5','h6','p','ul','ol','pre']):
                try:
                    if el.name in ['h1','h2','h3','h4','h5','h6']:
                        level = int(el.name[1])
                        text = re.sub(r'\s+', ' ', el.get_text()).strip()
                        if text:
                            md.append(f"\n{'#'*level} {text}\n")
                    elif el.name == 'p':
                        text = re.sub(r'\s+', ' ', el.get_text()).strip()
                        if text and len(text) > 10:
                            md.append(f"{text}\n\n")
                    elif el.name in ['ul','ol']:
                        for li in el.find_all('li', recursive=False):
                            text = re.sub(r'\s+', ' ', li.get_text()).strip()
                            if text:
                                md.append(f"- {text}\n")
                        md.append("\n")
                except:
                    pass

        content = ''.join(md)
        if len(content) > 500:
            (output_dir / 'integrations' / filename).write_text(content, encoding='utf-8')
            print(f"  ✓ Saved {filename}")
    time.sleep(1)

# Try to get English user guide
print("\n6. Attempting to fetch English user guide...")
guide_urls = [
    'https://admin.tilopay.com/files/en_tilopay_payfac_user_guide.pdf',
    'https://app.tilopay.com/files/en_tilopay_payfac_user_guide.pdf',
    'https://tilopay.com/files/en_tilopay_payfac_user_guide.pdf',
]

for url in guide_urls:
    r = fetch(url)
    if r and r.status_code == 200 and 'application/pdf' in r.headers.get('content-type', ''):
        (output_dir / 'user-guide-english.pdf').write_bytes(r.content)
        print(f"  ✓ Saved English user guide")
        break

print("\n✓ Remaining documentation fetch complete!\n")
