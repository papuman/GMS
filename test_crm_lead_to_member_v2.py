#!/usr/bin/env python3
"""
CRM Lead-to-Member Conversion Test Script for GMS Validation System (Odoo 19)

This script validates the complete CRM workflow for converting leads to paying gym members.
Compatible with Odoo 19.

Database: gms_validation
URL: http://localhost:8070
Credentials: admin/admin
"""

import sys
import json
from datetime import datetime, timedelta

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(message):
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.OKBLUE}→ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

class CRMTestResults:
    def __init__(self):
        self.test_scenarios = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.warnings = []
        self.recommendations = []
        self.crm_config = {}
        self.pipeline_stages = []
        self.lead_sources = []

    def add_test(self, name, status, details=None, error=None):
        self.total_tests += 1
        if status == 'passed':
            self.passed_tests += 1
        else:
            self.failed_tests += 1

        self.test_scenarios.append({
            'name': name,
            'status': status,
            'details': details,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })

    def add_warning(self, warning):
        self.warnings.append(warning)

    def add_recommendation(self, recommendation):
        self.recommendations.append(recommendation)

# Initialize test results
results = CRMTestResults()

print_header("GMS CRM Lead-to-Member Conversion Test (Odoo 19)")
print_info(f"Database: gms_validation")
print_info(f"URL: http://localhost:8070")
print_info(f"Test started at: {datetime.now()}")

# =============================================================================
# PART 1: Environment Setup and Configuration Discovery
# =============================================================================

print_header("PART 1: Discovering CRM Configuration")

try:
    # Get CRM module status
    print_info("Checking CRM module installation...")
    crm_module = env['ir.module.module'].search([('name', '=', 'crm')])
    sale_crm_module = env['ir.module.module'].search([('name', '=', 'sale_crm')])

    if crm_module and crm_module.state == 'installed':
        print_success(f"CRM module installed (version: {crm_module.latest_version})")
        results.crm_config['crm_module'] = 'installed'
    else:
        print_error("CRM module not installed!")
        results.add_test("CRM Module Check", "failed", error="CRM module not installed")
        sys.exit(1)

    if sale_crm_module and sale_crm_module.state == 'installed':
        print_success(f"Sales CRM module installed (version: {sale_crm_module.latest_version})")
        results.crm_config['sale_crm_module'] = 'installed'
    else:
        print_warning("Sales CRM module not installed")
        results.add_warning("Sales CRM module not installed - limited functionality")
        results.crm_config['sale_crm_module'] = 'not_installed'

    results.add_test("CRM Module Check", "passed",
                    details=f"CRM installed, Sale CRM: {results.crm_config['sale_crm_module']}")

except Exception as e:
    print_error(f"Error checking modules: {e}")
    results.add_test("CRM Module Check", "failed", error=str(e))

# Check CRM Teams
try:
    print_info("\nDiscovering CRM Teams/Sales Channels...")
    crm_teams = env['crm.team'].search([])

    if crm_teams:
        print_success(f"Found {len(crm_teams)} CRM team(s):")
        for team in crm_teams:
            print_info(f"  - {team.name} (ID: {team.id})")
        results.crm_config['crm_teams'] = len(crm_teams)
    else:
        print_warning("No CRM teams found - creating default team")
        default_team = env['crm.team'].create({
            'name': 'Gym Sales',
        })
        print_success(f"Created default team: {default_team.name}")
        crm_teams = default_team
        results.crm_config['crm_teams'] = 1

    results.add_test("CRM Teams Discovery", "passed",
                    details=f"Found/created {results.crm_config['crm_teams']} team(s)")

except Exception as e:
    print_error(f"Error discovering CRM teams: {e}")
    results.add_test("CRM Teams Discovery", "failed", error=str(e))

