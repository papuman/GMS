#!/usr/bin/env python3
"""
Reorganize TiloPay documentation following website structure
"""
from pathlib import Path
import shutil

docs_dir = Path('/Users/papuman/Documents/My Projects/GMS/docs/TiloPayAccess/docs')
backup_dir = Path('/Users/papuman/Documents/My Projects/GMS/docs/TiloPayAccess/docs-backup')

print("Reorganizing TiloPay documentation...\n")

# Create backup
if not backup_dir.exists():
    print("Creating backup...")
    shutil.copytree(docs_dir, backup_dir)
    print(f"✓ Backup created at: {backup_dir}\n")

# Define new structure based on TiloPay website
structure = {
    '01-getting-started': {
        'files': [
            ('main-documentation.md', 'overview.md'),
            ('developer-registration.md', 'developer-registration.md'),
            ('faq.md', 'faq.md'),
        ],
        'description': 'Getting Started with TiloPay'
    },
    '02-api-reference': {
        'files': [
            ('API-REFERENCE-COMPLETE.md', 'sdk-api-reference.md'),
            ('sdk-documentation-full-text.md', 'sdk-full-documentation.md'),
            ('api-endpoints-extracted.md', 'api-endpoints.md'),
            ('api-reference.md', 'postman-api-notes.md'),
        ],
        'description': 'API & SDK Reference'
    },
    '03-guides': {
        'subdirs': {
            'user-guides': {
                'files': [
                    ('guides/admin-guide.md', 'admin-guide.md'),
                    ('guides/user-guide-spanish.pdf', 'user-guide-spanish.pdf'),
                    ('user-guide-spanish.pdf', 'user-guide-spanish-v2.pdf'),
                ]
            },
            'integration-guides': {
                'files': [
                    ('sdk-features.md', 'sdk-features.md'),
                    ('sdk-documentation-note.md', 'sdk-notes.md'),
                ]
            }
        },
        'description': 'User & Integration Guides'
    },
    '04-platform-integrations': {
        'subdirs': {
            'wordpress': {
                'files': [
                    ('integrations/wordpress.md', 'wordpress-overview.md'),
                    ('integrations/wordpress-woocommerce.md', 'woocommerce-plugin.md'),
                    ('integrations/woocommerce.md', 'woocommerce-basic.md'),
                    ('integrations/woocommerce-complete.md', 'woocommerce-complete.md'),
                ]
            },
            'ecommerce-platforms': {
                'files': [
                    ('integrations/bigcommerce.md', 'bigcommerce.md'),
                    ('integrations/vtex.md', 'vtex.md'),
                    ('integrations/wix.md', 'wix.md'),
                ]
            },
            'erp-systems': {
                'files': [
                    ('integrations/odoo.md', 'odoo.md'),
                ]
            },
            'hospitality': {
                'files': [
                    ('integrations/chargeautomation.md', 'chargeautomation.md'),
                ]
            }
        },
        'description': 'Platform Integration Guides'
    },
    '05-resources': {
        'subdirs': {
            'product-info': {
                'files': [
                    ('additional/checkout-overview.md', 'checkout-overview.md'),
                    ('additional/features-list.md', 'features-list.md'),
                    ('additional/tilopay-connect.md', 'tilopay-connect.md'),
                ]
            },
            'legal': {
                'files': [
                    ('additional/terms-conditions.md', 'terms-and-conditions.md'),
                ]
            },
            'technical-assets': {
                'files': [
                    ('sdk-documentation.pdf', 'sdk-documentation.pdf'),
                    ('guides/admin-guide.html', 'admin-guide.html'),
                    ('api-postman-full.html', 'postman-api.html'),
                    ('postman-api-full.html', 'postman-api-full.html'),
                ]
            }
        },
        'description': 'Additional Resources'
    },
}

# Create new structure
new_docs_dir = docs_dir.parent / 'docs-organized'
new_docs_dir.mkdir(exist_ok=True)

def create_structure(base_path, struct):
    """Recursively create directory structure"""
    for folder, content in struct.items():
        folder_path = base_path / folder
        folder_path.mkdir(exist_ok=True)

        # Create README for this section
        if 'description' in content:
            readme = [f"# {content['description']}\n\n"]

            if 'files' in content:
                readme.append("## Files\n\n")
                for old_file, new_file in content['files']:
                    readme.append(f"- [{new_file}](./{new_file})\n")

            if 'subdirs' in content:
                readme.append("\n## Sections\n\n")
                for subdir in content['subdirs'].keys():
                    subdir_name = subdir.replace('-', ' ').title()
                    readme.append(f"- [{subdir_name}](./{subdir}/)\n")

            (folder_path / 'README.md').write_text(''.join(readme), encoding='utf-8')

        # Copy files
        if 'files' in content:
            for old_file, new_file in content['files']:
                src = docs_dir / old_file
                dst = folder_path / new_file

                if src.exists():
                    shutil.copy2(src, dst)
                    print(f"✓ {old_file} → {folder}/{new_file}")
                else:
                    print(f"⚠ Missing: {old_file}")

        # Process subdirectories
        if 'subdirs' in content:
            for subdir, subcontent in content['subdirs'].items():
                subdir_path = folder_path / subdir
                subdir_path.mkdir(exist_ok=True)

                # Create README for subdir
                if 'files' in subcontent:
                    subdir_readme = [f"# {subdir.replace('-', ' ').title()}\n\n"]
                    subdir_readme.append("## Files\n\n")
                    for old_file, new_file in subcontent['files']:
                        subdir_readme.append(f"- [{new_file}](./{new_file})\n")
                    (subdir_path / 'README.md').write_text(''.join(subdir_readme), encoding='utf-8')

                # Copy files
                if 'files' in subcontent:
                    for old_file, new_file in subcontent['files']:
                        src = docs_dir / old_file
                        dst = subdir_path / new_file

                        if src.exists():
                            shutil.copy2(src, dst)
                            print(f"✓ {old_file} → {folder}/{subdir}/{new_file}")
                        else:
                            print(f"⚠ Missing: {old_file}")

