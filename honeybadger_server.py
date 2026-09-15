#!/usr/bin/env python3
"""
Honeybadger Server - Receives Lynis and Trivy JSON reports via HTTP
"""

VERSION = "1.1.0"

import json
import os
import csv
import re
import yaml
import time
import tarfile
import io
import argparse
import secrets
import base64
from datetime import datetime, date, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
from html import escape as html_escape
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for authentication credentials (loaded at startup)
VALID_TOKENS = []
DASHBOARD_PASSWORD = ""


def load_token_file(token_file_path):
    """Load valid API tokens from YAML file

    Args:
        token_file_path: Path to YAML file containing tokens

    Returns:
        list: List of valid token strings

    Raises:
        FileNotFoundError: If token file doesn't exist
        yaml.YAMLError: If YAML is invalid
        ValueError: If token file has wrong structure or is empty
    """
    token_path = Path(token_file_path)

    # Check file exists
    if not token_path.exists():
        raise FileNotFoundError(f"Token file not found: {token_file_path}")

    # Check file is readable
    if not os.access(token_path, os.R_OK):
        raise PermissionError(f"Cannot read token file: {token_file_path}")

    # Read and parse YAML
    with open(token_path, 'r') as f:
        data = yaml.safe_load(f)

    # Validate structure
    if not isinstance(data, dict):
        raise ValueError(f"Token file must be a YAML object with 'tokens' key")

    if 'tokens' not in data:
        raise ValueError(f"Token file missing 'tokens' key")

    tokens = data['tokens']

    if not isinstance(tokens, list):
        raise ValueError(f"Token file 'tokens' must be a list")

    if len(tokens) == 0:
        raise ValueError(f"Token file contains no tokens")

    # Trim whitespace and validate tokens
    cleaned_tokens = []
    for token in tokens:
        if not isinstance(token, str):
            raise ValueError(f"All tokens must be strings")

        cleaned = token.strip()
        if not cleaned:
            raise ValueError(f"Token file contains empty string token")

        cleaned_tokens.append(cleaned)

    return cleaned_tokens


def load_password_file(password_file_path):
    """Load dashboard password from plaintext file

    Args:
        password_file_path: Path to plaintext file containing password

    Returns:
        str: Dashboard password (trimmed)

    Raises:
        FileNotFoundError: If password file doesn't exist
        ValueError: If password file is empty
    """
    password_path = Path(password_file_path)

    # Check file exists
    if not password_path.exists():
        raise FileNotFoundError(f"Dashboard password file not found: {password_file_path}")

    # Check file is readable
    if not os.access(password_path, os.R_OK):
        raise PermissionError(f"Cannot read dashboard password file: {password_file_path}")

    # Read file content
    with open(password_path, 'r') as f:
        content = f.read()

    # Split into lines and get first line
    lines = content.splitlines()

    if not lines:
        raise ValueError(f"Dashboard password file is empty")

    # Get first line and trim whitespace
    password = lines[0].strip()

    if not password:
        raise ValueError(f"Dashboard password file is empty (contains only whitespace)")

    # Warn if multiple lines
    if len(lines) > 1:
        logger.warning(f"Dashboard password file contains multiple lines, using first line only")

    return password


class ComplianceCache:
    """In-memory cache for compliance tracking"""

    def __init__(self, config):
        """Initialize cache with config"""
        self.config = config
        self.data = {}  # { "YYYY-MM": { "hostname-username": {...} } }
        self.submissions = []  # one entry per submission, never collapsed
        self.last_updated = None

    def _scan_submissions(self, storage_path):
        """Read every submission record into a flat, uncollapsed list.

        Three trees are read. Records written under a hardware serial and
        records that could not be matched both carry a `submission.json`.
        The period directories are the layout used before submissions were
        keyed on serial: they are read as archive records without a serial, so
        that switching layout does not empty a round that is already running.
        """
        for source, base in (('submissions', storage_path / 'submissions'),
                             ('unmatched', storage_path / 'unmatched')):
            if not base.is_dir():
                continue
            for key_dir in base.iterdir():
                if not key_dir.is_dir():
                    continue
                for record_dir in key_dir.iterdir():
                    record = self._read_record(record_dir, source)
                    if record:
                        self.submissions.append(record)

        for period_dir in storage_path.iterdir():
            if not period_dir.is_dir() or not is_audit_period_dirname(period_dir.name):
                continue
            for system_dir in period_dir.iterdir():
                if not system_dir.is_dir():
                    continue
                self.submissions.append(self._read_archive_record(system_dir, period_dir.name))

    def _read_record(self, record_dir, source):
        """Load one submission record written under the serial-keyed layout."""
        meta_path = record_dir / 'submission.json'
        if not meta_path.is_file():
            return None
        try:
            with open(meta_path) as handle:
                metadata = json.load(handle)
        except Exception as e:
            logger.warning(f"Could not read {meta_path}: {e}")
            return None

        metadata['source'] = source
        metadata['record_dir'] = str(record_dir)
        try:
            metadata['submitted_at_dt'] = datetime.fromisoformat(metadata['submitted_at'])
        except Exception:
            metadata['submitted_at_dt'] = datetime.fromtimestamp(record_dir.stat().st_mtime)
        return metadata

    def _read_archive_record(self, system_dir, audit_period):
        """Describe a pre-serial directory as a submission without an asset.

        These records carry no hardware serial, so they cannot be attributed to
        a register entry. They are kept visible rather than dropped: the round
        they belong to is closed history, and its evidence is the stored tar.
        """
        reports = []
        newest = None
        for report_file in system_dir.glob('*.json'):
            name = report_file.stem.replace('-report', '')
            if name != 'submission':
                reports.append(name)
            stamp = datetime.fromtimestamp(report_file.stat().st_mtime)
            newest = stamp if newest is None or stamp > newest else newest
        for tar_file in system_dir.glob('*.tar.gz'):
            stamp = datetime.fromtimestamp(tar_file.stat().st_mtime)
            newest = stamp if newest is None or stamp > newest else newest

        hostname, _, username = system_dir.name.rpartition('-')
        return {
            'schema_version': 0,
            'source': 'archive',
            'record_dir': str(system_dir),
            'submitted_at': (newest or datetime.now()).isoformat(),
            'submitted_at_dt': newest or datetime.now(),
            'audit_period': audit_period,
            'timeliness': None,
            'serial': None,
            'hostname': hostname or system_dir.name,
            'username': username,
            'os_type': self._archive_os_type(system_dir),
            'asset_id': None,
            'owner': None,
            'class': None,
            'unmatched_reason': 'no_serial',
            'evidence_predates_owner': False,
            'reports': sorted(set(reports)),
            'evidence': None,
        }

    @staticmethod
    def _archive_os_type(system_dir):
        fastfetch = system_dir / 'fastfetch-report.json'
        if not fastfetch.is_file():
            return 'unknown'
        try:
            with open(fastfetch) as handle:
                return json.load(handle).get('os', 'unknown')
        except Exception:
            return 'unknown'

    def submissions_in_period(self, audit_period):
        """Every submission belonging to a round, uncollapsed."""
        return [s for s in self.submissions if s.get('audit_period') == audit_period]

    def latest_by_asset(self):
        """The most recent submission per asset_id, across all rounds."""
        latest = {}
        for record in self.submissions:
            asset_id = record.get('asset_id')
            if not asset_id:
                continue
            current = latest.get(asset_id)
            if current is None or record['submitted_at_dt'] > current['submitted_at_dt']:
                latest[asset_id] = record
        return latest

    def unmatched(self, audit_period=None):
        """Submissions that could not be attributed, newest first."""
        records = [s for s in self.submissions if s.get('unmatched_reason')]
        if audit_period:
            records = [s for s in records if s.get('audit_period') == audit_period]
        return sorted(records, key=lambda r: r['submitted_at_dt'], reverse=True)

    def rebuild(self):
        """Scan filesystem and rebuild compliance cache"""
        if not self.config.compliance_enabled:
            logger.info("Compliance not enabled, skipping cache rebuild")
            return

        logger.info("Rebuilding compliance cache...")
        self.data = {}
        self.submissions = []
        storage_path = Path(self.config.storage_location)

        if not storage_path.exists():
            logger.warning(f"Storage location does not exist: {storage_path}")
            self.last_updated = datetime.now()
            return

        self._scan_submissions(storage_path)

        # Scan all audit period directories
        for period_dir in storage_path.iterdir():
            if not period_dir.is_dir():
                continue

            # Check if directory name matches YYYY-MM format
            if not is_audit_period_dirname(period_dir.name):
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

                # Scan for JSON report files
                for report_file in system_dir.glob('*.json'):
                    report_name = report_file.stem.replace('-report', '')
                    reports.append(report_name)
                    # Track latest file mtime as upload date
                    mtime = report_file.stat().st_mtime
                    file_date = datetime.fromtimestamp(mtime)
                    if upload_date is None or file_date > upload_date:
                        upload_date = file_date

                # Check for tar.gz files
                tar_files = list(system_dir.glob('*.tar.gz'))
                if tar_files:
                    reports.append('tar')
                    # Update upload date with tar file mtime if newer
                    for tar_file in tar_files:
                        mtime = tar_file.stat().st_mtime
                        file_date = datetime.fromtimestamp(mtime)
                        if upload_date is None or file_date > upload_date:
                            upload_date = file_date

                # Check completeness
                is_complete, missing = check_completeness(
                    reports,
                    self.config.required_reports_mandatory,
                    self.config.required_reports_one_of
                )

                # Extract OS type from fastfetch if available
                os_type = 'unknown'
                fastfetch_path = system_dir / 'fastfetch-report.json'
                if fastfetch_path.exists():
                    try:
                        with open(fastfetch_path, 'r') as f:
                            fastfetch_data = json.load(f)
                            os_type = fastfetch_data.get('os', 'unknown')
                    except Exception as e:
                        logger.warning(f"Could not read OS from fastfetch: {e}")

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
        reports: list of report types present (e.g., ['fastfetch', 'lynis', 'trivy'])
        required_mandatory: list of mandatory report types
        required_one_of: list of report types where at least one is required

    Returns:
        tuple: (is_complete: bool, missing: list)

    Examples:
        >>> check_completeness(['fastfetch', 'lynis', 'trivy'], ['fastfetch', 'lynis'], ['trivy', 'vulnix'])
        (True, [])
        >>> check_completeness(['fastfetch', 'lynis'], ['fastfetch', 'lynis'], ['trivy', 'vulnix'])
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


def is_audit_period_dirname(name):
    """Check whether a directory name has the YYYY-MM audit period shape

    Args:
        name: Directory name

    Returns:
        bool: True if the name is an audit period directory
    """
    return len(name) == 7 and name[4] == '-'


