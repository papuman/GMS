# -*- coding: utf-8 -*-
import re
import logging
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class L10nCRValidationRule(models.Model):
    """
    Configurable field validation rules for Costa Rica e-invoice documents.

    Supports:
    - Document-type specific validation (FE/TE/NC/ND)
    - Multiple validation types (regex, range, lookup, custom Python)
    - Date-based enforcement (e.g., CIIU mandatory after Oct 6, 2025)
    - Partner field validation with constraint logic
    - Localized error messages
    """
    _name = 'l10n_cr.validation.rule'
    _description = 'Costa Rica E-Invoice Validation Rules'
    _order = 'sequence, rule_name'

    # ===== RULE IDENTIFICATION =====

    rule_name = fields.Char(
        string='Rule Name',
        required=True,
        translate=True,
        help='Descriptive name for this validation rule (e.g., "FE Customer Email Required")',
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Execution order for validation rules (lower = earlier)',
    )

    code = fields.Char(
        string='Rule Code',
        size=32,
        required=True,
        index=True,
        help='Unique technical identifier for this rule (e.g., "fe_email_required")',
    )

    description = fields.Text(
        string='Description',
        translate=True,
        help='Detailed explanation of what this rule validates and why',
    )

    # ===== APPLICABILITY =====

    document_type = fields.Selection([
        ('all', 'All Document Types'),
        ('FE', 'Factura Electrónica Only'),
        ('TE', 'Tiquete Electrónico Only'),
        ('NC', 'Nota de Crédito Only'),
        ('ND', 'Nota de Débito Only'),
    ], string='Document Type',
        required=True,
        default='all',
        help='Which document types this rule applies to',
    )

    applies_to = fields.Selection([
        ('partner', 'Partner (Customer) Fields'),
        ('document', 'E-Invoice Document Fields'),
        ('line', 'Invoice/Order Line Items'),
        ('company', 'Company (Emisor) Fields'),
    ], string='Applies To',
        required=True,
        default='partner',
        help='Which entity this validation rule checks',
    )

    field_name = fields.Char(
        string='Field Name',
        required=True,
        help='Technical field name to validate (e.g., "email", "vat", "l10n_cr_economic_activity_id")',
    )

    field_label = fields.Char(
        string='Field Label',
        translate=True,
        help='Human-readable field label for error messages (e.g., "Email Address", "Cédula")',
    )

    # ===== VALIDATION LOGIC =====

    validation_type = fields.Selection([
        ('required', 'Required (Not Empty)'),
        ('regex', 'Regular Expression Pattern'),
        ('range', 'Numeric Range'),
        ('length', 'String Length'),
        ('email', 'Email Format'),
        ('phone', 'Phone Number Format'),
        ('lookup', 'Foreign Key Lookup'),
        ('custom', 'Custom Python Expression'),
    ], string='Validation Type',
        required=True,
        default='required',
        help='Type of validation to perform',
    )

    required = fields.Boolean(
        string='Field Required',
        default=True,
        help='If True, field must be present and non-empty',
    )

    validation_params = fields.Text(
        string='Validation Parameters',
        help=(
            'Validation-specific parameters (JSON or Python dict):\n'
            '- regex: {"pattern": "^[0-9]{9}$"}\n'
            '- range: {"min": 0, "max": 100}\n'
            '- length: {"min": 3, "max": 50}\n'
            '- lookup: {"model": "l10n_cr.ciiu.code", "field": "code"}\n'
            '- custom: {"expression": "record.vat and len(record.vat) == 9"}'
        ),
    )

    # ===== ERROR HANDLING =====

    error_message_es = fields.Text(
        string='Error Message (Spanish)',
        required=True,
        translate=True,
        help=(
            'Error message shown to user when validation fails (Spanish).\n'
            'Use placeholders: {field_label}, {field_value}, {expected}'
        ),
    )

    error_message_en = fields.Text(
        string='Error Message (English)',
        translate=True,
        help='Optional English translation of error message',
    )

    blocking = fields.Boolean(
        string='Blocking',
        default=True,
        help='If True, validation failure prevents document creation (raises ValidationError)',
    )

    severity = fields.Selection([
        ('error', 'Error (Blocking)'),
        ('warning', 'Warning (Allow with Confirmation)'),
        ('info', 'Info (Log Only)'),
    ], string='Severity',
        default='error',
        help='Severity level when validation fails',
    )

    # ===== DATE-BASED ENFORCEMENT =====

    enforcement_date = fields.Date(
        string='Enforcement Date',
        help=(
            'Rule becomes active starting this date (inclusive).\n'
            'Example: CIIU requirement starts Oct 6, 2025.\n'
            'Leave empty for always-active rules.'
        ),
    )

    enforcement_end_date = fields.Date(
        string='Enforcement End Date',
        help='Rule stops being enforced after this date (exclusive). Leave empty for no end date.',
    )

    date_field = fields.Char(
        string='Date Field to Check',
        default='invoice_date',
        help=(
            'Which date field to compare against enforcement_date.\n'
            'Examples: "invoice_date", "create_date", "write_date"'
        ),
    )

    # ===== STATUS =====

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Inactive rules are not evaluated',
    )

    test_mode = fields.Boolean(
        string='Test Mode',
        default=False,
        help='If True, validation failures are logged but do not block (for testing new rules)',
    )

    # ===== AUDIT TRAIL =====

    last_triggered = fields.Datetime(
        string='Last Triggered',
        readonly=True,
        help='Last time this rule detected a validation failure',
    )

    trigger_count = fields.Integer(
        string='Trigger Count',
        default=0,
        readonly=True,
        help='Number of times this rule has detected violations',
    )

    # ===== COMPUTED FIELDS =====

    is_currently_enforced = fields.Boolean(
        string='Currently Enforced',
        compute='_compute_is_currently_enforced',
        search='_search_is_currently_enforced',
        store=False,
        help='True if rule is active and within enforcement date range',
    )

    # ===== CONSTRAINTS (Odoo 19 format) =====
    _code_unique = models.UniqueIndex(
        '(code)',
        'Rule code must be unique!',
    )

    # ===== COMPUTE METHODS =====

    @api.depends('active', 'enforcement_date', 'enforcement_end_date')
    def _compute_is_currently_enforced(self):
        """Check if rule is currently active and within date range."""
        today = fields.Date.today()
        for rule in self:
            if not rule.active:
                rule.is_currently_enforced = False
                continue

            # Check start date
            if rule.enforcement_date and today < rule.enforcement_date:
                rule.is_currently_enforced = False
                continue

            # Check end date
            if rule.enforcement_end_date and today >= rule.enforcement_end_date:
                rule.is_currently_enforced = False
                continue

            rule.is_currently_enforced = True

    def _search_is_currently_enforced(self, operator, value):
        """
        Search method for is_currently_enforced computed field.

        Args:
            operator: Search operator (e.g., '=', '!=')
            value: Search value (True/False)

        Returns:
            domain: Search domain to filter records
        """
        today = fields.Date.today()

        # Build domain based on what "enforced" means
        if (operator == '=' and value) or (operator == '!=' and not value):
            # Looking for currently enforced rules
            domain = [
                ('active', '=', True),
                '|',
                    ('enforcement_date', '=', False),
                    ('enforcement_date', '<=', today),
                '|',
                    ('enforcement_end_date', '=', False),
                    ('enforcement_end_date', '>', today),
            ]
        else:
            # Looking for not enforced rules (inactive or outside date range)
            domain = [
                '|',
                    ('active', '=', False),
                    '|',
                        ('enforcement_date', '>', today),
                        ('enforcement_end_date', '<=', today),
            ]

        return domain

    # ===== VALIDATION METHODS =====

    def _is_applicable(self, document):
        """
        Check if this rule applies to the given document.

        Args:
            document: l10n_cr.einvoice.document record

        Returns:
            bool: True if rule should be evaluated for this document
        """
        self.ensure_one()

        # Check active status
        if not self.active:
            return False

        # Check document type
        if self.document_type != 'all' and self.document_type != document.document_type:
            return False

        # Check date-based enforcement
        if self.enforcement_date or self.enforcement_end_date:
            # Get date to check
            date_field_value = None

            if hasattr(document, self.date_field):
                date_field_value = getattr(document, self.date_field)
            elif hasattr(document.move_id, self.date_field):
                date_field_value = getattr(document.move_id, self.date_field)
            elif hasattr(document.pos_order_id, self.date_field):
                date_field_value = getattr(document.pos_order_id, self.date_field)

            if not date_field_value:
                date_field_value = fields.Date.today()

            # Convert datetime to date if needed
            if isinstance(date_field_value, datetime):
                date_field_value = date_field_value.date()

            # Check enforcement start
            if self.enforcement_date and date_field_value < self.enforcement_date:
                return False

            # Check enforcement end
            if self.enforcement_end_date and date_field_value >= self.enforcement_end_date:
                return False

        return True

    def _get_target_record(self, document):
        """
        Get the target record to validate based on applies_to field.

        Args:
            document: l10n_cr.einvoice.document record

        Returns:
            recordset: The record to validate (partner, document, line, etc.)
        """
        self.ensure_one()

        if self.applies_to == 'partner':
            return document.partner_id
        elif self.applies_to == 'document':
            return document
        elif self.applies_to == 'company':
            return document.company_id or self.env.company
        elif self.applies_to == 'line':
            # Return invoice lines or POS order lines
            if document.move_id:
                return document.move_id.invoice_line_ids
            elif document.pos_order_id:
                return document.pos_order_id.lines

        return document

    def _validate_field(self, record):
        """
        Validate a specific field on the given record.

        Args:
            record: Odoo recordset to validate

        Returns:
            tuple: (is_valid: bool, error_message: str or False)
        """
        self.ensure_one()

        if not record:
            if self.required:
                return (False, self._format_error_message(None, None, 'Record is empty'))
            return (True, False)

        # Get field value
        field_value = getattr(record, self.field_name, None) if hasattr(record, self.field_name) else None

        # Check if required
        if self.required:
            if field_value is None or (isinstance(field_value, str) and not field_value.strip()):
                return (False, self._format_error_message(
                    field_value,
                    None,
                    f'{self.field_label or self.field_name} is required'
                ))

        # If field is empty and not required, skip validation
        if field_value is None or (isinstance(field_value, str) and not field_value.strip()):
            return (True, False)

        # Perform type-specific validation
        if self.validation_type == 'required':
            # Already checked above
            return (True, False)

        elif self.validation_type == 'regex':
            return self._validate_regex(field_value)

        elif self.validation_type == 'range':
            return self._validate_range(field_value)

        elif self.validation_type == 'length':
            return self._validate_length(field_value)

        elif self.validation_type == 'email':
            return self._validate_email(field_value)

        elif self.validation_type == 'phone':
            return self._validate_phone(field_value)

        elif self.validation_type == 'lookup':
            return self._validate_lookup(field_value)

        elif self.validation_type == 'custom':
            return self._validate_custom(record, field_value)

        return (True, False)

    def _validate_regex(self, value):
        """Validate field value against regex pattern."""
        if not self.validation_params:
            return (False, 'Regex validation requires pattern parameter')

        try:
            params = safe_eval(self.validation_params, mode='eval')
            pattern = params.get('pattern')

            if not pattern:
                return (False, 'Regex pattern not specified')

            if not re.match(pattern, str(value)):
                return (False, self._format_error_message(
                    value,
                    pattern,
                    f'{self.field_label or self.field_name} does not match required pattern'
                ))
        except Exception as e:
            _logger.error(f'Regex validation error for rule {self.code}: {str(e)}')
            return (False, f'Validation error: {str(e)}')

        return (True, False)

    def _validate_range(self, value):
        """Validate numeric value is within range."""
        if not self.validation_params:
            return (False, 'Range validation requires min/max parameters')

        try:
            params = safe_eval(self.validation_params, mode='eval')
            min_val = params.get('min')
            max_val = params.get('max')

            numeric_value = float(value)

            if min_val is not None and numeric_value < min_val:
                return (False, self._format_error_message(
                    value,
                    f'>= {min_val}',
                    f'{self.field_label or self.field_name} must be at least {min_val}'
                ))

            if max_val is not None and numeric_value > max_val:
                return (False, self._format_error_message(
                    value,
                    f'<= {max_val}',
                    f'{self.field_label or self.field_name} must be at most {max_val}'
                ))

        except ValueError:
            return (False, self._format_error_message(
                value,
                'numeric value',
                f'{self.field_label or self.field_name} must be a number'
            ))
        except Exception as e:
            _logger.error(f'Range validation error for rule {self.code}: {str(e)}')
            return (False, f'Validation error: {str(e)}')

        return (True, False)

    def _validate_length(self, value):
        """Validate string length."""
        if not self.validation_params:
            return (False, 'Length validation requires min/max parameters')

        try:
            params = safe_eval(self.validation_params, mode='eval')
            min_len = params.get('min')
            max_len = params.get('max')

            str_value = str(value)
            value_len = len(str_value)

            if min_len is not None and value_len < min_len:
                return (False, self._format_error_message(
                    value,
                    f'at least {min_len} characters',
                    f'{self.field_label or self.field_name} must be at least {min_len} characters'
                ))

            if max_len is not None and value_len > max_len:
                return (False, self._format_error_message(
                    value,
                    f'at most {max_len} characters',
                    f'{self.field_label or self.field_name} must be at most {max_len} characters'
                ))

        except Exception as e:
            _logger.error(f'Length validation error for rule {self.code}: {str(e)}')
            return (False, f'Validation error: {str(e)}')

        return (True, False)

    def _validate_email(self, value):
        """Validate email address format."""
        EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

        str_value = str(value).strip()

        if not EMAIL_REGEX.match(str_value):
            return (False, self._format_error_message(
                value,
                'valid email format',
                f'{self.field_label or self.field_name} must be a valid email address'
            ))

        return (True, False)

    def _validate_phone(self, value):
        """Validate phone number format (Costa Rica)."""
        # Costa Rica phone format: 8 digits (landline/mobile)
        PHONE_REGEX = re.compile(r'^[0-9]{8}$')

        # Clean phone number (remove spaces, dashes, parentheses)
        clean_phone = re.sub(r'[\s\-\(\)]', '', str(value))

        if not PHONE_REGEX.match(clean_phone):
            return (False, self._format_error_message(
                value,
                '8 digits',
                f'{self.field_label or self.field_name} must be 8 digits'
            ))

        return (True, False)

    def _validate_lookup(self, value):
        """Validate foreign key lookup exists."""
        if not self.validation_params:
            return (False, 'Lookup validation requires model parameter')

        try:
            params = safe_eval(self.validation_params, mode='eval')
            model_name = params.get('model')
            field_name = params.get('field', 'id')

            if not model_name:
                return (False, 'Lookup model not specified')

            # Check if value is a recordset
            if hasattr(value, '_name'):
                # It's already a recordset, check if it exists
                if not value.exists():
                    return (False, self._format_error_message(
                        value,
                        'existing record',
                        f'{self.field_label or self.field_name} references a deleted record'
                    ))
            else:
                # It's a value, search for it
                target_model = self.env[model_name]
                domain = [(field_name, '=', value)]

                if not target_model.search_count(domain):
                    return (False, self._format_error_message(
                        value,
                        'valid reference',
                        f'{self.field_label or self.field_name} does not exist in {model_name}'
                    ))

        except Exception as e:
            _logger.error(f'Lookup validation error for rule {self.code}: {str(e)}')
            return (False, f'Validation error: {str(e)}')

        return (True, False)

    def _validate_custom(self, record, value):
        """Validate using custom Python expression."""
        if not self.validation_params:
            return (False, 'Custom validation requires expression parameter')

        try:
            params = safe_eval(self.validation_params, mode='eval')
            expression = params.get('expression')

            if not expression:
                return (False, 'Custom expression not specified')

            # Build evaluation context
            eval_context = {
                'record': record,
                'value': value,
                'env': self.env,
                'date': date,
                'datetime': datetime,
                'relativedelta': relativedelta,
            }

            # Evaluate expression
            result = safe_eval(expression, eval_context, mode='eval')

            if not result:
                return (False, self._format_error_message(
                    value,
                    'custom validation',
                    f'{self.field_label or self.field_name} failed custom validation'
                ))

        except Exception as e:
            _logger.error(f'Custom validation error for rule {self.code}: {str(e)}')
            return (False, f'Validation error: {str(e)}')

        return (True, False)

    def _format_error_message(self, field_value, expected_value, default_message):
        """Format error message with placeholders."""
        message = self.error_message_es or default_message

        # Replace placeholders
        message = message.replace('{field_label}', self.field_label or self.field_name)
        message = message.replace('{field_value}', str(field_value) if field_value is not None else '')
        message = message.replace('{expected}', str(expected_value) if expected_value else '')

        return message

    def validate_document(self, document):
        """
        Validate a document against this rule.

        Args:
            document: l10n_cr.einvoice.document record

        Returns:
            tuple: (is_valid: bool, error_message: str or False)

        Raises:
            ValidationError: If blocking=True and validation fails (and not in test mode or override)
        """
        self.ensure_one()

        # Check if validation override is active
        if hasattr(document, 'validation_override') and document.validation_override:
            _logger.info(
                f'Validation rule {self.code} skipped for document {document.name} '
                f'due to active validation override'
            )
            return (True, False)

        # Check if rule applies
        if not self._is_applicable(document):
            return (True, False)

        # Get target record
        target_record = self._get_target_record(document)

        # Validate
        is_valid, error_message = self._validate_field(target_record)

        # Update audit trail
        if not is_valid:
            self.sudo().write({
                'last_triggered': fields.Datetime.now(),
                'trigger_count': self.trigger_count + 1,
            })

            # Log violation
            _logger.warning(
                f'Validation rule {self.code} failed for document {document.name}: {error_message}'
            )

            # Raise error if blocking (and not in test mode)
            if self.blocking and not self.test_mode:
                raise ValidationError(_(error_message))

        return (is_valid, error_message)

    # ===== CLASS METHODS =====

    @api.model
    def validate_all_rules(self, document):
        """
        Validate document against all applicable rules.

        Args:
            document: l10n_cr.einvoice.document record

        Returns:
            tuple: (is_valid: bool, error_messages: list)

        Raises:
            ValidationError: If any blocking rule fails (and not in test mode)
        """
        rules = self.search([
            ('active', '=', True),
            '|',
            ('document_type', '=', 'all'),
            ('document_type', '=', document.document_type),
        ], order='sequence, rule_name')

        all_valid = True
        error_messages = []

        for rule in rules:
            try:
                is_valid, error_msg = rule.validate_document(document)

                if not is_valid:
                    all_valid = False
                    if error_msg:
                        error_messages.append(f'[{rule.rule_name}] {error_msg}')

            except ValidationError:
                # Re-raise blocking errors
                raise
            except Exception as e:
                _logger.error(f'Unexpected error validating rule {rule.code}: {str(e)}')
                error_messages.append(f'[{rule.rule_name}] Internal validation error')

        return (all_valid, error_messages)

    @api.model
    def load_default_rules(self):
        """
        Load default validation rules for Costa Rica e-invoicing.

        This method creates standard validation rules based on Hacienda v4.4 requirements.
        Can be called from data files or manually.
        """
        CIIU_MANDATORY_DATE = date(2025, 10, 6)

        default_rules = [
            # ===== FACTURA ELECTRONICA (FE) RULES =====
            {
                'code': 'fe_customer_required',
                'rule_name': 'FE: Customer Required',
                'sequence': 10,
                'document_type': 'FE',
                'applies_to': 'partner',
                'field_name': 'id',
                'field_label': 'Cliente',
                'validation_type': 'required',
                'required': True,
                'error_message_es': (
                    'La Factura Electrónica requiere un cliente.\n\n'
                    'Opciones:\n'
                    '- Seleccione un cliente, o\n'
                    '- Cambie el tipo de documento a Tiquete Electrónico (TE)'
                ),
                'blocking': True,
                'severity': 'error',
            },
            {
                'code': 'fe_customer_name_required',
                'rule_name': 'FE: Customer Name Required',
                'sequence': 20,
                'document_type': 'FE',
                'applies_to': 'partner',
                'field_name': 'name',
                'field_label': 'Nombre del Cliente',
                'validation_type': 'required',
                'required': True,
                'error_message_es': (
                    'El nombre del cliente es obligatorio para Factura Electrónica.\n\n'
                    'Cliente: {field_value}\n'
                    'Por favor actualice el registro del cliente o cambie a Tiquete (TE).'
                ),
                'blocking': True,
                'severity': 'error',
            },
            {
                'code': 'fe_customer_vat_required',
                'rule_name': 'FE: Customer VAT/ID Required',
                'sequence': 30,
                'document_type': 'FE',
                'applies_to': 'partner',
                'field_name': 'vat',
                'field_label': 'Cédula/VAT',
                'validation_type': 'required',
                'required': True,
                'error_message_es': (
                    'El número de cédula/identificación es obligatorio para Factura Electrónica.\n\n'
                    'Por favor actualice el registro del cliente o cambie a Tiquete (TE).'
                ),
                'blocking': True,
                'severity': 'error',
            },
            {
                'code': 'fe_customer_id_type_required',
                'rule_name': 'FE: Customer ID Type (Auto-detected from VAT)',
                'sequence': 40,
                'document_type': 'FE',
                'applies_to': 'partner',
                'field_name': 'vat',
                'field_label': 'Tipo de Identificación',
                'validation_type': 'required',
                'required': True,
                'error_message_es': (
                    'El tipo de identificación se determina automáticamente desde el formato de cédula/VAT.\n\n'
                    'Tipos: 01 (Física/9 dígitos), 02 (Jurídica/10 dígitos con 3xxx), '
                    '03 (DIMEX/11-12 dígitos), 04 (NITE), 05 (Extranjero)\n'
                    'Asegúrese de que el número de cédula/VAT tenga el formato correcto.'
                ),
                'blocking': False,
                'severity': 'info',
            },
            {
                'code': 'fe_customer_email_required',
                'rule_name': 'FE: Customer Email Required',
                'sequence': 50,
                'document_type': 'FE',
                'applies_to': 'partner',
                'field_name': 'email',
                'field_label': 'Correo Electrónico',
                'validation_type': 'email',
                'required': True,
                'error_message_es': (
                    'El correo electrónico del cliente es obligatorio para Factura Electrónica.\n\n'
                    'El email es obligatorio según normativa de Hacienda.\n'
                    'Por favor actualice el registro del cliente o cambie a Tiquete (TE).'
                ),
                'blocking': True,
                'severity': 'error',
            },
            {
                'code': 'fe_customer_ciiu_required',
                'rule_name': 'FE: Customer CIIU Required (after Oct 6, 2025)',
                'sequence': 60,
                'document_type': 'FE',
                'applies_to': 'partner',
                'field_name': 'l10n_cr_economic_activity_id',
                'field_label': 'Actividad Económica (CIIU)',
                'validation_type': 'required',
                'required': True,
                'enforcement_date': CIIU_MANDATORY_DATE,
                'date_field': 'invoice_date',
                'error_message_es': (
                    'La actividad económica (CIIU) es obligatoria para Factura Electrónica.\n\n'
                    'El CIIU es obligatorio desde el 6 de octubre de 2025 según normativa de Hacienda.\n\n'
                    'Opciones:\n'
                    '1. Agregue el código CIIU al registro del cliente\n'
                    '2. Cambie a Tiquete Electrónico (TE, no requiere CIIU)\n\n'
                    '¿No está seguro del CIIU? Podemos sugerirle uno según el tipo de cliente.'
                ),
                'blocking': True,
                'severity': 'error',
            },

            # ===== VAT FORMAT VALIDATION =====
            {
                'code': 'vat_cedula_fisica_format',
                'rule_name': 'VAT: Cédula Física Format (9 digits)',
                'sequence': 100,
                'document_type': 'all',
                'applies_to': 'partner',
                'field_name': 'vat',
                'field_label': 'Cédula Física',
                'validation_type': 'regex',
                'validation_params': '{"pattern": "^[0-9]{9}$"}',
                'error_message_es': (
                    'La Cédula Física debe tener exactamente 9 dígitos.\n\n'
                    'Valor actual: {field_value}'
                ),
                'blocking': False,  # Validated elsewhere with more context
                'severity': 'warning',
            },

            # ===== COMPANY/EMISOR VALIDATION =====
            {
                'code': 'company_certificate_valid',
                'rule_name': 'Company: Valid Signing Certificate',
                'sequence': 200,
                'document_type': 'all',
                'applies_to': 'company',
                'field_name': 'l10n_cr_signature_certificate',
                'field_label': 'Certificado de Firma',
                'validation_type': 'custom',
                'validation_params': '{"expression": "record.l10n_cr_signature_certificate and record.l10n_cr_certificate_expiration >= date.today()"}',
                'error_message_es': (
                    'El certificado de firma digital está vencido o no configurado.\n\n'
                    'Por favor actualice el certificado en la configuración de la empresa.'
                ),
                'blocking': True,
                'severity': 'error',
            },
        ]

        created_rules = self.env['l10n_cr.validation.rule']

        for rule_data in default_rules:
            # Check if rule already exists
            existing = self.search([('code', '=', rule_data['code'])], limit=1)

            if existing:
                _logger.info(f'Validation rule {rule_data["code"]} already exists, skipping')
                continue

            # Create rule
            try:
                created = self.create(rule_data)
                created_rules |= created
                _logger.info(f'Created validation rule: {rule_data["code"]}')
            except Exception as e:
                _logger.error(f'Failed to create validation rule {rule_data["code"]}: {str(e)}')

        return created_rules
