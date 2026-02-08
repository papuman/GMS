# -*- coding: utf-8 -*-
import os
import logging
import requests
from lxml import etree
import xmlschema

from odoo import models, api, _
from odoo.exceptions import ValidationError
from odoo.tools import config

_logger = logging.getLogger(__name__)


class XSDValidator(models.AbstractModel):
    _name = 'l10n_cr.xsd.validator'
    _description = 'XSD Schema Validator for Costa Rica E-Invoices'

    # XSD Schema URLs (Hacienda official schemas v4.4)
    XSD_URLS = {
        'FE': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/FacturaElectronica_V.4.4.xsd',
        'TE': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/TiqueteElectronico_V4.4.xsd',
        'NC': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/NotaCreditoElectronica_V4.4.xsd',
        'ND': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/NotaDebitoElectronica_V4.4.xsd',
    }

    @api.model
    def _get_schema_cache_dir(self):
        """Get the directory to cache XSD schemas."""
        # Use Odoo data directory
        data_dir = config.get('data_dir', '/tmp')
        cache_dir = os.path.join(data_dir, 'l10n_cr_einvoice', 'xsd_cache')

        # Create directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)

        return cache_dir

    @api.model
    def _get_cached_schema_path(self, doc_type):
        """Get the file path for a cached schema."""
        cache_dir = self._get_schema_cache_dir()
        filename = f'{doc_type}_v4.4.xsd'
        return os.path.join(cache_dir, filename)

    @api.model
    def _download_schema(self, doc_type):
        """Download XSD schema from Hacienda CDN."""
        if doc_type not in self.XSD_URLS:
            raise ValidationError(_('Unknown document type for XSD: %s') % doc_type)

        url = self.XSD_URLS[doc_type]
        cache_path = self._get_cached_schema_path(doc_type)

        try:
            _logger.info(f'Downloading XSD schema for {doc_type} from {url}')

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Save to cache
            with open(cache_path, 'wb') as f:
                f.write(response.content)

            _logger.info(f'Downloaded and cached XSD schema for {doc_type}')

            return cache_path

        except requests.exceptions.RequestException as e:
            _logger.error(f'Failed to download XSD schema: {str(e)}')
            raise ValidationError(_('Failed to download XSD schema: %s') % str(e))

    @api.model
    def _get_schema(self, doc_type):
        """Get the XSD schema for a document type (from cache or download)."""
        cache_path = self._get_cached_schema_path(doc_type)

        # Check if schema is cached
        if not os.path.exists(cache_path):
            cache_path = self._download_schema(doc_type)

        return cache_path

    @api.model
    def validate_xml(self, xml_content, doc_type):
        """
        Validate XML content against the appropriate XSD schema.

        Args:
            xml_content (str): XML content to validate
            doc_type (str): Document type (FE, TE, NC, ND)

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Parse XML
            try:
                xml_doc = etree.fromstring(xml_content.encode('utf-8'))
            except etree.XMLSyntaxError as e:
                return (False, f'Invalid XML syntax: {str(e)}')

            # Get schema file
            schema_path = self._get_schema(doc_type)

            # Load and parse schema
            try:
                with open(schema_path, 'rb') as schema_file:
                    schema_doc = etree.parse(schema_file)
                    schema = etree.XMLSchema(schema_doc)
            except Exception as e:
                _logger.error(f'Failed to load XSD schema: {str(e)}')
                return (False, f'Failed to load XSD schema: {str(e)}')

            # Validate
            is_valid = schema.validate(xml_doc)

            if not is_valid:
                # Collect all validation errors
                errors = []
                for error in schema.error_log:
                    errors.append(f'Line {error.line}: {error.message}')

                error_message = '\n'.join(errors)
                _logger.warning(f'XML validation failed for {doc_type}:\n{error_message}')

                return (False, error_message)

            _logger.info(f'XML validation successful for {doc_type}')
            return (True, '')

        except Exception as e:
            _logger.error(f'Unexpected error during validation: {str(e)}')
            return (False, str(e))

    @api.model
    def validate_xml_advanced(self, xml_content, doc_type):
        """
        Advanced validation using xmlschema library (supports XSD 1.1).

        Args:
            xml_content (str): XML content to validate
            doc_type (str): Document type (FE, TE, NC, ND)

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Get schema file
            schema_path = self._get_schema(doc_type)

            # Load schema
            try:
                schema = xmlschema.XMLSchema(schema_path)
            except Exception as e:
                _logger.error(f'Failed to load XSD schema: {str(e)}')
                return (False, f'Failed to load XSD schema: {str(e)}')

            # Validate
            try:
                schema.validate(xml_content)
                _logger.info(f'XML validation successful for {doc_type}')
                return (True, '')

            except xmlschema.XMLSchemaException as e:
                error_message = str(e)
                _logger.warning(f'XML validation failed for {doc_type}: {error_message}')
                return (False, error_message)

        except Exception as e:
            _logger.error(f'Unexpected error during validation: {str(e)}')
            return (False, str(e))

    @api.model
    def clear_schema_cache(self):
        """Clear all cached XSD schemas."""
        cache_dir = self._get_schema_cache_dir()

        try:
            for filename in os.listdir(cache_dir):
                if filename.endswith('.xsd'):
                    file_path = os.path.join(cache_dir, filename)
                    os.remove(file_path)
                    _logger.info(f'Removed cached schema: {filename}')

            return True

        except Exception as e:
            _logger.error(f'Error clearing schema cache: {str(e)}')
            return False

    @api.model
    def refresh_schemas(self):
        """Refresh all XSD schemas by re-downloading them."""
        self.clear_schema_cache()

        for doc_type in self.XSD_URLS.keys():
            try:
                self._download_schema(doc_type)
            except Exception as e:
                _logger.error(f'Failed to refresh schema for {doc_type}: {str(e)}')

        return True
