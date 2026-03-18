#!/usr/bin/env python3
"""
Honeybadger Server - Receives Lynis and Trivy JSON reports via HTTP
"""

import json
import os
import yaml
import time
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComplianceCache:
    """In-memory cache for compliance tracking"""

    def __init__(self, config):
        """Initialize cache with config"""
        self.config = config
        self.data = {}  # { "YYYY-MM": { "hostname-username": {...} } }
        self.last_updated = None

    def rebuild(self):
        """Scan filesystem and rebuild compliance cache"""
        if not self.config.compliance_enabled:
            logger.info("Compliance not enabled, skipping cache rebuild")
            return

        logger.info("Rebuilding compliance cache...")
        self.data = {}
        storage_path = Path(self.config.storage_location)

        if not storage_path.exists():
            logger.warning(f"Storage location does not exist: {storage_path}")
            self.last_updated = datetime.now()
            return

        # Scan all audit period directories
        for period_dir in storage_path.iterdir():
            if not period_dir.is_dir():
                continue

            # Check if directory name matches YYYY-MM format
            if not (len(period_dir.name) == 7 and period_dir.name[4] == '-'):
                continue

            audit_period = period_dir.name
            self.data[audit_period] = {}

            # Scan all system directories within this period
            for system_dir in period_dir.iterdir():
                if not system_dir.is_dir():
                    continue

                # Parse directory name: hostname-username
                parts = system_dir.name.rsplit('-', 1)
                if len(parts) != 2:
                    continue

                hostname = parts[0]
                username = parts[1]

                # Check which reports exist
                reports = []
                upload_date = None
                for report_file in system_dir.glob('*.json'):
                    report_name = report_file.stem.replace('-report', '')
                    reports.append(report_name)
                    # Track latest file mtime as upload date
                    mtime = report_file.stat().st_mtime
                    file_date = datetime.fromtimestamp(mtime)
                    if upload_date is None or file_date > upload_date:
                        upload_date = file_date

                # Check completeness
                is_complete, missing = check_completeness(
                    reports,
                    self.config.required_reports_mandatory,
                    self.config.required_reports_one_of
                )

                # Extract OS type from neofetch if available
                os_type = 'unknown'
                neofetch_path = system_dir / 'neofetch-report.json'
                if neofetch_path.exists():
                    try:
                        with open(neofetch_path, 'r') as f:
                            neofetch_data = json.load(f)
                            os_type = neofetch_data.get('os', 'unknown')
                    except Exception as e:
                        logger.warning(f"Could not read OS from neofetch: {e}")

                # Store in cache
                key = f"{hostname}-{username}"
                self.data[audit_period][key] = {
                    'hostname': hostname,
                    'username': username,
                    'os_type': os_type,
                    'upload_date': upload_date,
                    'reports': reports,
                    'is_complete': is_complete,
                    'missing': missing
                }

        self.last_updated = datetime.now()
        total_systems = sum(len(period) for period in self.data.values())
        logger.info(f"Cache rebuilt: {len(self.data)} periods, {total_systems} systems")

    def update_system(self, audit_period, hostname, username, report_type, os_type='unknown'):
        """Update cache for a single system after new upload

        Args:
            audit_period: Audit period (YYYY-MM)
            hostname: Hostname
            username: Username
            report_type: Type of report just uploaded
            os_type: OS type (optional)
        """
        if not self.config.compliance_enabled:
            return

        # Ensure period exists in cache
        if audit_period not in self.data:
            self.data[audit_period] = {}

        key = f"{hostname}-{username}"

        # Get existing entry or create new one
        if key in self.data[audit_period]:
            entry = self.data[audit_period][key]
        else:
            entry = {
                'hostname': hostname,
                'username': username,
                'os_type': os_type,
                'upload_date': datetime.now(),
                'reports': [],
                'is_complete': False,
                'missing': []
            }

        # Update reports list
        if report_type not in entry['reports']:
            entry['reports'].append(report_type)

        # Update upload date
        entry['upload_date'] = datetime.now()

        # Update OS type if provided
        if os_type != 'unknown':
            entry['os_type'] = os_type

        # Recalculate completeness
        entry['is_complete'], entry['missing'] = check_completeness(
            entry['reports'],
            self.config.required_reports_mandatory,
            self.config.required_reports_one_of
        )

        # Store updated entry
        self.data[audit_period][key] = entry

        logger.debug(f"Cache updated: {audit_period}/{key} - complete: {entry['is_complete']}")

    def get_period_status(self, audit_period):
        """Get all systems for an audit period

        Args:
            audit_period: Audit period (YYYY-MM)

        Returns:
            dict: System data for the period
        """
        return self.data.get(audit_period, {})

    def get_all_periods(self):
        """Get list of all audit periods with data

        Returns:
            list: Sorted list of audit periods (newest first)
        """
        periods = sorted(self.data.keys(), reverse=True)
        return periods


