/** @odoo-module **/

import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

/**
 * Cédula Lookup Component for POS
 *
 * Enhances partner selection with real-time Hacienda API lookup:
 * - Auto-fill customer data from government database
 * - Cache status indicators (fresh/stale/new)
 * - Visual feedback for API calls
 * - Error handling with fallback options
 */

patch(PartnerList.prototype, {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.dialog = useService("dialog");

        // Lookup state
        this.lookupState = useState({
            isLookingUp: false,
            cedulaInput: '',
            lastLookupResult: null,
            showSuggestion: false,
            cacheStatus: null,
        });
    },

    /**
     * Handle cédula input change with debounced validation
     */
    onCedulaInput(ev) {
        const cedula = ev.target.value;
        this.lookupState.cedulaInput = cedula;

        // Clear previous suggestion
        this.lookupState.showSuggestion = false;
        this.lookupState.lastLookupResult = null;

        // Debounce validation
        clearTimeout(this._validationTimeout);
        this._validationTimeout = setTimeout(() => {
            this.validateCedulaFormat(cedula);
        }, 500);
    },

    /**
     * Validate cédula format without API call
     */
    async validateCedulaFormat(cedula) {
        if (!cedula || cedula.trim() === '') {
            return;
        }

        try {
            const result = await this.rpc('/pos/cedula/validate', {
                cedula: cedula
            });

            if (result.valid) {
                // Format input field
                this.lookupState.cedulaInput = result.formatted;

                // Check cache status
                this.checkCacheStatus(result.clean);
            } else {
                // Show validation error
                this.notification.add(result.error, {
                    type: 'warning',
                    duration: 3000
                });
            }
        } catch (error) {
            console.error('Validation error:', error);
        }
    },

    /**
     * Check if cédula exists in cache
     */
    async checkCacheStatus(cedula) {
        try {
            const status = await this.rpc('/pos/cedula/cache_status', {
                cedula: cedula
            });

            this.lookupState.cacheStatus = status;

            // Show suggestion if in cache
            if (status.in_cache && status.status === 'fresh') {
                this.notification.add(
                    _t('Found in cache - Click "Lookup" to auto-fill'),
                    { type: 'info', duration: 3000 }
                );
            }
        } catch (error) {
            console.error('Cache status error:', error);
        }
    },

    /**
     * Perform cédula lookup with API call
     */
    async performCedulaLookup(forceRefresh = false) {
        const cedula = this.lookupState.cedulaInput;

        if (!cedula || cedula.trim() === '') {
            this.notification.add(
                _t('Please enter a cédula number'),
                { type: 'warning', duration: 3000 }
            );
            return;
        }

        this.lookupState.isLookingUp = true;
        this.lookupState.showSuggestion = false;

        try {
            const result = await this.rpc('/pos/cedula/lookup', {
                cedula: cedula,
                force_refresh: forceRefresh
            });

            this.lookupState.lastLookupResult = result;

            if (result.success) {
                // Show suggestion dialog
                this.lookupState.showSuggestion = true;
                this.showLookupModal(result);
            } else {
                // Show error
                this.handleLookupError(result);
            }
        } catch (error) {
            console.error('Lookup error:', error);
            this.notification.add(
                _t('System error. Please try again.'),
                { type: 'danger', duration: 5000 }
            );
        } finally {
            this.lookupState.isLookingUp = false;
        }
    },

    /**
     * Show lookup results modal
     */
    showLookupModal(result) {
        const { data, source, cache_info } = result;

        // Build description for confirmation dialog
        let description = _t('Name: ') + data.name + '\n';
        description += _t('Tax ID (Cédula): ') + data.vat + '\n';
        description += _t('Tax Regime: ') + (data.tax_regime || 'N/A') + '\n';
        description += _t('Source: ') + source;

        if (cache_info && cache_info.age_days !== undefined) {
            description += ' (' + cache_info.age_days + _t(' days old)');
        }

        if (data.ciiu_codes && data.ciiu_codes.length > 0) {
            description += '\n\n' + _t('Economic Activities:');
            data.ciiu_codes.forEach(ciiu => {
                description += '\n- ' + ciiu.code + ': ' + ciiu.description;
                if (ciiu.primary) {
                    description += ' (' + _t('Primary') + ')';
                }
            });
        }

        if (result.warning) {
            description += '\n\n' + _t('Warning: ') + result.warning;
        }

        description += '\n\n' + _t('Email is not provided by Hacienda API. You will be prompted to enter it after confirmation.');

        // Show modal using Odoo 19's ConfirmationDialog
        this.dialog.add(ConfirmationDialog, {
            title: _t('Company Found in Hacienda Registry'),
            body: description,
            confirmLabel: _t('Use This Data'),
            cancelLabel: _t('Cancel'),
            confirm: () => this.createPartnerFromLookup(result),
        });
    },

    /**
     * Handle lookup errors
     */
    handleLookupError(result) {
        const { error_type, message } = result;

        let errorTitle = _t('Lookup Failed');
        let errorBody = message || _t('Unknown error occurred');

        if (error_type === 'not_found') {
            errorTitle = _t('Cédula Not Found');
            errorBody = _t('This cédula may not be registered with Hacienda or may be invalid. You can still create the customer manually.');
        } else if (error_type === 'rate_limit') {
            errorTitle = _t('Rate Limit Exceeded');
            errorBody = _t('Too many requests. Please wait a moment and try again.');
        } else if (error_type === 'network' || error_type === 'timeout') {
            errorTitle = _t('Network Error');
            errorBody = _t('Cannot reach Hacienda API. Please check your connection and try again.');
        }

        this.dialog.add(ConfirmationDialog, {
            title: errorTitle,
            body: errorBody,
            confirmLabel: _t('OK'),
        });
    },

    /**
     * Create partner from lookup data
     */
    async createPartnerFromLookup(lookupResult) {
        const { data } = lookupResult;

        // Prompt for email (required for FE invoices)
        const email = await this.promptForEmail(data.name);

        if (!email) {
            this.notification.add(
                _t('Email is required for Factura Electrónica'),
                { type: 'warning', duration: 3000 }
            );
            return;
        }

        // Validate email format
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(email)) {
            this.notification.add(
                _t('Invalid email format'),
                { type: 'danger', duration: 3000 }
            );
            return;
        }

        try {
            // Create partner
            const partnerId = await this.rpc('/web/dataset/call_kw', {
                model: 'res.partner',
                method: 'create',
                args: [{
                    name: data.name,
                    vat: data.vat,
                    email: email,
                    l10n_cr_economic_activity_id: data.suggested_ciiu_id,
                    l10n_cr_cedula_verified: true,
                    l10n_cr_last_verified: new Date().toISOString(),
                    l10n_cr_verification_source: lookupResult.source,
                }],
                kwargs: {},
            });

            // Reload partners and find the newly created one
            // Force reload to get fresh data from server
            await this.pos.data.callRelated("res.partner", "get_new_partner", [
                this.pos.config.id,
                [['id', '=', partnerId]],
                0,
            ]);

            const allPartners = this.pos.models["res.partner"].getAll();
            const newPartner = allPartners.find(p => p.id === partnerId);

            if (newPartner) {
                // Use Odoo 19 PartnerList pattern: pass partner via getPayload callback
                this.props.getPayload(newPartner);
            }

            this.notification.add(
                _t('Customer created successfully'),
                { type: 'success', duration: 3000 }
            );

            // Close partner selection screen using Odoo 19 API
            this.props.close();

        } catch (error) {
            console.error('Error creating partner:', error);
            this.notification.add(
                _t('Error creating customer. Please try again.'),
                { type: 'danger', duration: 5000 }
            );
        }
    },

    /**
     * Prompt user for email input
     */
    async promptForEmail(companyName) {
        return new Promise((resolve) => {
            // Create a temporary input element to capture email
            let emailValue = '';

            const promptBody = _t('Email is required for sending electronic invoices (Factura Electrónica) to ') + companyName + '.';

            this.dialog.add(ConfirmationDialog, {
                title: _t('Enter Customer Email'),
                body: promptBody,
                confirmLabel: _t('Confirm'),
                cancelLabel: _t('Cancel'),
                confirm: () => {
                    // Since ConfirmationDialog doesn't support custom inputs,
                    // we need to prompt using browser's prompt as fallback
                    const input = window.prompt(_t('Enter email address for ') + companyName);
                    resolve(input ? input.trim() : '');
                },
                cancel: () => resolve(''),
            });
        });
    },

    /**
     * Auto-lookup when VAT is entered in partner form
     */
    async onPartnerVatChange(partner, vat) {
        if (!vat || vat.trim() === '') {
            return;
        }

        // Check if already verified
        if (partner.l10n_cr_cedula_verified) {
            return;
        }

        // Auto-trigger lookup
        this.lookupState.cedulaInput = vat;

        // Show suggestion notification
        this.notification.add(
            _t('Click "Lookup by Cédula" to auto-fill from Hacienda'),
            { type: 'info', duration: 5000 }
        );
    },

    /**
     * Force refresh lookup (skip cache)
     */
    async refreshLookup() {
        await this.performCedulaLookup(true);
    },

    /**
     * Get cache status color
     */
    getCacheStatusColor() {
        const status = this.lookupState.cacheStatus;

        if (!status || !status.in_cache) {
            return 'text-secondary';
        }

        switch (status.status) {
            case 'fresh':
                return 'text-success';
            case 'stale':
                return 'text-warning';
            case 'expired':
                return 'text-danger';
            default:
                return 'text-secondary';
        }
    },

    /**
     * Get cache status icon
     */
    getCacheStatusIcon() {
        const status = this.lookupState.cacheStatus;

        if (!status || !status.in_cache) {
            return 'fa-circle-o';
        }

        switch (status.status) {
            case 'fresh':
                return 'fa-check-circle';
            case 'stale':
                return 'fa-clock-o';
            case 'expired':
                return 'fa-times-circle';
            default:
                return 'fa-question-circle';
        }
    },

    /**
     * Get cache status text
     */
    getCacheStatusText() {
        const status = this.lookupState.cacheStatus;

        if (!status || !status.in_cache) {
            return _t('New');
        }

        const age = status.age_days;
        if (age === 0) {
            return _t('Fresh (today)');
        } else if (age === 1) {
            return _t('Fresh (1 day)');
        } else if (age <= 7) {
            return _t('Fresh (') + age + _t(' days)');
        } else if (age <= 30) {
            return _t('Stale (') + age + _t(' days)');
        } else {
            return _t('Very stale (') + age + _t(' days)');
        }
    },
});
