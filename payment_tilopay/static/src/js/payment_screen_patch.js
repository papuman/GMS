/** @odoo-module **/
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    /**
     * Fix: the original paymentMethodImage() references `this.paymentMethod`
     * which is undefined — the template passes `paymentMethod.id` from a
     * t-foreach loop variable, but the method never resolves the object.
     *
     * This patch looks up the payment method by id from the config list,
     * then applies the correct image logic.
     */
    paymentMethodImage(id) {
        const pm = this.payment_methods_from_config.find((m) => m.id === id);
        if (pm && pm.image) {
            return `/web/image/pos.payment.method/${id}/image`;
        } else if (pm && pm.type === "cash") {
            return "/point_of_sale/static/src/img/money.png";
        } else if (pm && pm.type === "pay_later") {
            return "/point_of_sale/static/src/img/pay-later.png";
        } else {
            return "/point_of_sale/static/src/img/card-bank.png";
        }
    },
});