# Check CRM Stages
try:
    print_info("\nDiscovering CRM Pipeline Stages...")
    stages = env['crm.stage'].search([], order='sequence')

    print_success(f"Found {len(stages)} stage(s):")
    for stage in stages:
        print_info(f"  - {stage.name} (Seq: {stage.sequence})")
        results.pipeline_stages.append({
            'id': stage.id,
            'name': stage.name,
            'sequence': stage.sequence,
        })

    results.add_test("Pipeline Stages Discovery", "passed",
                    details=f"Discovered {len(stages)} stages")

except Exception as e:
    print_error(f"Error discovering pipeline stages: {e}")
    results.add_test("Pipeline Stages Discovery", "failed", error=str(e))

# Check Lead Sources
try:
    print_info("\nDiscovering Lead Sources...")
    lead_sources = env['utm.source'].search([])

    print_success(f"Found {len(lead_sources)} lead source(s)")

    # Create gym-specific lead sources if they don't exist
    gym_sources = ['Website', 'Walk-in', 'Phone', 'Referral', 'Social Media', 'Email Campaign']
    created_sources = []

    for source_name in gym_sources:
        existing = env['utm.source'].search([('name', '=', source_name)], limit=1)
        if not existing:
            new_source = env['utm.source'].create({'name': source_name})
            created_sources.append(source_name)
            print_success(f"Created lead source: {source_name}")
            results.lead_sources.append(source_name)

    if created_sources:
        results.crm_config['created_sources'] = created_sources

    results.add_test("Lead Sources Discovery", "passed",
                    details=f"Found/created sources")

except Exception as e:
    print_error(f"Error managing lead sources: {e}")
    results.add_test("Lead Sources Discovery", "failed", error=str(e))

# Check products for memberships
try:
    print_info("\nDiscovering Membership Products...")
    # In Odoo 19, use 'type' field instead of 'detailed_type'
    membership_products = env['product.product'].search([
        ('type', '=', 'service'),
        ('name', 'ilike', 'membership')
    ])

    if membership_products:
        print_success(f"Found {len(membership_products)} membership product(s):")
        for product in membership_products:
            print_info(f"  - {product.name} (${product.list_price})")
        results.crm_config['membership_products'] = len(membership_products)
    else:
        print_warning("No membership products found - will create test products")
        results.crm_config['membership_products'] = 0

    results.add_test("Membership Products Check", "passed",
                    details=f"Found {results.crm_config['membership_products']} products")

except Exception as e:
    print_error(f"Error checking products: {e}")
    results.add_test("Membership Products Check", "failed", error=str(e))

# =============================================================================
# PART 2: Test Scenario 1 - Walk-in Inquiry → Monthly Membership Sale
# =============================================================================

print_header("PART 2: Test Scenario 1 - Walk-in Inquiry → Monthly Membership")

scenario1_data = {
    'name': 'Test Scenario 1',
    'lead': None,
    'opportunity': None,
    'partner': None,
    'sale_order': None,
    'status': 'pending'
}

