#!/bin/bash
set -e

# Run Odoo as a Python module
cd /opt
exec python3 -m odoo -c /etc/odoo/odoo.conf "$@"