def check_completeness(reports, required_mandatory, required_one_of):
    """
    Check if a report set is complete.

    Args:
        reports: list of report types present (e.g., ['neofetch', 'lynis', 'trivy'])
        required_mandatory: list of mandatory report types
        required_one_of: list of report types where at least one is required

    Returns:
        tuple: (is_complete: bool, missing: list)

    Examples:
        >>> check_completeness(['neofetch', 'lynis', 'trivy'], ['neofetch', 'lynis'], ['trivy', 'vulnix'])
        (True, [])
        >>> check_completeness(['neofetch', 'lynis'], ['neofetch', 'lynis'], ['trivy', 'vulnix'])
        (False, ['trivy or vulnix'])
    """
    missing = []

    # Check mandatory reports
    for report in required_mandatory:
        if report not in reports:
            missing.append(report)

    # Check one_of reports
    has_one = any(report in reports for report in required_one_of)
    if not has_one and required_one_of:
        missing.append(' or '.join(required_one_of))

    is_complete = len(missing) == 0
    return is_complete, missing


def get_audit_period(upload_date, audit_months):
    """
    Calculate which audit period an upload belongs to.

    Maps upload to the next audit month >= current month.
    If no audit month remains this year, use first audit month of next year.

    Args:
        upload_date: datetime object of when upload was received
        audit_months: list of integers (1-12) representing audit months

    Returns:
        str: Audit period in format "YYYY-MM"

    Examples:
        >>> get_audit_period(datetime(2026, 3, 15), [3, 9])
        '2026-03'
        >>> get_audit_period(datetime(2026, 4, 10), [3, 9])
        '2026-09'
        >>> get_audit_period(datetime(2026, 10, 5), [3, 9])
        '2027-03'
    """
    year = upload_date.year
    month = upload_date.month

    # Find next audit month >= current month this year
    future_months = [m for m in sorted(audit_months) if m >= month]

    if future_months:
        # Use first audit month >= current month this year
        target_month = min(future_months)
        return f"{year}-{target_month:02d}"
    else:
        # All audit months are in the past this year
        # Use first audit month of next year
        target_month = min(audit_months)
        return f"{year+1}-{target_month:02d}"


