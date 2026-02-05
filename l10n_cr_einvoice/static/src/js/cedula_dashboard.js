/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * Cédula Lookup Dashboard Client Action
 *
 * Real-time monitoring dashboard for cache health, API metrics, and usage statistics.
 */
class CedulaDashboard extends Component {
    static template = "l10n_cr_einvoice.CedulaDashboard";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            loading: true,
            data: null,
            lastUpdated: null,
        });

        // Auto-refresh every 30 seconds
        this.refreshInterval = null;

        onMounted(() => {
            this.loadDashboardData();
            this.refreshInterval = setInterval(() => {
                this.loadDashboardData();
            }, 30000); // 30 seconds
        });

        onWillUnmount(() => {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
        });
    }

    /**
     * Load dashboard data from backend
     */
    async loadDashboardData() {
        try {
            const data = await this.orm.call(
                "l10n_cr.cedula.dashboard",
                "get_dashboard_data",
                []
            );

            this.state.data = data;
            this.state.lastUpdated = new Date();
            this.state.loading = false;

            // Update DOM elements
            this.updateDashboardUI(data);
        } catch (error) {
            console.error("Failed to load dashboard data:", error);
            this.notification.add(
                this.env._t("Failed to load dashboard data"),
                { type: "danger" }
            );
        }
    }

    /**
     * Update dashboard UI with fresh data
     */
    updateDashboardUI(data) {
        if (!data) return;

        // Cache Health Metrics
        this.updateElement("total_cached", data.cache_health.total_cached);
        this.updateElement("fresh_count", data.cache_health.fresh_count);
        this.updateElement("refresh_needed", data.cache_health.refresh_needed);
        this.updateElement("stale_count", data.cache_health.stale_count);
        this.updateElement("expired_count", data.cache_health.expired_count);
        this.updateElement("cache_coverage", data.cache_health.cache_coverage + "%");
        this.updateElement("hit_rate", data.cache_health.hit_rate + "%");

        // Calculate fresh percentage
        if (data.cache_health.total_cached > 0) {
            const freshPct = (data.cache_health.fresh_count / data.cache_health.total_cached * 100).toFixed(1);
            this.updateElement("fresh_pct", freshPct + "%");
        }

        // Health Status
        this.updateElement("health_status", data.cache_health.health_status.toUpperCase());
        const healthIndicator = document.getElementById("health_indicator");
        if (healthIndicator) {
            const colors = {
                'healthy': '#28a745',
                'warning': '#ffc107',
                'critical': '#dc3545',
            };
            healthIndicator.style.backgroundColor = colors[data.cache_health.health_status] || '#6c757d';
        }

        // API Performance Metrics
        this.updateElement("api_success_rate", data.api_performance.success_rate + "%");
        this.updateElement("api_total_lookups", data.api_performance.total_lookups + " lookups");
        this.updateElement("api_failed_lookups", data.api_performance.failed_lookups);
        this.updateElement("api_failure_rate", data.api_performance.failure_rate + "% failure");
        this.updateElement("api_avg_response", data.api_performance.avg_response_time.toFixed(2) + "s");
        this.updateElement("api_rate_limit_hits", data.api_performance.rate_limit_hits);
        this.updateElement("api_fallback_count", data.api_performance.fallback_gometa_count);
        this.updateElement("api_not_found_count", data.api_performance.not_found_count);

        // Usage Statistics - Today
        this.updateElement("usage_today_total", data.usage_today.total_lookups);
        this.updateElement("usage_today_unique", data.usage_today.unique_cedulas);
        this.updateElement("usage_today_hits", data.usage_today.cache_hits);
        this.updateElement("usage_today_api", data.usage_today.api_calls);

        // Usage Statistics - Week
        this.updateElement("usage_week_total", data.usage_week.total_lookups);
        this.updateElement("usage_week_unique", data.usage_week.unique_cedulas);
        this.updateElement("usage_week_avg", data.usage_week.avg_lookups_per_day.toFixed(1));
        this.updateElement("usage_week_peak", data.usage_week.peak_hour + ":00");

        // Usage Statistics - Month
        this.updateElement("usage_month_total", data.usage_month.total_lookups);
        this.updateElement("usage_month_unique", data.usage_month.unique_cedulas);
        this.updateElement("usage_month_avg", data.usage_month.avg_lookups_per_day.toFixed(1));
        if (data.usage_month.total_lookups > 0) {
            const monthHitRate = (data.usage_month.cache_hits / data.usage_month.total_lookups * 100).toFixed(1);
            this.updateElement("usage_month_hit_rate", monthHitRate + "%");
        }

        // Top Looked-Up Cédulas Table
        this.updateTopCedulasTable(data.top_cedulas);
    }

    /**
     * Update DOM element text content
     */
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    /**
     * Update top cédulas table
     */
    updateTopCedulasTable(topCedulas) {
        const tbody = document.getElementById("top_cedulas_tbody");
        if (!tbody || !topCedulas) return;

        tbody.innerHTML = "";

        if (topCedulas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No data available</td></tr>';
            return;
        }

        topCedulas.forEach((cedula, index) => {
            const tierColors = {
                'fresh': 'success',
                'refresh': 'warning',
                'stale': 'orange',
                'expired': 'danger',
            };
            const tierClass = tierColors[cedula.cache_tier] || 'secondary';

            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${index + 1}</td>
                <td><strong>${cedula.cedula}</strong></td>
                <td>${cedula.name}</td>
                <td><span class="badge bg-info">${cedula.access_count}</span></td>
                <td><span class="badge bg-${tierClass}">${cedula.cache_tier}</span></td>
                <td>${cedula.last_access || 'Never'}</td>
            `;
            tbody.appendChild(row);
        });
    }

    /**
     * Manual refresh button handler
     */
    async onRefreshClick() {
        await this.loadDashboardData();
        this.notification.add(
            this.env._t("Dashboard refreshed"),
            { type: "success" }
        );
    }

    /**
     * Refresh stale cache button handler
     */
    async onRefreshStaleCache() {
        try {
            await this.orm.call(
                "l10n_cr.cedula.dashboard",
                "action_refresh_stale_cache",
                []
            );
            this.notification.add(
                this.env._t("Cache refresh started"),
                { type: "success" }
            );
            // Reload dashboard after 2 seconds
            setTimeout(() => this.loadDashboardData(), 2000);
        } catch (error) {
            this.notification.add(
                this.env._t("Failed to refresh cache"),
                { type: "danger" }
            );
        }
    }

    /**
     * Purge expired cache button handler
     */
    async onPurgeExpiredCache() {
        try {
            const result = await this.orm.call(
                "l10n_cr.cedula.dashboard",
                "action_purge_expired_cache",
                []
            );
            this.notification.add(
                this.env._t("Expired cache entries purged"),
                { type: "success" }
            );
            // Reload dashboard
            await this.loadDashboardData();
        } catch (error) {
            this.notification.add(
                this.env._t("Failed to purge cache"),
                { type: "danger" }
            );
        }
    }

    /**
     * View cache entries button handler
     */
    async onViewCacheEntries() {
        try {
            const action = await this.orm.call(
                "l10n_cr.cedula.dashboard",
                "action_view_cache_entries",
                []
            );
            this.actionService.doAction(action);
        } catch (error) {
            this.notification.add(
                this.env._t("Failed to open cache entries"),
                { type: "danger" }
            );
        }
    }

    /**
     * Test API connection button handler
     */
    async onTestAPIConnection() {
        try {
            await this.orm.call(
                "l10n_cr.cedula.dashboard",
                "action_test_api_connection",
                []
            );
            this.notification.add(
                this.env._t("API connection test successful"),
                { type: "success" }
            );
        } catch (error) {
            this.notification.add(
                this.env._t("API connection test failed"),
                { type: "danger" }
            );
        }
    }
}

// Register the client action
registry.category("actions").add("cedula_dashboard", CedulaDashboard);

export default CedulaDashboard;