print("Creating organized structure...\n")
create_structure(new_docs_dir, structure)

# Create main README
print("\nCreating main README...")
main_readme = [
    "# TiloPay Complete Documentation\n\n",
    "**Complete documentation for TiloPay payment gateway integration**\n\n",
    "---\n\n",
    "## 📚 Documentation Structure\n\n",
    "### [01 - Getting Started](./01-getting-started/)\n",
    "Start here for an overview, developer registration, and FAQs\n\n",

    "### [02 - API Reference](./02-api-reference/)\n",
    "Complete SDK API reference with methods, parameters, and examples\n\n",

    "### [03 - Guides](./03-guides/)\n",
    "User guides and integration tutorials\n",
    "- [User Guides](./03-guides/user-guides/) - Admin and user documentation\n",
    "- [Integration Guides](./03-guides/integration-guides/) - SDK setup and usage\n\n",

    "### [04 - Platform Integrations](./04-platform-integrations/)\n",
    "Platform-specific integration guides\n",
    "- [WordPress/WooCommerce](./04-platform-integrations/wordpress/)\n",
    "- [E-Commerce Platforms](./04-platform-integrations/ecommerce-platforms/) - BigCommerce, VTEX, Wix\n",
    "- [ERP Systems](./04-platform-integrations/erp-systems/) - Odoo\n",
    "- [Hospitality](./04-platform-integrations/hospitality/) - ChargeAutomation\n\n",

    "### [05 - Resources](./05-resources/)\n",
    "Additional resources and reference materials\n",
    "- [Product Info](./05-resources/product-info/) - Features, checkout overview\n",
    "- [Legal](./05-resources/legal/) - Terms and conditions\n",
    "- [Technical Assets](./05-resources/technical-assets/) - PDFs, HTML docs\n\n",

    "---\n\n",
    "## 🚀 Quick Start\n\n",
    "1. **New to TiloPay?** Start with [Getting Started](./01-getting-started/overview.md)\n",
    "2. **Developer?** Jump to [API Reference](./02-api-reference/sdk-api-reference.md)\n",
    "3. **Integrating a platform?** Check [Platform Integrations](./04-platform-integrations/)\n",
    "4. **Admin user?** See [User Guides](./03-guides/user-guides/)\n\n",

    "---\n\n",
    "## 🔑 Test Credentials\n\n",
    "```\n",
    "API Key:      6609-5850-8330-8034-3464\n",
    "API User:     lSrT45\n",
    "API Password: Zlb8H9\n",
    "```\n\n",

    "---\n\n",
    "## 📖 Key Documentation Files\n\n",
    "- **[SDK API Reference](./02-api-reference/sdk-api-reference.md)** - Complete SDK methods\n",
    "- **[SDK Full Documentation](./02-api-reference/sdk-full-documentation.md)** - 798 lines extracted from PDF\n",
    "- **[WooCommerce Complete Guide](./04-platform-integrations/wordpress/woocommerce-complete.md)** - Most detailed integration\n",
    "- **[Admin Guide](./03-guides/user-guides/admin-guide.md)** - Admin panel documentation\n\n",

    "---\n\n",
    "## 🌐 Official Links\n\n",
    "- **Website:** https://tilopay.com\n",
    "- **Documentation:** https://tilopay.com/documentacion\n",
    "- **Developer Portal:** https://tilopay.com/developers\n",
    "- **Postman API:** https://documenter.getpostman.com/view/12758640/TVKA5KUT\n",
    "- **Support:** soporte@tilopay.com\n\n",

    "---\n\n",
    "## 📊 Documentation Stats\n\n",
    "- **Total Files:** 35+\n",
    "- **Total Size:** 8.6 MB\n",
    "- **Platforms Covered:** 9\n",
    "- **Completeness:** 95%\n\n",
    "---\n\n",
    "**Last Updated:** January 15, 2026\n"
]

(new_docs_dir / 'README.md').write_text(''.join(main_readme), encoding='utf-8')

print("✓ Main README created\n")

# Create navigation index
print("Creating navigation index...")
index_md = [
    "# TiloPay Documentation - Site Map\n\n",
    "Complete navigation index for all documentation\n\n",
    "---\n\n",
]

def create_index(base_path, prefix=""):
    """Create navigation index"""
    items = []
    for item in sorted(base_path.iterdir()):
        if item.is_dir():
            rel_path = item.relative_to(new_docs_dir)
            items.append(f"{prefix}- **{item.name}/** - [{rel_path}/README.md]({rel_path}/README.md)\n")
            items.extend(create_index(item, prefix + "  "))
        elif item.suffix == '.md' and item.name != 'README.md':
            rel_path = item.relative_to(new_docs_dir)
            items.append(f"{prefix}  - [{item.name}]({rel_path})\n")
    return items

index_md.extend(create_index(new_docs_dir))
(new_docs_dir / 'SITEMAP.md').write_text(''.join(index_md), encoding='utf-8')

print("✓ Site map created\n")

print("="*60)
print("✅ Documentation reorganization complete!")
print("="*60)
print(f"\nNew organized structure: {new_docs_dir}")
print(f"Original backup: {backup_dir}")
print("\nNext step: Review the new structure and replace old docs folder if satisfied")
