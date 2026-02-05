/** @odoo-module **/

console.log('[E-Invoice TEST] Module loaded successfully!');

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.pos = useService("pos");
        console.log('[E-Invoice TEST] PaymentScreen patch applied!');
        console.log('[E-Invoice TEST] Methods:', {
            toggleEinvoiceEnabled: typeof this.toggleEinvoiceEnabled,
            setEinvoiceType: typeof this.setEinvoiceType,
        });

        onMounted(() => {
            const order = this.currentOrder;
            if (order) {
                if (order.l10n_cr_is_einvoice === undefined) {
                    order.l10n_cr_is_einvoice = false;
                }
                if (order.l10n_cr_is_einvoice && !order.einvoice_type) {
                    const partner = order.getPartner();
                    if (partner && partner.vat) {
                        order.einvoice_type = 'FE';
                    } else {
                        order.einvoice_type = 'TE';
                    }
                }
            }
        });
    },

    get currentOrder() {
        // Odoo 19: pos.get_order() changed to pos.selectedOrder
        return this.pos.selectedOrder || this.pos.get_order?.() || this.pos.order;
    },

    toggleEinvoiceEnabled() {
        console.log('[E-Invoice TEST] toggleEinvoiceEnabled called');
        const order = this.currentOrder;
        order.l10n_cr_is_einvoice = !order.l10n_cr_is_einvoice;

        if (order.l10n_cr_is_einvoice) {
            const partner = order.getPartner();
            if (partner && partner.vat) {
                order.einvoice_type = 'FE';
            } else {
                order.einvoice_type = 'TE';
            }
            // Don't auto-open partner selector - let user decide
            // Odoo 19: selectPartner() method doesn't exist
        }
        this.render(true);
    },

    // Wrapper methods - required because OWL templates can't use arrow functions with parameters
    selectTiquete() {
        console.log('[E-Invoice TEST] selectTiquete called');
        this.setEinvoiceType('TE');
    },

    selectFactura() {
        console.log('[E-Invoice TEST] selectFactura called');
        this.setEinvoiceType('FE');
    },

    setEinvoiceType(type) {
        console.log('[E-Invoice TEST] setEinvoiceType called with:', type);
        this.currentOrder.einvoice_type = type;

        // Show warning in UI if FE selected without partner (warning already in template)
        // Don't auto-open - user can click Customer button
        this.render(true);
    },

    async validateOrder(isForceValidate) {
        const order = this.currentOrder;
        if (!order.l10n_cr_is_einvoice) {
            return await super.validateOrder(isForceValidate);
        }
        if (order.einvoice_type === 'FE') {
            if (!order.getPartner()) {
                // Show error - user must select customer for Factura
                console.error('[E-Invoice] Factura requires a customer');
                // Don't proceed - let existing Customer button handle selection
                return;
            }
            if (!order.getPartner().vat) {
                console.warn('[E-Invoice] Partner has no VAT number for Factura');
            }
        }
        return await super.validateOrder(isForceValidate);
    }
});

console.log('[E-Invoice TEST] Module fully loaded - Order patch removed temporarily');
