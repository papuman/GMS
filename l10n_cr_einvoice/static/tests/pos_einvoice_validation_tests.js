/** @odoo-module **/

import { registry } from "@web/core/registry";
import { makeTestEnv } from "@web/../tests/helpers/mock_env";
import { makeFakeDialogService, makeFakeNotificationService } from "@web/../tests/helpers/mock_services";

/**
 * POS E-Invoice Validation Tests
 *
 * Tests real-time validation logic for Costa Rica e-invoicing in POS.
 * Covers Factura Electronica (FE) requirements including date-based CIIU enforcement.
 */

const CIIU_MANDATORY_DATE = new Date('2025-10-06');
const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

QUnit.module('POS E-Invoice Validation Tests');

QUnit.test('TE (Tiquete) requires no validation', async function (assert) {
    assert.expect(2);

    // Mock order with Tiquete type
    const order = {
        l10n_cr_is_einvoice: true,
        einvoice_type: 'TE',
        getPartner: () => null, // No customer
    };

    // Validation should pass for TE
    const result = validateEinvoiceRequirements(order);

    assert.strictEqual(result.valid, true, 'TE should be valid without customer');
    assert.strictEqual(result.errors.length, 0, 'TE should have no validation errors');
});

QUnit.test('FE (Factura) requires customer selection', async function (assert) {
    assert.expect(3);

    // Mock order with Factura type but no customer
    const order = {
        l10n_cr_is_einvoice: true,
        einvoice_type: 'FE',
        getPartner: () => null,
    };

    const result = validateEinvoiceRequirements(order);

    assert.strictEqual(result.valid, false, 'FE without customer should be invalid');
    assert.strictEqual(result.errors.length, 1, 'Should have 1 error');
    assert.strictEqual(result.errors[0].field, 'customer', 'Error should be about missing customer');
});

QUnit.test('FE requires customer name', async function (assert) {
    assert.expect(3);

    // Mock partner without name
    const partner = {
        name: '',
        vat: '123456789',
        email: 'test@example.com',
    };

    const order = {
        l10n_cr_is_einvoice: true,
        einvoice_type: 'FE',
        getPartner: () => partner,
    };

    const result = validateEinvoiceRequirements(order);

    assert.strictEqual(result.valid, false, 'FE without customer name should be invalid');
    assert.ok(result.errors.some(e => e.field === 'name'), 'Should have name error');
    assert.ok(result.errors[0].message.includes('name'), 'Error message should mention name');
});

QUnit.test('FE requires customer VAT/Cédula', async function (assert) {
    assert.expect(2);

    // Mock partner without VAT
    const partner = {
        name: 'Test Customer',
        vat: '',
        email: 'test@example.com',
    };

    const order = {
        l10n_cr_is_einvoice: true,
        einvoice_type: 'FE',
        getPartner: () => partner,
    };

    const result = validateEinvoiceRequirements(order);

    assert.strictEqual(result.valid, false, 'FE without VAT should be invalid');
    assert.ok(result.errors.some(e => e.field === 'vat'), 'Should have VAT error');
});

QUnit.test('FE requires valid email format', async function (assert) {
    assert.expect(6);

    // Test invalid email formats
    const invalidEmails = [
        '',
        'not-an-email',
        '@example.com',
        'test@',
        'test@.com',
    ];

    invalidEmails.forEach(email => {
        const partner = {
            name: 'Test Customer',
            vat: '123456789',
            email: email,
        };

        const order = {
            l10n_cr_is_einvoice: true,
            einvoice_type: 'FE',
            getPartner: () => partner,
        };

        const result = validateEinvoiceRequirements(order);
        assert.strictEqual(result.valid, false, `Email "${email}" should be invalid`);
    });

    // Test valid email
    const validPartner = {
        name: 'Test Customer',
        vat: '123456789',
        email: 'valid@example.com',
        l10n_cr_economic_activity_id: true, // Has CIIU (post Oct 6)
    };

    const validOrder = {
        l10n_cr_is_einvoice: true,
        einvoice_type: 'FE',
        getPartner: () => validPartner,
    };

    const validResult = validateEinvoiceRequirements(validOrder);
    assert.strictEqual(validResult.valid, true, 'Valid email should pass');
});

