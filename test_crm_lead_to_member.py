#!/usr/bin/env python3
"""
CRM Lead-to-Member Conversion Test Script for GMS Validation System

This script validates the complete CRM workflow for converting leads to paying gym members:
1. Creating leads from various sources (website, walk-in, phone)
2. Converting leads to opportunities
3. Adding membership products to opportunities
4. Converting opportunities to sales orders (new members)
5. Creating customer/partner records
6. Tracking lead sources and conversion metrics

Database: gms_validation
URL: http://localhost:8070
Credentials: admin/admin
"""

import sys
import json
from datetime import datetime, timedelta
from decimal import Decimal

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
    UNDERLINE = '\033[4m'

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

print_header("GMS CRM Lead-to-Member Conversion Test")
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
        print_warning("Sales CRM module not installed - opportunity to sale conversion may be limited")
        results.add_warning("Sales CRM module not installed - limited functionality")
        results.crm_config['sale_crm_module'] = 'not_installed'

    results.add_test("CRM Module Check", "passed",
                    details=f"CRM installed, Sale CRM: {results.crm_config['sale_crm_module']}")

except Exception as e:
    print_error(f"Error checking modules: {e}")
    results.add_test("CRM Module Check", "failed", error=str(e))

# Check CRM Teams (Sales Channels)
try:
    print_info("\nDiscovering CRM Teams/Sales Channels...")
    crm_teams = env['crm.team'].search([])

    if crm_teams:
        print_success(f"Found {len(crm_teams)} CRM team(s):")
        for team in crm_teams:
            print_info(f"  - {team.name} (ID: {team.id})")
            results.pipeline_stages.append({
                'team_id': team.id,
                'team_name': team.name,
                'stages': []
            })
        results.crm_config['crm_teams'] = len(crm_teams)
    else:
        print_warning("No CRM teams found - creating default 'Gym Sales' team")
        default_team = env['crm.team'].create({
            'name': 'Gym Sales',
            'use_leads': True,
            'use_opportunities': True,
        })
        print_success(f"Created default team: {default_team.name} (ID: {default_team.id})")
        crm_teams = default_team
        results.crm_config['crm_teams'] = 1
        results.pipeline_stages.append({
            'team_id': default_team.id,
            'team_name': default_team.name,
            'stages': []
        })

    results.add_test("CRM Teams Discovery", "passed",
                    details=f"Found/created {results.crm_config['crm_teams']} team(s)")

except Exception as e:
    print_error(f"Error discovering CRM teams: {e}")
    results.add_test("CRM Teams Discovery", "failed", error=str(e))

# Check CRM Stages (Pipeline Stages)
try:
    print_info("\nDiscovering CRM Pipeline Stages...")
    for team_info in results.pipeline_stages:
        team = env['crm.team'].browse(team_info['team_id'])
        stages = env['crm.stage'].search([
            '|', ('team_id', '=', team.id), ('team_id', '=', False)
        ], order='sequence')

        print_success(f"Team '{team.name}' has {len(stages)} stage(s):")
        for stage in stages:
            stage_type = "Won" if stage.is_won else ("Lost" if stage.fold else "Active")
            print_info(f"  - {stage.name} (Seq: {stage.sequence}, Type: {stage_type})")
            team_info['stages'].append({
                'id': stage.id,
                'name': stage.name,
                'sequence': stage.sequence,
                'is_won': stage.is_won,
                'fold': stage.fold
            })

    results.add_test("Pipeline Stages Discovery", "passed",
                    details=f"Discovered stages for {len(results.pipeline_stages)} team(s)")

except Exception as e:
    print_error(f"Error discovering pipeline stages: {e}")
    results.add_test("Pipeline Stages Discovery", "failed", error=str(e))

