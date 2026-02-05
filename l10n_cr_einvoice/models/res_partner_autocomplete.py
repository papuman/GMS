# -*- coding: utf-8 -*-
"""
Override partner autocomplete to work locally without external IAP calls.

This replaces Odoo's cloud-based company lookup with local database search.
"""
import logging

from odoo import models, api

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def autocomplete_by_name(self, name, **kwargs):
        """
        Override autocomplete to search local database only (no IAP calls).

        Instead of calling Odoo's external company database, we search
        existing partners in the local database.

        Args:
            name: Company name to search for
            **kwargs: Additional filters (timeout, limit, etc.)

        Returns:
            dict: Autocomplete results in Odoo's expected format:
                {
                    'data': [
                        {
                            'name': 'Company Name',
                            'vat': 'VAT Number',
                            'country_id': country_code,
                            'email': 'email@example.com',
                            ...
                        },
                        ...
                    ]
                }
        """
        if not name:
            return {'data': []}

        # Search existing partners in local database
        domain = [
            '|', '|',
            ('name', 'ilike', name),
            ('vat', 'ilike', name),
            ('email', 'ilike', name),
        ]

        # Limit results
        limit = kwargs.get('limit', 10)
        partners = self.search(domain, limit=limit, order='name')

        # Format results in Odoo's autocomplete format
        suggestions = []
        for partner in partners:
            suggestion = {
                'name': partner.name or '',
                'vat': partner.vat or '',
                'country_id': partner.country_id.code if partner.country_id else '',
                'email': partner.email or '',
                'phone': partner.phone or '',
                'street': partner.street or '',
                'city': partner.city or '',
                'zip': partner.zip or '',
            }

            # Add state if available
            if partner.state_id:
                suggestion['state_id'] = partner.state_id.name

            # Add industry if available
            if partner.industry_id:
                suggestion['industry_id'] = partner.industry_id.display_name

            # Mark as local result (not from external API)
            suggestion['local_match'] = True

            suggestions.append(suggestion)

        _logger.debug(
            'Local autocomplete for "%s": found %d matches',
            name,
            len(suggestions)
        )

        # Return in expected format (with 'data' key)
        return {'data': suggestions}

    @api.model
    def enrich_company(self, company_domain, partner_gid, vat):
        """
        Override company enrichment to work locally (no IAP calls).

        This is called when creating a new partner to fetch additional
        company details. We skip external enrichment and return empty.

        Returns:
            dict: Empty enrichment data (no external fetch)
        """
        _logger.debug(
            'Skipping external company enrichment for %s (IAP disabled)',
            company_domain
        )

        # Return empty enrichment (partner will be created with user input only)
        return {
            'data': {
                'name': '',
                'vat': vat or '',
                'country_id': '',
            }
        }
