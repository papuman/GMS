# -*- coding: utf-8 -*-
"""
Cédula Cache Model for Hacienda API Data
Stores company data fetched from Costa Rica Hacienda API
Multi-tier caching strategy with Fresh/Refresh/Stale/Expired tiers

Part of: GMS E-Invoice Validation & Cédula Lookup System
Architecture: architecture-einvoice-validation-cedula-lookup.md
Reference: DATA-MODEL-CEDULA-CACHE-IMPLEMENTATION.py
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class L10nCrCedulaCache(models.Model):
    """
    Cache model for Hacienda API company data lookups.

    Implements multi-tier caching strategy:
    - Fresh (0-7 days): Auto-serve, no API call
    - Refresh (5-7 days): Serve cache + background refresh
    - Stale (7-90 days): Emergency fallback only
    - Expired (>90 days): Auto-purge via daily cron

    Performance targets:
    - Cache hit: <500ms
    - API call: <5s
    - 90%+ hit rate
    """
    _name = 'l10n_cr.cedula.cache'
    _description = 'Hacienda Cédula/Tax ID Cache'
    _order = 'refreshed_at desc, fetched_at desc'
    _rec_name = 'name'

    # =============================================================================
    # CORE IDENTIFICATION FIELDS
    # =============================================================================

    cedula = fields.Char(
        string='Cédula/Tax ID',
        required=True,
        index=True,
        help='Costa Rica tax identification number (cédula jurídica or física). '
             'Stored in normalized format without hyphens.'
    )

    name = fields.Char(
        string='Company/Person Name',
        required=True,
        index=True,
        help='Legal name as registered in Hacienda database'
    )

    company_type = fields.Selection([
        ('person', 'Natural Person / Freelancer'),
        ('company', 'Limited Liability Company (SRL)'),
        ('corporation', 'Corporation'),
        ('cooperative', 'Cooperative'),
        ('trust', 'Trust / Fideicomiso'),
        ('nonprofit', 'Non-Profit / NGO'),
        ('agricultural', 'Agricultural Cooperative'),
        ('government', 'Government Entity'),
        ('other', 'Other / Unknown'),
    ],
        string='Company Type',
        default='other',
        help='Entity type/tax regime reported by Hacienda API'
    )

    tax_regime = fields.Char(
        string='Tax Regime',
        help='Tax regime code from Hacienda (e.g., "General", "Simplified")'
    )

    tax_status = fields.Selection([
        ('inscrito', 'Active / Registered (Inscrito)'),
        ('inactivo', 'Inactive / Cancelled (Inactivo)'),
        ('no_encontrado', 'Not Found in Registry'),
        ('error', 'Lookup Error / Unverified'),
    ],
        string='Tax Status',
        default='inscrito',
        required=True,
        index=True,
        help='Current registration status in Hacienda system'
    )

    # =============================================================================
    # ECONOMIC ACTIVITIES (CIIU CODES)
    # =============================================================================

    economic_activities = fields.Text(
        string='Economic Activities',
        help='JSON array of CIIU codes and descriptions from Hacienda. '
             'Format: [{"code": "9311", "description": "Gimnasios"}, ...]'
    )

    primary_activity = fields.Char(
        string='Primary Activity',
        help='First CIIU code from activities list (auto-assigned)'
    )

    ciiu_code_id = fields.Many2one(
        'l10n_cr.ciiu.code',
        string='Auto-assigned CIIU',
        help='Automatically matched CIIU from primary activity'
    )

    # =============================================================================
    # CACHE MANAGEMENT FIELDS
    # =============================================================================

    cache_tier = fields.Selection([
        ('fresh', 'Fresh (0-7 days)'),
        ('refresh', 'Refresh Zone (5-7 days)'),
        ('stale', 'Stale (7-90 days)'),
        ('expired', 'Expired (>90 days)'),
    ],
        compute='_compute_cache_tier',
        store=True,
        string='Cache Tier',
        help='Computed cache freshness tier based on age'
    )

    fetched_at = fields.Datetime(
        string='First Fetched',
        required=True,
        default=fields.Datetime.now,
        readonly=True,
        index=True,
        help='Timestamp when this cédula was first cached'
    )

    refreshed_at = fields.Datetime(
        string='Last Refreshed',
        required=True,
        default=fields.Datetime.now,
        readonly=True,
        index=True,
        help='Timestamp of last successful API refresh'
    )

    access_count = fields.Integer(
        string='Access Count',
        default=0,
        readonly=True,
        help='Number of times this cache entry was accessed. '
             'Used to prioritize frequently-used entries for refresh.'
    )

    last_access_at = fields.Datetime(
        string='Last Accessed',
        readonly=True,
        help='Timestamp of last cache hit'
    )

    # =============================================================================
    # CACHE AGE COMPUTED FIELDS
    # =============================================================================

    cache_age_hours = fields.Float(
        compute='_compute_cache_age',
        store=True,
        string='Cache Age (Hours)',
        help='Time elapsed since last refresh (in hours)'
    )

    cache_age_days = fields.Integer(
        compute='_compute_cache_age',
        store=True,
        string='Cache Age (Days)',
        help='Time elapsed since last refresh (in days)'
    )

    # =============================================================================
    # METADATA FIELDS
    # =============================================================================

    source = fields.Selection([
        ('hacienda', 'Hacienda API'),
        ('gometa', 'GoMeta API (fallback)'),
        ('manual', 'Manual Entry'),
    ],
        string='Data Source',
        default='hacienda',
        help='API source of this cache entry'
    )

    raw_response = fields.Text(
        string='Raw API Response',
        help='Complete JSON response from API (for debugging)'
    )

    error_message = fields.Text(
        string='Last Error',
        help='Error message from last failed API call (if any)'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        help='Company that owns this cache entry (multi-company isolation)'
    )

    # =============================================================================
    # CONSTRAINTS (Odoo 19 format)
    # =============================================================================
    _cedula_company_unique = models.UniqueIndex(
        '(cedula, company_id)',
        'This cédula is already cached for this company.',
    )

    # =============================================================================
    # COMPUTED FIELD METHODS
    # =============================================================================

    @api.depends('refreshed_at')
    def _compute_cache_age(self):
        """
        Calculate hours and days elapsed since last refresh.

        Returns:
            0.0 if never refreshed
            float(hours) and int(days) otherwise
        """
        now = datetime.now(timezone.utc)

        for cache in self:
            if not cache.refreshed_at:
                cache.cache_age_hours = 0.0
                cache.cache_age_days = 0
            else:
                # Parse refreshed_at (Odoo stores as UTC)
                refreshed = fields.Datetime.from_string(cache.refreshed_at)

                # Make timezone-aware if naive
                if not refreshed.tzinfo:
                    refreshed = refreshed.replace(tzinfo=timezone.utc)

                # Calculate delta
                delta = now - refreshed
                hours = delta.total_seconds() / 3600.0
                days = int(delta.days)

                cache.cache_age_hours = max(0.0, hours)
                cache.cache_age_days = max(0, days)

    @api.depends('cache_age_days')
    def _compute_cache_tier(self):
        """
        Determine cache tier based on age.

        Tiers:
        - Fresh (0-7 days): Auto-serve, no API call
        - Refresh (5-7 days): Serve + background refresh
        - Stale (7-90 days): Emergency fallback only
        - Expired (>90 days): Purge candidate
        """
        for cache in self:
            age_days = cache.cache_age_days

            if age_days > 90:
                cache.cache_tier = 'expired'
            elif age_days > 7:
                cache.cache_tier = 'stale'
            elif age_days >= 5:
                cache.cache_tier = 'refresh'
            else:
                cache.cache_tier = 'fresh'

    # =============================================================================
    # CACHE FRESHNESS CHECK METHODS
    # =============================================================================

    def is_fresh(self):
        """
        Check if cache is fresh (0-7 days old).

        Returns:
            bool: True if cache can be served without refresh
        """
        self.ensure_one()
        return self.cache_age_days < 7

    def needs_refresh(self):
        """
        Check if cache is in refresh zone (5-7 days old).

        Returns:
            bool: True if background refresh should be triggered
        """
        self.ensure_one()
        return 5 <= self.cache_age_days < 7

    def is_stale(self):
        """
        Check if cache is stale (7-90 days old).

        Returns:
            bool: True if cache should only be used as emergency fallback
        """
        self.ensure_one()
        return 7 <= self.cache_age_days <= 90

    def is_expired(self):
        """
        Check if cache is expired (>90 days old).

        Returns:
            bool: True if cache should be purged
        """
        self.ensure_one()
        return self.cache_age_days > 90

    # =============================================================================
    # CACHE ACCESS METHODS
    # =============================================================================

    def increment_access_count(self):
        """
        Increment access counter when cache is hit.
        Used to prioritize frequently-used entries for refresh.
        """
        for cache in self:
            cache.write({
                'access_count': cache.access_count + 1,
                'last_access_at': fields.Datetime.now(),
            })

    @api.model
    def get_cached(self, cedula, company=None):
        """
        Retrieve cached entry for cédula.

        Args:
            cedula (str): Tax ID number (normalized, no hyphens)
            company (res.company): Company context (defaults to current)

        Returns:
            l10n_cr.cedula.cache record or empty recordset
        """
        company = company or self.env.company

        cache = self.search([
            ('cedula', '=', cedula),
            ('company_id', '=', company.id),
        ], limit=1)

        if cache:
            # Increment access counter
            cache.increment_access_count()

            # Trigger background refresh if entry is in refresh tier
            if cache.cache_tier == 'refresh':
                try:
                    cache._enqueue_refresh_job()
                except Exception:
                    _logger.debug('Failed to enqueue refresh for %s', cedula)

            _logger.debug(
                'Cache HIT for cédula %s (age: %d days, tier: %s)',
                cedula, cache.cache_age_days, cache.cache_tier
            )
        else:
            _logger.debug('Cache MISS for cédula %s', cedula)

        return cache

    def refresh_if_needed(self):
        """
        Trigger background refresh if cache is in refresh zone.

        This method should be called when cache is accessed.
        If refresh is needed, enqueue background job.

        Returns:
            bool: True if refresh was triggered
        """
        self.ensure_one()

        if not self.needs_refresh():
            return False

        # Enqueue background refresh job
        self._enqueue_refresh_job()

        _logger.info(
            'Background refresh triggered for cédula %s (age: %d days)',
            self.cedula, self.cache_age_days
        )

        return True

    def _enqueue_refresh_job(self):
        """
        Enqueue background job to refresh this cache entry using ir.cron.

        Creates a one-time scheduled action that will call refresh_from_api()
        on this specific record. The cron runs once after 1 minute and then
        auto-deletes (numbercall=1).
        """
        self.ensure_one()
        self.env['ir.cron'].sudo().create({
            'name': f'Refresh cédula cache: {self.cedula}',
            'model_id': self.env['ir.model']._get_id('l10n_cr.cedula.cache'),
            'state': 'code',
            'code': f'model.browse({self.id}).refresh_from_api()',
            'interval_type': 'minutes',
            'interval_number': 1,
            'numbercall': 1,  # Run only once
            'doall': False,
        })
        _logger.info('Enqueued refresh job for cédula %s', self.cedula)

    def refresh_from_api(self):
        """
        Refresh this cache entry by calling the Hacienda API.

        Called by the one-time ir.cron job created by _enqueue_refresh_job().
        Updates the cache record with fresh data if the API call succeeds.
        """
        self.ensure_one()
        _logger.info('Refreshing cache entry for cédula %s from API', self.cedula)

        try:
            api = self.env['l10n_cr.hacienda.cedula.api']
            result = api.lookup_cedula(self.cedula)

            if result.get('success'):
                self.env['l10n_cr.cedula.cache'].update_cache(
                    cedula=self.cedula,
                    data={
                        'name': result.get('name'),
                        'tax_regime': result.get('tax_regime'),
                        'tax_status': 'inscrito',
                        'economic_activities': result.get('economic_activities', []),
                        'raw_response': json.dumps(result.get('raw_data', {})),
                    },
                    source='hacienda',
                    company=self.company_id,
                )
                _logger.info('Successfully refreshed cédula %s from API', self.cedula)
            else:
                error_msg = result.get('error', 'Unknown error')
                self.write({'error_message': error_msg[:500]})
                _logger.warning(
                    'Failed to refresh cédula %s from API: %s',
                    self.cedula, error_msg
                )
        except Exception as e:
            self.write({'error_message': str(e)[:500]})
            _logger.error(
                'Exception refreshing cédula %s from API: %s',
                self.cedula, str(e), exc_info=True
            )

    # =============================================================================
    # CACHE UPDATE METHODS
    # =============================================================================

    @api.model
    def update_cache(self, cedula, data, source='hacienda', company=None):
        """
        Create or update cache entry with fresh API data.

        Args:
            cedula (str): Tax ID number
            data (dict): Parsed API response with keys:
                - name (str): Company name
                - company_type (str): Entity type
                - tax_regime (str): Tax regime
                - tax_status (str): Registration status
                - economic_activities (list): CIIU codes
                - raw_response (str): Full JSON response
            source (str): 'hacienda' or 'gometa'
            company (res.company): Company context

        Returns:
            l10n_cr.cedula.cache record (created or updated)
        """
        company = company or self.env.company

        # Check for existing cache entry
        cache = self.search([
            ('cedula', '=', cedula),
            ('company_id', '=', company.id),
        ], limit=1)

        # Parse economic activities
        activities_json = None
        primary_activity = None
        if data.get('economic_activities'):
            import json
            activities_json = json.dumps(data['economic_activities'])
            primary_activity = data['economic_activities'][0].get('code') if data['economic_activities'] else None

        # Prepare values
        vals = {
            'name': data.get('name', 'Unknown'),
            'company_type': data.get('company_type', 'other'),
            'tax_regime': data.get('tax_regime'),
            'tax_status': data.get('tax_status', 'inscrito'),
            'economic_activities': activities_json,
            'primary_activity': primary_activity,
            'source': source,
            'raw_response': data.get('raw_response'),
            'refreshed_at': fields.Datetime.now(),
            'error_message': False,  # Clear any previous errors
        }

        if cache:
            # Update existing cache
            cache.write(vals)
            _logger.info('Cache UPDATED for cédula %s (source: %s)', cedula, source)
        else:
            # Create new cache entry
            vals.update({
                'cedula': cedula,
                'company_id': company.id,
                'fetched_at': fields.Datetime.now(),
            })
            cache = self.create(vals)
            _logger.info('Cache CREATED for cédula %s (source: %s)', cedula, source)

        # Auto-assign CIIU if possible
        if primary_activity:
            cache._auto_assign_ciiu()

        return cache

    def _auto_assign_ciiu(self):
        """
        Attempt to match primary activity code to CIIU catalog.

        If match found, link to l10n_cr.ciiu.code record.
        """
        self.ensure_one()

        if not self.primary_activity:
            return

        # Search CIIU catalog
        ciiu = self.env['l10n_cr.ciiu.code'].search([
            ('code', '=', self.primary_activity),
        ], limit=1)

        if ciiu:
            self.ciiu_code_id = ciiu
            _logger.debug(
                'Auto-assigned CIIU %s to cédula %s',
                ciiu.code, self.cedula
            )

    # =============================================================================
    # BULK OPERATIONS
    # =============================================================================

    @api.model
    def get_stale_cache_entries(self, company=None, limit=50):
        """
        Find cache entries that need refresh (for background jobs).

        Args:
            company (res.company): Company context (if None, searches all companies)
            limit (int): Max results to return

        Returns:
            RecordSet of l10n_cr.cedula.cache in refresh/stale tier
        """
        # Search for entries older than 5 days but not expired (>90 days)
        stale_cutoff = fields.Datetime.now() - timedelta(days=5)
        expired_cutoff = fields.Datetime.now() - timedelta(days=90)

        domain = [
            ('refreshed_at', '<', stale_cutoff),  # Older than 5 days
            ('refreshed_at', '>=', expired_cutoff),  # Not expired yet
        ]

        # Optionally filter by company
        if company:
            domain.append(('company_id', '=', company.id))

        # Order by access_count DESC (prioritize frequently-used)
        caches = self.search(domain, limit=limit, order='access_count desc, refreshed_at asc')

        company_info = company.name if company else 'all companies'
        _logger.info(
            'Found %d stale cache entries for refresh (company: %s)',
            len(caches), company_info
        )

        return caches

    @api.model
    def purge_expired_cache(self, company=None):
        """
        Delete cache entries older than 90 days.

        Should be called by daily cron job.

        Args:
            company (res.company): Company context

        Returns:
            int: Number of entries deleted
        """
        company = company or self.env.company

        # Find expired entries
        cutoff_date = fields.Datetime.now() - timedelta(days=90)

        domain = [
            ('company_id', '=', company.id),
            ('refreshed_at', '<', cutoff_date),
        ]

        expired = self.search(domain)
        count = len(expired)

        if count > 0:
            expired.unlink()
            _logger.info(
                'Purged %d expired cache entries (company: %s)',
                count, company.name
            )

        return count

    @api.model
    def get_cache_statistics(self, company=None):
        """
        Generate cache health statistics for monitoring dashboard.

        Args:
            company (res.company): Company context

        Returns:
            dict: {
                'total_entries': int,
                'fresh': int,
                'refresh_zone': int,
                'stale': int,
                'expired': int,
                'avg_access_count': float,
                'cache_coverage': float (%)
            }
        """
        company = company or self.env.company

        domain = [('company_id', '=', company.id)]
        all_caches = self.search(domain)

        if not all_caches:
            return {
                'total_entries': 0,
                'fresh': 0,
                'refresh_zone': 0,
                'stale': 0,
                'expired': 0,
                'avg_access_count': 0.0,
                'cache_coverage': 0.0,
            }

        fresh = all_caches.filtered(lambda c: c.cache_tier == 'fresh')
        refresh = all_caches.filtered(lambda c: c.cache_tier == 'refresh')
        stale = all_caches.filtered(lambda c: c.cache_tier == 'stale')
        expired = all_caches.filtered(lambda c: c.cache_tier == 'expired')

        total = len(all_caches)
        avg_access = sum(all_caches.mapped('access_count')) / total if total > 0 else 0.0

        # Cache coverage = (fresh + refresh) / total
        coverage = (len(fresh) + len(refresh)) / total * 100.0 if total > 0 else 0.0

        return {
            'total_entries': total,
            'fresh': len(fresh),
            'refresh_zone': len(refresh),
            'stale': len(stale),
            'expired': len(expired),
            'avg_access_count': avg_access,
            'cache_coverage': coverage,
        }

    # =============================================================================
    # CRON JOB METHODS
    # =============================================================================

    @api.model
    def _cron_refresh_stale_cache(self):
        """
        Background cron job to refresh stale cache entries.

        Configuration:
            - Runs every 6 hours (configurable)
            - Batch size controlled by system parameter
            - Rate-limited to 10 requests/sec max
            - Prioritizes by access_count (most used first)

        System Parameters:
            - l10n_cr_einvoice.cache_refresh_batch_size (default: 100)

        Process:
            1. Find entries in Refresh tier (5-7 days old)
            2. Sort by access_count DESC (high-traffic entries first)
            3. Refresh via Hacienda API with rate limiting
            4. Log statistics and errors

        Returns:
            dict: Execution statistics
        """
        start_time = datetime.now(timezone.utc)
        _logger.info('=== CRON START: Refresh Stale Cache Entries ===')

        # Get batch size from system parameters
        batch_size = int(self.env['ir.config_parameter'].sudo().get_param(
            'l10n_cr_einvoice.cache_refresh_batch_size', 100
        ))

        # Get entries needing refresh (search across all companies)
        # Use sudo() to bypass company restrictions in multi-company environments
        stale = self.sudo().get_stale_cache_entries(limit=batch_size)

        if not stale:
            _logger.info('No stale cache entries found. Exiting.')
            return {
                'success': True,
                'processed': 0,
                'refreshed': 0,
                'failed': 0,
                'duration_seconds': 0,
            }

        _logger.info('Found %d stale cache entries to refresh', len(stale))

        # Statistics tracking
        stats = {
            'processed': 0,
            'refreshed': 0,
            'failed': 0,
            'errors': [],
        }

        # Rate limiting: 10 requests/second = 0.1 second delay
        rate_limit_delay = 0.1

        # Process each cache entry
        for i, cache in enumerate(stale):
            stats['processed'] += 1

            try:
                _logger.debug(
                    'Refreshing cache [%d/%d]: cédula=%s, age=%d days, access_count=%d',
                    i + 1, len(stale), cache.cedula, cache.cache_age_days, cache.access_count
                )

                # Call Hacienda API to refresh data
                api = self.env['l10n_cr.hacienda.cedula.api']
                result = api.lookup_cedula(cache.cedula)

                if result.get('success'):
                    # Update cache with fresh data
                    self.update_cache(
                        cedula=cache.cedula,
                        data={
                            'name': result.get('name'),
                            'tax_regime': result.get('tax_regime'),
                            'tax_status': 'inscrito',
                            'economic_activities': result.get('economic_activities', []),
                            'raw_response': json.dumps(result.get('raw_data', {})),
                        },
                        source='hacienda',
                        company=cache.company_id,
                    )

                    stats['refreshed'] += 1
                    _logger.info('Successfully refreshed cédula %s', cache.cedula)

                else:
                    # API call failed
                    error_msg = result.get('error', 'Unknown error')
                    cache.write({'error_message': error_msg[:500]})
                    stats['failed'] += 1
                    stats['errors'].append({
                        'cedula': cache.cedula,
                        'error': error_msg,
                    })
                    _logger.warning('Failed to refresh cédula %s: %s', cache.cedula, error_msg)

            except Exception as e:
                # Unexpected error - log and continue
                error_msg = str(e)
                cache.write({'error_message': error_msg[:500]})
                stats['failed'] += 1
                stats['errors'].append({
                    'cedula': cache.cedula,
                    'error': error_msg,
                })
                _logger.error(
                    'Unexpected error refreshing cédula %s: %s',
                    cache.cedula, error_msg, exc_info=True
                )

            # Rate limiting: wait before next request
            if i < len(stale) - 1:  # Don't delay after last entry
                import time
                time.sleep(rate_limit_delay)

        # Calculate execution time
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        # Log summary
        _logger.info('=== CRON COMPLETE: Refresh Stale Cache ===')
        _logger.info('Processed: %d entries', stats['processed'])
        _logger.info('Refreshed: %d (%.1f%%)', stats['refreshed'],
                     (stats['refreshed'] / stats['processed'] * 100) if stats['processed'] > 0 else 0)
        _logger.info('Failed: %d (%.1f%%)', stats['failed'],
                     (stats['failed'] / stats['processed'] * 100) if stats['processed'] > 0 else 0)
        _logger.info('Duration: %.2f seconds (avg %.2f sec/entry)',
                     duration, duration / stats['processed'] if stats['processed'] > 0 else 0)

        # Send notification if failure rate > 50%
        if stats['processed'] > 0 and (stats['failed'] / stats['processed']) > 0.5:
            self._send_cron_failure_notification(
                cron_name='Refresh Stale Cache',
                stats=stats,
                duration=duration,
            )

        stats['duration_seconds'] = duration
        stats['success'] = True
        return stats

    @api.model
    def _cron_purge_expired_cache(self):
        """
        Background cron job to delete expired cache entries.

        Configuration:
            - Runs daily at 2:00 AM (configurable)
            - Max age controlled by system parameter

        System Parameters:
            - l10n_cr_einvoice.cache_max_age_days (default: 90)

        Process:
            1. Find entries older than max_age_days
            2. Archive to history table (optional future enhancement)
            3. Delete expired entries
            4. Log purge statistics

        Returns:
            dict: Execution statistics
        """
        start_time = datetime.now(timezone.utc)
        _logger.info('=== CRON START: Purge Expired Cache Entries ===')

        # Get max age from system parameters
        max_age_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'l10n_cr_einvoice.cache_max_age_days', 90
        ))

        _logger.info('Purging cache entries older than %d days', max_age_days)

        # Find expired entries
        cutoff_date = fields.Datetime.now() - timedelta(days=max_age_days)

        domain = [
            ('refreshed_at', '<', cutoff_date),
        ]

        # Count per company for logging
        expired_by_company = {}
        for company in self.env['res.company'].search([]):
            company_domain = domain + [('company_id', '=', company.id)]
            expired = self.search(company_domain)
            if expired:
                expired_by_company[company.name] = len(expired)

        # Delete all expired entries (all companies)
        expired_all = self.search(domain)
        total_count = len(expired_all)

        if total_count > 0:
            # Optional: Archive to history table before deletion
            # self._archive_to_history(expired_all)

            expired_all.unlink()

            _logger.info('=== CRON COMPLETE: Purge Expired Cache ===')
            _logger.info('Total purged: %d entries', total_count)
            for company_name, count in expired_by_company.items():
                _logger.info('  - %s: %d entries', company_name, count)
        else:
            _logger.info('No expired cache entries found. Exiting.')

        # Calculate execution time
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        _logger.info('Duration: %.2f seconds', duration)

        return {
            'success': True,
            'purged': total_count,
            'by_company': expired_by_company,
            'duration_seconds': duration,
        }

    @api.model
    def _cron_priority_refresh(self):
        """
        Background cron job to refresh high-access-count cache entries.

        Configuration:
            - Runs daily at 3:00 AM (configurable)
            - Priority threshold controlled by system parameter
            - Ensures frequently-used entries are always fresh

        System Parameters:
            - l10n_cr_einvoice.cache_priority_threshold (default: 10)
            - l10n_cr_einvoice.cache_refresh_batch_size (default: 100)

        Process:
            1. Find entries with access_count > threshold
            2. Refresh regardless of age (even if fresh)
            3. Ensures high-traffic entries never go stale
            4. Log statistics

        Returns:
            dict: Execution statistics
        """
        start_time = datetime.now(timezone.utc)
        _logger.info('=== CRON START: Priority Refresh (High-Access Entries) ===')

        # Get configuration from system parameters
        priority_threshold = int(self.env['ir.config_parameter'].sudo().get_param(
            'l10n_cr_einvoice.cache_priority_threshold', 10
        ))
        batch_size = int(self.env['ir.config_parameter'].sudo().get_param(
            'l10n_cr_einvoice.cache_refresh_batch_size', 100
        ))

        _logger.info('Priority threshold: access_count > %d', priority_threshold)

        # Find high-traffic cache entries
        domain = [
            ('access_count', '>', priority_threshold),
        ]

        # Order by access_count DESC (most used first)
        priority_entries = self.search(
            domain,
            limit=batch_size,
            order='access_count desc, refreshed_at asc'
        )

        if not priority_entries:
            _logger.info('No priority cache entries found. Exiting.')
            return {
                'success': True,
                'processed': 0,
                'refreshed': 0,
                'failed': 0,
                'duration_seconds': 0,
            }

        _logger.info('Found %d priority cache entries to refresh', len(priority_entries))

        # Statistics tracking
        stats = {
            'processed': 0,
            'refreshed': 0,
            'failed': 0,
            'errors': [],
        }

        # Rate limiting: 10 requests/second = 0.1 second delay
        rate_limit_delay = 0.1

        # Process each priority entry
        for i, cache in enumerate(priority_entries):
            stats['processed'] += 1

            try:
                _logger.debug(
                    'Priority refresh [%d/%d]: cédula=%s, access_count=%d, age=%d days',
                    i + 1, len(priority_entries), cache.cedula, cache.access_count, cache.cache_age_days
                )

                # Call Hacienda API to refresh data
                api = self.env['l10n_cr.hacienda.cedula.api']
                result = api.lookup_cedula(cache.cedula)

                if result.get('success'):
                    # Update cache with fresh data
                    self.update_cache(
                        cedula=cache.cedula,
                        data={
                            'name': result.get('name'),
                            'tax_regime': result.get('tax_regime'),
                            'tax_status': 'inscrito',
                            'economic_activities': result.get('economic_activities', []),
                            'raw_response': json.dumps(result.get('raw_data', {})),
                        },
                        source='hacienda',
                        company=cache.company_id,
                    )

                    stats['refreshed'] += 1
                    _logger.info('Successfully refreshed priority cédula %s', cache.cedula)

                else:
                    # API call failed
                    error_msg = result.get('error', 'Unknown error')
                    cache.write({'error_message': error_msg[:500]})
                    stats['failed'] += 1
                    stats['errors'].append({
                        'cedula': cache.cedula,
                        'error': error_msg,
                    })
                    _logger.warning('Failed to refresh priority cédula %s: %s', cache.cedula, error_msg)

            except Exception as e:
                # Unexpected error - log and continue
                error_msg = str(e)
                cache.write({'error_message': error_msg[:500]})
                stats['failed'] += 1
                stats['errors'].append({
                    'cedula': cache.cedula,
                    'error': error_msg,
                })
                _logger.error(
                    'Unexpected error refreshing priority cédula %s: %s',
                    cache.cedula, error_msg, exc_info=True
                )

            # Rate limiting: wait before next request
            if i < len(priority_entries) - 1:  # Don't delay after last entry
                import time
                time.sleep(rate_limit_delay)

        # Calculate execution time
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        # Log summary
        _logger.info('=== CRON COMPLETE: Priority Refresh ===')
        _logger.info('Processed: %d entries', stats['processed'])
        _logger.info('Refreshed: %d (%.1f%%)', stats['refreshed'],
                     (stats['refreshed'] / stats['processed'] * 100) if stats['processed'] > 0 else 0)
        _logger.info('Failed: %d (%.1f%%)', stats['failed'],
                     (stats['failed'] / stats['processed'] * 100) if stats['processed'] > 0 else 0)
        _logger.info('Duration: %.2f seconds (avg %.2f sec/entry)',
                     duration, duration / stats['processed'] if stats['processed'] > 0 else 0)

        # Send notification if failure rate > 50%
        if stats['processed'] > 0 and (stats['failed'] / stats['processed']) > 0.5:
            self._send_cron_failure_notification(
                cron_name='Priority Refresh',
                stats=stats,
                duration=duration,
            )

        stats['duration_seconds'] = duration
        stats['success'] = True
        return stats

    @api.model
    def _send_cron_failure_notification(self, cron_name, stats, duration):
        """
        Send notification when cron job has high failure rate.

        Args:
            cron_name (str): Name of the cron job
            stats (dict): Execution statistics
            duration (float): Execution time in seconds
        """
        try:
            # Get admin users to notify
            admin_users = self.env.ref('base.group_system').user_ids

            if not admin_users:
                _logger.warning('No admin users found to send cron failure notification')
                return

            # Build notification message
            failure_rate = (stats['failed'] / stats['processed'] * 100) if stats['processed'] > 0 else 0

            message = _(
                '<p><strong>Cron Job Failure Alert: %(cron_name)s</strong></p>'
                '<p>The scheduled cache maintenance job has encountered issues:</p>'
                '<ul>'
                '<li>Processed: %(processed)d entries</li>'
                '<li>Failed: %(failed)d entries (%(failure_rate).1f%%)</li>'
                '<li>Duration: %(duration).2f seconds</li>'
                '</ul>'
            ) % {
                'cron_name': cron_name,
                'processed': stats['processed'],
                'failed': stats['failed'],
                'failure_rate': failure_rate,
                'duration': duration,
            }

            # Add error samples (first 5 errors)
            if stats.get('errors'):
                error_samples = stats['errors'][:5]
                message += '<p><strong>Sample Errors:</strong></p><ul>'
                for err in error_samples:
                    message += '<li>Cédula %(cedula)s: %(error)s</li>' % {
                        'cedula': err['cedula'],
                        'error': err['error'][:100],
                    }
                message += '</ul>'

            # Send notification via internal message (Odoo 19 compatible)
            # user.notify_warning() does not exist in Odoo 19.
            # Instead, post a message on the admin user's partner record
            # which will appear in their inbox/chatter.
            notification_title = _('Cron Job Alert: %s') % cron_name
            for user in admin_users:
                try:
                    user.partner_id.message_post(
                        body=message,
                        subject=notification_title,
                        message_type='notification',
                        subtype_xmlid='mail.mt_note',
                    )
                except Exception as e:
                    _logger.error('Failed to notify user %s: %s', user.name, str(e))

            _logger.info('Sent failure notification to %d admin users', len(admin_users))

        except Exception as e:
            _logger.error('Failed to send cron failure notification: %s', str(e), exc_info=True)
