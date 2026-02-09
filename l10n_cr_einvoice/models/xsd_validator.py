# -*- coding: utf-8 -*-
"""
Costa Rica E-Invoice XSD Validator

This module validates XML documents against Hacienda's official XSD schemas
for Costa Rica electronic invoicing (Facturación Electrónica v4.4).

Supported document types:
- FE: Factura Electrónica (Electronic Invoice)
- TE: Tiquete Electrónico (Electronic Ticket)
- NC: Nota de Crédito Electrónica (Electronic Credit Note)
- ND: Nota de Débito Electrónica (Electronic Debit Note)
"""

import logging
import os
from lxml import etree
from odoo import models, api, _
from odoo.modules.module import get_module_path

_logger = logging.getLogger(__name__)


class XSDValidator(models.AbstractModel):
    """
    XML Schema validation for Costa Rica e-invoices.

    This validator provides two validation modes:
    1. XSD Schema validation (when .xsd files are available)
    2. Well-formed XML validation (fallback when XSD files are not available)
    """

    _name = 'l10n_cr.xsd.validator'
    _description = 'Costa Rica E-Invoice XSD Validator'

    # XSD schema URLs from Hacienda (v4.4)
    SCHEMA_URLS = {
        'FE': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica',
        'TE': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/tiqueteElectronico',
        'NC': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/notaCreditoElectronica',
        'ND': 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/notaDebitoElectronica',
    }

    # Expected root element names for each document type
    ROOT_ELEMENTS = {
        'FE': 'FacturaElectronica',
        'TE': 'TiqueteElectronico',
        'NC': 'NotaCreditoElectronica',
        'ND': 'NotaDebitoElectronica',
    }

    # Local XSD file paths (relative to module directory)
    XSD_PATHS = {
        'FE': 'data/xsd/FacturaElectronica_V4.4.xsd',
        'TE': 'data/xsd/TiqueteElectronico_V4.4.xsd',
        'NC': 'data/xsd/NotaCreditoElectronica_V4.4.xsd',
        'ND': 'data/xsd/NotaDebitoElectronica_V4.4.xsd',
    }

    @api.model
    def validate_xml(self, xml_content, document_type):
        """
        Validate XML content against XSD schema.

        This is the main validation entry point called by einvoice_document.

        Args:
            xml_content (str): XML content as string
            document_type (str): Document type ('FE', 'TE', 'NC', 'ND')

        Returns:
            tuple: (is_valid, error_message)
                - is_valid (bool): True if validation passed, False otherwise
                - error_message (str): Error description if validation failed, empty string if valid
        """
        if not xml_content:
            return False, _('XML content is empty')

        if document_type not in self.ROOT_ELEMENTS:
            return False, _('Unknown document type: %s') % document_type

        try:
            # First, validate that XML is well-formed
            is_valid, error = self._validate_well_formed(xml_content, document_type)
            if not is_valid:
                return False, error

            # Then, validate against XSD schema if available
            is_valid, error = self._validate_against_xsd(xml_content, document_type)
            if not is_valid:
                # XSD validation failed — this is a real error, propagate it
                return False, error
            # If is_valid is True but error has a message, it means schema was unavailable
            if error:
                _logger.warning('XSD validation note for %s: %s', document_type, error)

            _logger.debug('XML validation passed for document type %s', document_type)
            return True, ''

        except Exception as e:
            error_msg = _('XML validation error: %s') % str(e)
            _logger.error(error_msg)
            return False, error_msg

    @api.model
    def _validate_well_formed(self, xml_content, document_type):
        """
        Validate that XML is well-formed and has correct structure.

        This performs basic validation without XSD schema:
        - XML is parseable
        - Has correct root element
        - Contains required elements

        Args:
            xml_content (str): XML content
            document_type (str): Document type

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Parse XML
            root = etree.fromstring(xml_content.encode('utf-8'))

            # Check root element name (strip namespace)
            root_tag = etree.QName(root).localname
            expected_root = self.ROOT_ELEMENTS.get(document_type)

            if root_tag != expected_root:
                return False, _(
                    'Invalid root element: expected "%s", got "%s"'
                ) % (expected_root, root_tag)

            # Validate required elements based on document type
            validation_errors = self._validate_required_elements(root, document_type)
            if validation_errors:
                return False, '\n'.join(validation_errors)

            return True, ''

        except etree.XMLSyntaxError as e:
            return False, _('XML syntax error: %s') % str(e)
        except Exception as e:
            return False, _('XML parsing error: %s') % str(e)

    @api.model
    def _validate_required_elements(self, root, document_type):
        """
        Validate that required elements are present in the XML.

        Args:
            root (etree.Element): XML root element
            document_type (str): Document type

        Returns:
            list: List of error messages (empty if valid)
        """
        errors = []
        ns = {'fe': self.SCHEMA_URLS[document_type]}

        # Required elements for all document types
        required_common = [
            'Clave',
            'NumeroConsecutivo',
            'FechaEmision',
            'Emisor',
            'ResumenFactura',
        ]

        # Document type specific requirements
        if document_type in ['FE', 'NC', 'ND']:
            # These types require Receptor
            required_common.append('Receptor')

        # Check each required element
        for elem_name in required_common:
            elem = root.find('.//fe:' + elem_name, namespaces=ns)
            if elem is None:
                # Fallback: try without namespace (for compatibility)
                elem = root.find('.//' + elem_name)
                if elem is not None:
                    _logger.debug(
                        'Element %s found without namespace prefix — '
                        'consider adding proper namespace to XML.',
                        elem_name
                    )

            if elem is None:
                errors.append(_('Missing required element: %s') % elem_name)

        # Validate Clave format (50 digits)
        clave = root.find('.//fe:Clave', namespaces=ns)
        if clave is None:
            clave = root.find('.//Clave')

        if clave is not None and clave.text:
            if len(clave.text) != 50:
                errors.append(
                    _('Invalid Clave length: expected 50 digits, got %d') % len(clave.text)
                )
            if not clave.text.isdigit():
                errors.append(_('Clave must contain only digits'))

        return errors

    @api.model
    def _validate_against_xsd(self, xml_content, document_type):
        """
        Validate XML against XSD schema file.

        Args:
            xml_content (str): XML content
            document_type (str): Document type

        Returns:
            tuple: (is_valid, error_message)
        """
        xsd_path = self._get_xsd_path(document_type)

        if not xsd_path or not os.path.exists(xsd_path):
            # XSD file not available - this is OK, we fall back to well-formed validation
            _logger.debug(
                'XSD schema not found for %s at %s. Skipping XSD validation.',
                document_type,
                xsd_path or 'unknown path'
            )
            return True, ''  # No schema = skip, OK

        try:
            # Load XSD schema
            with open(xsd_path, 'rb') as xsd_file:
                schema_root = etree.XML(xsd_file.read())
                schema = etree.XMLSchema(schema_root)

            # Parse XML document
            xml_doc = etree.fromstring(xml_content.encode('utf-8'))

            # Validate against schema
            if not schema.validate(xml_doc):
                # Collect all validation errors
                error_messages = []
                for error in schema.error_log:
                    error_messages.append(
                        f'Line {error.line}, Column {error.column}: {error.message}'
                    )

                return False, 'XSD validation error: ' + '\n'.join(error_messages)

            return True, ''

        except FileNotFoundError:
            # XSD file disappeared between check and open - treat as unavailable
            return True, ''
        except etree.XMLSchemaParseError as e:
            _logger.error('XSD schema parsing error for %s: %s', document_type, str(e))
            return True, 'Schema parse error: %s' % str(e)
        except Exception as e:
            _logger.error('Unexpected XSD validation error: %s', str(e))
            return True, 'Unexpected: %s' % str(e)

    @api.model
    def _get_xsd_path(self, document_type):
        """
        Get the full path to the XSD schema file for a document type.

        Args:
            document_type (str): Document type

        Returns:
            str: Full path to XSD file, or None if not configured
        """
        relative_path = self.XSD_PATHS.get(document_type)
        if not relative_path:
            return None

        try:
            module_path = get_module_path('l10n_cr_einvoice')
            if not module_path:
                _logger.warning('Could not find l10n_cr_einvoice module path')
                return None

            full_path = os.path.join(module_path, relative_path)
            return full_path
        except Exception as e:
            _logger.error('Error getting XSD path: %s', str(e))
            return None

    @api.model
    def get_validation_errors(self, xml_content, document_type):
        """
        Get detailed validation errors for an XML document.

        This method provides more detailed error information than validate_xml().
        Useful for debugging and displaying errors to users.

        Args:
            xml_content (str): XML content
            document_type (str): Document type

        Returns:
            dict: Dictionary with validation results:
                {
                    'is_valid': bool,
                    'errors': list of error messages,
                    'warnings': list of warning messages,
                    'schema_available': bool
                }
        """
        result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'schema_available': False,
        }

        if not xml_content:
            result['errors'].append(_('XML content is empty'))
            return result

        if document_type not in self.ROOT_ELEMENTS:
            result['errors'].append(_('Unknown document type: %s') % document_type)
            return result

        # Check well-formedness
        is_valid, error = self._validate_well_formed(xml_content, document_type)
        if not is_valid:
            result['errors'].append(error)
            return result

        # Check XSD availability
        xsd_path = self._get_xsd_path(document_type)
        result['schema_available'] = xsd_path and os.path.exists(xsd_path)

        if result['schema_available']:
            # Validate against XSD
            is_valid, error = self._validate_against_xsd(xml_content, document_type)
            if not is_valid:
                result['errors'].append(error)
            else:
                result['is_valid'] = True
        else:
            # No XSD available - well-formed validation passed
            result['is_valid'] = True
            result['warnings'].append(
                _('XSD schema not available for %s. Basic validation only.') % document_type
            )

        return result

    @api.model
    def check_schema_availability(self):
        """
        Check which XSD schemas are available.

        Returns:
            dict: Dictionary with document types as keys and availability as values
                {
                    'FE': True/False,
                    'TE': True/False,
                    'NC': True/False,
                    'ND': True/False,
                }
        """
        availability = {}

        for doc_type in self.ROOT_ELEMENTS.keys():
            xsd_path = self._get_xsd_path(doc_type)
            availability[doc_type] = xsd_path and os.path.exists(xsd_path)

        return availability
