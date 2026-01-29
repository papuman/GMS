#!/usr/bin/env python3
"""
Comprehensive Database and Module Installation Validation
Checks module status, database tables, file synchronization, and dependencies
"""

import os
import subprocess
import json
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{text:^80}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text):
    print(f"  {text}")

def run_db_query(query):
    """Run a PostgreSQL query in the Docker container"""
    try:
        result = subprocess.run(
            ['docker', 'exec', 'gms_postgres', 'psql', '-U', 'odoo', '-d', 'gms_validation', '-t', '-c', query],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print_error(f"Database query failed: {e}")
        return None

def check_module_installation():
    """Check if l10n_cr_einvoice module is installed"""
    print_header("MODULE INSTALLATION STATUS")
    
    query = "SELECT name, state, latest_version FROM ir_module_module WHERE name = 'l10n_cr_einvoice';"
    result = run_db_query(query)
    
    if result and 'installed' in result:
        print_success(f"Module installed: {result}")
        return True
    else:
        print_error("Module not installed or not found")
        return False

def check_dependencies():
    """Check if dependency modules are installed"""
    print_header("DEPENDENCY MODULES")
    
    modules = ['base', 'account', 'l10n_cr', 'sale', 'product']
    all_ok = True
    
    for module in modules:
        query = f"SELECT state FROM ir_module_module WHERE name = '{module}';"
        result = run_db_query(query)
        
        if result and 'installed' in result:
            print_success(f"{module}: installed")
        else:
            print_error(f"{module}: NOT installed")
            all_ok = False
    
    return all_ok

def check_database_tables():
    """Check if required tables exist"""
    print_header("DATABASE TABLES")
    
    query = "\\dt l10n_cr*"
    result = run_db_query(query)
    
    if result and 'l10n_cr_einvoice_document' in result:
        print_success("l10n_cr_einvoice_document table exists")
        
        # Check fields
        query = "\\d l10n_cr_einvoice_document"
        result = run_db_query(query)
        
        required_fields = ['clave', 'state', 'xml_content', 'signed_xml', 'hacienda_response']
        for field in required_fields:
            if field in result:
                print_success(f"  Field '{field}' exists")
            else:
                print_error(f"  Field '{field}' MISSING")
        
        return True
    else:
        print_error("l10n_cr_einvoice_document table NOT found")
        return False

def check_account_move_integration():
    """Check if account_move table has einvoice fields"""
    print_header("ACCOUNT.MOVE INTEGRATION")
    
    query = "\\d account_move"
    result = run_db_query(query)
    
    required_fields = ['l10n_cr_einvoice_id', 'l10n_cr_einvoice_state', 'l10n_cr_clave', 'l10n_cr_requires_einvoice']
    all_ok = True
    
    for field in required_fields:
        if result and field in result:
            print_success(f"Field '{field}' exists")
        else:
            print_error(f"Field '{field}' MISSING")
            all_ok = False
    
    return all_ok

def check_sequences():
    """Check if sequences are created"""
    print_header("SEQUENCES")
    
    query = "SELECT code, name, number_next FROM ir_sequence WHERE code LIKE '%l10n_cr%' OR code LIKE '%einvoice%';"
    result = run_db_query(query)
    
    if result:
        lines = [l.strip() for l in result.split('\n') if l.strip()]
        for line in lines:
            print_success(f"Sequence: {line}")
        return len(lines) >= 4  # Expecting at least 4 sequences
    else:
        print_error("No sequences found")
        return False

def check_email_templates():
    """Check if email templates are loaded"""
    print_header("EMAIL TEMPLATES")
    
    query = "SELECT name, model FROM mail_template WHERE model LIKE '%einvoice%' OR model LIKE '%l10n_cr%';"
    result = run_db_query(query)
    
    if result and result.strip():
        lines = [l.strip() for l in result.split('\n') if l.strip()]
        for line in lines:
            print_success(f"Template: {line}")
        return True
    else:
        print_warning("No email templates found (Phase 5 may not be deployed)")
        return False

def check_menus():
    """Check if menu items are visible"""
    print_header("MENU ITEMS")
    
    query = "SELECT name::text FROM ir_ui_menu WHERE name::text LIKE '%Electronic%' OR name::text LIKE '%Hacienda%';"
    result = run_db_query(query)
    
    if result:
        lines = [l.strip() for l in result.split('\n') if l.strip()]
        for line in lines:
            print_success(f"Menu: {line}")
        return len(lines) > 0
    else:
        print_error("No menus found")
        return False

def check_python_dependencies():
    """Check if Python dependencies are installed"""
    print_header("PYTHON DEPENDENCIES")
    
    try:
        result = subprocess.run(
            ['docker', 'exec', 'gms_odoo', 'pip', 'list'],
            capture_output=True,
            text=True,
            check=True
        )
        
        required_packages = {
            'qrcode': '7.4',
            'cryptography': '41.0',
            'lxml': '5.2'
        }
        
        all_ok = True
        for package, min_version in required_packages.items():
            if package in result.stdout:
                print_success(f"{package} installed")
            else:
                print_error(f"{package} NOT installed")
                all_ok = False
        
        return all_ok
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to check Python dependencies: {e}")
        return False

def compare_directories():
    """Compare l10n_cr_einvoice directories"""
    print_header("FILE SYNCHRONIZATION")
    
    source = Path('/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/l10n_cr_einvoice')
    deployed = Path('/Users/javycarrillo/Library/CloudStorage/Dropbox/AI/Apps/GMS/odoo/addons/l10n_cr_einvoice')
    
    # Check Phase 5 files
    phase5_files = [
        'models/qr_generator.py',
        'data/email_templates.xml',
        'views/einvoice_dashboard_views.xml',
        'views/einvoice_wizard_views.xml',
        'views/res_company_views.xml'
    ]
    
    print_info("Phase 5 Files:")
    for file in phase5_files:
        source_file = source / file
        deployed_file = deployed / file
        
        if source_file.exists() and deployed_file.exists():
            print_success(f"  {file} - Present in both")
        elif source_file.exists() and not deployed_file.exists():
            print_error(f"  {file} - MISSING in deployed")
        elif not source_file.exists():
            print_warning(f"  {file} - Not in source")
    
    # Compare key files
    print_info("\nKey File Comparison:")
    key_files = [
        'models/hacienda_api.py',
        'models/einvoice_document.py',
        'models/__init__.py',
        '__manifest__.py'
    ]
    
    for file in key_files:
        source_file = source / file
        deployed_file = deployed / file
        
        if source_file.exists() and deployed_file.exists():
            # Compare file sizes
            source_size = source_file.stat().st_size
            deployed_size = deployed_file.stat().st_size
            
            if source_size == deployed_size:
                print_success(f"  {file} - Identical ({source_size} bytes)")
            else:
                print_warning(f"  {file} - DIFFERENT (source: {source_size}, deployed: {deployed_size})")
        else:
            print_error(f"  {file} - Missing in one location")

def check_company_configuration():
    """Check company configuration for einvoice"""
    print_header("COMPANY CONFIGURATION")
    
    query = "SELECT name, l10n_cr_hacienda_env, l10n_cr_auto_generate_einvoice, l10n_cr_auto_submit_einvoice, l10n_cr_auto_send_email FROM res_company LIMIT 5;"
    result = run_db_query(query)
    
    if result:
        print_success("Company configuration:")
        print_info(result)
        return True
    else:
        print_error("Failed to retrieve company configuration")
        return False

def main():
    """Main validation function"""
    print("\n" + "="*80)
    print("COMPREHENSIVE MODULE INSTALLATION VALIDATION".center(80))
    print("="*80 + "\n")
    
    results = {
        'Module Installation': check_module_installation(),
        'Dependency Modules': check_dependencies(),
        'Database Tables': check_database_tables(),
        'Account Move Integration': check_account_move_integration(),
        'Sequences': check_sequences(),
        'Email Templates': check_email_templates(),
        'Menu Items': check_menus(),
        'Python Dependencies': check_python_dependencies(),
        'Company Configuration': check_company_configuration()
    }
    
    # File synchronization (doesn't affect pass/fail)
    compare_directories()
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    passed = sum(results.values())
    total = len(results)
    
    for check, status in results.items():
        if status:
            print_success(f"{check}")
        else:
            print_error(f"{check}")
    
    print(f"\n{BLUE}Results: {passed}/{total} checks passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}✓ ALL VALIDATIONS PASSED{RESET}\n")
        return 0
    else:
        print(f"\n{RED}✗ SOME VALIDATIONS FAILED{RESET}\n")
        return 1

if __name__ == '__main__':
    exit(main())