def get_audit_period(upload_date, audit_months):
    """
    Determine which audit round a submission belongs to.

    A round opens in its audit month and stays open until the next one begins,
    so a submission belongs to the most recent audit month at or before its
    date. Scanning a fleet takes weeks, and a round that ran into the following
    month must keep its late submissions rather than filing them forward into a
    round that has not started.

    Args:
        upload_date: datetime or date of when the submission arrived
        audit_months: list of integers (1-12) representing audit months

    Returns:
        str: Audit period in format "YYYY-MM"

    Examples:
        >>> get_audit_period(datetime(2026, 9, 15), [3, 9])
        '2026-09'
        >>> get_audit_period(datetime(2026, 10, 2), [3, 9])
        '2026-09'
        >>> get_audit_period(datetime(2026, 4, 10), [3, 9])
        '2026-03'
        >>> get_audit_period(datetime(2026, 2, 10), [3, 9])
        '2025-09'
        >>> get_audit_period(datetime(2026, 3, 1), [3, 9])
        '2026-03'
    """
    year = upload_date.year
    month = upload_date.month

    # The most recent audit month at or before this one, in this year.
    past_months = [m for m in sorted(audit_months) if m <= month]

    if past_months:
        return f"{year}-{max(past_months):02d}"

    # Before the first audit month of the year: the last round of the year before.
    return f"{year - 1}-{max(audit_months):02d}"


def parse_audit_period(period):
    """Return the first day of an audit period given as 'YYYY-MM'.

    Examples:
        >>> parse_audit_period('2026-09')
        datetime.date(2026, 9, 1)
    """
    year, month = period.split('-')
    return date(int(year), int(month), 1)


def next_audit_period(period, audit_months):
    """The round that follows the given one.

    Examples:
        >>> next_audit_period('2026-03', [3, 9])
        '2026-09'
        >>> next_audit_period('2026-09', [3, 9])
        '2027-03'
    """
    start = parse_audit_period(period)
    later = [m for m in sorted(audit_months) if m > start.month]
    if later:
        return f"{start.year}-{min(later):02d}"
    return f"{start.year + 1}-{min(audit_months):02d}"


def get_round_windows(period, audit_months, grace_weeks):
    """Return (scan_start, scan_end, coverage_end) for an audit round.

    A round has two windows, and conflating them is what made submissions file
    themselves into rounds that had not begun:

      scan window      the audit month plus the grace period. The work happens
                       here, and this window decides which assets belong to the
                       round and whether a submission is on time.
      coverage window  runs until the next round opens. This is the period the
                       round makes a statement about.

    Examples:
        >>> get_round_windows('2026-09', [3, 9], 4)
        (datetime.date(2026, 9, 1), datetime.date(2026, 10, 29), datetime.date(2027, 2, 28))
        >>> get_round_windows('2026-03', [3, 9], 0)
        (datetime.date(2026, 3, 1), datetime.date(2026, 4, 1), datetime.date(2026, 8, 31))
    """
    scan_start = parse_audit_period(period)
    following = parse_audit_period(next_audit_period(period, audit_months))

    # End of the audit month itself, then the grace period on top.
    if scan_start.month == 12:
        month_end = date(scan_start.year + 1, 1, 1)
    else:
        month_end = date(scan_start.year, scan_start.month + 1, 1)
    scan_end = month_end + timedelta(weeks=grace_weeks)

    coverage_end = following - timedelta(days=1)
    return scan_start, min(scan_end, coverage_end), coverage_end


def classify_submission(submitted_at, audit_months, grace_weeks):
    """Return (period, 'on_time'|'late') for a submission.

    Late submissions still count toward their round. The distinction is kept
    because "this asset was scanned three weeks after the deadline" is an
    auditable fact, not a rounding error.

    Examples:
        >>> classify_submission(datetime(2026, 9, 15), [3, 9], 4)
        ('2026-09', 'on_time')
        >>> classify_submission(datetime(2026, 10, 2), [3, 9], 4)
        ('2026-09', 'on_time')
        >>> classify_submission(datetime(2026, 12, 1), [3, 9], 4)
        ('2026-09', 'late')
        >>> classify_submission(datetime(2026, 4, 10), [3, 9], 0)
        ('2026-03', 'late')
    """
    period = get_audit_period(submitted_at, audit_months)
    _, scan_end, _ = get_round_windows(period, audit_months, grace_weeks)

    moment = submitted_at.date() if isinstance(submitted_at, datetime) else submitted_at
    return period, ('on_time' if moment <= scan_end else 'late')


# Values a client writes when it could not read a serial. They look like data
# but identify nothing, so they must never be used as a lookup key.
SERIAL_PLACEHOLDERS = {
    'not available',
    'not available (vm or unknown hardware)',
    'to be filled by o.e.m.',
    'to be filled',
    'default string',
    'not specified',
    'system serial number',
    'none',
    'unknown',
}

VALID_ASSET_CLASSES = {'linux', 'macos', 'windows'}
VALID_ASSET_STATUSES = {'active', 'retired'}

# Where each recognised report type is written inside a submission record.
REPORT_FILENAMES = {
    'fastfetch': 'fastfetch-report.json',
    'lynis': 'lynis-report.json',
}

# What a complete submission requires, named after the requirement rather than
# the tool that satisfies it. Naming a requirement after a tool is what broke
# the previous model: the client moved from neofetch to fastfetch and the
# requirement went with it, and Windows arrives with a different hardening tool
# again. Requirements are stable; the tools behind them are not.
REQUIREMENT_SATISFIED_BY = {
    'linux': {'sysinfo': ('fastfetch',), 'hardening': ('lynis',)},
    'macos': {'sysinfo': ('fastfetch',), 'hardening': ('lynis',)},
    'windows': {'sysinfo': ('fastfetch',), 'hardening': ('hardeningkitty',)},
}

# Classes whose client cannot submit yet. Their assets are reported as manual
# rather than incomplete: a permanent red row for a reason the owner cannot act
# on is the fastest way to teach people to ignore a dashboard. See bean
# wtoorren-cikq.
MANUAL_CLASSES = {'windows'}


def owner_to_slug(owner):
    """Render an owner name the way the register's proof_file column does.

    First name and surname, lowercased, with Dutch name infixes dropped - the
    convention the compliance sheet already uses, so a downloaded archive can
    go straight into the audit folder under the name the sheet expects.

    Examples:
        >>> owner_to_slug('Wouter van der Toorren')
        'wouter.toorren'
        >>> owner_to_slug('Richard van Os')
        'richard.os'
        >>> owner_to_slug('Pim Snel')
        'pim.snel'
        >>> owner_to_slug('Madonna')
        'madonna'
        >>> owner_to_slug('')
        ''
    """
    infixes = {'van', 'de', 'der', 'den', 'het', 'ten', 'ter', 'te', 'op', 'aan'}
    parts = [re.sub(r'[^a-z0-9]', '', p.lower()) for p in (owner or '').split()]
    parts = [p for p in parts if p]
    significant = [p for p in parts if p not in infixes] or parts
    if not significant:
        return ''
    if len(significant) == 1:
        return significant[0]
    return f"{significant[0]}.{significant[-1]}"


def requirements_for_class(asset_class, overrides=None):
    """Requirements for a platform class, with config taking precedence."""
    table = dict(REQUIREMENT_SATISFIED_BY)
    for name, mapping in (overrides or {}).items():
        table[name] = {req: tuple(accepted) for req, accepted in mapping.items()}
    return table.get(asset_class, table.get('linux'))


def evaluate_completeness(asset_class, reports, overrides=None):
    """Return (is_complete, missing) for a set of arrived report types.

    Examples:
        >>> evaluate_completeness('linux', ['fastfetch', 'lynis'])
        (True, [])
        >>> evaluate_completeness('linux', ['fastfetch'])
        (False, ['hardening'])
        >>> evaluate_completeness('windows', ['fastfetch', 'lynis'])
        (False, ['hardening'])
        >>> evaluate_completeness('windows', ['fastfetch', 'hardeningkitty'])
        (True, [])
    """
    requirements = requirements_for_class(asset_class, overrides)
    arrived = set(reports or ())
    missing = [
        requirement
        for requirement, accepted in sorted(requirements.items())
        if not arrived.intersection(accepted)
    ]
    return not missing, missing


def compute_round_state(register, cache, period, audit_months, grace_weeks,
                        today=None, class_requirements=None):
    """Describe one audit round against the asset register.

    The register is the denominator: every asset in scope gets an entry here,
    including the ones that submitted nothing. That is the whole point - the
    previous model could only show what arrived, so an asset that never
    reported produced no row at all rather than a red one.

    Assets fall into five buckets, and they are kept apart on purpose. Counting
    an accounted-for asset as scanned would fold "we hold evidence" together
    with "we hold an excuse", and the deviation count is exactly what the ISO
    tool needs as a separate number.
    """
    today = today or date.today()
    scan_start, scan_end, coverage_end = get_round_windows(period, audit_months, grace_weeks)

    submissions = cache.submissions_in_period(period) if cache else []
    by_asset = {}
    for record in submissions:
        asset_id = record.get('asset_id')
        if not asset_id:
            continue
        current = by_asset.get(asset_id)
        if current is None or record['submitted_at_dt'] > current['submitted_at_dt']:
            by_asset[asset_id] = record

    scanned, outstanding, manual, accounted, unexplained = [], [], [], [], []
    seen_assets = set()

    for entry in (register.in_scope(scan_start, scan_end) if register and register.loaded else []):
        if entry['asset_id'] in seen_assets:
            continue
        seen_assets.add(entry['asset_id'])

        record = by_asset.get(entry['asset_id'])
        row = {'entry': entry, 'record': record}

        if record:
            complete, missing = evaluate_completeness(
                entry['class'], record.get('reports'), class_requirements
            )
            row['complete'] = complete
            row['missing'] = missing
            row['timeliness'] = record.get('timeliness')
            scanned.append(row)
            continue

        # Left scope during the round without ever being scanned. The departure
        # is the justification, but only if someone wrote one down: a window
        # closed without a reason is an unexplained disappearance, and
        # subtracting it silently would raise the coverage rate.
        left_during_round = entry['valid_to'] and scan_start <= entry['valid_to'] <= coverage_end
        if left_during_round:
            if entry.get('departure_reason'):
                accounted.append(row)
            else:
                unexplained.append(row)
            continue

        if entry['class'] in MANUAL_CLASSES:
            manual.append(row)
            continue

        outstanding.append(row)

    denominator = len(scanned) + len(accounted) + len(outstanding) + len(unexplained)

    return {
        'period': period,
        'scan_start': scan_start,
        'scan_end': scan_end,
        'coverage_end': coverage_end,
        'is_open': scan_start <= today <= coverage_end,
        'scanned': scanned,
        'accounted': accounted,
        'outstanding': outstanding,
        'unexplained': unexplained,
        'manual': manual,
        'retired': register.retired() if register and register.loaded else [],
        'unmatched': cache.unmatched(period) if cache else [],
        'denominator': denominator,
        'closeable': not outstanding and not unexplained,
    }