try:
    # Step 1: Create a lead from walk-in inquiry
    print_info("Step 1: Creating lead from walk-in inquiry...")

    walk_in_source = env['utm.source'].search([('name', '=', 'Walk-in')], limit=1)
    default_team = crm_teams[0] if crm_teams else env['crm.team'].search([], limit=1)

    lead_data = {
        'name': 'Monthly Membership Inquiry - John Doe',
        'type': 'lead',
        'contact_name': 'John Doe',
        'email_from': 'john.doe@example.com',
        'phone': '+1-555-0101',
        'description': 'Walk-in inquiry about monthly membership options.',
        'team_id': default_team.id,
        'source_id': walk_in_source.id if walk_in_source else False,
        'expected_revenue': 50.00,
    }

    lead1 = env['crm.lead'].create(lead_data)
    scenario1_data['lead'] = lead1

    print_success(f"Created lead: {lead1.name} (ID: {lead1.id})")
    print_info(f"  Contact: {lead1.contact_name}")
    print_info(f"  Email: {lead1.email_from}")
    print_info(f"  Source: {lead1.source_id.name if lead1.source_id else 'None'}")

    # Step 2: Convert lead to opportunity
    print_info("\nStep 2: Converting lead to opportunity...")

    convert_wizard = env['crm.lead2opportunity.partner'].with_context(
        active_model='crm.lead',
        active_id=lead1.id,
        active_ids=lead1.ids
    ).create({
        'name': 'convert',
        'action': 'create',
        'user_id': env.user.id,
    })

    convert_wizard.action_apply()
    lead1 = env['crm.lead'].browse(lead1.id)

    if lead1.type == 'opportunity':
        print_success(f"Converted to opportunity")
        print_info(f"  Partner: {lead1.partner_id.name if lead1.partner_id else 'None'}")
        print_info(f"  Stage: {lead1.stage_id.name}")
        scenario1_data['opportunity'] = lead1
        scenario1_data['partner'] = lead1.partner_id
    else:
        raise Exception("Lead not converted to opportunity")

    # Step 3: Create membership product
    print_info("\nStep 3: Creating monthly membership product...")

    monthly_membership = env['product.product'].search([
        ('name', '=', 'Monthly Membership - Test')
    ], limit=1)

    if not monthly_membership:
        monthly_membership = env['product.product'].create({
            'name': 'Monthly Membership - Test',
            'type': 'service',
            'list_price': 50.00,
            'description': 'Test monthly gym membership',
        })
        print_success(f"Created product: {monthly_membership.name}")

    print_success(f"Using product: {monthly_membership.name} (${monthly_membership.list_price})")

    # Step 4: Create sale order
    print_info("\nStep 4: Creating sale order...")

    sale_order = env['sale.order'].create({
        'partner_id': lead1.partner_id.id,
        'opportunity_id': lead1.id,
    })

    # Create order line with proper name field
    env['sale.order.line'].create({
        'order_id': sale_order.id,
        'product_id': monthly_membership.id,
        'name': monthly_membership.name,  # Explicitly set name
        'product_uom_qty': 1,
        'price_unit': monthly_membership.list_price,
    })

    scenario1_data['sale_order'] = sale_order

    print_success(f"Created sale order: {sale_order.name} (ID: {sale_order.id})")
    print_info(f"  Customer: {sale_order.partner_id.name}")
    print_info(f"  Amount Total: ${sale_order.amount_total}")

    # Confirm sale order
    sale_order.action_confirm()
    print_success(f"Sale order confirmed - State: {sale_order.state}")

    scenario1_data['status'] = 'completed'
    print_success("\n✓ Scenario 1 completed successfully!")
    results.test_scenarios.append(scenario1_data)
    results.add_test("Scenario 1: Walk-in → Monthly Membership", "passed",
                   details={
                       'lead_id': lead1.id,
                       'partner_id': lead1.partner_id.id,
                       'sale_order_id': sale_order.id,
                       'amount': float(sale_order.amount_total)
                   })

except Exception as e:
    print_error(f"\n✗ Scenario 1 failed: {e}")
    scenario1_data['status'] = 'failed'
    scenario1_data['error'] = str(e)
    results.test_scenarios.append(scenario1_data)
    results.add_test("Scenario 1: Walk-in → Monthly Membership", "failed", error=str(e))
    env.cr.rollback()  # Rollback on error

# =============================================================================
# PART 3: Test Scenario 2 - Website Lead → Annual Membership Sale
# =============================================================================

print_header("PART 3: Test Scenario 2 - Website Lead → Annual Membership")

scenario2_data = {
    'name': 'Test Scenario 2',
    'lead': None,
    'opportunity': None,
    'partner': None,
    'sale_order': None,
    'status': 'pending'
}

