/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.pos = useService("pos");
        this.popup = useService("popup");

        onMounted(() => {
            const order = this.pos.get_order();
            if (order) {
                // CRITICAL: Default is NO e-invoice (user must explicitly enable)
                if (order.l10n_cr_is_einvoice === undefined) {
                    order.l10n_cr_is_einvoice = false;
                }

                // Smart Default for document type ONLY if e-invoice enabled
                if (order.l10n_cr_is_einvoice && !order.einvoice_type) {
                    const partner = order.get_partner();
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
        return this.pos.get_order();
    },

    toggleEinvoiceEnabled() {
        const order = this.currentOrder;
        order.l10n_cr_is_einvoice = !order.l10n_cr_is_einvoice;

        if (order.l10n_cr_is_einvoice) {
            // Just enabled - set document type based on partner
            const partner = order.get_partner();
            if (partner && partner.vat) {
                order.einvoice_type = 'FE';
            } else {
                order.einvoice_type = 'TE';
            }

            // Auto-open partner selection if no partner set
            if (!partner) {
                this.selectPartner();
            }
        }
    },

    setEinvoiceType(type) {
        this.currentOrder.einvoice_type = type;

        // Auto-open partner selection if FE is chosen and no partner
        if (type === 'FE' && !this.currentOrder.get_partner()) {
            this.selectPartner();
        }
    },

    toggleEinvoiceType() {
        const newType = this.currentOrder.einvoice_type === 'FE' ? 'TE' : 'FE';
        this.setEinvoiceType(newType);
    },

    async validateOrder(isForceValidate) {
        // CRITICAL: Only validate e-invoice fields if e-invoice is ENABLED
        if (this.currentOrder.l10n_cr_is_einvoice) {
            // Validation Block: Factura requires Partner
            if (this.currentOrder.einvoice_type === 'FE' && !this.currentOrder.get_partner()) {
                const { confirmed } = await this.popup.add('ConfirmPopup', {
                    title: this.env._t('Cliente Requerido'),
                    body: this.env._t('Para Factura se requiere cliente. ¿Desea cambiar a Tiquete (Anónimo) y continuar?'),
                    confirmText: this.env._t('Sí, usar Tiquete'),
                    cancelText: this.env._t('No, seleccionar cliente')
                });

                if (confirmed) {
                    this.setEinvoiceType('TE');
                    await this.validateOrder(isForceValidate); // Recursively call validate with new type
                    return;
                } else {
                    this.selectPartner();
                    return;
                }
            }

            // Validation Block: Factura requires ID Number
            if (this.currentOrder.einvoice_type === 'FE' && this.currentOrder.get_partner() && !this.currentOrder.get_partner().vat) {
                const { confirmed } = await this.popup.add('ConfirmPopup', {
                    title: this.env._t('Cliente sin Cédula'),
                    body: this.env._t('El cliente seleccionado no tiene número de cédula. ¿Desea continuar (esto podría causar rechazo en Hacienda)?'),
                });
                if (!confirmed) return;
            }

            // Show processing feedback
            // this.env.services.notification.add(this.env._t("Generando documento electrónico..."), { type: "info", duration: 2000 });
        }

        // The export_as_JSON method will include l10n_cr_is_einvoice flag for backend

        await super.validateOrder(isForceValidate);
    }
});

// Patch Order to include E-Invoice fields in Receipt
import { Order } from "@point_of_sale/app/store/models";

patch(Order.prototype, {
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        if (this.l10n_cr_clave) {
            result.l10n_cr_clave = this.l10n_cr_clave;
        }
        if (this.l10n_cr_qr_code) {
            result.l10n_cr_qr_code = this.l10n_cr_qr_code;
        }
        return result;
    },
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.l10n_cr_is_einvoice = this.l10n_cr_is_einvoice || false;
        json.einvoice_type = this.einvoice_type || 'TE';
        return json;
    }
});
