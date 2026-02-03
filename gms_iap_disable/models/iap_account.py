# -*- coding: utf-8 -*-
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class IapAccount(models.Model):
    _inherit = 'iap.account'

    def web_read(self, *args, **kwargs):
        """Override to skip IAP server fetch entirely"""
        _logger.info('IAP: Skipping web_read IAP server fetch (disabled by gms_iap_disable)')
        # Always set context to disable IAP fetch
        return super(IapAccount, self.with_context(disable_iap_fetch=True)).web_read(*args, **kwargs)

    def write(self, vals):
        """Override to skip IAP warning email configuration updates"""
        if any(warning_attribute in vals for warning_attribute in ('warning_threshold', 'warning_user_ids')):
            _logger.info('IAP: Skipping warning email update to IAP server (disabled by gms_iap_disable)')
        # Always set context to disable IAP update
        return super(IapAccount, self.with_context(disable_iap_update=True)).write(vals)

    def _get_account_information_from_iap(self):
        """Override to prevent fetching account information from IAP server"""
        _logger.info('IAP: Skipping account information fetch from IAP server (disabled by gms_iap_disable)')
        # Return immediately without making any external calls
        return

    @api.model
    def get_credits(self, service_name):
        """Override to return mock credits without calling IAP server"""
        _logger.info('IAP: Returning mock credits for service "%s" (disabled by gms_iap_disable)', service_name)
        # Return a high number to prevent credit-related errors
        return 999999
