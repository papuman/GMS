/** @odoo-module **/

/**
 * TiloPay Payment Form Enhanced - Client-Side UX Handler
 *
 * Features:
 * - Loading states during payment processing
 * - Payment method selection animations
 * - Form validation with helpful messages
 * - Accessibility keyboard navigation
 * - Mobile-optimized interactions
 * - Error handling with retry logic
 * - Analytics event tracking
 */

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.TiloPayPaymentFormEnhanced = publicWidget.Widget.extend({
    selector: '.tilopay-payment-form, .o_payment_form',
    events: {
        'click .tilopay-payment-method': '_onSelectPaymentMethod',
        'click .tilopay-btn-pay': '_onSubmitPayment',
        'click .tilopay-btn-retry': '_onRetryPayment',
        'keydown .tilopay-payment-method': '_onPaymentMethodKeydown',
        'submit form': '_onFormSubmit',
    },

    /**
     * Initialize the widget
     */
    start: function () {
        this._super.apply(this, arguments);
        this._setupAccessibility();
        this._preloadResources();
        this._trackPageView();
        return Promise.resolve();
    },

    /**
     * Setup accessibility features
     */
    _setupAccessibility: function () {
        // Add ARIA labels to payment methods
        this.$('.tilopay-payment-method').each(function (index, element) {
            const $method = $(element);
            const methodName = $method.find('.tilopay-method-name').text();

            $method.attr({
                'role': 'radio',
                'aria-checked': $method.hasClass('selected') ? 'true' : 'false',
                'aria-label': `Método de pago: ${methodName}`,
                'tabindex': $method.hasClass('selected') ? '0' : '-1',
            });
        });

        // Add keyboard navigation hint
        if (!this.$('.tilopay-keyboard-hint').length) {
            this.$('.tilopay-payment-methods').before(
                '<div class="tilopay-sr-only tilopay-keyboard-hint" role="status" aria-live="polite">' +
                'Use las teclas de flecha para navegar entre métodos de pago. Presione Enter para seleccionar.' +
                '</div>'
            );
        }
    },

    /**
     * Preload resources for better performance
     */
    _preloadResources: function () {
        // Preload common icons (if using icon fonts)
        const icons = ['fa-credit-card', 'fa-mobile', 'fa-shield', 'fa-lock'];
        // Icons are typically already loaded via FontAwesome
    },

    /**
     * Track page view for analytics
     */
    _trackPageView: function () {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'page_view', {
                'page_title': 'Payment Portal',
                'page_location': window.location.href,
                'page_path': window.location.pathname,
            });
        }
        console.log('[TiloPay] Payment form loaded');
    },

    /**
     * Handle payment method selection
     */
    _onSelectPaymentMethod: function (ev) {
        ev.preventDefault();
        const $method = $(ev.currentTarget);
        const $radio = $method.find('input[type="radio"]');

        // Update UI
        this.$('.tilopay-payment-method').removeClass('selected').attr({
            'aria-checked': 'false',
            'tabindex': '-1',
        });

        $method.addClass('selected').attr({
            'aria-checked': 'true',
            'tabindex': '0',
        });

        // Check radio button
        $radio.prop('checked', true);

        // Focus for accessibility
        $method.focus();

        // Animate selection
        this._animateSelection($method);

        // Track selection
        this._trackEvent('select_payment_method', {
            'method': $radio.val(),
        });

        // Show method-specific info
        this._showPaymentMethodInfo($radio.val());
    },

    /**
     * Animate payment method selection
     */
    _animateSelection: function ($method) {
        $method.css('transform', 'scale(0.98)');
        setTimeout(() => {
            $method.css('transform', 'scale(1)');
        }, 150);
    },

    /**
     * Show payment method specific information
     */
    _showPaymentMethodInfo: function (method) {
        // Remove existing info
        this.$('.tilopay-method-info-dynamic').remove();

        let infoHtml = '';
        if (method === 'sinpe') {
            infoHtml = `
                <div class="tilopay-alert tilopay-alert-info tilopay-method-info-dynamic" role="status">
                    <i class="fa fa-info-circle tilopay-alert-icon"></i>
                    <div class="tilopay-alert-content">
                        <strong>SINPE Móvil:</strong> Será redirigido a su banco para completar el pago de forma segura.
                    </div>
                </div>
            `;
        } else if (method === 'card') {
            infoHtml = `
                <div class="tilopay-alert tilopay-alert-info tilopay-method-info-dynamic" role="status">
                    <i class="fa fa-credit-card tilopay-alert-icon"></i>
                    <div class="tilopay-alert-content">
                        <strong>Tarjeta de crédito/débito:</strong> Aceptamos Visa, Mastercard y American Express.
                    </div>
                </div>
            `;
        }

        if (infoHtml) {
            this.$('.tilopay-payment-methods').after(infoHtml);
        }
    },

    /**
     * Handle keyboard navigation for payment methods
     */
    _onPaymentMethodKeydown: function (ev) {
        const $methods = this.$('.tilopay-payment-method');
        const $current = $(ev.currentTarget);
        const currentIndex = $methods.index($current);

        let nextIndex = currentIndex;

        switch (ev.key) {
            case 'ArrowDown':
            case 'ArrowRight':
                ev.preventDefault();
                nextIndex = (currentIndex + 1) % $methods.length;
                break;
            case 'ArrowUp':
            case 'ArrowLeft':
                ev.preventDefault();
                nextIndex = (currentIndex - 1 + $methods.length) % $methods.length;
                break;
            case 'Enter':
            case ' ':
                ev.preventDefault();
                $current.trigger('click');
                return;
            default:
                return;
        }

        // Focus next method
        $methods.eq(nextIndex).focus().trigger('click');
    },

    /**
     * Validate form before submission
     */
    _validateForm: function () {
        const errors = [];

        // Check if payment method is selected
        const selectedMethod = this.$('input[name="payment_method"]:checked').val();
        if (!selectedMethod) {
            errors.push('Por favor seleccione un método de pago.');
        }

        // Check if amount exists and is valid
        const amount = parseFloat(this.$('[data-amount]').data('amount') || 0);
        if (amount <= 0) {
            errors.push('El monto del pago no es válido.');
        }

        // Display errors if any
        if (errors.length > 0) {
            this._showValidationErrors(errors);
            return false;
        }

        return true;
    },

    /**
     * Show validation errors to user
     */
    _showValidationErrors: function (errors) {
        // Remove existing error alert
        this.$('.tilopay-validation-errors').remove();

        const errorHtml = `
            <div class="tilopay-alert tilopay-alert-danger tilopay-validation-errors" role="alert">
                <i class="fa fa-exclamation-circle tilopay-alert-icon"></i>
                <div class="tilopay-alert-content">
                    <div class="tilopay-alert-title">Error de validación</div>
                    <ul style="margin: 0; padding-left: 20px;">
                        ${errors.map(err => `<li>${err}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;

        this.$('.tilopay-payment-card-body').prepend(errorHtml);

        // Scroll to error
        this.$('.tilopay-validation-errors')[0].scrollIntoView({
            behavior: 'smooth',
            block: 'center',
        });

        // Announce error to screen readers
        this._announceToScreenReader('Error: ' + errors.join('. '));
    },

    /**
     * Handle payment form submission
     */
    _onSubmitPayment: function (ev) {
        ev.preventDefault();

        // Validate form
        if (!this._validateForm()) {
            return;
        }

        // Show loading state
        this._showLoadingState();

        // Track payment attempt
        const selectedMethod = this.$('input[name="payment_method"]:checked').val();
        this._trackEvent('begin_payment', {
            'method': selectedMethod,
            'amount': parseFloat(this.$('[data-amount]').data('amount') || 0),
        });

        // Submit form after short delay for UX
        setTimeout(() => {
            this.$('form').submit();
        }, 500);
    },

    /**
     * Handle form submit event
     */
    _onFormSubmit: function (ev) {
        // Only handle TiloPay payments
        const providerCode = this.$('input[name="provider_code"]').val();
        if (providerCode !== 'tilopay') {
            return;
        }

        // Validate before allowing submission
        if (!this._validateForm()) {
            ev.preventDefault();
            return false;
        }

        // Show loading state
        this._showLoadingState();
    },

    /**
     * Show loading state during payment processing
     */
    _showLoadingState: function () {
        // Disable submit button
        const $submitBtn = this.$('.tilopay-btn-pay');
        $submitBtn.prop('disabled', true)
            .html('<i class="fa fa-spinner fa-spin tilopay-btn-icon"></i> Procesando...');

        // Disable all payment methods
        this.$('.tilopay-payment-method').css('pointer-events', 'none').css('opacity', '0.6');

        // Show loading overlay
        const loadingHtml = `
            <div class="tilopay-loading-overlay" style="
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                z-index: 9999;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <div class="tilopay-loading" style="background: white; padding: 2rem; border-radius: 1rem; max-width: 300px;">
                    <div class="tilopay-spinner"></div>
                    <div class="tilopay-loading-text">Procesando su pago</div>
                    <div class="tilopay-loading-subtext">Por favor espere, esto puede tomar unos segundos...</div>
                    <div class="tilopay-progress-bar">
                        <div class="tilopay-progress-fill"></div>
                    </div>
                </div>
            </div>
        `;

        $('body').append(loadingHtml);

        // Announce to screen readers
        this._announceToScreenReader('Procesando su pago. Por favor espere.');
    },

    /**
     * Handle retry payment button click
     */
    _onRetryPayment: function (ev) {
        ev.preventDefault();

        // Track retry attempt
        this._trackEvent('retry_payment', {
            'previous_error': this.$('[data-error-message]').data('error-message') || 'unknown',
        });

        // Redirect to payment page
        const retryUrl = $(ev.currentTarget).attr('href');
        window.location.href = retryUrl;
    },

    /**
     * Announce message to screen readers
     */
    _announceToScreenReader: function (message) {
        const $announcement = $('<div class="tilopay-sr-only" role="status" aria-live="polite"></div>');
        $announcement.text(message);
        $('body').append($announcement);

        // Remove after announcement
        setTimeout(() => {
            $announcement.remove();
        }, 1000);
    },

    /**
     * Track analytics event
     */
    _trackEvent: function (eventName, params) {
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, params);
        }
        console.log(`[TiloPay] Event: ${eventName}`, params);
    },
});

