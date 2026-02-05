# -*- coding: utf-8 -*-
# Core catalog models
from . import ciiu_code
from . import payment_method
from . import discount_code
from . import validation_rule

# Partner extensions
from . import res_partner
from . import res_partner_autocomplete
from . import cedula_cache
from . import cedula_lookup_service
from . import cedula_dashboard

# E-invoice core models
from . import einvoice_document
from . import einvoice_import_batch
from . import einvoice_import_error
from . import einvoice_analytics_dashboard
from . import einvoice_xml_parser
from . import einvoice_retry_queue

# Account extensions
from . import account_move
from . import account_move_line

# Tax Report models (Phase 9B)
from . import tax_report_period
from . import d150_vat_report
from . import d101_income_tax_report
from . import d151_informative_report
from . import tax_report_xml_generator

# API and generators
from . import hacienda_api
from . import hacienda_cedula_api
from . import xml_generator
from . import xsd_validator
from . import certificate_manager
from . import xml_signer
from . import qr_generator

# Company and settings
from . import res_config_settings
from . import res_company

# POS extensions
from . import pos_order
from . import pos_config
from . import pos_offline_queue