class Config:
    """Configuration loader for the server"""

    def __init__(self, config_file='config.yaml'):
        self.config_file = config_file
        self.load()

    def load(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                self.networkport = config.get('networkport', 7123)
                self.storage_location = config.get('storage_location', './reports')

                # Load compliance configuration
                compliance = config.get('compliance', {})
                self.compliance_enabled = compliance.get('enabled', False)
                self.audit_months = compliance.get('audit_months', [])

                # Load required reports configuration
                required_reports = compliance.get('required_reports', {})
                self.required_reports_mandatory = required_reports.get('mandatory', ['neofetch', 'lynis'])
                self.required_reports_one_of = required_reports.get('one_of', ['trivy', 'vulnix'])

                # Validate audit months
                if self.compliance_enabled:
                    if not self.audit_months:
                        raise ValueError("compliance.audit_months must be specified when compliance is enabled")
                    for month in self.audit_months:
                        if not isinstance(month, int) or month < 1 or month > 12:
                            raise ValueError(f"Invalid audit month '{month}'. Must be integer between 1 and 12")

                logger.info(f"Configuration loaded from {self.config_file}")
                logger.info(f"Network port: {self.networkport}")
                logger.info(f"Storage location: {self.storage_location}")
                logger.info(f"Compliance mode: {self.compliance_enabled}")
                if self.compliance_enabled:
                    logger.info(f"Audit months: {self.audit_months}")
                    logger.info(f"Required reports: {self.required_reports_mandatory} + one of {self.required_reports_one_of}")
        except FileNotFoundError:
            logger.error(f"Config file {self.config_file} not found")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file: {e}")
            raise
        except ValueError as e:
            logger.error(f"Configuration validation error: {e}")
            raise


class ReportHandler(BaseHTTPRequestHandler):
    """HTTP request handler for receiving reports"""

    config = None
    start_time = None
    compliance_cache = None

    def log_message(self, format, *args):
        """Override to use custom logger"""
        logger.info("%s - %s" % (self.address_string(), format % args))

    def validate_report_type(self, report_type):
        """Validate that the report type is supported"""
        valid_types = ['lynis', 'neofetch']
        if report_type.lower() not in valid_types:
            return False, f"Invalid report type '{report_type}'. Supported types: {', '.join(valid_types)}"
        return True, None

    def validate_report_structure(self, report_type, data):
        """Validate the structure of the report JSON based on type"""
        report_type_lower = report_type.lower()

        # Lynis validation
        if report_type_lower == 'lynis':
            if not isinstance(data, dict):
                return False, "Invalid Lynis report: must be a JSON object"
            # Check for common Lynis report fields
            if 'report_version' not in data and 'lynis_version' not in data:
                logger.warning("Lynis report may be invalid: missing 'report_version' or 'lynis_version' field")
            # Note: We log a warning but don't fail, to allow for different Lynis versions

        # Neofetch validation
        elif report_type_lower == 'neofetch':
            # Neofetch/system info should be a dict with basic system fields
            if not isinstance(data, dict):
                return False, "Invalid Neofetch report: must be a JSON object"
            # Basic validation - check if it has some system-related fields
            if not any(key in data for key in ['hostname', 'os', 'kernel', 'system']):
                logger.warning("Neofetch report may be invalid: missing common system info fields")

        return True, None

    def get_health_status(self):
        """Get health status information for monitoring"""
        storage_path = Path(self.config.storage_location)

        # Count reports
        total_reports = 0
        unique_hosts = set()
        report_counts = {'lynis': 0, 'neofetch': 0}

        if storage_path.exists():
            for item in storage_path.iterdir():
                if item.is_dir():
                    total_reports += 1
                    # Extract hostname from directory name
                    parts = item.name.rsplit('-', 1)
                    if len(parts) == 2:
                        host_user = parts[0]
                        host_parts = host_user.rsplit('-', 1)
                        if len(host_parts) == 2:
                            unique_hosts.add(host_parts[0])

                    # Count report types
                    if (item / 'lynis-report.json').exists():
                        report_counts['lynis'] += 1
                    if (item / 'neofetch-report.json').exists():
                        report_counts['neofetch'] += 1

        # Calculate uptime
        uptime_seconds = int(time.time() - self.start_time) if self.start_time else 0
        uptime_hours = uptime_seconds // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60

        return {
            'status': 'ok',
            'http_code': 200,
            'service': 'honeybadger-server',
            'timestamp': datetime.now().isoformat(),
            'uptime': {
                'seconds': uptime_seconds,
                'human_readable': f"{uptime_hours}h {uptime_minutes}m"
            },
            'statistics': {
                'total_report_directories': total_reports,
                'unique_hosts': len(unique_hosts),
                'reports_by_type': report_counts
            },
            'storage': {
                'location': str(storage_path),
                'accessible': storage_path.exists()
            }
        }

    def do_POST(self):
        """Handle POST requests with JSON report data"""
        try:
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "No content provided")
                return

            # Read the request body
            body = self.rfile.read(content_length)

            # Parse JSON data
            try:
                data = json.loads(body)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                self.send_error(400, f"Invalid JSON: {str(e)}")
                return

            # Get required parameters from headers or JSON data
            hostname = self.headers.get('X-Hostname') or data.get('hostname')
            username = self.headers.get('X-Username') or data.get('username')
            report_type = self.headers.get('X-Report-Type') or data.get('report_type', 'unknown')

            if not hostname or not username:
                self.send_error(400, "Missing required fields: hostname and username")
                return

            # Validate report type
            valid, error_msg = self.validate_report_type(report_type)
            if not valid:
                logger.error(f"Invalid report type: {error_msg}")
                self.send_error(400, error_msg)
                return

            # Validate report structure
            valid, error_msg = self.validate_report_structure(report_type, data)
            if not valid:
                logger.error(f"Invalid report structure: {error_msg}")
                self.send_error(400, error_msg)
                return

            # Extract OS type (will be used in compliance mode)
            os_type = self.headers.get('X-OS-Type', 'unknown')

            # Save the report
            saved_path, audit_period = self.save_report(hostname, username, report_type, data, os_type)

            # Update compliance cache if enabled
            if self.config.compliance_enabled and self.compliance_cache:
                self.compliance_cache.update_system(
                    audit_period, hostname, username, report_type.lower(), os_type
                )

            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {
                'status': 'success',
                'message': 'Report saved successfully',
                'path': str(saved_path)
            }

            # Add compliance-specific fields if enabled
            if self.config.compliance_enabled:
                response['audit_period'] = audit_period
                response['os_type'] = os_type

            self.wfile.write(json.dumps(response).encode())

            logger.info(f"Report saved: {saved_path}")

        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            self.send_error(500, f"Internal server error: {str(e)}")

    def save_report(self, hostname, username, report_type, data, os_type='unknown'):
        """Save report to disk with appropriate filename

        Args:
            hostname: System hostname
            username: User who performed scan
            report_type: Type of report (lynis, trivy, vulnix, neofetch)
            data: Report JSON data
            os_type: Operating system type (optional)

        Returns:
            tuple: (file_path, audit_period or None)
        """
        report_type_lower = report_type.lower()

        # Determine filename based on report type
        if report_type_lower == 'lynis':
            filename = 'lynis-report.json'
        elif report_type_lower == 'neofetch':
            filename = 'neofetch-report.json'
        else:
            filename = f'{report_type}-report.json'
            logger.warning(f"Unexpected report type '{report_type}', saving as '{filename}'")

        if self.config.compliance_enabled:
            # COMPLIANCE MODE: Use audit-period-based storage

            # Calculate audit period
            upload_date = datetime.now()
            audit_period = get_audit_period(upload_date, self.config.audit_months)

            # Create directory path: {audit-period}/{hostname-username}/
            dir_name = f"{hostname}-{username}"
            dir_path = Path(self.config.storage_location) / audit_period / dir_name

            # Create directory
            dir_path.mkdir(parents=True, exist_ok=True)

            file_path = dir_path / filename

            # Write JSON data to file
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

            return file_path, audit_period

        else:
            # LEGACY MODE: Use date-based storage

            # Get current date in yyyymmdd format
            date_str = datetime.now().strftime('%Y%m%d')

            # Create directory name: {hostname-username-YYYYMMDD}
            dir_name = f"{hostname}-{username}-{date_str}"
            dir_path = Path(self.config.storage_location) / dir_name

            # Create directory
            dir_path.mkdir(parents=True, exist_ok=True)

            file_path = dir_path / filename

            # Write JSON data to file
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

            return file_path, None

    def get_reports_status(self):
        """Scan reports directory and gather status information"""
        storage_path = Path(self.config.storage_location)

        if not storage_path.exists():
            return []

        reports = []

        # Scan all directories in storage location
        for item in storage_path.iterdir():
            if not item.is_dir():
                continue

            # Parse directory name: <hostname>-<username>-<yyyymmdd>
            parts = item.name.rsplit('-', 1)
            if len(parts) != 2:
                continue

            host_user = parts[0]
            date_str = parts[1]

            # Split host_user into hostname and username
            host_parts = host_user.rsplit('-', 1)
            if len(host_parts) != 2:
                hostname = host_user
                username = 'unknown'
            else:
                hostname = host_parts[0]
                username = host_parts[1]

            # Get the most recent file modification time in this directory
            files = list(item.glob('*.json'))
            if not files:
                continue

            latest_mtime = max(f.stat().st_mtime for f in files)
            last_update = datetime.fromtimestamp(latest_mtime)

            # Check which reports exist
            has_lynis = (item / 'lynis-report.json').exists()
            has_neofetch = (item / 'neofetch-report.json').exists()

            reports.append({
                'hostname': hostname,
                'username': username,
                'date': date_str,
                'last_update': last_update,
                'has_lynis': has_lynis,
                'has_neofetch': has_neofetch,
                'path': str(item)
            })

        # Sort by last update (most recent first)
        reports.sort(key=lambda x: x['last_update'], reverse=True)

        return reports

    def generate_compliance_dashboard_html(self, selected_period=None):
        """Generate compliance dashboard HTML"""

        if not self.compliance_cache:
            return "<html><body><h1>Error: Compliance cache not initialized</h1></body></html>"

        # Get all available periods
        all_periods = self.compliance_cache.get_all_periods()

        if not all_periods:
            return """<!DOCTYPE html>
<html><head><title>Honeybadger Compliance</title></head>
<body style="font-family: sans-serif; padding: 40px;">
<h1>No compliance data yet</h1>
<p>No reports have been uploaded in compliance mode.</p>
</body></html>"""

        # Default to most recent period if none selected
        if not selected_period:
            selected_period = all_periods[0]

        # Get systems for selected period
        systems = self.compliance_cache.get_period_status(selected_period)

        # Calculate summary statistics
        total_systems = len(systems)
        complete_systems = sum(1 for s in systems.values() if s['is_complete'])
        incomplete_systems = total_systems - complete_systems
        complete_pct = (complete_systems / total_systems * 100) if total_systems > 0 else 0

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Honeybadger Compliance Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white;
                      padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; margin-bottom: 10px; font-size: 28px; }}
        .subtitle {{ color: #666; margin-bottom: 20px; font-size: 14px; }}

        .period-selector {{ margin: 20px 0; display: flex; gap: 10px; align-items: center; }}
        .period-selector label {{ font-weight: 600; color: #333; }}
        .period-selector select {{ padding: 8px 12px; border: 1px solid #ddd;
                                   border-radius: 4px; font-size: 14px; cursor: pointer; }}

        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                 gap: 20px; margin: 20px 0; }}
        .stat-card {{ padding: 20px; background: #f8f9fa; border-radius: 6px;
                      border-left: 4px solid #007bff; }}
        .stat-number {{ font-size: 32px; font-weight: bold; color: #007bff; }}
        .stat-label {{ color: #666; font-size: 14px; margin-top: 5px; }}

        .filter-bar {{ margin: 20px 0; display: flex; gap: 10px; align-items: center; }}
        .filter-bar label {{ font-weight: 600; color: #333; }}
        .filter-bar select {{ padding: 8px 12px; border: 1px solid #ddd;
                             border-radius: 4px; font-size: 14px; }}

        .table-container {{ margin-top: 20px; border: 1px solid #dee2e6;
                           border-radius: 6px; overflow: auto; max-height: 600px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        thead {{ background: #f8f9fa; position: sticky; top: 0; z-index: 10; }}
        th {{ padding: 12px; text-align: left; font-weight: 600; color: #333;
              border-bottom: 2px solid #dee2e6; background: #f8f9fa; }}
        td {{ padding: 12px; border-bottom: 1px solid #dee2e6; }}
        tbody tr:hover {{ background: #f8f9fa; }}

        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px;
                 font-size: 12px; font-weight: 500; margin-right: 4px; }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; }}
        a.badge {{ text-decoration: none; transition: opacity 0.2s; }}
        a.badge:hover {{ opacity: 0.8; }}

        .status-complete {{ color: #28a745; font-weight: 600; }}
        .status-incomplete {{ color: #dc3545; font-weight: 600; }}
        .status-icon {{ font-size: 16px; margin-right: 4px; }}

        .empty-state {{ text-align: center; padding: 60px 20px; color: #666; }}
    </style>
    <script>
        function switchPeriod() {{
            const select = document.getElementById('periodSelect');
            const period = select.value;
            window.location.href = '/?period=' + period;
        }}

        function filterTable() {{
            const filterSelect = document.getElementById('filterSelect');
            const filterValue = filterSelect.value;
            const table = document.getElementById('complianceTable');
            const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

            for (let i = 0; i < rows.length; i++) {{
                const row = rows[i];
                const statusCell = row.cells[5].textContent.toLowerCase();

                if (filterValue === 'all') {{
                    row.style.display = '';
                }} else if (filterValue === 'complete' && statusCell.includes('complete')) {{
                    row.style.display = '';
                }} else if (filterValue === 'incomplete' && statusCell.includes('incomplete')) {{
                    row.style.display = '';
                }} else {{
                    row.style.display = 'none';
                }}
            }}
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>🦡 Honeybadger Compliance Dashboard</h1>
        <div class="subtitle">Security Audit Compliance Tracking</div>

        <div class="period-selector">
            <label for="periodSelect">Audit Period:</label>
            <select id="periodSelect" onchange="switchPeriod()">"""

        # Add period options
        for period in all_periods:
            selected = 'selected' if period == selected_period else ''
            html += f'<option value="{period}" {selected}>{period}</option>'

        html += f"""
            </select>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_systems}</div>
                <div class="stat-label">Total Systems</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{complete_systems}</div>
                <div class="stat-label">Complete</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{incomplete_systems}</div>
                <div class="stat-label">Incomplete</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{complete_pct:.0f}%</div>
                <div class="stat-label">Compliance Rate</div>
            </div>
        </div>

        <div class="filter-bar">
            <label for="filterSelect">Show:</label>
            <select id="filterSelect" onchange="filterTable()">
                <option value="all">All Systems</option>
                <option value="complete">Complete Only</option>
                <option value="incomplete">Incomplete Only</option>
            </select>
        </div>

        <div class="table-container">
            <table id="complianceTable">
                <thead>
                    <tr>
                        <th>Hostname</th>
                        <th>Username</th>
                        <th>OS Type</th>
                        <th>Upload Date</th>
                        <th>Reports</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>"""

        # Add table rows
        if not systems:
            html += """
                    <tr><td colspan="6" class="empty-state">No systems in this audit period</td></tr>"""
        else:
            for key in sorted(systems.keys()):
                system = systems[key]
                hostname = system['hostname']
                username = system['username']
                os_type = system['os_type']
                upload_date = system['upload_date'].strftime('%Y-%m-%d') if system['upload_date'] else 'N/A'
                reports = system['reports']
                is_complete = system['is_complete']
                missing = system['missing']

                # Build report badges
                badges = []
                report_map = {'neofetch': 'N', 'lynis': 'L', 'trivy': 'T', 'vulnix': 'V'}
                for report_type, badge_text in report_map.items():
                    if report_type in reports:
                        download_url = f"/reports/{selected_period}/{hostname}-{username}/{report_type}-report.json"
                        badges.append(f'<a href="{download_url}" class="badge badge-success" target="_blank">{badge_text}</a>')

                badges_html = ''.join(badges) if badges else '<span class="badge badge-danger">None</span>'

                # Status column
                if is_complete:
                    status_html = '<span class="status-complete"><span class="status-icon">✓</span>Complete</span>'
                else:
                    missing_text = ', '.join(missing)
                    status_html = f'<span class="status-incomplete"><span class="status-icon">⚠</span>Incomplete<br><small>Missing: {missing_text}</small></span>'

                html += f"""
                    <tr>
                        <td><strong>{hostname}</strong></td>
                        <td>{username}</td>
                        <td>{os_type}</td>
                        <td>{upload_date}</td>
                        <td>{badges_html}</td>
                        <td>{status_html}</td>
                    </tr>"""

        html += """
                </tbody>
            </table>
        </div>

        <div style="margin-top: 20px; text-align: center; color: #666; font-size: 12px;">
            Legend: N=Neofetch, L=Lynis, T=Trivy, V=Vulnix
        </div>
    </div>
</body>
</html>"""

        return html

    def generate_status_html(self):
        """Generate HTML status page"""
        reports = self.get_reports_status()

        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Honeybadger Server - Status</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }

        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            flex: 1;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }

        .stat-number {
            font-size: 32px;
            font-weight: bold;
            color: #007bff;
        }

        .stat-label {
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }

        .table-container {
            max-height: 600px;
            overflow-y: auto;
            margin-top: 20px;
            border: 1px solid #dee2e6;
            border-radius: 6px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        thead {
            background: #f8f9fa;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        th {
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #dee2e6;
            background: #f8f9fa;
        }

        td {
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }

        tbody tr:hover {
            background: #f8f9fa;
        }

        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }

        .badge-success {
            background: #d4edda;
            color: #155724;
        }

        .badge-secondary {
            background: #e2e3e5;
            color: #383d41;
        }

        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }

        a.badge {
            text-decoration: none;
            transition: opacity 0.2s;
        }

        a.badge:hover {
            opacity: 0.8;
            text-decoration: underline;
        }

        .status-ok {
            color: #28a745;
            font-weight: 600;
        }

        .status-nok {
            color: #dc3545;
            font-weight: 600;
        }

        .time-recent {
            color: #28a745;
            font-weight: 500;
        }

        .time-old {
            color: #dc3545;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }

        .empty-state-icon {
            font-size: 48px;
            margin-bottom: 20px;
        }

        .refresh-info {
            text-align: right;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }

        .filter-container {
            margin: 20px 0;
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .filter-input {
            flex: 1;
            padding: 10px 15px;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            font-size: 14px;
            font-family: inherit;
        }

        .filter-input:focus {
            outline: none;
            border-color: #007bff;
            box-shadow: 0 0 0 3px rgba(0,123,255,0.1);
        }

        .filter-label {
            color: #666;
            font-size: 14px;
            font-weight: 500;
        }

        .no-results {
            text-align: center;
            padding: 40px 20px;
            color: #666;
        }
    </style>
    <script>
        function filterTable() {
            const input = document.getElementById('searchInput');
            const filter = input.value.toLowerCase();
            const table = document.getElementById('reportsTable');
            const tbody = table.getElementsByTagName('tbody')[0];
            const rows = tbody.getElementsByTagName('tr');
            let visibleCount = 0;

            for (let i = 0; i < rows.length; i++) {
                const row = rows[i];
                const hostname = row.cells[0].textContent.toLowerCase();
                const username = row.cells[1].textContent.toLowerCase();
                const date = row.cells[2].textContent.toLowerCase();

                if (hostname.includes(filter) || username.includes(filter) || date.includes(filter)) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            }

            // Show/hide no results message
            const noResults = document.getElementById('noResults');
            if (visibleCount === 0 && filter !== '') {
                noResults.style.display = 'block';
            } else {
                noResults.style.display = 'none';
            }
        }

        setTimeout(function() {
            location.reload();
        }, 30000);
    </script>
</head>
<body>
    <div class="container">
        <h1>Honeybadger Server</h1>
        <div class="subtitle">Security Reports Dashboard</div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">""" + str(len(set((r['hostname'], r['username']) for r in reports))) + """</div>
                <div class="stat-label">Unique host-user combinations</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">""" + str(sum(1 for r in reports if r['has_lynis'])) + """</div>
                <div class="stat-label">Lynis reports</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">""" + str(sum(1 for r in reports if r['has_neofetch'])) + """</div>
                <div class="stat-label">Neofetch reports</div>
            </div>
        </div>
"""

        if not reports:
            html += """
        <div class="empty-state">
            <div class="empty-state-icon">📊</div>
            <h2>No reports found</h2>
            <p>No security reports have been received yet.</p>
        </div>
"""
        else:
            html += """
        <div class="filter-container">
            <span class="filter-label">Filter:</span>
            <input type="text" id="searchInput" class="filter-input" placeholder="Search by hostname, username, or date..." onkeyup="filterTable()">
        </div>

        <div class="table-container">
            <table id="reportsTable">
                <thead>
                    <tr>
                        <th>Hostname</th>
                        <th>Username</th>
                        <th>Report Date</th>
                        <th>Last Update</th>
                        <th>Reports</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""

            now = datetime.now()
            for report in reports:
                # Determine status: OK if both neofetch and lynis are present
                has_valid_combination = report['has_neofetch'] and report['has_lynis']

                status_text = 'OK' if has_valid_combination else 'NOK'
                status_class = 'status-ok' if has_valid_combination else 'status-nok'

                # Green if valid combination, red otherwise
                time_diff = now - report['last_update']
                if has_valid_combination and time_diff.days < 1:
                    time_class = 'time-recent'  # Green if valid and recent
                elif not has_valid_combination:
                    time_class = 'time-old'  # Red if invalid combination
                else:
                    time_class = ''  # Default color otherwise

                last_update_str = report['last_update'].strftime('%Y-%m-%d %H:%M:%S')

                # Build reports badges with links
                dir_name = f"{report['hostname']}-{report['username']}-{report['date']}"
                reports_badges = []
                if report['has_lynis']:
                    lynis_url = f"/reports/{dir_name}/lynis-report.json"
                    reports_badges.append(f'<a href="{lynis_url}" class="badge badge-success" target="_blank">Lynis</a>')
                if report['has_neofetch']:
                    neofetch_url = f"/reports/{dir_name}/neofetch-report.json"
                    reports_badges.append(f'<a href="{neofetch_url}" class="badge badge-success" target="_blank">Neofetch</a>')
                else:
                    # Show red badge if neofetch is missing (it's required)
                    reports_badges.append('<span class="badge badge-danger">Missing Neofetch</span>')
                if not any([report['has_lynis'], report['has_neofetch']]):
                    reports_badges = ['<span class="badge badge-secondary">None</span>']

                html += f"""
                <tr>
                    <td><strong>{report['hostname']}</strong></td>
                    <td>{report['username']}</td>
                    <td>{report['date']}</td>
                    <td class="{time_class}">{last_update_str}</td>
                    <td>{' '.join(reports_badges)}</td>
                    <td><span class="{status_class}">{status_text}</span></td>
                </tr>
"""

            html += """
                </tbody>
            </table>
        </div>

        <div id="noResults" class="no-results" style="display: none;">
            <p>No reports match your search criteria.</p>
        </div>
"""

        html += """
        <div class="refresh-info">
            Page automatically refreshes every 30 seconds
        </div>
    </div>
</body>
</html>
"""
        return html

    def do_GET(self):
        """Handle GET requests"""
        from urllib.parse import urlparse, parse_qs

        # Parse URL and query parameters
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        if path == '/' or path == '/status':
            # Dashboard page - check compliance mode
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()

            if self.config.compliance_enabled:
                # Compliance dashboard
                selected_period = query_params.get('period', [None])[0]
                html = self.generate_compliance_dashboard_html(selected_period)
            else:
                # Legacy dashboard
                html = self.generate_status_html()

            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/health':
            # Health check with monitoring information
            try:
                health_data = self.get_health_status()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(health_data, indent=2).encode())
            except Exception as e:
                logger.error(f"Error generating health status: {e}", exc_info=True)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = {
                    'status': 'error',
                    'http_code': 500,
                    'service': 'honeybadger-server',
                    'error': str(e)
                }
                self.wfile.write(json.dumps(error_response).encode())
        elif self.path.startswith('/reports/'):
            # Serve report JSON files
            try:
                # Remove /reports/ prefix and decode URL
                file_path = unquote(self.path[9:])  # Remove '/reports/'
                full_path = Path(self.config.storage_location) / file_path

                # Security check: ensure path is within storage location
                full_path = full_path.resolve()
                storage_path = Path(self.config.storage_location).resolve()

                if not str(full_path).startswith(str(storage_path)):
                    self.send_error(403, "Access denied")
                    return

                # Check if file exists and is a file
                if not full_path.exists() or not full_path.is_file():
                    self.send_error(404, "Report not found")
                    return

                # Read and serve the JSON file
                with open(full_path, 'r') as f:
                    content = f.read()

                # Create download filename: <folder>-<report>.json
                # e.g., testserver01-testuser-20260316-lynis-report.json
                folder_name = full_path.parent.name
                report_name = full_path.name
                download_filename = f"{folder_name}-{report_name}"

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Disposition', f'attachment; filename="{download_filename}"')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))

            except Exception as e:
                logger.error(f"Error serving report: {e}", exc_info=True)
                self.send_error(500, f"Internal server error: {str(e)}")
        else:
            self.send_error(404, "Not found")


def run_server(config):
    """Start the HTTP server"""
    # Set config and start time on handler class
    ReportHandler.config = config
    ReportHandler.start_time = time.time()

    # Create storage directory if it doesn't exist
    Path(config.storage_location).mkdir(parents=True, exist_ok=True)

    # Initialize and build compliance cache
    cache = ComplianceCache(config)
    cache.rebuild()
    ReportHandler.compliance_cache = cache

    # Create and start server
    server_address = ('', config.networkport)
    httpd = HTTPServer(server_address, ReportHandler)

    logger.info(f"Honeybadger Server starting on port {config.networkport}")
    logger.info(f"Storing reports in: {config.storage_location}")
    logger.info(f"Health check available at: http://localhost:{config.networkport}/health")
    logger.info("Press Ctrl+C to stop the server")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        httpd.shutdown()


def main():
    """Main entry point"""
    try:
        # Load configuration
        config = Config()

        # Start server
        run_server(config)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
