#!/usr/bin/env python3
"""
Direct E2E Test Runner for Hacienda Sandbox

Runs E2E tests directly using Odoo's environment.
"""
import sys
import odoo
from odoo.tests.common import get_db_name
from odoo.tests.loader import TestLoader
from odoo.tests.runner import OdooTestRunner

def main():
    # Configure Odoo
    odoo.tools.config.parse_config([
        '-d', 'GMS',
        '--db_host', 'db',
        '--db_port', '5432',
        '--db_user', 'odoo',
        '--db_password', 'odoo',
    ])

    # Initialize registry
    dbname = 'GMS'
    registry = odoo.registry(dbname)

    with registry.cursor() as cr:
        # Load E2E test module
        loader = TestLoader()
        suite = loader.loadTestsFromModule(
            'l10n_cr_einvoice.tests.test_e2e_sandbox_lifecycle'
        )

        # Run tests
        runner = OdooTestRunner(verbosity=2)
        result = runner.run(suite)

        # Return exit code
        return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(main())