def normalise_serial(raw):
    """Return a usable hardware serial, or None when there is none.

    A usable serial is a single token: non-empty, no whitespace, and not one of
    the placeholder strings a client writes when it cannot read the hardware.
    Everything else counts as absent - a missing serial is a state to report,
    not a key to guess at.

    Examples:
        >>> normalise_serial(' pf50l2mr\\n')
        'PF50L2MR'
        >>> normalise_serial('\\ufeffMP1Y69AC')
        'MP1Y69AC'
        >>> normalise_serial('Not available') is None
        True
        >>> normalise_serial('Mac OS X\\t') is None
        True
        >>> normalise_serial('00000000') is None
        True
        >>> normalise_serial(None) is None
        True
    """
    if raw is None:
        return None

    value = raw.replace('﻿', '').strip()
    if not value:
        return None

    # A real serial is one token. The macOS client has been seen writing
    # "Mac OS X\t", which is a fragment of unrelated output.
    if len(value.split()) != 1:
        return None

    if value.lower() in SERIAL_PLACEHOLDERS:
        return None

    # All-zero serials are a BIOS default, not an identity.
    if set(value) <= {'0'}:
        return None

    return value.upper()


def parse_register_date(value, field, row_number):
    """Parse an ISO date from the register, treating blank as open-ended."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(
            f"assets.csv row {row_number}: {field} '{value}' is not a YYYY-MM-DD date"
        )


class AssetRegisterError(Exception):
    """Raised when the asset register cannot be trusted as a lookup key."""


class AssetRegister:
    """The set of assets in ISO scope, exported from the compliance sheet.

    The register is the denominator: compliance is measured against the assets
    that are expected to report, not against whatever happened to arrive.
    `asset_id` is the durable identity; a serial is the key an incoming
    submission is matched on, and one asset may have several over its life.
    """

    def __init__(self, csv_path=None):
        self.csv_path = csv_path
        self.rows = []
        self.loaded = False

    def load(self):
        """Read and validate the register. Raises AssetRegisterError on faults.

        Validation fails fast rather than degrading: a register that cannot be
        trusted produces a compliance report that cannot be trusted either.
        """
        self.rows = []
        self.loaded = False

        if not self.csv_path:
            logger.info("No asset register configured - round and fleet views unavailable")
            return

        path = Path(self.csv_path)
        if not path.exists():
            logger.warning(
                f"Asset register not found at {path} - round and fleet views unavailable"
            )
            return

        with open(path, newline='', encoding='utf-8-sig') as handle:
            reader = csv.DictReader(handle)
            required = {'asset_id', 'serial', 'owner', 'class'}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise AssetRegisterError(
                    f"assets.csv is missing required column(s): {', '.join(sorted(missing))}"
                )

            for offset, raw_row in enumerate(reader, start=2):
                self.rows.append(self._parse_row(raw_row, offset))

        self._check_serial_overlaps()

        self.loaded = True
        assets = {row['asset_id'] for row in self.rows}
        active = {row['asset_id'] for row in self.rows if row['status'] == 'active'}
        logger.info(
            f"Asset register loaded: {len(self.rows)} row(s), "
            f"{len(assets)} asset(s), {len(active)} active"
        )

    def _parse_row(self, raw_row, row_number):
        def field(name):
            return (raw_row.get(name) or '').strip()

        asset_id = field('asset_id')
        if not asset_id:
            raise AssetRegisterError(f"assets.csv row {row_number}: asset_id is empty")

        serial = normalise_serial(raw_row.get('serial'))
        if not serial:
            raise AssetRegisterError(
                f"assets.csv row {row_number} ({asset_id}): "
                f"serial '{field('serial')}' is empty or not a usable serial"
            )

        asset_class = field('class').lower()
        if asset_class not in VALID_ASSET_CLASSES:
            raise AssetRegisterError(
                f"assets.csv row {row_number} ({asset_id}): unknown class '{asset_class}'. "
                f"Expected one of {', '.join(sorted(VALID_ASSET_CLASSES))}"
            )

        status = (field('status') or 'active').lower()
        if status not in VALID_ASSET_STATUSES:
            raise AssetRegisterError(
                f"assets.csv row {row_number} ({asset_id}): unknown status '{status}'. "
                f"Expected one of {', '.join(sorted(VALID_ASSET_STATUSES))}"
            )

        try:
            valid_from = parse_register_date(raw_row.get('valid_from'), 'valid_from', row_number)
            valid_to = parse_register_date(raw_row.get('valid_to'), 'valid_to', row_number)
            owner_since = parse_register_date(raw_row.get('owner_since'), 'owner_since', row_number)
        except ValueError as exc:
            raise AssetRegisterError(str(exc)) from exc

        if valid_from and valid_to and valid_to < valid_from:
            raise AssetRegisterError(
                f"assets.csv row {row_number} ({asset_id}): valid_to precedes valid_from"
            )

        return {
            'asset_id': asset_id,
            'serial': serial,
            'owner': field('owner'),
            'model': field('model'),
            'class': asset_class,
            'status': status,
            'owner_since': owner_since,
            'valid_from': valid_from,
            'valid_to': valid_to,
            'departure_reason': field('departure_reason'),
            'row_number': row_number,
        }

    def _check_serial_overlaps(self):
        """One serial may appear more than once, but never for overlapping periods.

        A serial that is valid for two assets at the same moment makes the
        lookup ambiguous, which is worse than having no register at all.
        """
        by_serial = {}
        for row in self.rows:
            by_serial.setdefault(row['serial'], []).append(row)

        for serial, rows in by_serial.items():
            if len(rows) == 1:
                continue
            ordered = sorted(rows, key=lambda r: (r['valid_from'] or date.min))
            for earlier, later in zip(ordered, ordered[1:]):
                earlier_end = earlier['valid_to'] or date.max
                later_start = later['valid_from'] or date.min
                if later_start < earlier_end:
                    raise AssetRegisterError(
                        f"assets.csv: serial {serial} has overlapping validity in rows "
                        f"{earlier['row_number']} and {later['row_number']} "
                        f"({earlier['asset_id']} and {later['asset_id']})"
                    )

    def lookup(self, serial, on_date=None):
        """Resolve a serial to the register row valid on the given date."""
        if not serial:
            return None
        on_date = on_date or date.today()

        candidates = [row for row in self.rows if row['serial'] == serial]
        for row in candidates:
            if row['valid_from'] and on_date < row['valid_from']:
                continue
            if row['valid_to'] and on_date >= row['valid_to']:
                continue
            return row

        # Outside every validity window the serial is still known; returning the
        # closest row keeps a historical submission attributable to its asset.
        if candidates:
            return sorted(candidates, key=lambda r: (r['valid_from'] or date.min))[-1]
        return None

    def in_scope(self, window_start, window_end):
        """Active rows whose validity window overlaps the given scan window.

        Scope is computed from recorded dates rather than from a snapshot, so a
        device replaced mid-round is in scope and a closed round stays
        reproducible after the register moves on.
        """
        result = []
        for row in self.rows:
            if row['status'] != 'active':
                continue
            starts = row['valid_from'] or date.min
            ends = row['valid_to'] or date.max
            if starts <= window_end and ends >= window_start:
                result.append(row)
        return result

    def retired(self):
        """Rows excluded from the denominator but kept visible with their history."""
        return [row for row in self.rows if row['status'] == 'retired']


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
                self.required_reports_mandatory = required_reports.get('mandatory', ['fastfetch', 'lynis'])
                self.required_reports_one_of = required_reports.get('one_of', ['trivy', 'vulnix'])

                # Asset register: the denominator compliance is measured against
                self.asset_register_path = compliance.get('asset_register')

                # Per-class requirement overrides. Requirements are named after
                # what they are - sysinfo, hardening - and the tools that
                # satisfy them differ per platform and change over time.
                self.class_requirements = required_reports.get('per_class', {})

                # Weeks past the audit month during which a submission still
                # counts toward the round, and during which an asset entering
                # scope still belongs to it. One value, both boundaries.
                self.grace_weeks = compliance.get('grace_weeks', 4)

                # Validate audit months
                if self.compliance_enabled:
                    if not self.audit_months:
                        raise ValueError("compliance.audit_months must be specified when compliance is enabled")
                    for month in self.audit_months:
                        if not isinstance(month, int) or month < 1 or month > 12:
                            raise ValueError(f"Invalid audit month '{month}'. Must be integer between 1 and 12")
                    if not isinstance(self.grace_weeks, int) or self.grace_weeks < 0:
                        raise ValueError(
                            f"Invalid compliance.grace_weeks '{self.grace_weeks}'. "
                            "Must be a non-negative integer"
                        )

                logger.info(f"Configuration loaded from {self.config_file}")
                logger.info(f"Network port: {self.networkport}")
                logger.info(f"Storage location: {self.storage_location}")
                logger.info(f"Compliance mode: {self.compliance_enabled}")
                if self.compliance_enabled:
                    logger.info(f"Audit months: {self.audit_months}")
                    logger.info(f"Grace period: {self.grace_weeks} week(s)")
                    logger.info(f"Required reports: {self.required_reports_mandatory} + one of {self.required_reports_one_of}")
                    logger.info(f"Asset register: {self.asset_register_path or 'not configured'}")
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
    asset_register = None

    def log_message(self, format, *args):
        """Override to use custom logger"""
        logger.info("%s - %s" % (self.address_string(), format % args))

    def _validate_bearer_token(self):
        """Validate Bearer token from Authorization header

        Returns:
            bool: True if token is valid, False otherwise
        """
        auth_header = self.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return False

        # Extract token (remove "Bearer " prefix)
        token = auth_header[7:]

        # Compare against all valid tokens using constant-time comparison
        return any(secrets.compare_digest(token, valid_token) for valid_token in VALID_TOKENS)

    def _validate_basic_auth(self):
        """Validate HTTP Basic Authentication from Authorization header

        Returns:
            bool: True if password is valid, False otherwise
        """
        auth_header = self.headers.get('Authorization', '')

        if not auth_header.startswith('Basic '):
            return False

        try:
            # Extract and decode base64 credentials
            encoded = auth_header[6:]  # Remove "Basic " prefix
            decoded = base64.b64decode(encoded).decode('utf-8')

            # Split on first colon to get username and password
            # Username is ignored - only password matters
            if ':' not in decoded:
                return False

            _, password = decoded.split(':', 1)

            # Compare password using constant-time comparison
            return secrets.compare_digest(password, DASHBOARD_PASSWORD)

        except Exception:
            # Malformed header or decode error
            return False

    def _send_json_error(self, code, message):
        """Send JSON error response for API endpoints

        Args:
            code: HTTP status code
            message: Error message
        """
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode())

    def _send_html_error(self, code, message, include_auth_header=False):
        """Send HTML error response for dashboard endpoints

        Args:
            code: HTTP status code
            message: Error message
            include_auth_header: Whether to include WWW-Authenticate header
        """
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')

        if include_auth_header and code == 401:
            self.send_header('WWW-Authenticate', 'Basic realm="Honeybadger Dashboard"')

        self.end_headers()

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Authentication Required</title>
    <style>
        body {{ font-family: sans-serif; padding: 40px; text-align: center; }}
        h1 {{ color: #dc3545; }}
        p {{ color: #666; }}
    </style>
</head>
<body>
    <h1>{code} {message}</h1>
    <p>Please provide valid credentials to access the dashboard.</p>
</body>
</html>"""
        self.wfile.write(html.encode())

    def validate_report_type(self, report_type):
        """Validate that the report type is supported"""
        valid_types = ['lynis', 'fastfetch', 'trivy', 'vulnix']
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

        # Fastfetch validation
        elif report_type_lower == 'fastfetch':
            # Fastfetch/system info should be a dict with basic system fields
            if not isinstance(data, dict):
                return False, "Invalid Fastfetch report: must be a JSON object"
            # Basic validation - check if it has some system-related fields
            if not any(key in data for key in ['hostname', 'os', 'kernel', 'system']):
                logger.warning("Fastfetch report may be invalid: missing common system info fields")

        # Trivy validation
        elif report_type_lower == 'trivy':
            if not isinstance(data, dict):
                return False, "Invalid Trivy report: must be a JSON object"
            # Check for common Trivy report fields
            if 'Results' not in data and 'ArtifactName' not in data:
                logger.warning("Trivy report may be invalid: missing 'Results' or 'ArtifactName' field")

        # Vulnix validation
        elif report_type_lower == 'vulnix':
            if not isinstance(data, dict):
                return False, "Invalid Vulnix report: must be a JSON object"
            # Check for vulnerabilities field
            if 'vulnerabilities' not in data:
                logger.warning("Vulnix report may be invalid: missing 'vulnerabilities' field")

        return True, None

    def detect_report_type_from_filename(self, filename):
        """Detect report type from filename patterns

        Args:
            filename: Name of the file (can include directory path)

        Returns:
            str or None: Report type if detected, None otherwise
        """
        # Extract just the filename without path
        basename = os.path.basename(filename).lower()

        # Match patterns for each report type
        if 'lynis' in basename and basename.endswith('.json'):
            return 'lynis'
        elif 'fastfetch' in basename and basename.endswith('.json'):
            return 'fastfetch'
        elif 'trivy' in basename and basename.endswith('.json'):
            return 'trivy'
        elif 'vulnix' in basename and basename.endswith('.json'):
            return 'vulnix'

        return None

    def validate_tar_member_path(self, member):
        """Validate tar member path for security

        Args:
            member: TarInfo object from tarfile

        Returns:
            tuple: (is_valid, error_message)
        """
        # Reject absolute paths
        if member.name.startswith('/'):
            return False, f"Tar archive contains dangerous path: {member.name}"

        # Reject parent directory traversal
        if '..' in member.name:
            return False, f"Tar archive contains dangerous path: {member.name}"

        # Reject symlinks
        if member.issym() or member.islnk():
            return False, f"Tar archive contains symlink: {member.name}"

        # Check nesting depth (max 3 levels)
        depth = member.name.count('/')
        if depth > 3:
            return False, f"Tar archive contains deeply nested path: {member.name}"

        return True, None

    def validate_tar_size_limits(self, content_length, member_sizes):
        """Validate tar archive and individual file sizes

        Args:
            content_length: Total size of tar archive in bytes
            member_sizes: Dict mapping member names to their sizes in bytes

        Returns:
            tuple: (is_valid, error_message)
        """
        MAX_TAR_SIZE = 50 * 1024 * 1024  # 50MB
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

        # Check total tar size
        if content_length > MAX_TAR_SIZE:
            return False, f"Tar archive too large (max 50MB)"

        # Check individual file sizes
        for member_name, size in member_sizes.items():
            if size > MAX_FILE_SIZE:
                return False, f"File too large: {member_name} (max 10MB per file)"

        return True, None

    def extract_and_validate_tar(self, tar_data, content_length):
        """Extract and validate tar archive contents

        Args:
            tar_data: Bytes of tar archive
            content_length: Size of tar archive in bytes

        Returns:
            tuple: (success, result)
                On success: (True, {
                    'reports': [(filename, report_type, json_content), ...],
                    'unrecognised': [{'file': name, 'reason': message}, ...],
                })
                On failure: (False, error_message)

        A member the server cannot make sense of is reported in 'unrecognised',
        not treated as a reason to reject the archive. Only an archive that is
        itself unusable - unreadable, oversized, or carrying an unsafe path -
        is a hard failure.
        """
        try:
            # Open tar archive with auto-detection of compression
            tar = tarfile.open(fileobj=io.BytesIO(tar_data), mode='r:*')
        except tarfile.TarError as e:
            return False, f"Invalid tar archive: {str(e)}"
        except Exception as e:
            return False, f"Invalid tar archive: corrupted data"

        try:
            members = tar.getmembers()

            # Check if tar is empty
            if not members:
                return False, "Tar archive contains no report files"

            # Check file count limit
            if len(members) > 100:
                return False, f"Tar archive contains too many files (max 100, found {len(members)})"

            # Pre-scan: validate all member paths and collect sizes
            member_sizes = {}
            json_files = []

            for member in members:
                # Validate path security for every member, including the
                # non-JSON files the client bundles alongside the reports
                valid, error_msg = self.validate_tar_member_path(member)
                if not valid:
                    return False, error_msg

                # Only process files (skip directories)
                if not member.isfile():
                    continue

                # Only process JSON files
                if not member.name.endswith('.json'):
                    continue

                # Collect size for validation
                member_sizes[member.name] = member.size
                json_files.append(member)

            # Validate size limits
            valid, error_msg = self.validate_tar_size_limits(content_length, member_sizes)
            if not valid:
                return False, error_msg

            # Extract and process JSON files
            results = []
            unrecognised = []
            for member in json_files:
                # Detect report type from filename
                report_type = self.detect_report_type_from_filename(member.name)
                if not report_type:
                    unrecognised.append({
                        'file': member.name,
                        'reason': 'Unrecognised report type'
                    })
                    continue

                # Extract file content
                try:
                    file_obj = tar.extractfile(member)
                    content = file_obj.read()

                    # Parse JSON
                    json_content = json.loads(content)

                    results.append((member.name, report_type, json_content))
                except json.JSONDecodeError as e:
                    unrecognised.append({
                        'file': member.name,
                        'reason': f"Invalid JSON: {str(e)}"
                    })
                except Exception as e:
                    unrecognised.append({
                        'file': member.name,
                        'reason': f"Error extracting file: {str(e)}"
                    })

            # The hardware serial identifies the asset. It is not a report, so
            # it is read separately and never appears in 'reports'.
            serial = None
            for member in members:
                if not member.isfile():
                    continue
                if os.path.basename(member.name).lower() != 'hardware-serial.txt':
                    continue
                valid, error_msg = self.validate_tar_member_path(member)
                if not valid:
                    break
                try:
                    handle = tar.extractfile(member)
                    serial = normalise_serial(handle.read().decode('utf-8', errors='replace'))
                except Exception as e:
                    logger.warning(f"Could not read hardware serial from archive: {e}")
                break

            tar.close()
            return True, {
                'reports': results,
                'unrecognised': unrecognised,
                'serial': serial,
            }

        except Exception as e:
            tar.close()
            return False, f"Error processing tar archive: {str(e)}"

    def get_health_status(self):
        """Get health status information for monitoring"""
        storage_path = Path(self.config.storage_location)

        # Count systems, not audit periods. Where the system directories sit
        # depends on the storage mode, so the walk differs per mode.
        total_reports = 0
        unique_hosts = set()
        report_counts = {'lynis': 0, 'fastfetch': 0}

        def count_system_dir(system_dir, hostname):
            """Count one system directory and the report types it holds"""
            nonlocal total_reports
            total_reports += 1
            if hostname:
                unique_hosts.add(hostname)
            if (system_dir / 'lynis-report.json').exists():
                report_counts['lynis'] += 1
            if (system_dir / 'fastfetch-report.json').exists():
                report_counts['fastfetch'] += 1

        if storage_path.exists():
            if self.config.compliance_enabled:
                # COMPLIANCE MODE: reports/{audit-period}/{hostname-username}/
                for period_dir in storage_path.iterdir():
                    if not period_dir.is_dir():
                        continue
                    if not is_audit_period_dirname(period_dir.name):
                        continue

                    for system_dir in period_dir.iterdir():
                        if not system_dir.is_dir():
                            continue

                        # Extract hostname from {hostname}-{username}
                        parts = system_dir.name.rsplit('-', 1)
                        hostname = parts[0] if len(parts) == 2 else None
                        count_system_dir(system_dir, hostname)
            else:
                # LEGACY MODE: reports/{hostname-username-YYYYMMDD}/
                for item in storage_path.iterdir():
                    if not item.is_dir():
                        continue

                    # Extract hostname from {hostname}-{username}-{yyyymmdd}
                    hostname = None
                    parts = item.name.rsplit('-', 1)
                    if len(parts) == 2:
                        host_parts = parts[0].rsplit('-', 1)
                        if len(host_parts) == 2:
                            hostname = host_parts[0]
                    count_system_dir(item, hostname)

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
        # Validate Bearer token authentication
        if not self._validate_bearer_token():
            auth_header = self.headers.get('Authorization', '')
            if not auth_header:
                self._send_json_error(401, "Missing Authorization header")
            elif not auth_header.startswith('Bearer '):
                self._send_json_error(401, "Invalid Authorization header format. Expected: Bearer <token>")
            else:
                self._send_json_error(401, "Invalid authentication token")
            return

        # Route to tar handler if path is /submit-tar
        if self.path == '/submit-tar':
            self.do_POST_submit_tar()
            return

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

            # If this is a fastfetch report, extract OS type from the data itself
            if report_type.lower() == 'fastfetch' and isinstance(data, dict) and 'os' in data:
                os_type = data.get('os', os_type)
                logger.info(f"Extracted OS type from fastfetch data: {os_type}")

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

    def do_POST_submit_tar(self):
        """Handle POST requests with tar archive

        Stores the archive whole and extracts the reports it recognises,
        reporting per-file status for any JSON member it does not.
        """
        try:
            # Get required headers
            hostname = self.headers.get('X-Hostname')
            username = self.headers.get('X-Username')

            if not hostname or not username:
                self.send_error(400, "Missing required headers: X-Hostname and X-Username")
                return

            # Get content length and validate
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "No content provided")
                return

            # Check size limit (50MB)
            MAX_TAR_SIZE = 50 * 1024 * 1024
            if content_length > MAX_TAR_SIZE:
                self.send_error(413, "Tar archive too large (max 50MB)")
                return

            # Read request body
            tar_data = self.rfile.read(content_length)

            # Extract the reports the server recognises. Unrecognised members
            # are reported back, not treated as a reason to reject the archive.
            success, extraction = self.extract_and_validate_tar(tar_data, content_length)
            if not success:
                self.send_error(400, extraction)
                return

            extracted_reports = extraction['reports']
            unrecognised = extraction['unrecognised']
            serial = extraction['serial']

            # OS type comes from the archive's fastfetch report; the X-OS-Type
            # header is only a fallback for archives without one
            os_type = self.headers.get('X-OS-Type', 'unknown')
            for _, report_type, data in extracted_reports:
                if report_type == 'fastfetch' and isinstance(data, dict) and 'os' in data:
                    os_type = data.get('os', os_type)
                    logger.info(f"Extracted OS type from fastfetch data: {os_type}")
                    break

            if self.config.compliance_enabled:
                record_dir, metadata, saved_reports = self.store_submission(
                    hostname, username, serial, tar_data, extracted_reports, os_type
                )
                tar_path = record_dir / metadata['evidence']
                audit_period = metadata['audit_period']
            else:
                # Legacy mode keeps its flat date-named directories untouched.
                date_str = datetime.now().strftime('%Y%m%d')
                dir_path = Path(self.config.storage_location) / f"{hostname}-{username}-{date_str}"
                dir_path.mkdir(parents=True, exist_ok=True)
                tar_path = dir_path / f"honeybadger-{datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz"
                with open(tar_path, 'wb') as f:
                    f.write(tar_data)
                saved_reports = []
                for member_name, report_type, data in extracted_reports:
                    saved_path, _ = self.save_report(hostname, username, report_type, data, os_type)
                    saved_reports.append({
                        'file': member_name,
                        'report_type': report_type,
                        'path': str(saved_path),
                    })
                metadata = {'unmatched_reason': None, 'asset_id': None, 'timeliness': None}
                audit_period = None

            logger.info(f"Tar archive stored: {tar_path} ({content_length} bytes)")

            if self.config.compliance_enabled and self.compliance_cache:
                self.compliance_cache.rebuild()

            # 200 when every JSON member was recognised and the submission
            # resolved to an asset; 207 when something needs attention but the
            # evidence is stored either way.
            needs_attention = bool(unrecognised) or not saved_reports \
                or bool(metadata.get('unmatched_reason'))
            status_code = 207 if needs_attention else 200

            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {
                'status': 'success' if status_code == 200 else 'partial',
                'message': 'Submission stored',
                'path': str(tar_path),
                'size': content_length,
                'os_type': os_type,
                'serial': serial,
                'asset_id': metadata.get('asset_id'),
                'audit_period': audit_period,
                'timeliness': metadata.get('timeliness'),
                'unmatched_reason': metadata.get('unmatched_reason'),
                'reports_saved': saved_reports,
                'unrecognised': unrecognised
            }

            self.wfile.write(json.dumps(response, indent=2).encode())

        except Exception as e:
            logger.error(f"Error saving tar submission: {e}", exc_info=True)
            self.send_error(500, f"Internal server error: {str(e)}")

    def resolve_submission(self, serial, submitted_at):
        """Match a submission to a register entry.

        Returns (entry_or_None, unmatched_reason_or_None). The two ways a
        submission fails to resolve need different fixes and are kept apart:
        a missing serial is a client problem, an unknown serial is a register
        problem.
        """
        if not serial:
            return None, 'no_serial'

        register = self.asset_register
        if not register or not register.loaded:
            # Without a register nothing can be matched, but the submission is
            # not the thing at fault - record it as unknown and move on.
            return None, 'serial_not_in_register'

        entry = register.lookup(serial, submitted_at.date())
        if entry is None:
            return None, 'serial_not_in_register'
        return entry, None

    def store_submission(self, hostname, username, serial, tar_data,
                         extracted_reports, os_type, submitted_at=None):
        """Write one submission as its own timestamped record.

        A submission is the unit: one upload, one moment, stored under the
        hardware serial that identifies the asset. Records are never
        overwritten, so two scans of the same machine in one round both
        survive, and the audit period is computed from the timestamp rather
        than baked into the path.

        Returns (record_dir, metadata).
        """
        submitted_at = submitted_at or datetime.now()
        entry, unmatched_reason = self.resolve_submission(serial, submitted_at)

        period, timeliness = classify_submission(
            submitted_at, self.config.audit_months, self.config.grace_weeks
        )

        storage = Path(self.config.storage_location)
        if entry is not None:
            base = storage / 'submissions' / serial
        else:
            base = storage / 'unmatched' / f"{hostname}-{username}"

        stamp = submitted_at.strftime('%Y-%m-%dT%H-%M-%S')
        record_dir = base / stamp
        suffix = 1
        while record_dir.exists():
            suffix += 1
            record_dir = base / f"{stamp}-{suffix}"
        record_dir.mkdir(parents=True, exist_ok=False)

        tar_name = f"honeybadger-{submitted_at.strftime('%Y%m%d-%H%M%S')}.tar.gz"
        with open(record_dir / tar_name, 'wb') as handle:
            handle.write(tar_data)

        saved_reports = []
        for member_name, report_type, data in extracted_reports:
            filename = REPORT_FILENAMES.get(report_type, f'{report_type}-report.json')
            with open(record_dir / filename, 'w') as handle:
                json.dump(data, handle, indent=2)
            saved_reports.append({
                'file': member_name,
                'report_type': report_type,
                'path': str(record_dir / filename),
            })

        # Register state is written into the record rather than joined at read
        # time. The register moves - owners change, devices are replaced - and a
        # closed round must keep reporting what was true when it was scanned.
        evidence_predates_owner = False
        if entry and entry.get('owner_since'):
            evidence_predates_owner = submitted_at.date() < entry['owner_since']

        metadata = {
            'schema_version': 1,
            'submitted_at': submitted_at.isoformat(),
            'audit_period': period,
            'timeliness': timeliness,
            'serial': serial,
            'hostname': hostname,
            'username': username,
            'os_type': os_type,
            'asset_id': entry['asset_id'] if entry else None,
            'owner': entry['owner'] if entry else None,
            'class': entry['class'] if entry else None,
            'unmatched_reason': unmatched_reason,
            'evidence_predates_owner': evidence_predates_owner,
            'reports': sorted({r['report_type'] for r in saved_reports}),
            'evidence': tar_name,
        }
        with open(record_dir / 'submission.json', 'w') as handle:
            json.dump(metadata, handle, indent=2)

        if unmatched_reason:
            logger.warning(
                f"Submission stored as unmatched ({unmatched_reason}): "
                f"{hostname}-{username} serial={serial or '-'} -> {record_dir}"
            )
        else:
            logger.info(
                f"Submission stored: {metadata['asset_id']} ({serial}) "
                f"period {period}, {timeliness} -> {record_dir}"
            )

        return record_dir, metadata, saved_reports

    def save_report(self, hostname, username, report_type, data, os_type='unknown'):
        """Save report to disk with appropriate filename

        Args:
            hostname: System hostname
            username: User who performed scan
            report_type: Type of report (lynis, trivy, vulnix, fastfetch)
            data: Report JSON data
            os_type: Operating system type (optional)

        Returns:
            tuple: (file_path, audit_period or None)
        """
        report_type_lower = report_type.lower()

        # Determine filename based on report type
        if report_type_lower == 'lynis':
            filename = 'lynis-report.json'
        elif report_type_lower == 'fastfetch':
            filename = 'fastfetch-report.json'
        elif report_type_lower == 'trivy':
            filename = 'trivy-report.json'
        elif report_type_lower == 'vulnix':
            filename = 'vulnix-report.json'
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
            has_fastfetch = (item / 'fastfetch-report.json').exists()

            reports.append({
                'hostname': hostname,
                'username': username,
                'date': date_str,
                'last_update': last_update,
                'has_lynis': has_lynis,
                'has_fastfetch': has_fastfetch,
                'path': str(item)
            })

        # Sort by last update (most recent first)
        reports.sort(key=lambda x: x['last_update'], reverse=True)

        return reports

    DASHBOARD_CSS = """
        :root{--ground:#f6f7f8;--surface:#fff;--surface-2:#eceff2;--surface-3:#f9fafb;
          --line:#d8dde2;--line-soft:#e6eaee;--ink:#1b1f24;--ink-2:#59626c;--ink-3:#8a939d;
          --accent:#2f5d8c;--accent-soft:#e3ecf5;--ok:#2c7a51;--ok-soft:#e0f0e7;
          --warn:#9a6a0a;--warn-soft:#f7edd8;--crit:#b23b32;--crit-soft:#f8e3e1;
          --manual:#665a8c;--manual-soft:#eae7f3;}
        @media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
          --ground:#14171b;--surface:#1b2026;--surface-2:#232a31;--surface-3:#1f252b;
          --line:#303942;--line-soft:#272f37;--ink:#e3e8ed;--ink-2:#98a3ae;--ink-3:#6d7883;
          --accent:#72a6dc;--accent-soft:#1d2c3c;--ok:#5cb684;--ok-soft:#182c22;
          --warn:#d7a446;--warn-soft:#2e2718;--crit:#e08177;--crit-soft:#32201e;
          --manual:#a596cd;--manual-soft:#242038;}}
        *{box-sizing:border-box}
        body{margin:0;background:var(--ground);color:var(--ink);font-size:14px;line-height:1.5;
          font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
        .mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-variant-numeric:tabular-nums}
        .wrap{max-width:1120px;margin:0 auto;padding:28px 24px 64px}
        .top{display:flex;justify-content:space-between;align-items:flex-end;gap:24px;
          flex-wrap:wrap;margin-bottom:22px}
        .brand{display:flex;align-items:baseline;gap:10px}
        .brand h1{font-size:19px;font-weight:600;margin:0}
        .ctx{text-align:right;font-size:12.5px;color:var(--ink-2)}
        .ctx strong{color:var(--ink)}
        .tabs{display:flex;gap:2px;border-bottom:1px solid var(--line);margin-bottom:26px}
        .tab{font:inherit;font-weight:500;color:var(--ink-2);padding:9px 14px;
          border-bottom:2px solid transparent;margin-bottom:-1px;text-decoration:none}
        .tab:hover{color:var(--ink)}
        .tab.on{color:var(--ink);border-bottom-color:var(--accent);font-weight:600}
        .summary{background:var(--surface);border:1px solid var(--line);border-radius:6px;
          padding:22px 24px;margin-bottom:26px;display:grid;
          grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:32px}
        @media (max-width:760px){.summary{grid-template-columns:1fr}}
        .sum-h{font-size:11.5px;text-transform:uppercase;letter-spacing:.07em;
          color:var(--ink-3);font-weight:600;margin:0 0 12px}
        .figure{display:flex;align-items:baseline;gap:9px;margin-bottom:14px}
        .figure .big{font-size:38px;font-weight:600;line-height:1}
        .figure .of{font-size:14px;color:var(--ink-2)}
        .meter{display:flex;height:9px;border-radius:5px;overflow:hidden;
          background:var(--surface-2);margin-bottom:14px}
        .seg-ok{background:var(--ok)}.seg-exc{background:var(--warn)}.seg-open{background:var(--line)}
        .key{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:12.5px;color:var(--ink-2)}
        .key i{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:6px}
        .key b{color:var(--ink)}
        .owners{display:flex;flex-direction:column;gap:7px}
        .owner{display:grid;grid-template-columns:minmax(0,1fr) 62px 44px;align-items:center;
          gap:12px;font-size:13px}
        .owner .nm{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .owner .bar{height:6px;border-radius:3px;background:var(--surface-2);overflow:hidden}
        .owner .bar span{display:block;height:100%;background:var(--ok)}
        .owner .ct{font-size:12px;color:var(--ink-2);text-align:right}
        .owner.done .ct{color:var(--ok);font-weight:600}
        .owner.zero .nm{font-weight:600}.owner.zero .ct{color:var(--crit)}
        .alert{border:1px solid var(--line);border-left:3px solid var(--warn);
          background:var(--surface);border-radius:5px;padding:14px 18px;margin-bottom:26px}
        .alert h3{margin:0 0 4px;font-size:13.5px;font-weight:600}
        .alert p{margin:0 0 10px;font-size:12.5px;color:var(--ink-2);max-width:68ch}
        .alert.crit{border-left-color:var(--crit)}
        .tblwrap{border:1px solid var(--line);border-radius:6px;background:var(--surface);
          overflow-x:auto;margin-bottom:12px}
        table{width:100%;border-collapse:collapse;min-width:720px}
        thead th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-3);
          font-weight:600;text-align:left;padding:10px 14px;border-bottom:1px solid var(--line);
          background:var(--surface-3);white-space:nowrap}
        tbody td{padding:11px 14px;border-bottom:1px solid var(--line-soft);vertical-align:middle}
        tbody tr:last-child td{border-bottom:0}
        .grp td{background:var(--surface-3);padding:7px 14px;font-size:11px;font-weight:600;
          letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3)}
        tr.s-ok td:first-child{box-shadow:inset 3px 0 0 var(--ok)}
        tr.s-exc td:first-child{box-shadow:inset 3px 0 0 var(--warn)}
        tr.s-open td:first-child{box-shadow:inset 3px 0 0 var(--crit)}
        tr.s-man td:first-child{box-shadow:inset 3px 0 0 var(--manual)}
        .sub{display:block;font-size:11.5px;color:var(--ink-3);margin-top:2px}
        .pill{display:inline-flex;align-items:center;gap:5px;font-size:11.5px;font-weight:600;
          padding:2px 8px;border-radius:10px;white-space:nowrap}
        .p-ok{background:var(--ok-soft);color:var(--ok)}
        .p-exc{background:var(--warn-soft);color:var(--warn)}
        .p-open{background:var(--crit-soft);color:var(--crit)}
        .p-man{background:var(--manual-soft);color:var(--manual)}
        .badge{display:inline-block;font-size:11px;font-weight:600;padding:1px 6px;
          border-radius:3px;background:var(--ok-soft);color:var(--ok);margin-right:3px;
          text-decoration:none}
        .badge.tar{background:var(--accent-soft);color:var(--accent)}
        .badge.none{background:var(--surface-2);color:var(--ink-3)}
        .chip{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;white-space:nowrap}
        .chip i{width:7px;height:7px;border-radius:50%;flex:none}
        .d-fresh i{background:var(--ok)}.d-prev i{background:var(--warn)}.d-stale i{background:var(--crit)}
        .d-fresh{color:var(--ok);font-weight:600}.d-prev{color:var(--warn)}.d-stale{color:var(--crit)}
        .legend{font-size:12px;color:var(--ink-3);display:flex;flex-wrap:wrap;gap:6px 20px;
          margin-bottom:24px}
        .empty{padding:40px 20px;text-align:center;color:var(--ink-3)}
        .dash{color:var(--ink-3)}
    """

    def _dashboard_shell(self, title, active_tab, period, body):
        """Wrap a view in the shared page shell."""
        register = self.asset_register
        register_note = (
            f"Register: {len(register.rows)} rows"
            if register and register.loaded else
            "No asset register configured"
        )
        tabs = ''.join(
            f'<a class="tab{" on" if key == active_tab else ""}" '
            f'href="/?view={key}&period={html_escape(period)}">{label}</a>'
            for key, label in (('round', 'Scan round'), ('fleet', 'All assets'))
        )
        return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_escape(title)}</title><style>{self.DASHBOARD_CSS}</style></head>