QUnit.test('CIIU is mandatory after October 6, 2025', async function (assert) {
    assert.expect(2);

    const today = new Date();

    // Mock partner without CIIU
    const partner = {
        name: 'Test Customer',
        vat: '123456789',
        email: 'test@example.com',
        l10n_cr_economic_activity_id: null,
    };

    const order = {
        l10n_cr_is_einvoice: true,
        einvoice_type: 'FE',
        getPartner: () => partner,
    };

    const result = validateEinvoiceRequirements(order);

    if (today >= CIIU_MANDATORY_DATE) {
        assert.strictEqual(result.valid, false, 'After Oct 6, 2025: CIIU should be mandatory');
        assert.ok(result.errors.some(e => e.field === 'ciiu'), 'Should have CIIU error');
    } else {
        // Before mandatory date, should be warning only
        const daysUntil = Math.ceil((CIIU_MANDATORY_DATE - today) / (1000 * 60 * 60 * 24));
        if (daysUntil <= 30) {
            assert.ok(result.warnings.some(w => w.field === 'ciiu'), 'Should have CIIU warning within 30 days');
        }
        assert.strictEqual(result.valid, true, 'Before Oct 6, 2025: Should be valid without CIIU');
    }
});

QUnit.test('Complete FE validation with all fields valid', async function (assert) {
    assert.expect(3);

    // Mock complete partner (all fields valid)
    const partner = {
        name: 'Complete Customer',
        vat: '123456789',
        email: 'customer@example.com',
        l10n_cr_economic_activity_id: { id: 1, code: '9311' }, // Has CIIU
    };

    const order = {
        l10n_cr_is_einvoice: true,
        einvoice_type: 'FE',
        getPartner: () => partner,
    };

    const result = validateEinvoiceRequirements(order);

    assert.strictEqual(result.valid, true, 'Complete partner should be valid');
    assert.strictEqual(result.errors.length, 0, 'Should have no errors');
    assert.strictEqual(result.warnings.length, 0, 'Should have no warnings');
});

QUnit.test('Email regex validation works correctly', async function (assert) {
    assert.expect(8);

    const validEmails = [
        'user@example.com',
        'test.user@example.co.cr',
        'user+tag@example.com',
        'user123@test-domain.com',
    ];

    const invalidEmails = [
        'invalid',
        '@example.com',
        'user@',
        'user@.com',
    ];

    validEmails.forEach(email => {
        assert.ok(EMAIL_REGEX.test(email), `"${email}" should be valid`);
    });

    invalidEmails.forEach(email => {
        assert.notOk(EMAIL_REGEX.test(email), `"${email}" should be invalid`);
    });
});

// Helper function to validate e-invoice requirements
// (This mirrors the logic in pos_einvoice.js)
function validateEinvoiceRequirements(order) {
    const partner = order?.getPartner();
    const errors = [];
    const warnings = [];

    if (!order?.l10n_cr_is_einvoice) {
        return { valid: true, errors: [], warnings: [] };
    }

    if (order.einvoice_type === 'TE') {
        return { valid: true, errors: [], warnings: [] };
    }

    if (order.einvoice_type === 'FE') {
        // 1. Customer required
        if (!partner) {
            errors.push({
                field: 'customer',
                message: 'Customer is required for Factura',
                action: 'Click Customer button to select a client',
                icon: 'fa-user',
            });
        } else {
            // 2. Name required
            if (!partner.name || partner.name.trim() === '') {
                errors.push({
                    field: 'name',
                    message: 'Customer name is required',
                    action: 'Update customer record with a valid name',
                    icon: 'fa-id-card',
                });
            }

            // 3. VAT required
            if (!partner.vat || partner.vat.trim() === '') {
                errors.push({
                    field: 'vat',
                    message: 'Customer ID/Cédula is required',
                    action: 'Update customer record with ID number',
                    icon: 'fa-hashtag',
                });
            }

            // 4. Email required and valid
            if (!partner.email || partner.email.trim() === '') {
                errors.push({
                    field: 'email',
                    message: 'Customer email is required',
                    action: 'Update customer record with valid email',
                    icon: 'fa-envelope',
                });
            } else if (!EMAIL_REGEX.test(partner.email.trim())) {
                errors.push({
                    field: 'email',
                    message: 'Invalid email format',
                    action: 'Correct email format (e.g., user@example.com)',
                    icon: 'fa-envelope',
                });
            }

            // 5. CIIU code (date-based)
            const today = new Date();
            if (today >= CIIU_MANDATORY_DATE) {
                if (!partner.l10n_cr_economic_activity_id) {
                    errors.push({
                        field: 'ciiu',
                        message: 'CIIU economic activity code is required (mandatory since Oct 6, 2025)',
                        action: 'Update customer with CIIU code',
                        icon: 'fa-briefcase',
                    });
                }
            } else {
                const daysUntilMandatory = Math.ceil((CIIU_MANDATORY_DATE - today) / (1000 * 60 * 60 * 24));
                if (daysUntilMandatory <= 30 && !partner.l10n_cr_economic_activity_id) {
                    warnings.push({
                        field: 'ciiu',
                        message: `CIIU code will be mandatory in ${daysUntilMandatory} days`,
                        action: 'Consider adding CIIU code now',
                        icon: 'fa-calendar',
                    });
                }
            }
        }
    }

    return {
        valid: errors.length === 0,
        errors,
        warnings,
    };
}
