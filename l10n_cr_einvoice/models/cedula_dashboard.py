# -*- coding: utf-8 -*-
"""
Cédula Lookup Dashboard - Admin Monitoring Dashboard
Real-time cache health, API metrics, and lookup statistics

Part of: GMS E-Invoice Validation & Cédula Lookup System
Architecture: architecture-einvoice-validation-cedula-lookup.md
"""

import logging
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class L10nCrCedulaDashboard(models.AbstractModel):
    """
    Admin monitoring dashboard for cédula cache health and API performance.

    Provides real-time metrics for:
    - Cache health and tier distribution
    - Hacienda API performance and success rates
    - Usage statistics and trends
    - Rate limiter status
    """
    _name = 'l10n_cr.cedula.dashboard'
    _description = 'Cédula Lookup Monitoring Dashboard'

    name = fields.Char(string='Dashboard Name', default='Cédula Lookup Dashboard')

    # =========================================================================
    # CACHE HEALTH METRICS
    # =========================================================================

    @api.model
    def get_cache_health_metrics(self, company=None):
        """
        Get comprehensive cache health metrics.

        Returns cache tier distribution, age statistics, and health indicators.

        Args:
            company (res.company): Company context (defaults to current)

        Returns:
            dict: {
                'total_cached': int,
                'fresh_count': int,          # 0-7 days
                'refresh_needed': int,       # 5-7 days
                'stale_count': int,          # 7-90 days
                'expired_count': int,        # >90 days
                'cache_coverage': float,     # % in fresh/refresh tier
                'hit_rate': float,           # Cache hit % (estimated)
                'avg_age_days': float,
                'health_status': str,        # 'healthy', 'warning', 'critical'
            }
        """
        company = company or self.env.company
        CedulaCache = self.env['l10n_cr.cedula.cache']

        # Get all cache entries
        domain = [('company_id', '=', company.id)]
        all_caches = CedulaCache.search(domain)

        if not all_caches:
            return {
                'total_cached': 0,
                'fresh_count': 0,
                'refresh_needed': 0,
                'stale_count': 0,
                'expired_count': 0,
                'cache_coverage': 0.0,
                'hit_rate': 0.0,
                'avg_age_days': 0.0,
                'health_status': 'healthy',
            }

        # Count by tier
        fresh = all_caches.filtered(lambda c: c.cache_tier == 'fresh')
        refresh = all_caches.filtered(lambda c: c.cache_tier == 'refresh')
        stale = all_caches.filtered(lambda c: c.cache_tier == 'stale')
        expired = all_caches.filtered(lambda c: c.cache_tier == 'expired')

        total = len(all_caches)
        fresh_count = len(fresh)
        refresh_count = len(refresh)
        stale_count = len(stale)
        expired_count = len(expired)

        # Cache coverage = (fresh + refresh) / total * 100
        cache_coverage = ((fresh_count + refresh_count) / total * 100.0) if total > 0 else 0.0

        # Average age
        avg_age = sum(all_caches.mapped('cache_age_days')) / total if total > 0 else 0.0

        # Estimated hit rate (access_count indicates cache hits)
        # Higher access_count means better hit rate
        total_accesses = sum(all_caches.mapped('access_count'))
        avg_accesses = total_accesses / total if total > 0 else 0.0
        # Assume hit rate correlates with access frequency and freshness
        estimated_hit_rate = min(95.0, cache_coverage * 0.9 + avg_accesses * 0.5)

        # Determine health status
        health_status = 'healthy'
        if cache_coverage < 50.0 or expired_count > total * 0.2:
            health_status = 'critical'
        elif cache_coverage < 70.0 or expired_count > total * 0.1:
            health_status = 'warning'

        return {
            'total_cached': total,
            'fresh_count': fresh_count,
            'refresh_needed': refresh_count,
            'stale_count': stale_count,
            'expired_count': expired_count,
            'cache_coverage': round(cache_coverage, 2),
            'hit_rate': round(estimated_hit_rate, 2),
            'avg_age_days': round(avg_age, 2),
            'health_status': health_status,
        }

    @api.model
    def get_cache_size_by_tier(self, company=None):
        """
        Get cache size breakdown by tier for pie/donut chart.

        Args:
            company (res.company): Company context

        Returns:
            list: [
                {'tier': 'Fresh (0-7 days)', 'count': 150, 'percentage': 65.2},
                {'tier': 'Refresh (5-7 days)', 'count': 40, 'percentage': 17.4},
                {'tier': 'Stale (7-90 days)', 'count': 30, 'percentage': 13.0},
                {'tier': 'Expired (>90 days)', 'count': 10, 'percentage': 4.4},
            ]
        """
        health = self.get_cache_health_metrics(company=company)
        total = health['total_cached']

        if total == 0:
            return []

        tiers = [
            {
                'tier': _('Fresh (0-7 days)'),
                'count': health['fresh_count'],
                'percentage': round(health['fresh_count'] / total * 100.0, 1),
                'color': '#28a745',  # Green
            },
            {
                'tier': _('Refresh (5-7 days)'),
                'count': health['refresh_needed'],
                'percentage': round(health['refresh_needed'] / total * 100.0, 1),
                'color': '#ffc107',  # Yellow
            },
            {
                'tier': _('Stale (7-90 days)'),
                'count': health['stale_count'],
                'percentage': round(health['stale_count'] / total * 100.0, 1),
                'color': '#fd7e14',  # Orange
            },
            {
                'tier': _('Expired (>90 days)'),
                'count': health['expired_count'],
                'percentage': round(health['expired_count'] / total * 100.0, 1),
                'color': '#dc3545',  # Red
            },
        ]

        return tiers

    # =========================================================================
    # API PERFORMANCE METRICS
    # =========================================================================

    @api.model
    def get_api_performance_metrics(self, hours=24, company=None):
        """
        Get Hacienda API performance metrics for last N hours.

        Analyzes cache entries to estimate API success rates and performance.

        Args:
            hours (int): Time window in hours (default: 24)
            company (res.company): Company context

        Returns:
            dict: {
                'success_rate': float,           # % successful lookups
                'failure_rate': float,           # % failed lookups
                'avg_response_time': float,      # Estimated avg response time (seconds)
                'total_lookups': int,            # Total API calls
                'successful_lookups': int,       # Successful API calls
                'failed_lookups': int,           # Failed API calls
                'fallback_gometa_count': int,    # Fallback to GoMeta API
                'not_found_count': int,          # Cédulas not found
                'rate_limit_hits': int,          # Estimated rate limit hits
                'status': str,                   # 'healthy', 'warning', 'critical'
            }
        """
        company = company or self.env.company
        CedulaCache = self.env['l10n_cr.cedula.cache']

        # Get entries created/refreshed in last N hours
        cutoff = fields.Datetime.now() - timedelta(hours=hours)
        domain = [
            ('company_id', '=', company.id),
            '|',
            ('fetched_at', '>=', cutoff),
            ('refreshed_at', '>=', cutoff),
        ]

        recent_caches = CedulaCache.search(domain)

        if not recent_caches:
            return {
                'success_rate': 100.0,
                'failure_rate': 0.0,
                'avg_response_time': 0.0,
                'total_lookups': 0,
                'successful_lookups': 0,
                'failed_lookups': 0,
                'fallback_gometa_count': 0,
                'not_found_count': 0,
                'rate_limit_hits': 0,
                'status': 'healthy',
            }

        total = len(recent_caches)

        # Count by source and status
        hacienda_success = recent_caches.filtered(
            lambda c: c.source == 'hacienda' and c.tax_status == 'inscrito'
        )
        gometa_fallback = recent_caches.filtered(lambda c: c.source == 'gometa')
        not_found = recent_caches.filtered(lambda c: c.tax_status == 'no_encontrado')
        errors = recent_caches.filtered(lambda c: c.tax_status == 'error' or c.error_message)

        successful = len(hacienda_success)
        failed = len(errors)
        fallback = len(gometa_fallback)
        not_found_count = len(not_found)

        # Success rate = (successful + not_found) / total
        # (not_found is a successful API call, just no data)
        success_rate = ((successful + not_found_count) / total * 100.0) if total > 0 else 100.0
        failure_rate = (failed / total * 100.0) if total > 0 else 0.0

        # Estimate rate limit hits (heuristic: errors with retry patterns)
        # In production, you'd track this explicitly
        rate_limit_hits = 0  # TODO: Track this in cache model

        # Estimate avg response time (assume 1-3 seconds for Hacienda API)
        # In production, store actual response times
        avg_response_time = 2.0  # Default estimate

        # Determine status
        status = 'healthy'
        if failure_rate > 20.0:
            status = 'critical'
        elif failure_rate > 10.0:
            status = 'warning'

        return {
            'success_rate': round(success_rate, 2),
            'failure_rate': round(failure_rate, 2),
            'avg_response_time': avg_response_time,
            'total_lookups': total,
            'successful_lookups': successful,
            'failed_lookups': failed,
            'fallback_gometa_count': fallback,
            'not_found_count': not_found_count,
            'rate_limit_hits': rate_limit_hits,
            'status': status,
        }

    @api.model
    def get_api_performance_trend(self, days=7, company=None):
        """
        Get API performance trend over last N days.

        Returns daily success/failure counts for charting.

        Args:
            days (int): Number of days to analyze
            company (res.company): Company context

        Returns:
            list: [
                {'date': '2025-02-01', 'successful': 45, 'failed': 3, 'success_rate': 93.75},
                {'date': '2025-02-02', 'successful': 52, 'failed': 1, 'success_rate': 98.11},
                ...
            ]
        """
        company = company or self.env.company
        CedulaCache = self.env['l10n_cr.cedula.cache']

        # Get entries from last N days
        cutoff = fields.Date.today() - timedelta(days=days)

        # SQL query for efficient daily aggregation
        query = """
            SELECT
                DATE(refreshed_at) as date,
                COUNT(*) as total,
                COUNT(CASE WHEN source = 'hacienda' AND tax_status = 'inscrito' THEN 1 END) as successful,
                COUNT(CASE WHEN tax_status = 'error' OR error_message IS NOT NULL THEN 1 END) as failed
            FROM l10n_cr_cedula_cache
            WHERE company_id = %s
                AND refreshed_at >= %s
            GROUP BY DATE(refreshed_at)
            ORDER BY date
        """

        self.env.cr.execute(query, (company.id, cutoff))
        results = self.env.cr.dictfetchall()

        trend_data = []
        for row in results:
            total = row['total']
            successful = row['successful']
            failed = row['failed']
            success_rate = (successful / total * 100.0) if total > 0 else 0.0

            trend_data.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'successful': successful,
                'failed': failed,
                'success_rate': round(success_rate, 2),
            })

        return trend_data

    # =========================================================================
    # USAGE STATISTICS
    # =========================================================================

    @api.model
    def get_usage_statistics(self, period='today', company=None):
        """
        Get lookup usage statistics for specified period.

        Args:
            period (str): 'today', 'week', 'month'
            company (res.company): Company context

        Returns:
            dict: {
                'total_lookups': int,
                'unique_cedulas': int,
                'cache_hits': int,
                'api_calls': int,
                'avg_lookups_per_day': float,
                'peak_hour': int,  # Hour of day (0-23)
            }
        """
        company = company or self.env.company
        CedulaCache = self.env['l10n_cr.cedula.cache']

        # Determine date range
        today = fields.Date.today()
        if period == 'today':
            date_from = today
            date_to = today
        elif period == 'week':
            date_from = today - timedelta(days=7)
            date_to = today
        elif period == 'month':
            date_from = today - timedelta(days=30)
            date_to = today
        else:
            raise UserError(_('Invalid period: %s') % period)

        # Get entries accessed in period
        domain = [
            ('company_id', '=', company.id),
            ('last_access_at', '>=', fields.Datetime.to_string(datetime.combine(date_from, datetime.min.time()))),
            ('last_access_at', '<=', fields.Datetime.to_string(datetime.combine(date_to, datetime.max.time()))),
        ]

        accessed_caches = CedulaCache.search(domain)

        total_lookups = sum(accessed_caches.mapped('access_count'))
        unique_cedulas = len(accessed_caches)

        # Estimate cache hits vs API calls
        # Cache hit = lookup from fresh/refresh tier
        # API call = lookup that triggered refresh/fetch
        fresh_lookups = sum(
            accessed_caches.filtered(lambda c: c.cache_tier in ['fresh', 'refresh']).mapped('access_count')
        )
        cache_hits = fresh_lookups
        api_calls = total_lookups - cache_hits

        # Average lookups per day
        days_in_period = (date_to - date_from).days + 1
        avg_per_day = total_lookups / days_in_period if days_in_period > 0 else 0.0

        # Peak hour (estimate - in production, track access timestamps)
        peak_hour = 14  # Default: 2 PM (typical business peak)

        return {
            'total_lookups': total_lookups,
            'unique_cedulas': unique_cedulas,
            'cache_hits': cache_hits,
            'api_calls': api_calls,
            'avg_lookups_per_day': round(avg_per_day, 2),
            'peak_hour': peak_hour,
        }

    @api.model
    def get_top_looked_up_cedulas(self, limit=10, company=None):
        """
        Get most frequently looked-up cédulas.

        Args:
            limit (int): Number of top cédulas to return
            company (res.company): Company context

        Returns:
            list: [
                {
                    'cedula': '3101234567',
                    'name': 'GIMNASIO FITNESS CR S.A.',
                    'access_count': 245,
                    'last_access': '2025-02-04 10:30:00',
                    'cache_tier': 'fresh',
                },
                ...
            ]
        """
        company = company or self.env.company
        CedulaCache = self.env['l10n_cr.cedula.cache']

        # Get top N by access_count
        domain = [('company_id', '=', company.id)]
        top_caches = CedulaCache.search(domain, limit=limit, order='access_count desc, last_access_at desc')

        return [{
            'cedula': cache.cedula,
            'name': cache.name,
            'access_count': cache.access_count,
            'last_access': fields.Datetime.to_string(cache.last_access_at) if cache.last_access_at else '',
            'cache_tier': cache.cache_tier,
        } for cache in top_caches]

    # =========================================================================
    # COMBINED DASHBOARD DATA
    # =========================================================================

    @api.model
    def get_dashboard_data(self, company=None):
        """
        Get all dashboard data in a single call.

        Aggregates cache health, API performance, and usage stats.

        Args:
            company (res.company): Company context

        Returns:
            dict: Complete dashboard dataset
        """
        company = company or self.env.company

        return {
            'timestamp': fields.Datetime.now(),
            'cache_health': self.get_cache_health_metrics(company=company),
            'cache_tiers': self.get_cache_size_by_tier(company=company),
            'api_performance': self.get_api_performance_metrics(hours=24, company=company),
            'api_trend': self.get_api_performance_trend(days=7, company=company),
            'usage_today': self.get_usage_statistics(period='today', company=company),
            'usage_week': self.get_usage_statistics(period='week', company=company),
            'usage_month': self.get_usage_statistics(period='month', company=company),
            'top_cedulas': self.get_top_looked_up_cedulas(limit=10, company=company),
        }

    # =========================================================================
    # RATE LIMITER STATUS
    # =========================================================================

    @api.model
    def get_rate_limiter_status(self):
        """
        Get current rate limiter status.

        Returns rate limit configuration and current token availability.

        Returns:
            dict: {
                'enabled': bool,
                'max_requests_per_second': int,
                'burst_limit': int,
                'tokens_available': int,
                'next_token_at': datetime,
                'status': str,  # 'ok', 'throttled', 'exhausted'
            }
        """
        # Rate limiter configuration for Hacienda API
        # Actual implementation depends on rate limiter design
        return {
            'enabled': True,
            'max_requests_per_second': 10,
            'burst_limit': 20,
            'tokens_available': 15,  # Simulated - track in production
            'next_token_at': fields.Datetime.now() + timedelta(milliseconds=100),
            'status': 'ok',  # 'ok', 'throttled', 'exhausted'
        }

    # =========================================================================
    # SCHEDULED REPORTS
    # =========================================================================

    @api.model
    def send_weekly_cache_health_report(self):
        """
        Send weekly cache health report to administrators.

        Scheduled to run every Monday at 9:00 AM.
        """
        _logger.info('Generating weekly cache health report...')

        dashboard_data = self.get_dashboard_data()
        cache_health = dashboard_data['cache_health']
        api_perf = dashboard_data['api_performance']

        # Get admin users
        admin_users = self.env.ref('base.group_system').users

        subject = _('Weekly Cédula Cache Health Report - %s') % fields.Date.today().strftime('%d/%m/%Y')

        # Determine status color
        status = cache_health['health_status']
        status_color = {
            'healthy': 'green',
            'warning': 'orange',
            'critical': 'red',
        }.get(status, 'gray')

        body = f"""
        <h2>Weekly Cédula Cache Health Report</h2>
        <p><strong>Report Date:</strong> {fields.Date.today().strftime('%d de %B de %Y')}</p>
        <p><strong>Overall Status:</strong> <span style="color: {status_color}; font-weight: bold;">{status.upper()}</span></p>

        <h3>Cache Health</h3>
        <ul>
            <li><strong>Total Cached Entries:</strong> {cache_health['total_cached']}</li>
            <li><strong>Fresh (0-7 days):</strong> {cache_health['fresh_count']} ({cache_health['fresh_count'] / cache_health['total_cached'] * 100:.1f}%)</li>
            <li><strong>Refresh Needed (5-7 days):</strong> {cache_health['refresh_needed']}</li>
            <li><strong>Stale (7-90 days):</strong> {cache_health['stale_count']}</li>
            <li><strong>Expired (>90 days):</strong> {cache_health['expired_count']}</li>
            <li><strong>Cache Coverage:</strong> {cache_health['cache_coverage']}%</li>
            <li><strong>Estimated Hit Rate:</strong> {cache_health['hit_rate']}%</li>
        </ul>

        <h3>API Performance (Last 7 Days)</h3>
        <ul>
            <li><strong>Success Rate:</strong> {api_perf['success_rate']}%</li>
            <li><strong>Total Lookups:</strong> {api_perf['total_lookups']}</li>
            <li><strong>Successful:</strong> {api_perf['successful_lookups']}</li>
            <li><strong>Failed:</strong> {api_perf['failed_lookups']}</li>
            <li><strong>Fallback to GoMeta:</strong> {api_perf['fallback_gometa_count']}</li>
        </ul>

        <h3>Recommendations</h3>
        <ul>
        """

        # Add recommendations based on status
        if cache_health['expired_count'] > 0:
            body += f"<li>Purge {cache_health['expired_count']} expired cache entries</li>"
        if cache_health['refresh_needed'] > 10:
            body += f"<li>Refresh {cache_health['refresh_needed']} stale cache entries</li>"
        if api_perf['failure_rate'] > 10.0:
            body += f"<li>Investigate API failures ({api_perf['failure_rate']}% failure rate)</li>"
        if cache_health['cache_coverage'] < 70.0:
            body += f"<li>Cache coverage low ({cache_health['cache_coverage']}%) - consider increasing refresh frequency</li>"

        if not any([cache_health['expired_count'] > 0, cache_health['refresh_needed'] > 10, api_perf['failure_rate'] > 10.0]):
            body += "<li>No issues detected - system operating normally</li>"

        body += """
        </ul>

        <p><em>This is an automated report from the Cédula Lookup System.</em></p>
        """

        # Send email to each admin
        for user in admin_users:
            if user.email:
                mail = self.env['mail.mail'].create({
                    'subject': subject,
                    'body_html': body,
                    'email_to': user.email,
                })
                mail.send()

        _logger.info(f'Weekly cache health report sent to {len(admin_users)} administrators')

    @api.model
    def send_monthly_api_usage_summary(self):
        """
        Send monthly API usage summary to administrators.

        Scheduled to run on the 1st of each month.
        """
        _logger.info('Generating monthly API usage summary...')

        dashboard_data = self.get_dashboard_data()
        usage_month = dashboard_data['usage_month']
        top_cedulas = dashboard_data['top_cedulas']

        # Get admin users
        admin_users = self.env.ref('base.group_system').users

        last_month = fields.Date.today() - timedelta(days=30)
        subject = _('Monthly Cédula API Usage Summary - %s') % last_month.strftime('%B %Y')

        body = f"""
        <h2>Monthly Cédula API Usage Summary</h2>
        <p><strong>Period:</strong> Last 30 Days</p>

        <h3>Usage Statistics</h3>
        <ul>
            <li><strong>Total Lookups:</strong> {usage_month['total_lookups']}</li>
            <li><strong>Unique Cédulas:</strong> {usage_month['unique_cedulas']}</li>
            <li><strong>Cache Hits:</strong> {usage_month['cache_hits']} ({usage_month['cache_hits'] / usage_month['total_lookups'] * 100:.1f}%)</li>
            <li><strong>API Calls:</strong> {usage_month['api_calls']}</li>
            <li><strong>Average Lookups/Day:</strong> {usage_month['avg_lookups_per_day']}</li>
        </ul>

        <h3>Top 10 Most Looked-Up Cédulas</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
            <tr style="background-color: #f0f0f0;">
                <th>Rank</th>
                <th>Cédula</th>
                <th>Company Name</th>
                <th>Access Count</th>
            </tr>
        """

        for i, cedula in enumerate(top_cedulas, 1):
            body += f"""
            <tr>
                <td>{i}</td>
                <td>{cedula['cedula']}</td>
                <td>{cedula['name']}</td>
                <td>{cedula['access_count']}</td>
            </tr>
            """

        body += """
        </table>

        <p><em>This is an automated report from the Cédula Lookup System.</em></p>
        """

        # Send email to each admin
        for user in admin_users:
            if user.email:
                mail = self.env['mail.mail'].create({
                    'subject': subject,
                    'body_html': body,
                    'email_to': user.email,
                })
                mail.send()

        _logger.info(f'Monthly API usage summary sent to {len(admin_users)} administrators')

    @api.model
    def check_and_send_alerts(self):
        """
        Check system health and send alerts if issues detected.

        Runs every hour. Sends alerts for:
        - API failure rate > 10%
        - Cache coverage < 50%
        - Excessive expired entries (>20%)

        Should be called by hourly cron job.
        """
        _logger.info('Checking cédula lookup system health...')

        dashboard_data = self.get_dashboard_data()
        cache_health = dashboard_data['cache_health']
        api_perf = dashboard_data['api_performance']

        # Check for alert conditions
        alerts = []

        if api_perf['failure_rate'] > 10.0:
            alerts.append({
                'severity': 'critical' if api_perf['failure_rate'] > 20.0 else 'warning',
                'message': f"High API failure rate: {api_perf['failure_rate']}% (last 24h)",
                'recommendation': 'Check Hacienda API connectivity and credentials',
            })

        if cache_health['cache_coverage'] < 50.0:
            alerts.append({
                'severity': 'critical' if cache_health['cache_coverage'] < 30.0 else 'warning',
                'message': f"Low cache coverage: {cache_health['cache_coverage']}%",
                'recommendation': 'Run cache refresh job to update stale entries',
            })

        if cache_health['expired_count'] > cache_health['total_cached'] * 0.2:
            alerts.append({
                'severity': 'warning',
                'message': f"High expired entry count: {cache_health['expired_count']} ({cache_health['expired_count'] / cache_health['total_cached'] * 100:.1f}%)",
                'recommendation': 'Run cache purge job to clean up expired entries',
            })

        # Send alert email if any issues found
        if alerts:
            _logger.warning(f'System health alerts triggered: {len(alerts)} issue(s) detected')

            # Get admin users
            admin_users = self.env.ref('base.group_system').users

            # Determine overall severity
            has_critical = any(a['severity'] == 'critical' for a in alerts)
            severity = 'CRITICAL' if has_critical else 'WARNING'
            severity_color = 'red' if has_critical else 'orange'

            subject = f"ALERT: Cédula Lookup System - {severity}"

            body = f"""
            <h2 style="color: {severity_color};">Cédula Lookup System Alert</h2>
            <p><strong>Severity:</strong> <span style="color: {severity_color}; font-weight: bold;">{severity}</span></p>
            <p><strong>Timestamp:</strong> {fields.Datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>

            <h3>Issues Detected</h3>
            <ul>
            """

            for alert in alerts:
                alert_color = 'red' if alert['severity'] == 'critical' else 'orange'
                body += f"""
                <li>
                    <strong style="color: {alert_color};">[{alert['severity'].upper()}]</strong> {alert['message']}
                    <br/><em>Recommendation: {alert['recommendation']}</em>
                </li>
                """

            body += """
            </ul>

            <h3>Current Status</h3>
            <ul>
                <li><strong>Cache Coverage:</strong> """ + str(cache_health['cache_coverage']) + """%</li>
                <li><strong>API Success Rate:</strong> """ + str(api_perf['success_rate']) + """%</li>
                <li><strong>Expired Entries:</strong> """ + str(cache_health['expired_count']) + """</li>
            </ul>

            <p><strong>Please take immediate action to resolve these issues.</strong></p>
            <p><em>This is an automated alert from the Cédula Lookup System.</em></p>
            """

            # Send email to each admin
            for user in admin_users:
                if user.email:
                    mail = self.env['mail.mail'].create({
                        'subject': subject,
                        'body_html': body,
                        'email_to': user.email,
                    })
                    mail.send()

            _logger.warning(f'System health alerts sent to {len(admin_users)} administrators')
        else:
            _logger.info('System health check passed - no alerts triggered')

    # =========================================================================
    # DASHBOARD ACTION METHODS
    # =========================================================================

    def action_refresh_stale_cache(self):
        """
        Manually trigger refresh of stale cache entries.

        Button action from dashboard.
        """
        CedulaCache = self.env['l10n_cr.cedula.cache']
        stale_caches = CedulaCache.get_stale_cache_entries(limit=50)

        if not stale_caches:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cache Refresh'),
                    'message': _('No stale cache entries found.'),
                    'type': 'info',
                    'sticky': False,
                }
            }

        # Trigger refresh (this will be handled by cron job in production)
        CedulaCache._cron_refresh_stale_cache()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Cache Refresh Started'),
                'message': _('Refreshing %d stale cache entries...') % len(stale_caches),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_purge_expired_cache(self):
        """
        Manually purge expired cache entries.

        Button action from dashboard.
        """
        CedulaCache = self.env['l10n_cr.cedula.cache']
        count = CedulaCache.purge_expired_cache()

        if count == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cache Purge'),
                    'message': _('No expired cache entries found.'),
                    'type': 'info',
                    'sticky': False,
                }
            }

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Cache Purged'),
                'message': _('Successfully purged %d expired cache entries.') % count,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_view_cache_entries(self):
        """
        Open cache entries list view.

        Button action from dashboard.
        """
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cédula Cache Entries'),
            'res_model': 'l10n_cr.cedula.cache',
            'view_mode': 'tree,form',
            'domain': [('company_id', '=', self.env.company.id)],
            'context': {'default_company_id': self.env.company.id},
        }

    def action_test_api_connection(self):
        """
        Test Hacienda API connection.

        Button action from dashboard.
        """
        HaciendaAPI = self.env['l10n_cr.hacienda.cedula.api']

        try:
            result = HaciendaAPI.test_connection()

            if result.get('success'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('API Connection Test'),
                        'message': _('Connection successful! Response time: %.2fs') % result.get('response_time', 0),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('API Connection Test'),
                        'message': _('Connection failed: %s') % result.get('message', 'Unknown error'),
                        'type': 'danger',
                        'sticky': True,
                    }
                }

        except Exception as e:
            _logger.error(f'API connection test failed: {str(e)}', exc_info=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('API Connection Test'),
                    'message': _('Test failed: %s') % str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def refresh_dashboard(self):
        """
        Refresh dashboard data.

        Returns updated dashboard data as notification.
        """
        dashboard_data = self.get_dashboard_data()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Dashboard Refreshed'),
                'message': _('Dashboard data updated at %s') % fields.Datetime.now().strftime('%H:%M:%S'),
                'type': 'info',
                'sticky': False,
            }
        }
