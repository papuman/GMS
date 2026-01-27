/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.pos = useService("pos");
        this.popup = useService("popup"); // Assuming popup service is needed for popup.add

        onMounted(() => {
            const order = this.pos.get_order();
            if (order) {
                // Smart Default: If partner has VAT, assume Factura
                const partner = order.get_partner();
                if (!order.einvoice_type) {
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

        // Pass data to backend by setting it on the order before validation
        this.currentOrder.l10n_cr_is_einvoice = true;
        // The export_as_JSON method in the model will need to include this

        // Show processing feedback (optional, as validation usually closes screen)
        // this.env.services.notification.add(this.env._t("Generando documento electrónico..."), { type: "info", duration: 2000 });

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
