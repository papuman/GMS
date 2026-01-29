#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Synchronization Check for l10n_cr_einvoice Module

Verifies that all required files are present and synchronized between:
- Main location: l10n_cr_einvoice/
- Odoo location: odoo/addons/l10n_cr_einvoice/

Author: GMS Development Team
Date: 2025-12-28
"""

import os
import json
from datetime import datetime
from pathlib import Path

# ANSI color codes
class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

BASE_PATH = '/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS'
MAIN_LOC = f'{BASE_PATH}/l10n_cr_einvoice'
ODOO_LOC = f'{BASE_PATH}/odoo/addons/l10n_cr_einvoice'

# Required files by phase
FILES_BY_PHASE = {
    'Phase 1 & 2': {
        'models': [
            '__init__.py',
            'einvoice_document.py',
            'account_move.py',
            'xml_generator.py',
            'xsd_validator.py',
            'res_company.py',
            'res_config_settings.py',
        ]
    },
    'Phase 3': {
        'models': [
            'certificate_manager.py',
            'xml_signer.py',
            'hacienda_api.py',
        ]
    },
    'Phase 5': {
        'models': [
            'qr_generator.py',
        ],
        'reports': [
            '__init__.py',
            'einvoice_report_templates.xml',
        ]
    },
    'Module Core': {
        '.': [
            '__init__.py',
            '__manifest__.py',
        ]
    }
}

def check_file_exists(location, subdir, filename):
    """Check if file exists at location/subdir/filename"""
    if subdir == '.':
        path = f'{location}/{filename}'
    else:
        path = f'{location}/{subdir}/{filename}'
    return os.path.exists(path)

def get_file_size(location, subdir, filename):
    """Get file size in bytes"""
    if subdir == '.':
        path = f'{location}/{filename}'
    else:
        path = f'{location}/{subdir}/{filename}'

    try:
        return os.path.getsize(path)
    except:
        return 0

def get_file_mtime(location, subdir, filename):
    """Get file modification time"""
    if subdir == '.':
        path = f'{location}/{filename}'
    else:
        path = f'{location}/{subdir}/{filename}'

    try:
        return os.path.getmtime(path)
    except:
        return 0

def compare_files():
    """Compare files between main and odoo locations"""

    print(f"\n{Color.BOLD}{Color.CYAN}{'='*80}{Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}FILE SYNCHRONIZATION CHECK{Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}l10n_cr_einvoice Module{Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}{'='*80}{Color.END}\n")

    results = {
        'timestamp': datetime.now().isoformat(),
        'main_location': MAIN_LOC,
        'odoo_location': ODOO_LOC,
        'files': {},
        'summary': {}
    }

    total_files = 0
    synced_files = 0
    main_only = 0
    odoo_only = 0
    missing_files = 0
    size_mismatch = 0

    for phase, subdirs in FILES_BY_PHASE.items():
        print(f"{Color.BOLD}{Color.MAGENTA}{phase}{Color.END}")
        print("-" * 80)

        for subdir, files in subdirs.items():
            for filename in files:
                total_files += 1

                # Check existence
                main_exists = check_file_exists(MAIN_LOC, subdir, filename)
                odoo_exists = check_file_exists(ODOO_LOC, subdir, filename)

                # Get sizes
                main_size = get_file_size(MAIN_LOC, subdir, filename)
                odoo_size = get_file_size(ODOO_LOC, subdir, filename)

                # Get modification times
                main_mtime = get_file_mtime(MAIN_LOC, subdir, filename)
                odoo_mtime = get_file_mtime(ODOO_LOC, subdir, filename)

                # Display path
                file_path = f"{subdir}/{filename}" if subdir != '.' else filename

                # Determine status
                if main_exists and odoo_exists:
                    if main_size == odoo_size:
                        print(f"  {Color.GREEN}✓{Color.END} {file_path:50} [SYNCED]")
                        synced_files += 1
                        status = 'synced'
                    else:
                        time_diff = main_mtime - odoo_mtime
                        if time_diff > 0:
                            print(f"  {Color.YELLOW}⚠{Color.END} {file_path:50} [SIZE MISMATCH - Main newer]")
                        else:
                            print(f"  {Color.YELLOW}⚠{Color.END} {file_path:50} [SIZE MISMATCH - Odoo newer]")
                        print(f"      Main: {main_size:,} bytes | Odoo: {odoo_size:,} bytes")
                        size_mismatch += 1
                        status = 'size_mismatch'

                elif main_exists and not odoo_exists:
                    print(f"  {Color.YELLOW}⚠{Color.END} {file_path:50} [MAIN ONLY - needs copy]")
                    print(f"      Main: {main_size:,} bytes")
                    main_only += 1
                    status = 'main_only'

                elif not main_exists and odoo_exists:
                    print(f"  {Color.YELLOW}⚠{Color.END} {file_path:50} [ODOO ONLY]")
                    print(f"      Odoo: {odoo_size:,} bytes")
                    odoo_only += 1
                    status = 'odoo_only'

                else:
                    print(f"  {Color.RED}✗{Color.END} {file_path:50} [MISSING FROM BOTH]")
                    missing_files += 1
                    status = 'missing'

                # Store results
                results['files'][file_path] = {
                    'phase': phase,
                    'status': status,
                    'main_exists': main_exists,
                    'odoo_exists': odoo_exists,
                    'main_size': main_size,
                    'odoo_size': odoo_size,
                    'main_mtime': datetime.fromtimestamp(main_mtime).isoformat() if main_mtime else None,
                    'odoo_mtime': datetime.fromtimestamp(odoo_mtime).isoformat() if odoo_mtime else None,
                }

        print()

    # Summary
    print(f"{Color.BOLD}{Color.CYAN}{'='*80}{Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}SUMMARY{Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}{'='*80}{Color.END}\n")

    print(f"Total Files Checked: {total_files}")
    print(f"{Color.GREEN}Synced:{Color.END} {synced_files}")
    print(f"{Color.YELLOW}Size Mismatch:{Color.END} {size_mismatch}")
    print(f"{Color.YELLOW}Main Only:{Color.END} {main_only}")
    print(f"{Color.YELLOW}Odoo Only:{Color.END} {odoo_only}")
    print(f"{Color.RED}Missing:{Color.END} {missing_files}")

    sync_percentage = (synced_files / total_files * 100) if total_files > 0 else 0
    print(f"\n{Color.BOLD}Sync Status: {sync_percentage:.1f}%{Color.END}")

    results['summary'] = {
        'total_files': total_files,
        'synced': synced_files,
        'size_mismatch': size_mismatch,
        'main_only': main_only,
        'odoo_only': odoo_only,
        'missing': missing_files,
        'sync_percentage': sync_percentage
    }

    # Actions needed
    if main_only > 0 or size_mismatch > 0:
        print(f"\n{Color.BOLD}{Color.YELLOW}ACTIONS NEEDED{Color.END}")
        print("-" * 80)

        if main_only > 0:
            print(f"\n{Color.YELLOW}Files to copy from main to odoo location:{Color.END}")
            for file_path, info in results['files'].items():
                if info['status'] == 'main_only':
                    print(f"  - {file_path}")

            print(f"\n{Color.CYAN}Copy command:{Color.END}")
            print(f"  cp -v {MAIN_LOC}/models/qr_generator.py {ODOO_LOC}/models/")
            print(f"  cp -v {MAIN_LOC}/reports/einvoice_report_templates.xml {ODOO_LOC}/reports/")

        if size_mismatch > 0:
            print(f"\n{Color.YELLOW}Files with size mismatch (review before syncing):{Color.END}")
            for file_path, info in results['files'].items():
                if info['status'] == 'size_mismatch':
                    print(f"  - {file_path}")
                    print(f"    Main: {info['main_size']:,} bytes ({info['main_mtime']})")
                    print(f"    Odoo: {info['odoo_size']:,} bytes ({info['odoo_mtime']})")

    # Integration status
    print(f"\n{Color.BOLD}{Color.CYAN}INTEGRATION STATUS{Color.END}")
    print("-" * 80)

    phase_status = {}
    for phase in ['Phase 1 & 2', 'Phase 3', 'Phase 5']:
        phase_files = [f for f, info in results['files'].items() if info['phase'] == phase]
        phase_synced = [f for f, info in results['files'].items()
                       if info['phase'] == phase and info['status'] == 'synced']

        if len(phase_files) > 0:
            phase_pct = (len(phase_synced) / len(phase_files) * 100)
            if phase_pct == 100:
                status_icon = f"{Color.GREEN}✓{Color.END}"
            elif phase_pct >= 50:
                status_icon = f"{Color.YELLOW}⚠{Color.END}"
            else:
                status_icon = f"{Color.RED}✗{Color.END}"

            print(f"{status_icon} {phase:20} {phase_pct:5.1f}% ({len(phase_synced)}/{len(phase_files)})")
            phase_status[phase] = {
                'percentage': phase_pct,
                'synced': len(phase_synced),
                'total': len(phase_files)
            }

    results['phase_status'] = phase_status

    # Save results
    results_file = f'{BASE_PATH}/file_sync_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{Color.GREEN}Results saved to: {results_file}{Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}{'='*80}{Color.END}\n")

    return results

if __name__ == '__main__':
    print(f"{Color.BOLD}{Color.CYAN}")
    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║          File Synchronization Check - l10n_cr_einvoice               ║")
    print("╚═══════════════════════════════════════════════════════════════════════╝")
    print(f"{Color.END}")

    results = compare_files()

    # Exit code based on sync status
    if results['summary']['synced'] == results['summary']['total_files']:
        exit(0)  # All synced
    else:
        exit(1)  # Action needed
