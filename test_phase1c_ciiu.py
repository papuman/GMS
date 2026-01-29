#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1C Validation Script: Recipient Economic Activity Field
Tests all features of the CIIU economic activity implementation

Usage:
    python3 test_phase1c_ciiu.py

Or in Odoo shell:
    odoo-bin shell -d your_database
    >>> exec(open('test_phase1c_ciiu.py').read())
"""

import logging
from datetime import date, timedelta

_logger = logging.getLogger(__name__)


def test_phase1c_ciiu(env):
    """
    Comprehensive test suite for Phase 1C: Recipient Economic Activity Field.

    Args:
        env: Odoo environment

    Returns:
        dict: Test results summary
    """
    results = {
        'total_tests': 0,
        'passed': 0,
        'failed': 0,
        'errors': [],
    }

    def test(name, condition, error_msg=""):
        """Helper function to run a test."""
        results['total_tests'] += 1
        if condition:
            results['passed'] += 1
            print(f"✅ {name}")
            return True
        else:
            results['failed'] += 1
            results['errors'].append(f"{name}: {error_msg}")
            print(f"❌ {name}: {error_msg}")
            return False

    print("\n" + "="*80)
    print("PHASE 1C: RECIPIENT ECONOMIC ACTIVITY FIELD - VALIDATION TESTS")
    print("="*80 + "\n")

    # ========================================================================
    # TEST GROUP 1: CIIU Code Catalog
    # ========================================================================
    print("\n📋 TEST GROUP 1: CIIU Code Catalog")
    print("-" * 80)

    # Test 1.1: CIIU model exists
    try:
        CIIUCode = env['l10n_cr.ciiu.code']
        test("1.1: CIIU Code model exists", True)
    except Exception as e:
        test("1.1: CIIU Code model exists", False, str(e))
        return results

    # Test 1.2: CIIU codes loaded
    ciiu_count = CIIUCode.search_count([])
    test(
        "1.2: CIIU codes loaded (100+ codes)",
        ciiu_count >= 100,
        f"Only {ciiu_count} codes found"
    )

    # Test 1.3: Code 9311 exists (Gyms)
    ciiu_9311 = CIIUCode.search([('code', '=', '9311')], limit=1)
    test(
        "1.3: Code 9311 (Gyms) exists",
        bool(ciiu_9311),
        "Code 9311 not found"
    )

    # Test 1.4: name_get() format correct
    if ciiu_9311:
        name_display = ciiu_9311.name_get()[0][1]
        test(
            "1.4: name_get() format is 'Code - Name'",
            name_display.startswith('9311 -'),
            f"Got: {name_display}"
        )

    # Test 1.5: Code validation (4 digits)
    try:
        invalid_code = CIIUCode.create({
            'code': '123',  # Invalid: only 3 digits
            'name': 'Test Invalid Code',
            'section': 'S',
        })
        test("1.5: Code validation (4 digits)", False, "Invalid code accepted")
        invalid_code.unlink()  # Clean up
    except Exception:
        test("1.5: Code validation (4 digits)", True)

    # Test 1.6: Code uniqueness
    if ciiu_9311:
        try:
            duplicate = CIIUCode.create({
                'code': '9311',  # Duplicate
                'name': 'Duplicate Code',
                'section': 'R',
            })
            test("1.6: Code uniqueness constraint", False, "Duplicate code accepted")
            duplicate.unlink()  # Clean up
        except Exception:
            test("1.6: Code uniqueness constraint", True)

    # ========================================================================
    # TEST GROUP 2: Partner Model Extension
    # ========================================================================
    print("\n👥 TEST GROUP 2: Partner Model Extension")
    print("-" * 80)

    Partner = env['res.partner']

    # Test 2.1: Partner has economic activity field
    test(
        "2.1: Partner has l10n_cr_economic_activity_id field",
        hasattr(Partner, 'l10n_cr_economic_activity_id')
    )

    # Test 2.2: Partner has activity code field
    test(
        "2.2: Partner has l10n_cr_activity_code field",
        hasattr(Partner, 'l10n_cr_activity_code')
    )

    # Test 2.3: Create test partner and assign CIIU
    costa_rica = env.ref('base.cr', raise_if_not_found=False)
    if costa_rica and ciiu_9311:
        test_partner = Partner.create({
            'name': 'Test Gym Phase 1C',
            'country_id': costa_rica.id,
            'vat': '3101234567',
            'is_company': True,
        })

        test_partner.l10n_cr_economic_activity_id = ciiu_9311.id

        test(
            "2.3: Assign economic activity to partner",
            test_partner.l10n_cr_activity_code == '9311',
            f"Expected '9311', got '{test_partner.l10n_cr_activity_code}'"
        )

        # Test 2.4: Missing CIIU detection
        test_partner.l10n_cr_economic_activity_id = False
        test(
            "2.4: Missing CIIU detection (l10n_cr_missing_ciiu)",
            test_partner.l10n_cr_missing_ciiu == True,
            f"Expected True, got {test_partner.l10n_cr_missing_ciiu}"
        )

        # Clean up
        test_partner.unlink()

    # Test 2.5: Smart suggestion for gym category
    if costa_rica and ciiu_9311:
        # Find or create gym category
        gym_category = env['res.partner.category'].search([
            ('name', 'ilike', 'gym')
        ], limit=1)
        if not gym_category:
            gym_category = env['res.partner.category'].create({
                'name': 'Gym'
            })

        test_partner = Partner.create({
            'name': 'Smart Gym Test',
            'country_id': costa_rica.id,
            'category_id': [(4, gym_category.id)],
        })

        suggested = test_partner.l10n_cr_suggested_ciiu_id

        test(
            "2.5: Smart suggestion for gym category",
            suggested and suggested.code == '9311',
            f"Expected code 9311, got {suggested.code if suggested else 'None'}"
        )

        # Clean up
        test_partner.unlink()

    # ========================================================================
    # TEST GROUP 3: XML Generator Updates
    # ========================================================================
    print("\n📄 TEST GROUP 3: XML Generator Updates")
    print("-" * 80)

    XMLGen = env['l10n_cr.xml.generator']

    # Test 3.1: CIIU mandatory date constant exists
    test(
        "3.1: CIIU_MANDATORY_DATE constant exists",
        hasattr(XMLGen, 'CIIU_MANDATORY_DATE')
    )

    # Test 3.2: _get_ciiu_mandatory_date() method exists
    test(
        "3.2: _get_ciiu_mandatory_date() method exists",
        hasattr(XMLGen, '_get_ciiu_mandatory_date')
    )

    # Test 3.3: Generate XML with economic activity
    if costa_rica and ciiu_9311:
        from lxml import etree

        test_partner = Partner.create({
            'name': 'XML Test Gym',
            'country_id': costa_rica.id,
            'vat': '3101234567',
            'l10n_cr_economic_activity_id': ciiu_9311.id,
        })

        # Create mock root element
        root = etree.Element('FacturaElectronica')
        xml_gen = XMLGen.create({})

        # Test _add_receptor with CIIU
        try:
            xml_gen._add_receptor(root, test_partner, date.today())
            xml_str = etree.tostring(root, encoding='unicode')

            test(
                "3.3: XML contains <ActividadEconomica> tag",
                '<ActividadEconomica>9311</ActividadEconomica>' in xml_str,
                f"Tag not found in XML: {xml_str[:200]}"
            )
        except Exception as e:
            test("3.3: XML contains <ActividadEconomica> tag", False, str(e))

        # Clean up
        test_partner.unlink()

    # Test 3.4: Grace period logic (before deadline)
    if costa_rica:
        from lxml import etree

        test_partner = Partner.create({
            'name': 'Grace Period Test',
            'country_id': costa_rica.id,
            'vat': '3101234567',
            # NO economic activity
        })

        root = etree.Element('FacturaElectronica')
        xml_gen = XMLGen.create({})

        # Before deadline should succeed with warning
        past_date = date(2025, 10, 5)  # Day before deadline
        try:
            xml_gen._add_receptor(root, test_partner, past_date)
            test("3.4: Grace period allows missing CIIU (warning only)", True)
        except Exception as e:
            test("3.4: Grace period allows missing CIIU (warning only)", False, str(e))

        # Clean up
        test_partner.unlink()

    # Test 3.5: Hard error after deadline
    if costa_rica:
        from lxml import etree

        test_partner = Partner.create({
            'name': 'Post Deadline Test',
            'country_id': costa_rica.id,
            'vat': '3101234567',
            # NO economic activity
        })

        root = etree.Element('FacturaElectronica')
        xml_gen = XMLGen.create({})

        # After deadline should raise error
        future_date = date(2025, 10, 7)  # Day after deadline
        try:
            xml_gen._add_receptor(root, test_partner, future_date)
            test("3.5: Hard error after deadline", False, "No error raised")
        except Exception as e:
            error_msg = str(e)
            test(
                "3.5: Hard error after deadline",
                'economic activity' in error_msg.lower(),
                f"Wrong error: {error_msg}"
            )

        # Clean up
        test_partner.unlink()

    # ========================================================================
    # TEST GROUP 4: Bulk Assignment Wizard
    # ========================================================================
    print("\n🔧 TEST GROUP 4: Bulk Assignment Wizard")
    print("-" * 80)

    # Test 4.1: Wizard model exists
    try:
        BulkAssign = env['l10n_cr.ciiu.bulk.assign']
        test("4.1: Bulk assignment wizard model exists", True)
    except Exception as e:
        test("4.1: Bulk assignment wizard model exists", False, str(e))
        BulkAssign = None

    # Test 4.2: Wizard has required fields
    if BulkAssign:
        test(
            "4.2: Wizard has ciiu_code_id field",
            hasattr(BulkAssign, 'ciiu_code_id')
        )
        test(
            "4.3: Wizard has filter_mode field",
            hasattr(BulkAssign, 'filter_mode')
        )
        test(
            "4.4: Wizard has action_assign method",
            hasattr(BulkAssign, 'action_assign')
        )

    # Test 4.5: Bulk assign to multiple partners
    if BulkAssign and costa_rica and ciiu_9311:
        # Create test partners
        partners = Partner.create([
            {
                'name': f'Bulk Test Partner {i}',
                'country_id': costa_rica.id,
                'vat': f'310123456{i}',
            }
            for i in range(5)
        ])

        wizard = BulkAssign.create({
            'ciiu_code_id': ciiu_9311.id,
            'filter_mode': 'selected',
            'partner_ids': [(6, 0, partners.ids)],
        })

        wizard.action_assign()

        assigned_count = sum(1 for p in partners if p.l10n_cr_activity_code == '9311')

        test(
            "4.5: Bulk assign to 5 partners",
            assigned_count == 5,
            f"Only {assigned_count}/5 partners assigned"
        )

        # Clean up
        partners.unlink()

    # ========================================================================
    # TEST GROUP 5: Security
    # ========================================================================
    print("\n🔒 TEST GROUP 5: Security")
    print("-" * 80)

    # Test 5.1: Check access rights exist
    access = env['ir.model.access'].search([
        ('model_id.model', '=', 'l10n_cr.ciiu.code')
    ])
    test(
        "5.1: CIIU code access rights configured",
        len(access) >= 2,
        f"Expected 2+ access rules, found {len(access)}"
    )

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Success Rate: {results['passed']/results['total_tests']*100:.1f}%")

    if results['failed'] > 0:
        print("\n⚠️  FAILED TESTS:")
        for error in results['errors']:
            print(f"  - {error}")
    else:
        print("\n🎉 ALL TESTS PASSED!")

    print("\n" + "="*80 + "\n")

    return results


if __name__ == '__main__':
    print("⚠️  This script should be run in Odoo shell:")
    print("    odoo-bin shell -d your_database")
    print("    >>> exec(open('test_phase1c_ciiu.py').read())")
    print("    >>> test_phase1c_ciiu(env)")
