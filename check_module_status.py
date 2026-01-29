#!/usr/bin/env python3
import xmlrpc.client
import json

url = "http://localhost:8069"
db = "gms_validation"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

results = {}

# Check module installation
module_ids = models.execute_kw(db, uid, password, 'ir.module.module', 'search_read',
    [[('name', '=', 'l10n_cr_einvoice')]],
    {'fields': ['name', 'state', 'installed_version', 'latest_version']})

if module_ids:
    results['module_status'] = module_ids[0]
    
    # Get dependencies
    dep_ids = models.execute_kw(db, uid, password, 'ir.module.module.dependency', 'search_read',
        [[('module_id', '=', module_ids[0]['id'])]],
        {'fields': ['name', 'state']})
    results['dependencies'] = dep_ids
else:
    results['module_status'] = {'error': 'Module not found'}

# Check key dependency modules
dep_modules = ['base', 'account', 'l10n_cr', 'sale', 'product']
results['dependency_modules'] = []
for dep_name in dep_modules:
    dep = models.execute_kw(db, uid, password, 'ir.module.module', 'search_read',
        [[('name', '=', dep_name)]],
        {'fields': ['name', 'state']})
    if dep:
        results['dependency_modules'].append(dep[0])

# Check models exist
results['models'] = {}

# Check document types
try:
    doc_types = models.execute_kw(db, uid, password, 'l10n_cr_einvoice.document_type', 'search_count', [[]])
    results['models']['l10n_cr_einvoice.document_type'] = {'exists': True, 'count': doc_types}
except Exception as e:
    results['models']['l10n_cr_einvoice.document_type'] = {'exists': False, 'error': str(e)}

# Check hacienda responses
try:
    responses = models.execute_kw(db, uid, password, 'l10n_cr_einvoice.hacienda_response', 'search_count', [[]])
    results['models']['l10n_cr_einvoice.hacienda_response'] = {'exists': True, 'count': responses}
except Exception as e:
    results['models']['l10n_cr_einvoice.hacienda_response'] = {'exists': False, 'error': str(e)}

# Check sequences
sequences = models.execute_kw(db, uid, password, 'ir.sequence', 'search_read',
    [[('code', 'like', 'l10n_cr')]],
    {'fields': ['code', 'name', 'number_next']})
results['sequences'] = sequences

# Check email templates
templates = models.execute_kw(db, uid, password, 'mail.template', 'search_read',
    [[('model', 'like', 'einvoice')]],
    {'fields': ['name', 'model']})
results['email_templates'] = templates

# Check menus
menus = models.execute_kw(db, uid, password, 'ir.ui.menu', 'search_read',
    [[('name', 'like', 'Hacienda')]],
    {'fields': ['name', 'parent_id']})
results['menus'] = menus

print(json.dumps(results, indent=2))