try:
    print_info("Step 1: Creating lead from website inquiry...")

    website_source = env['utm.source'].search([('name', '=', 'Website')], limit=1)

    lead2 = env['crm.lead'].create({
        'name': 'Annual Membership Inquiry - Sarah Smith',
        'type': 'lead',
        'contact_name': 'Sarah Smith',
        'email_from': 'sarah.smith@example.com',
        'phone': '+1-555-0102',
        'description': 'Website contact form - interested in annual membership.',
        'team_id': default_team.id,
        'source_id': website_source.id if website_source else False,
        'expected_revenue': 500.00,
    })

    scenario2_data['lead'] = lead2
    print_success(f"Created lead: {lead2.name} (ID: {lead2.id})")

    # Convert to opportunity
    print_info("\nStep 2: Converting to opportunity...")

    convert_wizard2 = env['crm.lead2opportunity.partner'].with_context(
        active_model='crm.lead',
        active_id=lead2.id,
        active_ids=lead2.ids
    ).create({
        'name': 'convert',
        'action': 'create',
        'user_id': env.user.id,
    })

    convert_wizard2.action_apply()
    lead2 = env['crm.lead'].browse(lead2.id)

    print_success(f"Converted to opportunity")
    scenario2_data['opportunity'] = lead2
    scenario2_data['partner'] = lead2.partner_id

    # Create annual membership product
    print_info("\nStep 3: Creating annual membership product...")

    annual_membership = env['product.product'].search([
        ('name', '=', 'Annual Membership - Test')
    ], limit=1)

    if not annual_membership:
        annual_membership = env['product.product'].create({
            'name': 'Annual Membership - Test',
            'type': 'service',
            'list_price': 500.00,
            'description': 'Test annual gym membership (12 months)',
        })

    print_success(f"Using product: {annual_membership.name}")

    # Create sale order
    print_info("\nStep 4: Creating sale order...")

    sale_order2 = env['sale.order'].create({
        'partner_id': lead2.partner_id.id,
        'opportunity_id': lead2.id,
    })

    env['sale.order.line'].create({
        'order_id': sale_order2.id,
        'product_id': annual_membership.id,
        'name': annual_membership.name,
        'product_uom_qty': 1,
        'price_unit': annual_membership.list_price,
    })

    scenario2_data['sale_order'] = sale_order2
    print_success(f"Created sale order: {sale_order2.name}")

    sale_order2.action_confirm()
    print_success(f"Sale order confirmed")

    scenario2_data['status'] = 'completed'
    print_success("\n✓ Scenario 2 completed successfully!")
    results.test_scenarios.append(scenario2_data)
    results.add_test("Scenario 2: Website → Annual Membership", "passed",
                   details={
                       'lead_id': lead2.id,
                       'sale_order_id': sale_order2.id,
                       'amount': float(sale_order2.amount_total)
                   })

except Exception as e:
    print_error(f"\n✗ Scenario 2 failed: {e}")
    scenario2_data['status'] = 'failed'
    scenario2_data['error'] = str(e)
    results.test_scenarios.append(scenario2_data)
    results.add_test("Scenario 2: Website → Annual Membership", "failed", error=str(e))
    env.cr.rollback()

# =============================================================================
# PART 4: Test Scenario 3 - Phone Inquiry → Family Memberships
# =============================================================================

print_header("PART 4: Test Scenario 3 - Phone Inquiry → Family Memberships")

scenario3_data = {
    'name': 'Test Scenario 3',
    'lead': None,
    'opportunity': None,
    'partner': None,
    'sale_order': None,
    'status': 'pending'
}