# Check Lead Sources
try:
    print_info("\nDiscovering Lead Sources...")
    lead_sources = env['utm.source'].search([])

    if lead_sources:
        print_success(f"Found {len(lead_sources)} lead source(s):")
        for source in lead_sources[:10]:  # Show first 10
            print_info(f"  - {source.name}")
            results.lead_sources.append(source.name)
    else:
        print_warning("No lead sources found - will create gym-specific sources")

    # Create gym-specific lead sources if they don't exist
    gym_sources = ['Website', 'Walk-in', 'Phone', 'Referral', 'Social Media', 'Email Campaign']
    created_sources = []

    for source_name in gym_sources:
        existing = env['utm.source'].search([('name', '=', source_name)], limit=1)
        if not existing:
            new_source = env['utm.source'].create({'name': source_name})
            created_sources.append(source_name)
            print_success(f"Created lead source: {source_name}")

    if created_sources:
        results.crm_config['created_sources'] = created_sources
        print_success(f"Created {len(created_sources)} gym-specific lead sources")

    results.add_test("Lead Sources Discovery", "passed",
                    details=f"Found/created {len(gym_sources)} sources")

except Exception as e:
    print_error(f"Error managing lead sources: {e}")
    results.add_test("Lead Sources Discovery", "failed", error=str(e))

# Check membership products
try:
    print_info("\nDiscovering Membership Products...")
    membership_products = env['product.product'].search([
        ('detailed_type', '=', 'service'),
        ('name', 'ilike', 'membership')
    ])

    if membership_products:
        print_success(f"Found {len(membership_products)} membership product(s):")
        for product in membership_products:
            print_info(f"  - {product.name} (${product.list_price})")
        results.crm_config['membership_products'] = len(membership_products)
    else:
        print_warning("No membership products found - will use generic products for testing")
        results.crm_config['membership_products'] = 0
        results.add_recommendation(
            "Create specific membership products (Monthly, Annual, Family) for better CRM tracking"
        )

    results.add_test("Membership Products Check", "passed" if membership_products else "warning",
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
        'description': 'Walk-in inquiry about monthly membership options. Interested in general fitness.',
        'team_id': default_team.id,
        'source_id': walk_in_source.id if walk_in_source else False,
        'expected_revenue': 50.00,  # Monthly membership estimate
    }

    lead1 = env['crm.lead'].create(lead_data)
    scenario1_data['lead'] = lead1

    print_success(f"Created lead: {lead1.name} (ID: {lead1.id})")
    print_info(f"  Contact: {lead1.contact_name}")
    print_info(f"  Email: {lead1.email_from}")
    print_info(f"  Phone: {lead1.phone}")
    print_info(f"  Source: {lead1.source_id.name if lead1.source_id else 'None'}")
    print_info(f"  Expected Revenue: ${lead1.expected_revenue}")

    # Step 2: Convert lead to opportunity
    print_info("\nStep 2: Converting lead to opportunity...")

    # Use the lead2opportunity wizard
    convert_wizard = env['crm.lead2opportunity.partner'].with_context(
        active_model='crm.lead',
        active_id=lead1.id,
        active_ids=lead1.ids
    ).create({
        'name': 'convert',
        'action': 'create',  # Create new partner
        'user_id': env.user.id,
    })

    convert_wizard.action_apply()

    # Reload lead to get updated type
    lead1 = env['crm.lead'].browse(lead1.id)

    if lead1.type == 'opportunity':
        print_success(f"Converted to opportunity: {lead1.name}")
        print_info(f"  Partner created: {lead1.partner_id.name if lead1.partner_id else 'None'}")
        print_info(f"  Stage: {lead1.stage_id.name}")
        scenario1_data['opportunity'] = lead1
        scenario1_data['partner'] = lead1.partner_id
    else:
        print_error("Lead conversion to opportunity failed!")
        raise Exception("Lead type did not change to opportunity")

    # Step 3: Add membership product to opportunity
    print_info("\nStep 3: Adding membership product to opportunity...")

    # Try to find a monthly membership product, or use a generic service
    monthly_membership = env['product.product'].search([
        ('name', 'ilike', 'monthly membership')
    ], limit=1)

    if not monthly_membership:
        # Create a test membership product
        monthly_membership = env['product.product'].create({
            'name': 'Monthly Membership - Test',
            'detailed_type': 'service',
            'list_price': 50.00,
            'description': 'Test monthly gym membership product',
        })
        print_success(f"Created test product: {monthly_membership.name}")

    print_success(f"Using product: {monthly_membership.name} (${monthly_membership.list_price})")

    # Update expected revenue to match product price
    lead1.write({'expected_revenue': monthly_membership.list_price})
    print_info(f"  Updated expected revenue: ${lead1.expected_revenue}")

    # Step 4: Convert opportunity to sale order
    print_info("\nStep 4: Converting opportunity to sale order...")

    if sale_crm_module and sale_crm_module.state == 'installed':
        # Use the opportunity to quotation wizard
        sale_wizard = env['crm.opportunity.to.quotation'].with_context(
            active_model='crm.lead',
            active_id=lead1.id,
            active_ids=lead1.ids
        ).create({
            'partner_id': lead1.partner_id.id,
            'opportunity_id': lead1.id,
        })

        action = sale_wizard.action_apply()

        # Get the created sale order
        if action and 'res_id' in action:
            sale_order = env['sale.order'].browse(action['res_id'])
        else:
            # Search for the sale order
            sale_order = env['sale.order'].search([
                ('opportunity_id', '=', lead1.id)
            ], limit=1)

        if sale_order:
            # Add product line to sale order
            env['sale.order.line'].create({
                'order_id': sale_order.id,
                'product_id': monthly_membership.id,
                'product_uom_qty': 1,
                'price_unit': monthly_membership.list_price,
            })

            scenario1_data['sale_order'] = sale_order

            print_success(f"Created sale order: {sale_order.name} (ID: {sale_order.id})")
            print_info(f"  Customer: {sale_order.partner_id.name}")
            print_info(f"  Amount Total: ${sale_order.amount_total}")
            print_info(f"  State: {sale_order.state}")

            # Confirm the sale order
            sale_order.action_confirm()
            print_success(f"Sale order confirmed - State: {sale_order.state}")

            scenario1_data['status'] = 'completed'
            results.add_test("Scenario 1: Walk-in → Monthly Membership", "passed",
                           details={
                               'lead_id': lead1.id,
                               'partner_id': lead1.partner_id.id,
                               'sale_order_id': sale_order.id,
                               'amount': float(sale_order.amount_total)
                           })
        else:
            print_error("Sale order not created!")
            raise Exception("Sale order creation failed")
    else:
        print_warning("Sale CRM module not installed - creating manual sale order")

        # Create manual sale order
        sale_order = env['sale.order'].create({
            'partner_id': lead1.partner_id.id,
            'opportunity_id': lead1.id,
            'order_line': [(0, 0, {
                'product_id': monthly_membership.id,
                'product_uom_qty': 1,
                'price_unit': monthly_membership.list_price,
            })]
        })

        scenario1_data['sale_order'] = sale_order
        print_success(f"Created manual sale order: {sale_order.name}")

        sale_order.action_confirm()
        print_success(f"Sale order confirmed")

        scenario1_data['status'] = 'completed'
        results.add_test("Scenario 1: Walk-in → Monthly Membership", "passed",
                       details={
                           'lead_id': lead1.id,
                           'partner_id': lead1.partner_id.id,
                           'sale_order_id': sale_order.id,
                           'amount': float(sale_order.amount_total)
                       })

    print_success("\n✓ Scenario 1 completed successfully!")
    results.test_scenarios.append(scenario1_data)

