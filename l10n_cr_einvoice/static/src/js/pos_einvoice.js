/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onMounted, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

// Email validation regex
const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

/**
 * Patch PosOrder to extend canBeValidated() - the Odoo way
 * This grays out the Validate button when requirements aren't met
 */
patch(PosOrder.prototype, {
    /**
     * Check if e-invoice requirements are met for Factura (FE)
     */
    isEinvoiceValid() {
        // If e-invoice not enabled, always valid
        if (!this.l10n_cr_is_einvoice) {
            return true;
        }

        // Tiquete has no requirements
        if (this.einvoice_type === 'TE') {
            return true;
        }

        // Factura requires customer with complete data
        const partner = this.getPartner();
        if (!partner) {
            return false;
        }

        // Required: name, vat, email
        if (!partner.name || !partner.vat || !partner.email) {
            return false;
        }

        // Email must be valid format
        if (!EMAIL_REGEX.test(partner.email.trim())) {
            return false;
        }

        // After CIIU mandatory date: CIIU code required (date loaded from server config)
        const ciiuDate = this.pos?.config?._l10n_cr_ciiu_mandatory_date;
        if (ciiuDate && new Date() >= new Date(ciiuDate) && !partner.l10n_cr_activity_code) {
            return false;
        }

        return true;
    },

    /**
     * Override canBeValidated to include e-invoice requirements
     * This is the Odoo pattern - Validate button grays out automatically
     */
    canBeValidated() {
        // First check standard Odoo requirements (isPaid, valid empty order)
        const baseValid = super.canBeValidated();
        if (!baseValid) {
            return false;
        }

        // Then check e-invoice requirements
        return this.isEinvoiceValid();
    },

    // Include E-Invoice fields in Receipt
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        if (result) {
            if (this.l10n_cr_clave) {
                result.l10n_cr_clave = this.l10n_cr_clave;
            }
            if (this.l10n_cr_qr_code) {
                result.l10n_cr_qr_code = this.l10n_cr_qr_code;
            }
        }
        return result;
    },

    // Include E-Invoice fields when saving order
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.l10n_cr_is_einvoice = this.l10n_cr_is_einvoice || false;
        json.einvoice_type = this.einvoice_type || 'TE';
        return json;
    }
});

/**
 * Patch PaymentScreen for E-Invoice UI controls.
 *
 * POS model records are NOT individually reactive (only RecordStore is).
 * Direct property assignment (order.field = value) doesn't trigger re-renders.
 * We use useState() to create a reactive trigger — when einvoiceState changes,
 * the component re-renders, re-evaluating canBeValidated() with the updated values.
 */
patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.dialog = useService("dialog");

        // Reactive state for e-invoice UI — drives component re-renders
        const order = this.currentOrder;
        const enabled = order ? (order.l10n_cr_is_einvoice || false) : false;
        let type = 'TE';
        if (enabled && order) {
            const partner = order.getPartner();
            type = (partner && partner.vat) ? 'FE' : 'TE';
        }
        this.einvoiceState = useState({ enabled, type });

        // Sync initial state to order
        if (order) {
            order.l10n_cr_is_einvoice = this.einvoiceState.enabled;
            order.einvoice_type = this.einvoiceState.type;
        }
    },

    get einvoiceEnabled() {
        return this.einvoiceState.enabled;
    },

    get einvoiceType() {
        // Pure getter — no side effects during render
        return this.einvoiceState.type;
    },

    async validateOrder(isForceValidate) {
        // Check e-invoice requirements before proceeding
        const order = this.currentOrder;
        if (order && this.einvoiceState.enabled && this.einvoiceState.type === 'FE') {
            const partner = order.getPartner();
            const missing = [];

            if (!partner) {
                missing.push(_t('Customer (select a customer first)'));
            } else {
                if (!partner.name) missing.push(_t('Customer Name'));
                if (!partner.vat) missing.push(_t('Cédula / Tax ID'));
                if (!partner.email) missing.push(_t('Email Address'));
                // Only check CIIU after mandatory date (loaded from server config)
                const ciiuDate = this.pos?.config?._l10n_cr_ciiu_mandatory_date;
                if (ciiuDate && new Date() >= new Date(ciiuDate) && !partner.l10n_cr_activity_code) {
                    missing.push(_t('Economic Activity (CIIU Code)'));
                }
            }

            if (missing.length > 0) {
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
            // Just enabled - set document type based on partner
            const partner = order.getPartner();
            newType = (partner && partner.vat) ? 'FE' : 'TE';
        }

        // Update reactive state (triggers re-render → canBeValidated() re-evaluated)
        this.einvoiceState.enabled = newEnabled;
        this.einvoiceState.type = newType;

        // Sync to order for persistence/serialization
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

    /**
     * Call this when the partner changes on the current order.
     * Re-derives the e-invoice document type (FE vs TE) from the new partner.
     * If e-invoice is not enabled, this is a no-op.
     */
    onPartnerChange() {
        if (this.einvoiceState.enabled) {
            const partner = this.currentOrder.getPartner();
            const newType = (partner && partner.vat) ? 'FE' : 'TE';
            this.einvoiceState.type = newType;
            this.currentOrder.einvoice_type = newType;
        }
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
