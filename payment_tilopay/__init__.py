# -*- coding: utf-8 -*-

from . import models
from . import controllers

def _post_init_hook(env):
    """
    Post-initialization hook to set up TiloPay payment provider.
    Creates or updates the TiloPay payment provider record.
    """
    # Create TiloPay provider if it doesn't exist
    provider = env['payment.provider'].search([('code', '=', 'tilopay')], limit=1)
    if not provider:
        env['payment.provider'].create({
            'name': 'TiloPay',
            'code': 'tilopay',
            'state': 'disabled',  # Admin must configure and enable
            'is_published': False,
        })