except Exception as e:
    print_error(f"\n✗ Scenario 1 failed: {e}")
    scenario1_data['status'] = 'failed'
    scenario1_data['error'] = str(e)
    results.test_scenarios.append(scenario1_data)
    results.add_test("Scenario 1: Walk-in → Monthly Membership", "failed", error=str(e))

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
    # Step 1: Create a lead from website inquiry
    print_info("Step 1: Creating lead from website inquiry...")

    website_source = env['utm.source'].search([('name', '=', 'Website')], limit=1)

    lead_data = {
        'name': 'Annual Membership Inquiry - Sarah Smith',
        'type': 'lead',
        'contact_name': 'Sarah Smith',
        'email_from': 'sarah.smith@example.com',
        'phone': '+1-555-0102',
        'description': 'Website contact form submission. Interested in annual membership for cost savings.',
        'team_id': default_team.id,
        'source_id': website_source.id if website_source else False,
        'expected_revenue': 500.00,  # Annual membership estimate
    }

    lead2 = env['crm.lead'].create(lead_data)
    scenario2_data['lead'] = lead2

    print_success(f"Created lead: {lead2.name} (ID: {lead2.id})")
    print_info(f"  Source: Website")

    # Step 2: Convert lead to opportunity with existing partner check
    print_info("\nStep 2: Converting lead to opportunity...")

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

    # Step 3: Create annual membership product and add to opportunity
    print_info("\nStep 3: Creating annual membership product...")

    annual_membership = env['product.product'].search([
        ('name', 'ilike', 'annual membership')
    ], limit=1)

    if not annual_membership:
        annual_membership = env['product.product'].create({
            'name': 'Annual Membership - Test',
            'detailed_type': 'service',
            'list_price': 500.00,
            'description': 'Test annual gym membership product (12 months)',
        })
        print_success(f"Created test product: {annual_membership.name}")

    print_success(f"Using product: {annual_membership.name} (${annual_membership.list_price})")

    lead2.write({'expected_revenue': annual_membership.list_price})

    # Step 4: Convert to sale order
    print_info("\nStep 4: Converting to sale order...")

    sale_order2 = env['sale.order'].create({
        'partner_id': lead2.partner_id.id,
        'opportunity_id': lead2.id,
        'order_line': [(0, 0, {
            'product_id': annual_membership.id,
            'product_uom_qty': 1,
            'price_unit': annual_membership.list_price,
        })]
    })

    scenario2_data['sale_order'] = sale_order2
    print_success(f"Created sale order: {sale_order2.name}")

    sale_order2.action_confirm()
    print_success(f"Sale order confirmed")

    # Move opportunity to won stage
    won_stage = env['crm.stage'].search([('is_won', '=', True)], limit=1)
    if won_stage:
        lead2.write({'stage_id': won_stage.id})
        print_success(f"Moved opportunity to Won stage: {won_stage.name}")

    scenario2_data['status'] = 'completed'
    print_success("\n✓ Scenario 2 completed successfully!")
    results.test_scenarios.append(scenario2_data)
    results.add_test("Scenario 2: Website → Annual Membership", "passed",
                   details={
                       'lead_id': lead2.id,
                       'partner_id': lead2.partner_id.id,
                       'sale_order_id': sale_order2.id,
                       'amount': float(sale_order2.amount_total)
                   })