<body><div class="wrap">
  <div class="top">
    <div class="brand"><span>&#129441;</span><h1>Badgersbay</h1></div>
    <div class="ctx">Audit round <strong class="mono">{html_escape(period)}</strong><br>{html_escape(register_note)}</div>
  </div>
  <div class="tabs">{tabs}</div>
  {body}
</div></body></html>"""

    def generate_round_view_html(self, period):
        """Progress of one audit round against the asset register."""
        state = compute_round_state(
            self.asset_register, self.compliance_cache, period,
            self.config.audit_months, self.config.grace_weeks,
            class_requirements=getattr(self.config, 'class_requirements', None),
        )

        if not (self.asset_register and self.asset_register.loaded):
            body = ('<div class="alert crit"><h3>No asset register configured</h3>'
                    '<p>Without a register the server can show what arrived but not which '
                    'systems are missing. Set <code>compliance.asset_register</code> in '
                    'config.yaml to the CSV exported from the ISO compliance sheet.</p></div>')
            return self._dashboard_shell('Badgersbay Scan Round', 'round', period, body)

        scanned, accounted = state['scanned'], state['accounted']
        outstanding, unexplained = state['outstanding'], state['unexplained']
        total = state['denominator'] or 1

        def pct(n):
            return f"{n / total * 100:.4f}%"

        # This panel is a call list, so it counts what still needs chasing.
        # An accounted-for asset is resolved even though it was never scanned:
        # its owner has nothing left to do.
        owners = {}
        for bucket, resolved in ((scanned, True), (accounted, True),
                                 (outstanding, False), (unexplained, False)):
            for row in bucket:
                owner = row['entry']['owner'] or 'unassigned'
                tally = owners.setdefault(owner, [0, 0])
                tally[1] += 1
                if resolved:
                    tally[0] += 1
        owner_rows = ''.join(
            f'<div class="owner {"done" if d == t else "zero" if d == 0 else ""}">'
            f'<span class="nm">{html_escape(name)}</span>'
            f'<span class="bar"><span style="width:{d / t * 100:.0f}%"></span></span>'
            f'<span class="ct mono">{d}/{t}</span></div>'
            for name, (d, t) in sorted(owners.items(), key=lambda kv: (kv[1][0] / kv[1][1], kv[0]))
        )

        manual_note = (
            f'<p style="margin:14px 0 0;font-size:12.5px;color:var(--ink-2);max-width:46ch">'
            f'{len(state["manual"])} asset(s) are handled manually while their client cannot '
            f'submit, and are not counted in the denominator.</p>'
            if state['manual'] else ''
        )

        summary = f"""
  <div class="summary">
    <div>
      <h2 class="sum-h">Progress</h2>
      <div class="figure"><span class="big mono">{len(scanned)}</span>
        <span class="of">of {state['denominator']} assets scanned</span></div>
      <div class="meter">
        <span class="seg-ok" style="width:{pct(len(scanned))}"></span>
        <span class="seg-exc" style="width:{pct(len(accounted))}"></span>
        <span class="seg-open" style="width:{pct(len(outstanding) + len(unexplained))}"></span>
      </div>
      <div class="key">
        <span><i class="seg-ok"></i><b>{len(scanned)}</b> scanned</span>
        <span><i class="seg-exc"></i><b>{len(accounted)}</b> accounted for</span>
        <span><i class="seg-open"></i><b>{len(outstanding) + len(unexplained)}</b> outstanding</span>
      </div>
      <p style="margin:14px 0 0;font-size:12.5px;color:var(--ink-2);max-width:46ch">
        Scan window {state['scan_start']} to {state['scan_end']}.
        {'Round is closeable.' if state['closeable'] else 'Round closes when nothing is outstanding.'}
      </p>{manual_note}
    </div>
    <div><h2 class="sum-h">By owner</h2><div class="owners">{owner_rows}</div></div>
  </div>"""

        alerts = ''
        if state['unmatched']:
            by_reason = {}
            for record in state['unmatched']:
                by_reason.setdefault(record['unmatched_reason'], []).append(record)
            blocks = []
            for reason, records in sorted(by_reason.items()):
                explanation = (
                    'The archive carried no usable hardware serial. That is a client problem: '
                    'the audit ran without root, or the platform writes the wrong field.'
                    if reason == 'no_serial' else
                    'The serial is not in the register. That is a register problem: a new '
                    'asset, a department outside scope, or a wrong serial column.'
                )
                rows = ''.join(
                    f'<div class="mono" style="font-size:12.5px">'
                    f'{html_escape(record["hostname"])}/{html_escape(record["username"])} '
                    f'&middot; {html_escape(str(record["serial"] or "no serial"))} '
                    f'&middot; {html_escape(record["submitted_at"][:16])}</div>'
                    for record in records
                )
                blocks.append(
                    f'<div class="alert"><h3>{len(records)} submission(s): '
                    f'{html_escape(reason.replace("_", " "))}</h3>'
                    f'<p>{explanation}</p>{rows}</div>'
                )
            alerts += ''.join(blocks)

        if unexplained:
            rows = ''.join(
                f'<div class="mono" style="font-size:12.5px">'
                f'{html_escape(row["entry"]["asset_id"])} &middot; '
                f'{html_escape(row["entry"]["owner"])} &middot; left '
                f'{row["entry"]["valid_to"]}</div>'
                for row in unexplained
            )
            alerts += (
                f'<div class="alert crit"><h3>{len(unexplained)} asset(s) left scope '
                f'without a reason</h3><p>These are counted as outstanding rather than '
                f'removed from the denominator. Dropping them silently would raise the '
                f'coverage rate, which is the one direction a compliance figure must never '
                f'move by accident.</p>{rows}</div>'
            )

        return self._dashboard_shell(
            'Badgersbay Scan Round', 'round', period,
            summary + alerts + self._round_table(state, period)
        )

    def _round_table(self, state, period):
        """The per-asset table, grouped by state."""
        def row_html(row, css, status_html, reports_html, seen):
            entry = row['entry']
            return f"""
            <tr class="{css}">
              <td class="mono"><strong>{html_escape(entry['asset_id'])}</strong></td>
              <td>{html_escape(entry['owner'])}</td>
              <td>{html_escape(entry['class'])}</td>
              <td class="mono" style="font-size:12px">{html_escape(entry['serial'])}</td>
              <td class="mono">{seen}</td>
              <td>{reports_html}</td>
              <td>{status_html}</td>
            </tr>"""

        latest = self.compliance_cache.latest_by_asset() if self.compliance_cache else {}

        def last_seen(entry):
            record = latest.get(entry['asset_id'])
            if not record:
                return '<span class="dash">never</span>'
            return html_escape(record['submitted_at'][:10])

        def badges(record, entry):
            if not record:
                return '<span class="badge none">none</span>'
            out = []
            for report_type in record.get('reports', []):
                filename = REPORT_FILENAMES.get(report_type)
                if filename and record.get('record_dir'):
                    href = f"/evidence/{html_escape(entry['serial'])}/" \
                           f"{html_escape(os.path.basename(record['record_dir']))}/{filename}"
                    out.append(f'<a class="badge" href="{href}">{report_type[0].upper()}</a>')
                else:
                    out.append(f'<span class="badge">{report_type[0].upper()}</span>')
            if record.get('evidence'):
                href = f"/evidence/{html_escape(entry['serial'])}/" \
                       f"{html_escape(os.path.basename(record['record_dir']))}/" \
                       f"{html_escape(record['evidence'])}"
                out.append(f'<a class="badge tar" href="{href}">TAR</a>')
            return ''.join(out) or '<span class="badge none">none</span>'

        groups = []
        if state['scanned']:
            rows = []
            for row in state['scanned']:
                late = '' if row['timeliness'] == 'on_time' else \
                    '<span class="sub">covered late</span>'
                owner_warning = '<span class="sub">evidence predates current holder</span>' \
                    if row['record'].get('evidence_predates_owner') else ''
                if row['complete']:
                    status = f'<span class="pill p-ok">&#10003; scanned</span>{late}{owner_warning}'
                else:
                    status = (f'<span class="pill p-open">&#9888; incomplete</span>'
                              f'<span class="sub">missing: {html_escape(", ".join(row["missing"]))}</span>'
                              f'{late}{owner_warning}')
                rows.append(row_html(row, 's-ok' if row['complete'] else 's-open', status,
                                     badges(row['record'], row['entry']),
                                     html_escape(row['record']['submitted_at'][:10])))
            groups.append((f"Scanned this round &mdash; {len(state['scanned'])}", rows))

        if state['accounted']:
            rows = [row_html(
                row, 's-exc',
                f'<span class="pill p-exc">&#9680; accounted for</span>'
                f'<span class="sub">{html_escape(row["entry"]["departure_reason"])}</span>',
                '<span class="badge none">none</span>', last_seen(row['entry'])
            ) for row in state['accounted']]
            groups.append((f"Accounted for &mdash; {len(state['accounted'])}", rows))

        for bucket, label, css, status in (
            (state['outstanding'], 'Outstanding', 's-open',
             '<span class="pill p-open">&#9888; outstanding</span>'),
            (state['unexplained'], 'Left scope without a reason', 's-open',
             '<span class="pill p-open">&#9888; unexplained departure</span>'),
            (state['manual'], 'Manual &mdash; outside the denominator', 's-man',
             '<span class="pill p-man">&#9675; manual</span>'
             '<span class="sub">client cannot submit yet</span>'),
        ):
            if not bucket:
                continue
            rows = [row_html(row, css, status, '<span class="badge none">none</span>',
                             last_seen(row['entry'])) for row in bucket]
            groups.append((f"{label} &mdash; {len(bucket)}", rows))

        if state['retired']:
            rows = [row_html({'entry': entry}, 's-man',
                             '<span class="pill p-man">retired</span>'
                             f'<span class="sub">{html_escape(entry["departure_reason"])}</span>',
                             '<span class="badge none">none</span>', last_seen(entry))
                    for entry in state['retired']]
            groups.append((f"Retired &mdash; {len(state['retired'])}", rows))

        if not groups:
            return '<div class="tblwrap"><div class="empty">No assets in scope for this round</div></div>'

        body = ''.join(
            f'<tr class="grp"><td colspan="7">{label}</td></tr>' + ''.join(rows)
            for label, rows in groups
        )
        return f"""
  <div class="tblwrap"><table>
    <thead><tr><th style="width:104px">Asset</th><th>Owner</th><th style="width:78px">Class</th>
      <th style="width:150px">Serial</th><th style="width:104px">Last seen</th>
      <th style="width:96px">Reports</th><th style="width:230px">Status</th></tr></thead>
    <tbody>{body}</tbody>
  </table></div>
  <div class="legend"><span>F = Fastfetch</span><span>L = Lynis</span>
    <span>TAR = stored archive</span></div>"""

    def generate_fleet_view_html(self, period):
        """Latest known state of every asset, regardless of round."""
        register = self.asset_register
        if not (register and register.loaded):
            body = ('<div class="alert crit"><h3>No asset register configured</h3>'
                    '<p>The fleet view lists the register, so it needs one.</p></div>')
            return self._dashboard_shell('Badgersbay Fleet', 'fleet', period, body)

        latest = self.compliance_cache.latest_by_asset() if self.compliance_cache else {}
        previous = None
        try:
            periods = sorted({s['audit_period'] for s in self.compliance_cache.submissions})
            older = [p for p in periods if p < period]
            previous = older[-1] if older else None
        except Exception:
            previous = None

        seen = set()
        rows = []
        for entry in sorted(register.rows, key=lambda e: e['asset_id']):
            if entry['asset_id'] in seen:
                continue
            seen.add(entry['asset_id'])
            record = latest.get(entry['asset_id'])

            if record is None:
                freshness = '<span class="chip d-stale"><i></i>never submitted</span>'
                css, when, os_type = 's-open', '<span class="dash">never</span>', \
                    '<span class="dash">unknown</span>'
            else:
                when = html_escape(record['submitted_at'][:10])
                os_type = html_escape(record.get('os_type') or 'unknown')
                if record['audit_period'] == period:
                    freshness = f'<span class="chip d-fresh"><i></i>{html_escape(period)}</span>'
                    css = 's-ok'
                elif previous and record['audit_period'] == previous:
                    freshness = (f'<span class="chip d-prev"><i></i>'
                                 f'{html_escape(record["audit_period"])}</span>')
                    css = 's-exc'
                else:
                    freshness = (f'<span class="chip d-stale"><i></i>'
                                 f'{html_escape(record["audit_period"])}</span>')
                    css = 's-open'

            status = 'retired' if entry['status'] == 'retired' else html_escape(entry['class'])
            rows.append(f"""
            <tr class="{css}">
              <td class="mono"><strong>{html_escape(entry['asset_id'])}</strong></td>
              <td>{html_escape(entry['owner'])}</td>
              <td>{status}</td>
              <td>{os_type}</td>
              <td class="mono">{when}</td>
              <td>{freshness}</td>
            </tr>""")

        table = f"""
  <div class="tblwrap"><table>
    <thead><tr><th style="width:104px">Asset</th><th>Owner</th><th style="width:78px">Class</th>
      <th style="width:200px">Operating system</th><th style="width:104px">Last seen</th>
      <th style="width:150px">Coverage</th></tr></thead>
    <tbody>{''.join(rows) or '<tr><td colspan="6" class="empty">Register is empty</td></tr>'}</tbody>
  </table></div>
  <div class="legend">
    <span><span class="chip d-fresh"><i></i>current round</span></span>
    <span><span class="chip d-prev"><i></i>previous round only</span></span>
    <span><span class="chip d-stale"><i></i>older, or never</span></span>
    <span>Disk encryption, screen lock, firewall and hardening score arrive with
      asset-inventory.json from the client.</span>
  </div>"""
        return self._dashboard_shell('Badgersbay Fleet', 'fleet', period, table)

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

        .dashboard-header {{ display: flex; justify-content: space-between; align-items: center;
                            margin-bottom: 20px; flex-wrap: wrap; gap: 15px; }}
        .header-actions {{ display: flex; align-items: center; gap: 15px; }}
        .refresh-btn {{ background: #0066cc; color: white; border: none;
                       padding: 10px 20px; border-radius: 6px; cursor: pointer;
                       font-size: 14px; font-weight: 500; display: flex;
                       align-items: center; gap: 8px; transition: background 0.2s; }}
        .refresh-btn:hover {{ background: #0052a3; }}
        .refresh-btn:active {{ transform: scale(0.98); }}
        .refresh-btn:disabled {{ opacity: 0.6; cursor: not-allowed; }}
        .refresh-icon {{ display: inline-block; transition: transform 0.5s; }}
        .refresh-btn.refreshing .refresh-icon {{ animation: spin 0.5s linear; }}
        @keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
        .last-updated {{ color: #666; font-size: 13px; font-style: italic; }}
    </style>
    <script>
        function refreshDashboard() {{
            const btn = document.getElementById('refreshBtn');
            btn.classList.add('refreshing');
            btn.disabled = true;
            location.reload();
        }}

        function updateTimestamp() {{
            const now = new Date();
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            const timestamp = hours + ':' + minutes + ':' + seconds;
            const elem = document.getElementById('lastUpdated');
            if (elem) {{
                elem.textContent = 'Last updated: ' + timestamp;
            }}
        }}

        document.addEventListener('DOMContentLoaded', updateTimestamp);

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

                // Note: "incomplete" contains the substring "complete", so the
                // incomplete check must be evaluated first / excluded explicitly.
                const isIncomplete = statusCell.includes('incomplete');

                if (filterValue === 'all') {{
                    row.style.display = '';
                }} else if (filterValue === 'complete') {{
                    row.style.display = (!isIncomplete && statusCell.includes('complete')) ? '' : 'none';
                }} else if (filterValue === 'incomplete') {{
                    row.style.display = isIncomplete ? '' : 'none';
                }} else {{
                    row.style.display = 'none';
                }}
            }}
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="dashboard-header">
            <div>
                <h1>🦡 Honeybadger Compliance Dashboard</h1>
                <div class="subtitle">Security Audit Compliance Tracking</div>
            </div>
            <div class="header-actions">
                <button id="refreshBtn" class="refresh-btn" onclick="refreshDashboard()">
                    <span class="refresh-icon">🔄</span> Refresh
                </button>
                <span id="lastUpdated" class="last-updated"></span>
            </div>
        </div>

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
                <div class="stat-label">Coverage Rate</div>
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
                report_map = {'fastfetch': 'F', 'lynis': 'L'}
                for report_type, badge_text in report_map.items():
                    if report_type in reports:
                        download_url = f"/reports/{selected_period}/{hostname}-{username}/{report_type}-report.json"
                        badges.append(f'<a href="{download_url}" class="badge badge-success" target="_blank">{badge_text}</a>')

                # Check for tar files
                if 'tar' in reports:
                    try:
                        # Find the tar file(s) to link to
                        tar_dir = Path(self.config.storage_location) / selected_period / f"{hostname}-{username}"
                        tar_files = list(tar_dir.glob('*.tar.gz'))
                        if tar_files:
                            # Link to most recent tar file
                            tar_file = sorted(tar_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
                            download_url = f"/reports/{selected_period}/{hostname}-{username}/{tar_file.name}"
                            badges.append(f'<a href="{download_url}" class="badge badge-success" target="_blank">TAR</a>')
                    except Exception as e:
                        logger.error(f"Error generating TAR badge for {hostname}-{username}: {e}")
                        badges.append('<span class="badge badge-danger">TAR?</span>')

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
            Legend: F=Fastfetch, L=Lynis, TAR=Tar Archive
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

        .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .refresh-btn {
            background: #0066cc;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: background 0.2s;
        }

        .refresh-btn:hover {
            background: #0052a3;
        }

        .refresh-btn:active {
            transform: scale(0.98);
        }

        .refresh-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .refresh-icon {
            display: inline-block;
            transition: transform 0.5s;
        }

        .refresh-btn.refreshing .refresh-icon {
            animation: spin 0.5s linear;
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .last-updated {
            color: #666;
            font-size: 13px;
            font-style: italic;
        }
    </style>
    <script>
        function refreshDashboard() {
            const btn = document.getElementById('refreshBtn');
            btn.classList.add('refreshing');
            btn.disabled = true;
            location.reload();
        }

        function updateTimestamp() {
            const now = new Date();
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            const timestamp = hours + ':' + minutes + ':' + seconds;
            const elem = document.getElementById('lastUpdated');
            if (elem) {
                elem.textContent = 'Last updated: ' + timestamp;
            }
        }

        document.addEventListener('DOMContentLoaded', updateTimestamp);

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
    </script>
</head>
<body>
    <div class="container">
        <div class="dashboard-header">
            <div>
                <h1>Honeybadger Server</h1>
                <div class="subtitle">Security Reports Dashboard</div>
            </div>
            <div class="header-actions">
                <button id="refreshBtn" class="refresh-btn" onclick="refreshDashboard()">
                    <span class="refresh-icon">🔄</span> Refresh
                </button>
                <span id="lastUpdated" class="last-updated"></span>
            </div>
        </div>

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
                <div class="stat-number">""" + str(sum(1 for r in reports if r['has_fastfetch'])) + """</div>
                <div class="stat-label">Fastfetch reports</div>
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
                # Determine status: OK if both fastfetch and lynis are present
                has_valid_combination = report['has_fastfetch'] and report['has_lynis']

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
                if report['has_fastfetch']:
                    fastfetch_url = f"/reports/{dir_name}/fastfetch-report.json"
                    reports_badges.append(f'<a href="{fastfetch_url}" class="badge badge-success" target="_blank">Fastfetch</a>')
                else:
                    # Show red badge if fastfetch is missing (it's required)
                    reports_badges.append('<span class="badge badge-danger">Missing Fastfetch</span>')
                if not any([report['has_lynis'], report['has_fastfetch']]):
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

        # Skip authentication for /health endpoint
        if path == '/health':
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
            return

        # Validate Basic Authentication for all other GET endpoints
        if not self._validate_basic_auth():
            self._send_html_error(401, "Unauthorized", include_auth_header=True)
            return

        if path == '/' or path == '/status':
            # Dashboard page - check compliance mode
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()

            if self.config.compliance_enabled:
                period = query_params.get('period', [None])[0] \
                    or get_audit_period(datetime.now(), self.config.audit_months)
                view = query_params.get('view', ['round'])[0]
                if view == 'fleet':
                    html = self.generate_fleet_view_html(period)
                else:
                    html = self.generate_round_view_html(period)
                logger.info(f"Generated {view} view for {period}: {len(html)} chars")
            else:
                # Legacy dashboard
                html = self.generate_status_html()
                logger.info(f"Generated legacy dashboard HTML: {len(html)} chars")

            encoded = html.encode('utf-8')
            logger.info(f"Encoded to {len(encoded)} bytes, writing to client...")
            self.wfile.write(encoded)
            logger.info("Dashboard sent successfully")
        elif self.path.startswith('/evidence/'):
            # Serve a file from one submission record.
            # /evidence/<serial>/<timestamp>/<filename>
            try:
                parts = [unquote(p) for p in self.path[len('/evidence/'):].split('/')]
                if len(parts) != 3 or any(p in ('', '.', '..') or '/' in p for p in parts):
                    self._send_html_error(400, "Malformed evidence path")
                    return

                serial, stamp, filename = parts
                base = (Path(self.config.storage_location) / 'submissions').resolve()
                target = (base / serial / stamp / filename).resolve()
                if not str(target).startswith(str(base) + os.sep) or not target.is_file():
                    self._send_html_error(404, "Evidence not found")
                    return

                # Downloads carry the register's proof-file convention, so the
                # file can go straight into the audit folder under the name the
                # compliance sheet expects.
                download_name = target.name
                record = target.parent / 'submission.json'
                if record.is_file() and target.suffix == '.gz':
                    try:
                        with open(record) as handle:
                            meta = json.load(handle)
                        if meta.get('asset_id'):
                            owner_slug = owner_to_slug(meta.get('owner'))
                            download_name = (
                                f"{meta['asset_id']}-{meta['submitted_at'][:10]}"
                                f"{'-' + owner_slug if owner_slug else ''}.tar.gz"
                            )
                    except Exception as e:
                        logger.warning(f"Could not build download name for {target}: {e}")

                content_type = 'application/gzip' if target.suffix == '.gz' else 'application/json'
                payload = target.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Disposition', f'attachment; filename="{download_name}"')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                logger.error(f"Error serving evidence {self.path}: {e}", exc_info=True)
                self._send_html_error(500, "Internal server error")
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

                # Determine file type and content type
                is_json = full_path.suffix == '.json'
                is_tar = full_path.suffix == '.gz' or full_path.name.endswith('.tar.gz')

                # Create download filename: <folder>-<report>.json
                # e.g., testserver01-testuser-20260316-lynis-report.json
                folder_name = full_path.parent.name
                report_name = full_path.name
                download_filename = f"{folder_name}-{report_name}"

                self.send_response(200)

                # Set content type based on file type
                if is_json:
                    self.send_header('Content-Type', 'application/json')
                    # Read as text
                    with open(full_path, 'r') as f:
                        content = f.read()
                    content_bytes = content.encode('utf-8')
                elif is_tar:
                    self.send_header('Content-Type', 'application/gzip')
                    # Read as binary
                    with open(full_path, 'rb') as f:
                        content_bytes = f.read()
                else:
                    self.send_header('Content-Type', 'application/octet-stream')
                    # Read as binary for unknown types
                    with open(full_path, 'rb') as f:
                        content_bytes = f.read()

                self.send_header('Content-Disposition', f'attachment; filename="{download_filename}"')
                self.send_header('Content-Length', str(len(content_bytes)))
                self.end_headers()
                self.wfile.write(content_bytes)

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

    # Load the asset register. A register that cannot be trusted is a hard stop:
    # it is the denominator of every compliance figure the server reports.
    # An absent register is not - the server still accepts submissions, it just
    # cannot say who is missing.
    register = AssetRegister(config.asset_register_path if config.compliance_enabled else None)
    try:
        register.load()
    except AssetRegisterError as exc:
        logger.error(f"Asset register is invalid: {exc}")
        raise
    ReportHandler.asset_register = register

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


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        prog='honeybadger_server',
        description='Honeybadger Server - Centralized security report aggregation'
    )

    parser.add_argument(
        '--config',
        metavar='PATH',
        type=str,
        help='Path to configuration file (default: search in working dir, script dir, /etc/honeybadger/)'
    )

    parser.add_argument(
        '--token-file',
        metavar='PATH',
        type=str,
        required=True,
        help='Path to YAML file containing valid API tokens (format: tokens: [token1, token2]). Example: --token-file /etc/honeybadger/tokens.yaml'
    )

    parser.add_argument(
        '--dashboard-password-file',
        metavar='PATH',
        type=str,
        required=True,
        help='Path to plaintext file containing dashboard password. Example: --dashboard-password-file /etc/honeybadger/password.txt'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'honeybadger-server version {VERSION}'
    )

    return parser.parse_args()


def find_config_file(cli_config_path=None):
    """Find configuration file using fallback search order

    Search order:
    1. CLI argument (--config)
    2. Current working directory
    3. Script directory
    4. /etc/honeybadger/

    Args:
        cli_config_path: Optional path from --config argument

    Returns:
        Path: Absolute path to configuration file

    Exits:
        Exit code 1 if config file not found or not readable
    """
    searched_locations = []

    # 1. CLI argument (highest priority)
    if cli_config_path:
        config_path = Path(cli_config_path).expanduser().resolve()
        searched_locations.append(str(config_path))

        if config_path.exists():
            return config_path
        else:
            logger.error(f"Configuration file not found: {config_path}")
            logger.error(f"Searched location: {config_path}")
            exit(1)

    # 2. Current working directory
    cwd_config = Path.cwd() / 'config.yaml'
    searched_locations.append(str(cwd_config))
    if cwd_config.exists():
        return cwd_config

    # 3. Script directory (legacy/backward compatibility)
    script_config = Path(__file__).parent / 'config.yaml'
    searched_locations.append(str(script_config))
    if script_config.exists():
        return script_config

    # 4. System-wide location
    system_config = Path('/etc/honeybadger/config.yaml')
    searched_locations.append(str(system_config))
    if system_config.exists():
        return system_config

    # No config found anywhere
    logger.error("Configuration file not found in any location")
    logger.error("Searched locations:")
    for location in searched_locations:
        logger.error(f"  - {location}")
    exit(1)


def main():
    """Main entry point"""
    global VALID_TOKENS, DASHBOARD_PASSWORD

    try:
        # Parse command line arguments
        args = parse_arguments()

        # Find configuration file
        config_path = find_config_file(args.config)

        # Load configuration
        config = Config(str(config_path))

        # Load authentication credentials before starting server
        try:
            logger.info("Loading authentication credentials...")
            VALID_TOKENS = load_token_file(args.token_file)
            DASHBOARD_PASSWORD = load_password_file(args.dashboard_password_file)
            logger.info(f"Loaded {len(VALID_TOKENS)} token(s) and dashboard password")
        except FileNotFoundError as e:
            logger.error(str(e))
            logger.error("Please check that the file exists and the path is correct")
            return 1
        except PermissionError as e:
            logger.error(str(e))
            logger.error("Please check file permissions")
            return 1
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML syntax in token file: {e}")
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                logger.error(f"Error at line {mark.line + 1}, column {mark.column + 1}")
            return 1
        except ValueError as e:
            logger.error(f"Authentication file validation error: {e}")
            return 1

        # Start server
        run_server(config)

    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML syntax in configuration file: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Configuration validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
