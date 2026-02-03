# -*- coding: utf-8 -*-
# Part of GMS. See LICENSE file for full copyright and licensing details.
import datetime
import logging
from ast import literal_eval

import requests

from odoo import api, fields, release, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.models import AbstractModel
from odoo.tools.translate import _
from odoo.tools import config

_logger = logging.getLogger(__name__)


class PublisherWarrantyContractSHAAR(AbstractModel):
    """
    Override the publisher_warranty.contract model to use SHAAR licensing server
    instead of Odoo's default publisher warranty server.

    This is a clean inheritance that:
    1. Preserves all telemetry collection logic (SHAAR needs same data)
    2. Changes only the target URL to use SHAAR endpoint
    3. Maintains request/response format compatibility
    4. Reads URL from publisher_warranty_url config parameter
    """
    _inherit = 'publisher_warranty.contract'

    @api.model
    def _get_sys_logs(self):
        """
        Override to send publisher warranty messages to SHAAR licensing server.

        SHAAR provides a drop-in replacement endpoint that accepts the same
        request format and returns compatible responses.
        """
        msg = self._get_message()
        arguments = {'arg0': str(msg), "action": "update"}

        # Read SHAAR URL from config parameter
        url = config.get("publisher_warranty_url")

        if not url:
            _logger.warning(
                "SHAAR licensing: publisher_warranty_url not configured in odoo.conf. "
                "Please add: publisher_warranty_url = https://your-shaar-instance.vercel.app/api/license/publisher-warranty"
            )
            # Return empty response to avoid breaking the cron
            return {
                "messages": [],
                "enterprise_info": {}
            }

        try:
            _logger.info("SHAAR licensing: Sending telemetry to %s", url)
            r = requests.post(url, data=arguments, timeout=30)
            r.raise_for_status()
            result = literal_eval(r.text)
            _logger.info("SHAAR licensing: Successfully received response from SHAAR server")
            return result
        except requests.exceptions.RequestException as e:
            _logger.error("SHAAR licensing: Failed to connect to SHAAR server at %s: %s", url, str(e))
            # Return empty response to avoid breaking the cron
            return {
                "messages": [],
                "enterprise_info": {}
            }
        except Exception as e:
            _logger.error("SHAAR licensing: Error processing SHAAR response: %s", str(e))
            # Return empty response to avoid breaking the cron
            return {
                "messages": [],
                "enterprise_info": {}
            }
