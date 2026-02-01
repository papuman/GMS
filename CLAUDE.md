# GMS Project - Claude Code Context

## Tech Stack

- **Odoo Enterprise 19** (19.0+e-20251007) - NOT community, NOT older versions
  - Odoo 19 uses subcommand CLI: `python3 -m odoo server [options]`, `python3 -m odoo shell`, etc.
  - `display_notification` does NOT render HTML in messages -- keep them plain text
  - Hacienda API uses **OAuth2 bearer tokens** (Keycloak IDP), NOT Basic Auth
- **PostgreSQL 13** via Docker
- **Docker Compose** setup: `gms_odoo` + `gms_postgres` containers
- **Database name:** `GMS` (only database -- do not create others)
- **Port:** localhost:8070 -> container 8069

## Custom Module

- `l10n_cr_einvoice` - Costa Rica electronic invoicing for Hacienda
- Mounted at: `/opt/odoo/custom_addons/l10n_cr_einvoice`

## Hacienda API Authentication

The Costa Rica Hacienda API uses OAuth2 Resource Owner Password flow:
- **Sandbox IDP:** `https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token` (client_id: `api-stag`)
- **Production IDP:** `https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token` (client_id: `api-prod`)
- Credentials and certificate PIN are stored in `docs/Tribu-CR/Credentials.md`

## Docker Commands

- Module update: `docker compose run --rm odoo -d GMS -u l10n_cr_einvoice --stop-after-init --no-http`
- Module install: `docker compose run --rm odoo -d GMS -i l10n_cr_einvoice --stop-after-init --no-http`
- Odoo shell: `docker compose run --rm odoo shell -d GMS --no-http`
- The entrypoint already runs `python3 -m odoo -c /etc/odoo/odoo.conf "$@"` -- do NOT pass `odoo` or `server` as args

## Important: Use Project Documentation First

Before guessing, trial-and-error, or fetching external resources, **always check the project's existing documentation** under `docs/`, `_bmad-output/`, and research directories. This project has extensive reference material including:

- Hacienda v4.4 XSD schemas, annexes, and element structures
- Competitive analysis and implementation guides
- PRD, architecture docs, and epic specifications

When facing schema validation errors or unknown API structures, read the local docs first -- do not iterate through external API error responses one at a time.