except Exception as e:
    print_error(f"\n✗ Scenario 2 failed: {e}")
    scenario2_data['status'] = 'failed'
    scenario2_data['error'] = str(e)
    results.test_scenarios.append(scenario2_data)
    results.add_test("Scenario 2: Website → Annual Membership", "failed", error=str(e))

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
    # Step 1: Create a lead from phone inquiry
    print_info("Step 1: Creating lead from phone inquiry...")

    phone_source = env['utm.source'].search([('name', '=', 'Phone')], limit=1)

    lead_data = {
        'name': 'Family Membership Inquiry - The Johnson Family',
        'type': 'lead',
        'contact_name': 'Michael Johnson',
        'email_from': 'mjohnson@example.com',
        'phone': '+1-555-0103',
        'description': 'Phone inquiry about family membership options. Needs memberships for 3 family members.',
        'team_id': default_team.id,
        'source_id': phone_source.id if phone_source else False,
        'expected_revenue': 150.00,  # 3 x monthly membership
    }

    lead3 = env['crm.lead'].create(lead_data)
    scenario3_data['lead'] = lead3

    print_success(f"Created lead: {lead3.name} (ID: {lead3.id})")

    # Step 2: Convert to opportunity
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

    # Step 3: Create sale order with multiple membership products
    print_info("\nStep 3: Creating sale order with 3 family memberships...")

    # Use monthly membership for family members
    if not monthly_membership:
        monthly_membership = env['product.product'].search([
            ('name', 'ilike', 'monthly membership')
        ], limit=1)

    sale_order3 = env['sale.order'].create({
        'partner_id': lead3.partner_id.id,
        'opportunity_id': lead3.id,
        'order_line': [(0, 0, {
            'product_id': monthly_membership.id,
            'product_uom_qty': 3,  # 3 family members
            'price_unit': monthly_membership.list_price,
        })]
    })

    scenario3_data['sale_order'] = sale_order3
    print_success(f"Created sale order: {sale_order3.name}")
    print_info(f"  Quantity: 3 memberships")
    print_info(f"  Total: ${sale_order3.amount_total}")

    sale_order3.action_confirm()
    print_success(f"Sale order confirmed")

    # Move to won stage
    if won_stage:
        lead3.write({'stage_id': won_stage.id})

    scenario3_data['status'] = 'completed'
    print_success("\n✓ Scenario 3 completed successfully!")
    results.test_scenarios.append(scenario3_data)
    results.add_test("Scenario 3: Phone → Family Memberships", "passed",
                   details={
                       'lead_id': lead3.id,
                       'partner_id': lead3.partner_id.id,
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

# =============================================================================
# PART 5: Test Scenario 4 - Lost Opportunity (Didn't Convert)
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
    # Step 1: Create a lead
    print_info("Step 1: Creating lead from website inquiry...")

    lead_data = {
        'name': 'Pricing Inquiry - Jane Williams',
        'type': 'lead',
        'contact_name': 'Jane Williams',
        'email_from': 'jane.williams@example.com',
        'phone': '+1-555-0104',
        'description': 'Asked about pricing but found it too expensive.',
        'team_id': default_team.id,
        'source_id': website_source.id if website_source else False,
        'expected_revenue': 50.00,
    }

    lead4 = env['crm.lead'].create(lead_data)
    scenario4_data['lead'] = lead4

    print_success(f"Created lead: {lead4.name} (ID: {lead4.id})")

    # Step 2: Convert to opportunity
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

    # Step 3: Mark opportunity as lost
    print_info("\nStep 3: Marking opportunity as lost...")

    # Check if lost reason exists, create if not
    lost_reason = env['crm.lost.reason'].search([('name', '=', 'Too Expensive')], limit=1)
    if not lost_reason:
        lost_reason = env['crm.lost.reason'].create({
            'name': 'Too Expensive'
        })
        print_success(f"Created lost reason: {lost_reason.name}")

    scenario4_data['lost_reason'] = lost_reason

    # Mark as lost
    lead4.action_set_lost(lost_reason_id=lost_reason.id)

    print_success(f"Opportunity marked as lost")
    print_info(f"  Reason: {lost_reason.name}")
    print_info(f"  Active: {lead4.active}")
    print_info(f"  Probability: {lead4.probability}%")

    scenario4_data['status'] = 'completed'
    print_success("\n✓ Scenario 4 completed successfully!")
    results.test_scenarios.append(scenario4_data)
    results.add_test("Scenario 4: Lost Opportunity", "passed",
                   details={
                       'lead_id': lead4.id,
                       'lost_reason': lost_reason.name,
                       'probability': lead4.probability
                   })

except Exception as e:
    print_error(f"\n✗ Scenario 4 failed: {e}")
    scenario4_data['status'] = 'failed'
    scenario4_data['error'] = str(e)
    results.test_scenarios.append(scenario4_data)
    results.add_test("Scenario 4: Lost Opportunity", "failed", error=str(e))

# =============================================================================
# PART 6: Generate Conversion Metrics and Analysis
# =============================================================================

print_header("PART 6: Analyzing CRM Metrics and Conversion Rates")

try:
    print_info("Calculating conversion metrics...")

    # Count total leads created
    total_leads = env['crm.lead'].search_count([
        ('type', '=', 'lead'),
        ('create_date', '>=', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
    ])

    # Count converted opportunities
    total_opportunities = env['crm.lead'].search_count([
        ('type', '=', 'opportunity'),
        ('create_date', '>=', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
    ])

    # Count won opportunities
    won_opportunities = env['crm.lead'].search_count([
        ('type', '=', 'opportunity'),
        ('stage_id.is_won', '=', True),
        ('create_date', '>=', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
    ])

    # Count lost opportunities
    lost_opportunities = env['crm.lead'].search_count([
        ('type', '=', 'opportunity'),
        ('probability', '=', 0),
        ('active', '=', False),
        ('create_date', '>=', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
    ])

    # Calculate revenue from won opportunities
    won_opps = env['crm.lead'].search([
        ('type', '=', 'opportunity'),
        ('stage_id.is_won', '=', True),
        ('create_date', '>=', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
    ])

    total_revenue = sum(opp.expected_revenue for opp in won_opps)

    # Count sale orders from opportunities
    sale_orders = env['sale.order'].search([
        ('opportunity_id', '!=', False),
        ('create_date', '>=', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
    ])

    confirmed_orders = sale_orders.filtered(lambda so: so.state in ['sale', 'done'])

    print_success(f"\nConversion Metrics:")
    print_info(f"  Total Leads Created: {total_leads}")
    print_info(f"  Converted to Opportunities: {total_opportunities}")
    print_info(f"  Won Opportunities: {won_opportunities}")
    print_info(f"  Lost Opportunities: {lost_opportunities}")
    print_info(f"  Sale Orders Created: {len(sale_orders)}")
    print_info(f"  Confirmed Sale Orders: {len(confirmed_orders)}")
    print_info(f"  Total Revenue (Won): ${total_revenue:.2f}")

    if total_opportunities > 0:
        win_rate = (won_opportunities / total_opportunities) * 100
        print_info(f"  Win Rate: {win_rate:.1f}%")

    results.crm_config['metrics'] = {
        'total_leads': total_leads,
        'total_opportunities': total_opportunities,
        'won_opportunities': won_opportunities,
        'lost_opportunities': lost_opportunities,
        'sale_orders': len(sale_orders),
        'confirmed_orders': len(confirmed_orders),
        'total_revenue': float(total_revenue),
        'win_rate': (won_opportunities / total_opportunities * 100) if total_opportunities > 0 else 0
    }

    results.add_test("Conversion Metrics Analysis", "passed",
                   details=results.crm_config['metrics'])

except Exception as e:
    print_error(f"Error calculating metrics: {e}")
    results.add_test("Conversion Metrics Analysis", "failed", error=str(e))

# =============================================================================
# PART 7: Test CRM Features and Limitations
# =============================================================================

print_header("PART 7: Testing Additional CRM Features")

# Test lead assignment
try:
    print_info("Testing lead assignment to sales team members...")

    # Get sales users
    sales_users = env['res.users'].search([
        ('groups_id', 'in', env.ref('sales_team.group_sale_salesman').id)
    ], limit=3)

    if sales_users:
        print_success(f"Found {len(sales_users)} sales user(s)")

        # Assign lead to user
        if scenario1_data.get('lead'):
            scenario1_data['lead'].write({'user_id': sales_users[0].id})
            print_success(f"Assigned lead to user: {sales_users[0].name}")
    else:
        print_warning("No sales users found for assignment testing")
        results.add_recommendation(
            "Configure sales team members for proper lead assignment and tracking"
        )

    results.add_test("Lead Assignment", "passed" if sales_users else "warning")

except Exception as e:
    print_error(f"Error testing lead assignment: {e}")
    results.add_test("Lead Assignment", "failed", error=str(e))

# Test lead activities and scheduling
try:
    print_info("\nTesting activity scheduling on leads...")

    if scenario2_data.get('opportunity'):
        # Schedule a follow-up activity
        activity_type = env['mail.activity.type'].search([
            ('name', 'in', ['Call', 'Email', 'Meeting'])
        ], limit=1)

        if activity_type:
            activity = env['mail.activity'].create({
                'res_model': 'crm.lead',
                'res_id': scenario2_data['opportunity'].id,
                'activity_type_id': activity_type.id,
                'summary': 'Follow up on membership inquiry',
                'date_deadline': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
                'user_id': env.user.id,
            })

            print_success(f"Created activity: {activity.summary}")
            print_info(f"  Type: {activity_type.name}")
            print_info(f"  Due: {activity.date_deadline}")

            results.add_test("Activity Scheduling", "passed",
                           details={'activity_id': activity.id})
        else:
            print_warning("No activity types found")
            results.add_test("Activity Scheduling", "warning")

except Exception as e:
    print_error(f"Error testing activities: {e}")
    results.add_test("Activity Scheduling", "failed", error=str(e))

# Test lead notes and communication logging
try:
    print_info("\nTesting lead communication logging...")

    if scenario1_data.get('opportunity'):
        # Log a note/message
        message = scenario1_data['opportunity'].message_post(
            body="Customer visited gym for a tour. Very interested in personal training add-on.",
            subject="Tour Completed",
            message_type='comment'
        )

        print_success(f"Logged communication on opportunity")
        print_info(f"  Message ID: {message.id}")

        results.add_test("Communication Logging", "passed")

except Exception as e:
    print_error(f"Error testing communication logging: {e}")
    results.add_test("Communication Logging", "failed", error=str(e))

# =============================================================================
# PART 8: Identify Limitations and Recommendations
# =============================================================================

print_header("PART 8: Analyzing Limitations and Generating Recommendations")

# Check for sales automation
print_info("Checking for sales automation capabilities...")
automation_module = env['ir.module.module'].search([('name', '=', 'base_automation')])
if automation_module and automation_module.state == 'installed':
    print_success("Sales automation module installed")
    results.add_recommendation(
        "Configure automated actions for lead nurturing (e.g., auto-assign leads, send welcome emails)"
    )
else:
    print_warning("Sales automation not available")
    results.add_recommendation(
        "Install base_automation module for automated lead nurturing workflows"
    )

# Check for email marketing integration
print_info("\nChecking for email marketing integration...")
mass_mailing = env['ir.module.module'].search([('name', '=', 'mass_mailing_crm')])
if mass_mailing and mass_mailing.state == 'installed':
    print_success("Email marketing integration available")
else:
    print_warning("Email marketing integration not installed")
    results.add_recommendation(
        "Install mass_mailing_crm for email campaigns targeting leads and opportunities"
    )

# Check for website CRM integration
print_info("\nChecking for website integration...")
website_crm = env['ir.module.module'].search([('name', '=', 'website_crm')])
if website_crm and website_crm.state == 'installed':
    print_success("Website CRM integration available")
else:
    print_warning("Website CRM integration not installed")
    results.add_recommendation(
        "Install website_crm for online membership inquiry forms that auto-create leads"
    )

# General gym-specific recommendations
results.add_recommendation(
    "Create specific membership product categories (Individual, Family, Student, Senior) for better reporting"
)
results.add_recommendation(
    "Configure CRM stages specific to gym sales process (Inquiry, Tour Scheduled, Tour Completed, Negotiating, Closed)"
)
results.add_recommendation(
    "Set up automated lead scoring based on inquiry type and expected revenue"
)
results.add_recommendation(
    "Create custom fields for gym-specific data (fitness goals, preferred workout times, medical conditions)"
)
results.add_recommendation(
    "Integrate with calendar for automated tour scheduling"
)

# =============================================================================
# PART 9: Generate Test Results Summary
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

print_info(f"\nTest Scenarios Completed:")
for scenario in results.test_scenarios:
    status_icon = "✓" if scenario['status'] == 'completed' else "✗"
    print_info(f"  {status_icon} {scenario['name']}: {scenario['status']}")

if results.warnings:
    print_warning(f"\nWarnings ({len(results.warnings)}):")
    for warning in results.warnings:
        print_warning(f"  - {warning}")

print_info(f"\nRecommendations ({len(results.recommendations)}):")
for rec in results.recommendations:
    print_info(f"  - {rec}")

# Print JSON summary for parsing
print_info("\n" + "="*80)
print_info("JSON Test Results (for automated parsing):")
print("="*80)
print(json.dumps({
    'test_summary': {
        'total_tests': results.total_tests,
        'passed_tests': results.passed_tests,
        'failed_tests': results.failed_tests,
        'success_rate': success_rate
    },
    'crm_config': results.crm_config,
    'pipeline_stages': results.pipeline_stages,
    'test_scenarios': [
        {
            'name': s['name'],
            'status': s['status'],
            'lead_id': s['lead'].id if s.get('lead') else None,
            'partner_id': s['partner'].id if s.get('partner') else None,
            'sale_order_id': s['sale_order'].id if s.get('sale_order') else None,
        } for s in results.test_scenarios
    ],
    'metrics': results.crm_config.get('metrics', {}),
    'warnings': results.warnings,
    'recommendations': results.recommendations
}, indent=2))

print_header("Test Execution Completed")
print_success(f"Test completed at: {datetime.now()}")
print_success(f"Report will be generated: CRM-TEST-RESULTS.md")
