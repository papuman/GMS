/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

// CIIU mandatory date (October 6, 2025)
const CIIU_MANDATORY_DATE = new Date('2025-10-06');

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

        // After Oct 6, 2025: CIIU code required
        if (new Date() >= CIIU_MANDATORY_DATE && !partner.l10n_cr_economic_activity_id) {
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
 * Patch PaymentScreen for E-Invoice UI controls
 */
patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.dialog = useService("dialog");

        onMounted(() => {
            const order = this.currentOrder;
            if (order) {
                // Default is NO e-invoice (user must explicitly enable)
                if (order.l10n_cr_is_einvoice === undefined) {
                    order.l10n_cr_is_einvoice = false;
                }

                // Smart default for document type
                if (order.l10n_cr_is_einvoice && !order.einvoice_type) {
                    const partner = order.getPartner();
                    order.einvoice_type = (partner && partner.vat) ? 'FE' : 'TE';
                }
            }
        });
    },

    async validateOrder(isForceValidate) {
        // Check e-invoice requirements before proceeding
        const order = this.currentOrder;
        if (order && order.l10n_cr_is_einvoice && order.einvoice_type === 'FE') {
            const partner = order.getPartner();
            const missing = [];

            if (!partner) {
                missing.push(_t('Customer (select a customer first)'));
            } else {
                if (!partner.name) missing.push(_t('Customer Name'));
                if (!partner.vat) missing.push(_t('Cédula / Tax ID'));
                if (!partner.email) missing.push(_t('Email Address'));
                // Only check CIIU after Oct 6, 2025
                if (new Date() >= CIIU_MANDATORY_DATE && !partner.l10n_cr_economic_activity_id) {
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
        order.l10n_cr_is_einvoice = !order.l10n_cr_is_einvoice;

        if (order.l10n_cr_is_einvoice) {
            // Just enabled - set document type based on partner
            const partner = order.getPartner();
            order.einvoice_type = (partner && partner.vat) ? 'FE' : 'TE';
        }
    },

    selectTiquete() {
        this.currentOrder.einvoice_type = 'TE';
    },

    selectFactura() {
        this.currentOrder.einvoice_type = 'FE';
    },
});
