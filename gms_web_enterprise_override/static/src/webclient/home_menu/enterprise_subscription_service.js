/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SubscriptionManager } from "@web_enterprise/webclient/home_menu/enterprise_subscription_service";
import { _t } from "@web/core/l10n/translation";

// Patch the SubscriptionManager to disable Odoo.com redirects
patch(SubscriptionManager.prototype, {
    /**
     * Override buy method to prevent redirect to odoo.com
     * Instead, show a notification with contact information
     */
    async buy() {
        this.notification.add(
            _t(
                "To purchase or upgrade your subscription, please contact your system administrator or SHAAR support."
            ),
            {
                type: "info",
                title: _t("License Purchase")
            }
        );
    },

    /**
     * Override renew method to prevent redirect to odoo.com
     * Instead, show a notification with contact information
     */
    async renew() {
        this.notification.add(
            _t(
                "To renew your subscription, please contact your system administrator or SHAAR support."
            ),
            {
                type: "info",
                title: _t("License Renewal")
            }
        );
    },

    /**
     * Override upsell method to prevent redirect to odoo.com
     * Instead, show a notification with contact information
     */
    async upsell() {
        this.notification.add(
            _t(
                "To upgrade your subscription for additional users or apps, please contact your system administrator or SHAAR support."
            ),
            {
                type: "info",
                title: _t("Subscription Upgrade")
            }
        );
    },
});
