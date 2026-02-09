/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onMounted, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

// Email validation regex
const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

/**
 * Validate FE customer requirements.
 * Returns { valid: boolean, missing: string[] }
 *
 * Hacienda v4.4 mandatory FE receptor fields:
 *   1. Customer selected (partner exists)
 *   2. Name (non-empty)
 *   3. VAT / Cédula (non-empty)
 *   4. Email (non-empty, valid format)
 *   5. Economic Activity / CIIU (mandatory from Oct 6, 2025)
 */
function checkFERequirements(partner, ciiuMandatoryDate) {
    const missing = [];

    if (!partner) {
        missing.push(_t('Customer (select a customer first)'));
        return { valid: false, missing };
    }

    if (!partner.name) {
        missing.push(_t('Customer Name'));
    }
    if (!partner.vat) {
        missing.push(_t('Cédula / Tax ID'));
    }
    if (!partner.email) {
        missing.push(_t('Email Address'));
    } else if (!EMAIL_REGEX.test(partner.email.trim())) {
        missing.push(_t('Valid Email Address'));
    }

    // CIIU mandatory since Oct 6, 2025
    if (ciiuMandatoryDate && new Date() >= new Date(ciiuMandatoryDate)) {
        if (!partner.l10n_cr_activity_code) {
            missing.push(_t('Economic Activity (CIIU Code)'));
        }
    }

    return { valid: missing.length === 0, missing };
}

/**
 * Patch PaymentScreen for E-Invoice UI controls and Validate button gating.
 *
 * Key design: the Validate button state is driven by `canValidateOrder` getter
 * on PaymentScreen, which reads from the reactive `einvoiceState` (useState).
 * This avoids reading model fields through the WithLazyGetterTrap proxy,
 * ensuring OWL reactivity works correctly.
 *
 * The template override in pos_einvoice.xml replaces the Validate button's
 * class expression with `{{ canValidateOrder ? 'highlight' : 'disabled' }}`.
 */
patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.dialog = useService("dialog");

        // Reactive state for e-invoice UI — drives component re-renders.
        // This is the SINGLE SOURCE OF TRUTH for the e-invoice toggle state.
        const order = this.currentOrder;
        const enabled = order ? (order.l10n_cr_is_einvoice || false) : false;
        let type = 'TE';
        if (enabled && order) {
            const partner = order.getPartner();
            type = (partner && partner.vat) ? 'FE' : 'TE';
        }
        this.einvoiceState = useState({ enabled, type });

        // Sync initial state to order (for serialization to server)
        if (order) {
            order.l10n_cr_is_einvoice = this.einvoiceState.enabled;
            order.einvoice_type = this.einvoiceState.type;
        }
    },

    get einvoiceEnabled() {
        return this.einvoiceState.enabled;
    },

    get einvoiceType() {
        return this.einvoiceState.type;
    },

    /**
     * Master validation getter for the Validate button.
     * Combines Odoo's base validation + FE requirements.
     *
     * Used directly in the template (overridden in pos_einvoice.xml) instead of
     * currentOrder.canBeValidated(), because the reactive einvoiceState lives here
     * on the PaymentScreen component, not on the PosOrder record.
     */
    get canValidateOrder() {
        const order = this.currentOrder;
        if (!order) {
            return false;
        }

        // Base Odoo checks: order is paid, has items/payments, no refund in process
        if (!order.canBeValidated() || order.isRefundInProcess()) {
            return false;
        }

        // E-invoice FE requirements — only when Factura Electrónica is selected
        if (this.einvoiceState.enabled && this.einvoiceState.type === 'FE') {
            const partner = order.getPartner();
            const ciiuDate = this.pos?.config?._l10n_cr_ciiu_mandatory_date;
            const { valid } = checkFERequirements(partner, ciiuDate);
            return valid;
        }

        return true;
    },

    /**
     * Override validateOrder to show a helpful dialog when FE requirements are missing.
     * Even though the button is grayed out, it's still clickable (Odoo uses CSS class,
     * not HTML disabled attribute). This catches clicks on the "disabled" button.
     */
    async validateOrder(isForceValidate) {
        const order = this.currentOrder;
        if (order && this.einvoiceState.enabled && this.einvoiceState.type === 'FE') {
            const partner = order.getPartner();
            const ciiuDate = this.pos?.config?._l10n_cr_ciiu_mandatory_date;
            const { valid, missing } = checkFERequirements(partner, ciiuDate);

            if (!valid) {
                this.dialog.add(AlertDialog, {
                    title: _t('Factura Electrónica - Missing Information'),
                    body: _t('The following information is required for Factura Electrónica (FE):\n\n') +
                          missing.map(f => '- ' + f).join('\n') +
                          '\n\n' + _t('Please complete the customer data or switch to Tiquete Electrónico (TE).'),
                });
                return;
            }
        }
        await super.validateOrder(isForceValidate);
    },

    toggleEinvoiceEnabled() {
        const order = this.currentOrder;
        const newEnabled = !this.einvoiceState.enabled;
        let newType = this.einvoiceState.type;

        if (newEnabled) {
            // Just enabled — set document type based on partner
            const partner = order.getPartner();
            newType = (partner && partner.vat) ? 'FE' : 'TE';
        }

        // Update reactive state (triggers re-render → canValidateOrder re-evaluated)
        this.einvoiceState.enabled = newEnabled;
        this.einvoiceState.type = newType;

        // Sync to order for serialization to server via serializeForORM()
        order.l10n_cr_is_einvoice = newEnabled;
        order.einvoice_type = newType;
    },

    selectTiquete() {
        this.einvoiceState.type = 'TE';
        this.currentOrder.einvoice_type = 'TE';
    },

    selectFactura() {
        const partner = this.currentOrder.getPartner();
        if (!partner || !partner.vat) {
            this.dialog.add(AlertDialog, {
                title: _t('Factura Electrónica'),
                body: _t('Para emitir Factura Electrónica (FE) debe seleccionar un cliente con cédula/NIT.\n\nSeleccione un cliente primero o use Tiquete Electrónico (TE).'),
            });
            return;
        }
        this.einvoiceState.type = 'FE';
        this.currentOrder.einvoice_type = 'FE';
    },
});

/**
 * Patch ReceiptScreen to show e-invoice feedback notification.
 * After order sync, Hacienda has already responded (synchronous flow).
 * We fetch the result and show a toast: green=accepted, red=rejected, etc.
 */
patch(ReceiptScreen.prototype, {
    setup() {
        super.setup();

        onMounted(async () => {
            const order = this.currentOrder;
            if (order && order.l10n_cr_is_einvoice) {
                await this._showEinvoiceFeedback(order);
            }
        });
    },

    async _showEinvoiceFeedback(order) {
        try {
            const result = await this.pos.data.call(
                "pos.order",
                "get_einvoice_feedback",
                [[order.id]]
            );
            if (result && result.message) {
                this.notification.add(result.message, { type: result.type });
            }
        } catch {
            // Silent fail — never block the receipt screen
        }
    },
});
