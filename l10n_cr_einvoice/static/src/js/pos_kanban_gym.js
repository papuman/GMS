/** @odoo-module **/

import { PosKanbanRenderer } from "@point_of_sale/backend/pos_kanban_view/pos_kanban_view";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(PosKanbanRenderer.prototype, {
    get shopScenarios() {
        const scenarios = super.shopScenarios;

        // Add Gym scenario to the shop scenarios
        scenarios.push({
            name: _t("Gym"),
            description: _t("Memberships, day passes, personal training"),
            functionName: "load_onboarding_gym_scenario",
            iconFile: this.isDarkTheme
                ? "gym-icon-dark.png"
                : "gym-icon.png",
        });

        return scenarios;
    }
});