/**
 * Payment Status Page Enhancements
 */
publicWidget.registry.TiloPayPaymentStatus = publicWidget.Widget.extend({
    selector: '.tilopay-payment-status',

    start: function () {
        this._super.apply(this, arguments);
        this._animateStatusIcon();
        this._setupAutoRefresh();
        return Promise.resolve();
    },

    /**
     * Animate status icon on page load
     */
    _animateStatusIcon: function () {
        const $icon = this.$('.tilopay-status-icon');
        if ($icon.length) {
            setTimeout(() => {
                $icon.addClass('animated');
            }, 100);
        }

        // Animate checkmark for success page
        const $checkmark = this.$('.tilopay-checkmark');
        if ($checkmark.length) {
            // SVG animation is handled by CSS
        }
    },

    /**
     * Auto-refresh for pending payments
     */
    _setupAutoRefresh: function () {
        const status = this.$('[data-payment-status]').data('payment-status');

        if (status === 'pending') {
            // Auto-refresh after 10 seconds for pending payments
            const refreshTimer = setTimeout(() => {
                this._showRefreshNotification();
            }, 10000);

            // Store timer so it can be cleared
            this._refreshTimer = refreshTimer;
        }
    },

    /**
     * Show refresh notification for pending payments
     */
    _showRefreshNotification: function () {
        const $notification = $(`
            <div class="tilopay-alert tilopay-alert-info tilopay-auto-refresh" role="status">
                <i class="fa fa-refresh tilopay-alert-icon tilopay-pulse"></i>
                <div class="tilopay-alert-content">
                    Verificando el estado del pago...
                </div>
            </div>
        `);

        this.$('.tilopay-payment-card-body').prepend($notification);

        // Auto-refresh after showing notification
        setTimeout(() => {
            window.location.reload();
        }, 3000);
    },

    /**
     * Clean up on destroy
     */
    destroy: function () {
        if (this._refreshTimer) {
            clearTimeout(this._refreshTimer);
        }
        this._super.apply(this, arguments);
    },
});

/**
 * Smooth scroll for anchor links
 */
$(document).ready(function () {
    // Smooth scroll for internal links
    $('a[href^="#"]').on('click', function (e) {
        const target = $(this.getAttribute('href'));
        if (target.length) {
            e.preventDefault();
            target[0].scrollIntoView({
                behavior: 'smooth',
                block: 'start',
            });
        }
    });

    // Auto-hide alerts after 10 seconds
    setTimeout(() => {
        $('.tilopay-alert').not('.tilopay-alert-danger').fadeOut(500);
    }, 10000);
});

export default {
    TiloPayPaymentFormEnhanced: publicWidget.registry.TiloPayPaymentFormEnhanced,
    TiloPayPaymentStatus: publicWidget.registry.TiloPayPaymentStatus,
};