try:
    print_info("Step 1: Creating lead from phone inquiry...")

    phone_source = env['utm.source'].search([('name', '=', 'Phone')], limit=1)

    lead3 = env['crm.lead'].create({
        'name': 'Family Membership Inquiry - Johnson Family',
        'type': 'lead',
        'contact_name': 'Michael Johnson',
        'email_from': 'mjohnson@example.com',
        'phone': '+1-555-0103',
        'description': 'Phone inquiry - needs 3 family memberships.',
        'team_id': default_team.id,
        'source_id': phone_source.id if phone_source else False,
        'expected_revenue': 150.00,
    })

    scenario3_data['lead'] = lead3
    print_success(f"Created lead: {lead3.name} (ID: {lead3.id})")

    # Convert to opportunity
    print_info("\nStep 2: Converting to opportunity...")

    convert_wizard3 = env['crm.lead2opportunity.partner'].with_context(
        active_model='crm.lead',
        active_id=lead3.id,
        active_ids=lead3.ids
    ).create({
        'name': 'convert',
        'action': 'create',
        'user_id': env.user.id,
    })

    convert_wizard3.action_apply()
    lead3 = env['crm.lead'].browse(lead3.id)

    print_success(f"Converted to opportunity")
    scenario3_data['opportunity'] = lead3
    scenario3_data['partner'] = lead3.partner_id

    # Create sale order with multiple memberships
    print_info("\nStep 3: Creating sale order with 3 memberships...")

    sale_order3 = env['sale.order'].create({
        'partner_id': lead3.partner_id.id,
        'opportunity_id': lead3.id,
    })

    env['sale.order.line'].create({
        'order_id': sale_order3.id,
        'product_id': monthly_membership.id,
        'name': f"{monthly_membership.name} (Family - 3 members)",
        'product_uom_qty': 3,
        'price_unit': monthly_membership.list_price,
    })

    scenario3_data['sale_order'] = sale_order3
    print_success(f"Created sale order: {sale_order3.name}")
    print_info(f"  Quantity: 3 memberships")
    print_info(f"  Total: ${sale_order3.amount_total}")

    sale_order3.action_confirm()
    print_success(f"Sale order confirmed")

    scenario3_data['status'] = 'completed'
    print_success("\n✓ Scenario 3 completed successfully!")
    results.test_scenarios.append(scenario3_data)
    results.add_test("Scenario 3: Phone → Family Memberships", "passed",
                   details={
                       'lead_id': lead3.id,
                       'sale_order_id': sale_order3.id,
                       'amount': float(sale_order3.amount_total),
                       'quantity': 3
                   })

except Exception as e:
    print_error(f"\n✗ Scenario 3 failed: {e}")
    scenario3_data['status'] = 'failed'
    scenario3_data['error'] = str(e)
    results.test_scenarios.append(scenario3_data)
    results.add_test("Scenario 3: Phone → Family Memberships", "failed", error=str(e))
    env.cr.rollback()

# =============================================================================
# PART 5: Test Scenario 4 - Lost Opportunity
# =============================================================================

print_header("PART 5: Test Scenario 4 - Lost Opportunity")

scenario4_data = {
    'name': 'Test Scenario 4',
    'lead': None,
    'opportunity': None,
    'lost_reason': None,
    'status': 'pending'
}

try:
    print_info("Step 1: Creating lead...")

    lead4 = env['crm.lead'].create({
        'name': 'Pricing Inquiry - Jane Williams',
        'type': 'lead',
        'contact_name': 'Jane Williams',
        'email_from': 'jane.williams@example.com',
        'phone': '+1-555-0104',
        'description': 'Asked about pricing but found it too expensive.',
        'team_id': default_team.id,
        'source_id': website_source.id if website_source else False,
        'expected_revenue': 50.00,
    })

    scenario4_data['lead'] = lead4
    print_success(f"Created lead: {lead4.name} (ID: {lead4.id})")

    # Convert to opportunity
    print_info("\nStep 2: Converting to opportunity...")

    convert_wizard4 = env['crm.lead2opportunity.partner'].with_context(
        active_model='crm.lead',
        active_id=lead4.id,
        active_ids=lead4.ids
    ).create({
        'name': 'convert',
        'action': 'create',
        'user_id': env.user.id,
    })

    convert_wizard4.action_apply()
    lead4 = env['crm.lead'].browse(lead4.id)

    print_success(f"Converted to opportunity")
    scenario4_data['opportunity'] = lead4

    # Mark as lost
    print_info("\nStep 3: Marking opportunity as lost...")

    lost_reason = env['crm.lost.reason'].search([('name', '=', 'Too Expensive')], limit=1)
    if not lost_reason:
        lost_reason = env['crm.lost.reason'].create({'name': 'Too Expensive'})

    scenario4_data['lost_reason'] = lost_reason

    lead4.action_set_lost(lost_reason_id=lost_reason.id)

    print_success(f"Opportunity marked as lost")
    print_info(f"  Reason: {lost_reason.name}")
    print_info(f"  Probability: {lead4.probability}%")

    scenario4_data['status'] = 'completed'
    print_success("\n✓ Scenario 4 completed successfully!")
    results.test_scenarios.append(scenario4_data)
    results.add_test("Scenario 4: Lost Opportunity", "passed",
                   details={
                       'lead_id': lead4.id,
                       'lost_reason': lost_reason.name
                   })

except Exception as e:
    print_error(f"\n✗ Scenario 4 failed: {e}")
    scenario4_data['status'] = 'failed'
    scenario4_data['error'] = str(e)
    results.test_scenarios.append(scenario4_data)
    results.add_test("Scenario 4: Lost Opportunity", "failed", error=str(e))
    env.cr.rollback()

# Commit all successful transactions
env.cr.commit()

# =============================================================================
# PART 6: Generate Conversion Metrics
# =============================================================================

print_header("PART 6: Analyzing CRM Metrics")

try:
    print_info("Calculating conversion metrics...")

    # Count leads and opportunities
    total_leads = env['crm.lead'].search_count([('type', '=', 'lead')])
    total_opportunities = env['crm.lead'].search_count([('type', '=', 'opportunity')])

    # Count sale orders
    sale_orders = env['sale.order'].search([('opportunity_id', '!=', False)])
    confirmed_orders = sale_orders.filtered(lambda so: so.state in ['sale', 'done'])

    # Calculate revenue
    total_revenue = sum(so.amount_total for so in confirmed_orders)

    print_success(f"\nConversion Metrics:")
    print_info(f"  Total Leads: {total_leads}")
    print_info(f"  Total Opportunities: {total_opportunities}")
    print_info(f"  Sale Orders: {len(sale_orders)}")
    print_info(f"  Confirmed Orders: {len(confirmed_orders)}")
    print_info(f"  Total Revenue: ${total_revenue:.2f}")

    results.crm_config['metrics'] = {
        'total_leads': total_leads,
        'total_opportunities': total_opportunities,
        'sale_orders': len(sale_orders),
        'confirmed_orders': len(confirmed_orders),
        'total_revenue': float(total_revenue),
    }

    results.add_test("Conversion Metrics Analysis", "passed",
                   details=results.crm_config['metrics'])

except Exception as e:
    print_error(f"Error calculating metrics: {e}")
    results.add_test("Conversion Metrics Analysis", "failed", error=str(e))

# =============================================================================
# FINAL: Generate Summary
# =============================================================================

print_header("Test Results Summary")

print_success(f"\nTotal Tests Run: {results.total_tests}")
print_success(f"Passed: {results.passed_tests}")
if results.failed_tests > 0:
    print_error(f"Failed: {results.failed_tests}")
else:
    print_info(f"Failed: {results.failed_tests}")

success_rate = (results.passed_tests / results.total_tests * 100) if results.total_tests > 0 else 0
print_info(f"Success Rate: {success_rate:.1f}%")

# Add recommendations
results.add_recommendation("Create specific membership product types (Individual, Family, Student)")
results.add_recommendation("Configure CRM stages for gym sales (Inquiry → Tour → Negotiating → Won)")
results.add_recommendation("Set up automated lead assignment rules")
results.add_recommendation("Integrate website contact forms to auto-create leads")
results.add_recommendation("Add custom fields for fitness goals and preferences")

print_info(f"\nRecommendations:")
for rec in results.recommendations:
    print_info(f"  - {rec}")

print_header("Test Execution Completed")
print_success(f"Test completed at: {datetime.now()}")
