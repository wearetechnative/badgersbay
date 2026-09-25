#!/usr/bin/env python3
"""End-to-end tests for reading the audit's findings from asset-inventory.json.

Run with:

    python3 -m unittest test_asset_inventory -v

Each test starts a real server on an ephemeral port against a throwaway
storage directory and a throwaway register, and submits real archives over
HTTP. The point is not to exercise the functions in isolation - the doctests
in honeybadger_server.py do that - but to show that a submission from the
current client arrives, is stored, and reaches the fleet view.

The archive in test-archive-current-client.tar.gz was produced by the
honeybadger client, not written by hand: its asset-inventory.json comes from
the client's own generator run against its own output directory.
"""

import io
import json
import logging
import os
import re
import shutil
import tarfile
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from base64 import b64encode
from http.server import HTTPServer
from pathlib import Path

import honeybadger_server as hb

HERE = Path(__file__).resolve().parent
REAL_ARCHIVE = HERE / 'test-archive-current-client.tar.gz'
REAL_INVENTORY = HERE / 'test-asset-inventory.json'

# The serial inside the real archive, and the register row that claims it.
REAL_SERIAL = 'PF50L2MR'
REAL_ASSET_ID = 'TARI-00023'

REGISTER_CSV = (
    'asset_id,serial,owner,model,class,status,owner_since,valid_from,valid_to,'
    'departure_reason\n'
    f'{REAL_ASSET_ID},{REAL_SERIAL},Wouter van der Toorren,LENOVO 21K9CTO1WW,'
    'linux,active,2024-01-01,2024-01-01,,\n'
    'TARI-00099,NOSUCHSERIAL,Never Submitted,Some Laptop,'
    'linux,active,2024-01-01,2024-01-01,,\n'
)

TOKEN = 'test-token'
PASSWORD = 'test-password'


def repack(members):
    """Build a tar.gz from {archive path: bytes}."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        for name, payload in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))
    return buffer.getvalue()


def real_archive_members():
    """The real archive's members, as {archive path: bytes}."""
    members = {}
    with tarfile.open(REAL_ARCHIVE, 'r:gz') as tar:
        for info in tar.getmembers():
            if not info.isfile():
                continue
            members[info.name] = tar.extractfile(info).read()
    return members


class ServerHarness(unittest.TestCase):
    """A real server, a throwaway storage tree, and a real register."""

    def setUp(self):
        # The server is chatty by design; the tests that care about a log line
        # raise the level themselves via assertLogs.
        previous_level = hb.logger.level
        hb.logger.setLevel(logging.ERROR)
        self.addCleanup(hb.logger.setLevel, previous_level)

        self.workdir = Path(tempfile.mkdtemp(prefix='badgersbay-test-'))
        self.addCleanup(shutil.rmtree, self.workdir, ignore_errors=True)

        register_path = self.workdir / 'assets.csv'
        register_path.write_text(REGISTER_CSV)

        config_path = self.workdir / 'config.yaml'
        config_path.write_text(
            'networkport: 0\n'
            f'storage_location: {self.workdir / "reports"}\n'
            'compliance:\n'
            '  enabled: true\n'
            '  audit_months: [3, 9]\n'
            f'  asset_register: {register_path}\n'
            '  grace_weeks: 4\n'
            '  required_reports:\n'
            '    mandatory:\n'
            '      - fastfetch\n'
            '      - lynis\n'
            '    one_of: []\n'
        )

        config = hb.Config(str(config_path))
        register = hb.AssetRegister(config.asset_register_path,
                                    state_dir=self.workdir)
        register.load()

        cache = hb.ComplianceCache(config)
        cache.rebuild()

        hb.VALID_TOKENS = [TOKEN]
        hb.DASHBOARD_PASSWORD = PASSWORD

        hb.ReportHandler.config = config
        hb.ReportHandler.asset_register = register
        hb.ReportHandler.compliance_cache = cache
        hb.ReportHandler.exception_store = hb.ExceptionStore(config.storage_location)
        hb.ReportHandler.exception_store.rebuild()
        hb.ReportHandler.start_time = None

        self.config = config
        self.cache = cache
        self.storage = Path(config.storage_location)

        self.httpd = HTTPServer(('127.0.0.1', 0), hb.ReportHandler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)

    # -- helpers ---------------------------------------------------------

    def submit(self, tar_bytes, hostname='lobos', username='wtoorren'):
        """POST an archive, returning (status_code, parsed_body)."""
        request = urllib.request.Request(
            f'http://127.0.0.1:{self.port}/submit-tar',
            data=tar_bytes,
            headers={
                'Authorization': f'Bearer {TOKEN}',
                'X-Hostname': hostname,
                'X-Username': username,
                'Content-Type': 'application/octet-stream',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            body = error.read()
            try:
                return error.code, json.loads(body)
            except ValueError:
                return error.code, {'raw': body.decode('utf-8', 'replace')}

    def fleet_html(self):
        """Fetch the fleet view as a dashboard user would."""
        credentials = b64encode(f'admin:{PASSWORD}'.encode()).decode()
        request = urllib.request.Request(
            f'http://127.0.0.1:{self.port}/?view=fleet',
            headers={'Authorization': f'Basic {credentials}'},
        )
        with urllib.request.urlopen(request) as response:
            return response.read().decode()

    def round_html(self, period=None):
        """Fetch the round view as a dashboard user would."""
        credentials = b64encode(f'admin:{PASSWORD}'.encode()).decode()
        query = f'?period={period}' if period else '/'
        request = urllib.request.Request(
            f'http://127.0.0.1:{self.port}/{query}',
            headers={'Authorization': f'Basic {credentials}'},
        )
        with urllib.request.urlopen(request) as response:
            return response.read().decode()

    def view_html(self, view, period=None):
        """Fetch one view for one round, as a dashboard user would."""
        credentials = b64encode(f'admin:{PASSWORD}'.encode()).decode()
        query = f'?view={view}' + (f'&period={period}' if period else '')
        request = urllib.request.Request(
            f'http://127.0.0.1:{self.port}/{query}',
            headers={'Authorization': f'Basic {credentials}'},
        )
        with urllib.request.urlopen(request) as response:
            return response.read().decode()

    def evidence_url(self, *segments):
        return 'http://127.0.0.1:{}/evidence/{}'.format(
            self.port, '/'.join(segments))

    def download(self, *segments):
        """Fetch one evidence file, returning (Content-Disposition, bytes).

        Three segments are the serial-keyed form; four name the tree.
        """
        credentials = b64encode(f'admin:{PASSWORD}'.encode()).decode()
        request = urllib.request.Request(
            self.evidence_url(*segments),
            headers={'Authorization': f'Basic {credentials}'})
        with urllib.request.urlopen(request) as response:
            return response.headers.get('Content-Disposition'), response.read()

    def download_status(self, *segments):
        """The status code the evidence route answers a path with."""
        credentials = b64encode(f'admin:{PASSWORD}'.encode()).decode()
        request = urllib.request.Request(
            self.evidence_url(*segments),
            headers={'Authorization': f'Basic {credentials}'})
        try:
            with urllib.request.urlopen(request) as response:
                return response.status
        except urllib.error.HTTPError as error:
            error.read()
            return error.code

    def unmatched_records(self):
        """Every submission.json written under the unmatched tree."""
        return sorted((self.storage / 'unmatched').rglob('submission.json'))

    def health(self):
        """Fetch /health, which takes no authentication."""
        with urllib.request.urlopen(
                f'http://127.0.0.1:{self.port}/health') as response:
            return json.loads(response.read())

    def records(self):
        """Every submission.json written under the serial-keyed tree."""
        return sorted((self.storage / 'submissions').rglob('submission.json'))

    def only_record(self):
        paths = self.records()
        self.assertEqual(len(paths), 1, f"expected one record, got {paths}")
        return json.loads(paths[0].read_text())


class TestRealArchive(ServerHarness):
    """A submission from the current client, end to end."""

    def test_answers_200_with_no_unrecognised_member(self):
        """The regression this change fixes: asset-inventory.json was a 207."""
        status, body = self.submit(REAL_ARCHIVE.read_bytes())
        self.assertEqual(status, 200, body)
        self.assertEqual(body['unrecognised'], [])
        self.assertEqual(body['asset_id'], REAL_ASSET_ID)
        self.assertTrue(body['inventory'])

    def test_findings_reach_the_record(self):
        self.submit(REAL_ARCHIVE.read_bytes())
        record = self.only_record()

        inventory = record['inventory']
        # The captured archive's own generation, not whatever the server
        # constant happens to be. Tying the two together would make this
        # assertion pass by definition and hide the case it exists for: the
        # client runs ahead of the server, so a real submission is routinely
        # a generation the server was not written against.
        self.assertEqual(inventory['schema_version'], 1)
        self.assertEqual(inventory['platform'], 'linux')

        findings = inventory['findings']
        self.assertEqual(findings['disk_encryption']['value'], 'Yes')
        self.assertEqual(findings['disk_encryption']['finding'], 'Yes (LUKS)')
        self.assertEqual(findings['hardening_score']['value'], 72)
        self.assertEqual(findings['hardening_score']['tool'], 'lynis')
        self.assertEqual(findings['screen_lock']['value'], 'Yes')
        self.assertEqual(findings['firewall']['value'], 'Yes')
        self.assertEqual(findings['os_uptodate']['value'], 'Yes')

    def test_the_whole_document_is_kept(self):
        """Fields the server does not model must survive the trip."""
        self.submit(REAL_ARCHIVE.read_bytes())
        record = self.only_record()

        raw = record['inventory_raw']
        self.assertEqual(raw, json.loads(REAL_INVENTORY.read_text()))
        # identity and vulnerable_packages have no column, and are kept anyway
        self.assertEqual(raw['identity']['serial'], REAL_SERIAL)
        self.assertIn('vulnerable_packages', raw['findings'])
        self.assertIn('vulnerable_packages', record['inventory']['findings'])

    def test_stored_beside_the_reports_and_downloadable(self):
        self.submit(REAL_ARCHIVE.read_bytes())
        record_dir = self.records()[0].parent
        stored = record_dir / hb.ASSET_INVENTORY_FILENAME
        self.assertTrue(stored.is_file())

        credentials = b64encode(f'admin:{PASSWORD}'.encode()).decode()
        url = (f'http://127.0.0.1:{self.port}/evidence/{REAL_SERIAL}/'
               f'{record_dir.name}/{hb.ASSET_INVENTORY_FILENAME}')
        request = urllib.request.Request(
            url, headers={'Authorization': f'Basic {credentials}'})
        with urllib.request.urlopen(request) as response:
            self.assertEqual(json.loads(response.read())['schema_version'], 1)

    def test_the_inventory_is_not_a_report(self):
        """It must never enter the report set, or completeness would move."""
        status, body = self.submit(REAL_ARCHIVE.read_bytes())
        self.assertEqual(status, 200, body)
        self.assertEqual(sorted(self.only_record()['reports']),
                         ['fastfetch', 'lynis'])
        self.assertNotIn('asset-inventory',
                         [r['report_type'] for r in body['reports_saved']])
        self.assertIsNone(hb.ReportHandler.detect_report_type_from_filename(
            hb.ReportHandler, 'output-x/asset-inventory.json'))

    def test_findings_reach_the_fleet_view(self):
        self.submit(REAL_ARCHIVE.read_bytes())
        self.cache.rebuild()
        html = self.fleet_html()

        for _, label in hb.INVENTORY_COLUMNS:
            self.assertIn(f'>{label}<', html)
        # The value, and the finding it came from, both on the row
        self.assertIn('title="Yes (LUKS)"', html)
        self.assertIn('title="Yes (auto-lock: 5 minutes)"', html)
        # Dutch, because the 0.4.1 client that made this archive wrote its
        # findings in Dutch. The server shows a finding as it arrived.
        self.assertIn('title="72/100 - drempel &gt;=65 gehaald"', html)
        self.assertIn('>72<', html)

    def test_a_counted_finding_shows_its_number(self):
        """A finding that measures without judging still reports a number.

        The client counts vulnerable packages but asserts no value for them,
        because the register contradicts itself about which literal means
        compliant. The count is the measurement; the verdict is nobody's to
        add here.
        """
        members = real_archive_members()
        document = json.loads(REAL_INVENTORY.read_text())
        document['schema_version'] = 2
        document['findings']['vulnerable_packages'] = {
            'value': None,
            'count': 3,
            'finding': '3 vulnerable packages found',
        }
        for name in list(members):
            if name.endswith(hb.ASSET_INVENTORY_FILENAME):
                members[name] = json.dumps(document).encode()

        status, body = self.submit(repack(members))
        self.assertEqual(status, 200, body)
        self.cache.rebuild()

        html = self.fleet_html()
        row = html.split(REAL_ASSET_ID, 1)[1].split('</tr>', 1)[0]
        cell = row.split('<td class="fnd">')[-1]
        self.assertIn('title="3 vulnerable packages found"', cell)
        self.assertIn('>3<', cell)
        self.assertNotIn('unknown', cell)
        # and no verdict of the dashboard's own
        for verdict_class in ('p-ok', 'p-open', 'p-exc'):
            self.assertNotIn(verdict_class, row)

    def test_a_finding_with_neither_value_nor_count_reads_unknown(self):
        """The captured archive predates the count: nothing is invented."""
        self.submit(REAL_ARCHIVE.read_bytes())
        self.cache.rebuild()

        row = self.fleet_html().split(REAL_ASSET_ID, 1)[1].split('</tr>', 1)[0]
        # The column's own cell, not merely somewhere on the row: an
        # unqualified search would pass on any other column reading unknown.
        cell = row.split('<td class="fnd">')[-1]
        self.assertIn('unknown', cell)
        self.assertIn('geen package audit tool aanwezig', cell)

    def test_the_view_adds_no_verdict(self):
        """No finding cell may be coloured as a pass or a failure."""
        self.submit(REAL_ARCHIVE.read_bytes())
        self.cache.rebuild()
        html = self.fleet_html()

        row = html.split(REAL_ASSET_ID, 1)[1].split('</tr>', 1)[0]
        for verdict_class in ('p-ok', 'p-open', 'p-exc', 'd-fresh', 'd-stale'):
            for cell in row.split('<td class="fnd">')[1:]:
                self.assertNotIn(verdict_class, cell)


class TestCompletenessUnaffected(ServerHarness):
    """Criterion 5: an older client must not become incomplete."""

    def test_complete_with_and_without_an_inventory(self):
        members = real_archive_members()
        without = {name: payload for name, payload in members.items()
                   if not name.endswith(hb.ASSET_INVENTORY_FILENAME)}

        status, body = self.submit(repack(without))
        self.assertEqual(status, 200, body)
        self.assertFalse(body['inventory'])

        record = self.only_record()
        self.assertIsNone(record['inventory'])
        self.assertIsNone(record['inventory_raw'])

        complete, missing = hb.evaluate_completeness('linux', record['reports'])
        self.assertTrue(complete)
        self.assertEqual(missing, [])

    def test_requirements_never_mention_the_inventory(self):
        for asset_class in hb.VALID_ASSET_CLASSES:
            for accepted in hb.requirements_for_class(asset_class).values():
                self.assertNotIn('asset-inventory', accepted)
                self.assertNotIn('inventory', accepted)

    def test_an_asset_without_an_inventory_reads_as_unknown(self):
        members = real_archive_members()
        without = {name: payload for name, payload in members.items()
                   if not name.endswith(hb.ASSET_INVENTORY_FILENAME)}
        self.submit(repack(without))
        self.cache.rebuild()

        html = self.fleet_html()
        row = html.split(REAL_ASSET_ID, 1)[1].split('</tr>', 1)[0]
        cells = row.split('<td class="fnd">')[1:]
        self.assertEqual(len(cells), len(hb.INVENTORY_COLUMNS))
        for cell in cells:
            self.assertIn('unknown', cell)
        # unknown, not a failure: the row keeps the state its coverage earned
        self.assertNotIn('s-open', row)

    def test_a_never_seen_asset_reads_as_unknown(self):
        """The register row with no submission at all."""
        html = self.fleet_html()
        row = html.split('TARI-00099', 1)[1].split('</tr>', 1)[0]
        cells = row.split('<td class="fnd">')[1:]
        self.assertEqual(len(cells), len(hb.INVENTORY_COLUMNS))
        for cell in cells:
            self.assertIn('unknown', cell)


class TestDeclinedValue(ServerHarness):
    """Criterion 3: a null value reads as unknown with the client's reason."""

    def test_reason_is_shown_and_available_on_the_row(self):
        members = real_archive_members()
        document = json.loads(REAL_INVENTORY.read_text())
        document['findings']['screen_lock'] = {
            'value': None,
            'finding': 'not determined - no session information available',
        }
        for name in list(members):
            if name.endswith(hb.ASSET_INVENTORY_FILENAME):
                members[name] = json.dumps(document).encode()

        status, _ = self.submit(repack(members))
        self.assertEqual(status, 200)
        self.cache.rebuild()

        record = self.only_record()
        self.assertIsNone(record['inventory']['findings']['screen_lock']['value'])

        html = self.fleet_html()
        row = html.split(REAL_ASSET_ID, 1)[1].split('</tr>', 1)[0]
        self.assertIn('not determined - no session information available', row)
        self.assertIn('unknown', row)

    def test_unknown_with_a_reason_is_not_blank(self):
        text, reason, known = hb.inventory_cell(
            {'findings': {'firewall': {'value': None, 'finding': 'no tool'}}},
            'firewall')
        self.assertEqual((text, reason, known), ('unknown', 'no tool', False))


class TestUnknownSchemaVersion(ServerHarness):
    """Criterion 6: an unrecognised generation is kept, not refused."""

    def test_stored_and_rendered_for_what_is_understood(self):
        members = real_archive_members()
        document = json.loads(REAL_INVENTORY.read_text())
        document['schema_version'] = 99
        document['findings']['something_new'] = {'value': 'Maybe',
                                                 'finding': 'from the future'}
        for name in list(members):
            if name.endswith(hb.ASSET_INVENTORY_FILENAME):
                members[name] = json.dumps(document).encode()

        status, body = self.submit(repack(members))
        self.assertEqual(status, 200, body)
        self.cache.rebuild()

        record = self.only_record()
        self.assertEqual(record['inventory']['schema_version'], 99)
        self.assertEqual(record['inventory_raw']['schema_version'], 99)
        # the unmodelled field survives rather than being dropped at the door
        self.assertEqual(
            record['inventory']['findings']['something_new']['value'], 'Maybe')

        html = self.fleet_html()
        self.assertIn('title="Yes (LUKS)"', html)
        self.assertIn('>72<', html)


class TestMalformedInventory(ServerHarness):
    """Criterion 7: logged and skipped, never fatal to the submission."""

    def test_submission_is_stored_regardless(self):
        members = real_archive_members()
        for name in list(members):
            if name.endswith(hb.ASSET_INVENTORY_FILENAME):
                members[name] = b'{"schema_version": 1, "findings": {'

        with self.assertLogs(hb.logger, level='WARNING') as captured:
            status, body = self.submit(repack(members))

        self.assertIn(status, (200, 207))
        self.assertTrue(any('asset inventory' in line.lower()
                            for line in captured.output), captured.output)

        record = self.only_record()
        self.assertIsNone(record['inventory'])
        self.assertEqual(sorted(record['reports']), ['fastfetch', 'lynis'])
        self.assertEqual(record['asset_id'], REAL_ASSET_ID)
        self.assertTrue((self.records()[0].parent / record['evidence']).is_file())

        # and the fleet view still renders, reading unknown for the columns
        self.cache.rebuild()
        row = self.fleet_html().split(REAL_ASSET_ID, 1)[1].split('</tr>', 1)[0]
        self.assertEqual(len(row.split('<td class="fnd">')) - 1,
                         len(hb.INVENTORY_COLUMNS))

    def test_a_document_with_no_findings_is_kept_whole(self):
        members = real_archive_members()
        for name in list(members):
            if name.endswith(hb.ASSET_INVENTORY_FILENAME):
                members[name] = json.dumps({'schema_version': 1,
                                            'note': 'no findings here'}).encode()

        status, body = self.submit(repack(members))
        self.assertEqual(status, 200, body)

        record = self.only_record()
        self.assertIsNone(record['inventory'])
        self.assertEqual(record['inventory_raw']['note'], 'no findings here')


class TestHealthCountsWhatTheServerReads(ServerHarness):
    """/health reported zero on a server that was receiving submissions.

    It walked one of two layouts chosen by a configuration flag, and the
    serial-keyed tree the server actually writes was in neither.
    """

    def test_a_real_submission_is_counted(self):
        self.submit(REAL_ARCHIVE.read_bytes())

        stats = self.health()['statistics']
        self.assertEqual(stats['total_report_directories'], 1)
        self.assertEqual(stats['by_source']['matched'], 1)
        self.assertEqual(stats['reports_by_type']['lynis'], 1)
        self.assertEqual(stats['reports_by_type']['fastfetch'], 1)

    def test_the_hostname_comes_from_the_record(self):
        self.submit(REAL_ARCHIVE.read_bytes(), hostname='lobos')

        self.assertEqual(self.health()['statistics']['unique_hosts'], 1)

    def test_an_unmatched_submission_is_counted_and_named(self):
        """A machine scanning without being credited is the interesting case."""
        members = real_archive_members()
        for name in list(members):
            if name.endswith('hardware-serial.txt'):
                members[name] = b'SERIALNOTINREGISTER\n'

        self.submit(repack(members), hostname='stranger')

        stats = self.health()['statistics']
        self.assertEqual(stats['total_report_directories'], 1)
        self.assertEqual(stats['by_source']['unmatched'], 1)
        self.assertEqual(stats['by_source']['matched'], 0)

    def test_archive_period_directories_are_still_counted(self):
        """Fixing one blind spot must not open another."""
        archived = self.storage / '2026-03' / 'oldhost-olduser'
        archived.mkdir(parents=True)
        (archived / 'lynis-report.json').write_text('{}')

        stats = self.health()['statistics']
        self.assertEqual(stats['total_report_directories'], 1)
        self.assertEqual(stats['by_source']['archived'], 1)
        self.assertEqual(stats['unique_hosts'], 1)
        self.assertEqual(stats['reports_by_type']['lynis'], 1)

    def test_an_empty_tree_reports_zero(self):
        stats = self.health()['statistics']
        self.assertEqual(stats['total_report_directories'], 0)
        self.assertEqual(stats['by_source'],
                         {'matched': 0, 'unmatched': 0, 'archived': 0})


class TestDownloadsAreNamedForTheirAsset(ServerHarness):
    """A report named for itself carries the same name on every asset.

    Downloading two assets into one folder overwrote one with the other, and a
    file called lynis-report.json has to be renamed by hand before it is
    evidence of anything.
    """

    def test_a_report_names_the_asset_and_the_round(self):
        self.submit(REAL_ARCHIVE.read_bytes())
        record_dir = self.records()[0].parent

        disposition, _ = self.download(
            REAL_SERIAL, record_dir.name, 'lynis-report.json')

        self.assertIn(REAL_ASSET_ID, disposition)
        self.assertIn('-lynis.json', disposition)
        self.assertNotIn('"lynis-report.json"', disposition)

    def test_the_archive_keeps_its_convention(self):
        """The one file that was already right must stay right."""
        self.submit(REAL_ARCHIVE.read_bytes())
        record_dir = self.records()[0].parent
        archive = next(record_dir.glob('*.tar.gz'))

        disposition, _ = self.download(
            REAL_SERIAL, record_dir.name, archive.name)

        self.assertIn(REAL_ASSET_ID, disposition)
        self.assertIn('.tar.gz', disposition)
        self.assertNotIn('-lynis', disposition)

    def test_two_assets_do_not_collide(self):
        """The regression: both used to arrive as lynis-report.json.

        Asserted on the naming itself rather than end to end, because the
        evidence route serves only registered assets - a second asset would
        need a second register entry, and the collision is a property of the
        name.
        """
        first = hb.evidence_download_name('lynis-report.json', {
            'asset_id': 'TARI-00023', 'owner': 'Wouter van der Toorren',
            'submitted_at': '2026-09-17T09:00:00'})
        second = hb.evidence_download_name('lynis-report.json', {
            'asset_id': 'TARI-00030', 'owner': 'Bas Anneveld',
            'submitted_at': '2026-09-17T09:00:00'})

        self.assertNotEqual(first, second)
        self.assertNotIn('lynis-report.json', (first, second))


class TestUnmatchedEvidenceIsReachable(ServerHarness):
    """A machine that scanned and was credited to nobody had no URL.

    The round view names two reasons - the client could not read the hardware,
    or the register is behind - and both are settled by opening what the
    machine sent. The route resolved under the serial-keyed tree only, so that
    was the one thing nobody could do.
    """

    def submit_unmatched(self, serial=b'SERIALNOTINREGISTER\n', hostname='stranger'):
        """Submit the real archive under a serial no register row claims."""
        members = real_archive_members()
        for name in list(members):
            if name.endswith('hardware-serial.txt'):
                if serial is None:
                    del members[name]
                else:
                    members[name] = serial
        status, body = self.submit(repack(members), hostname=hostname)
        record = json.loads(self.unmatched_records()[0].read_text())
        return status, body, record

    def unmatched_dir(self):
        paths = self.unmatched_records()
        self.assertEqual(len(paths), 1, f"expected one record, got {paths}")
        return paths[0].parent

    def test_an_unmatched_report_downloads(self):
        self.submit_unmatched()
        record_dir = self.unmatched_dir()

        disposition, payload = self.download(
            'unmatched', record_dir.parent.name, record_dir.name,
            'lynis-report.json')

        self.assertTrue(payload)
        self.assertIn('SERIALNOTINREGISTER', disposition)
        self.assertIn('-lynis.json', disposition)

    def test_the_archive_downloads_too(self):
        """The tar is the whole of what arrived, so it is the file wanted."""
        self.submit_unmatched()
        record_dir = self.unmatched_dir()
        archive = next(record_dir.glob('*.tar.gz'))

        disposition, payload = self.download(
            'unmatched', record_dir.parent.name, record_dir.name, archive.name)

        self.assertEqual(payload, (record_dir / archive.name).read_bytes())
        self.assertIn('.tar.gz', disposition)

    def test_a_submission_with_no_serial_is_named_for_its_host(self):
        """The reason the register cannot help: there is nothing to look up."""
        _, _, record = self.submit_unmatched(serial=None, hostname='lobos')
        self.assertEqual(record['unmatched_reason'], 'no_serial')
        record_dir = self.unmatched_dir()

        disposition, _ = self.download(
            'unmatched', record_dir.parent.name, record_dir.name,
            'lynis-report.json')

        self.assertIn('lobos-wtoorren', disposition)
        self.assertNotIn('"lynis-report.json"', disposition)

    def test_the_round_view_links_it_beside_the_reason(self):
        self.submit_unmatched()
        record_dir = self.unmatched_dir()

        html = self.round_html()

        href = (f'/evidence/unmatched/{record_dir.parent.name}/'
                f'{record_dir.name}/lynis-report.json')
        self.assertIn(href, html)
        self.assertIn('serial not in register', html)
        # The link is inside the block for the reason, not loose on the page.
        block = html.split('serial not in register', 1)[1]
        self.assertIn(href, block.split('</div></div>', 1)[0])

    def test_the_matched_link_is_the_tree_form_too(self):
        """One shape for both trees; the record's own path is what names it."""
        self.submit(REAL_ARCHIVE.read_bytes())
        record_dir = self.records()[0].parent

        html = self.round_html()

        self.assertIn(
            f'/evidence/submissions/{REAL_SERIAL}/{record_dir.name}/'
            'lynis-report.json', html)


class TestEvidenceRouteRefusesWhatItDoesNotServe(ServerHarness):
    """Serving a second tree must not turn the route into a file browser."""

    def test_the_three_segment_form_still_serves_a_matched_record(self):
        """Links already filed in a compliance sheet keep working."""
        self.submit(REAL_ARCHIVE.read_bytes())
        record_dir = self.records()[0].parent

        disposition, payload = self.download(
            REAL_SERIAL, record_dir.name, 'lynis-report.json')

        self.assertTrue(payload)
        self.assertIn(REAL_ASSET_ID, disposition)

    def test_the_period_archive_is_not_served(self):
        """It is history the server reads and never writes."""
        archived = self.storage / '2026-03' / 'oldhost-olduser'
        archived.mkdir(parents=True)
        (archived / 'lynis-report.json').write_text('{}')

        self.assertEqual(
            self.download_status('2026-03', 'oldhost-olduser',
                                 'x', 'lynis-report.json'),
            400)

    def test_a_climbing_path_is_refused(self):
        self.assertEqual(
            self.download_status('unmatched', 'lobos-wtoorren', '..',
                                 'submission.json'),
            400)
        self.assertEqual(self.download_status('..', 'etc', 'passwd'), 400)

    def test_a_missing_record_is_not_found_rather_than_refused(self):
        self.assertEqual(
            self.download_status('unmatched', 'nobody-nowhere',
                                 '2026-09-17T09-00-00', 'lynis-report.json'),
            404)


class TestEarlierRoundsAreReachable(ServerHarness):
    """A closed round is what an auditor asks about, and it had no affordance.

    The routing already honoured ?period=; what was missing was a way to get
    there without knowing the URL scheme.
    """

    def test_the_selector_is_on_both_views(self):
        self.submit(REAL_ARCHIVE.read_bytes())
        self.cache.rebuild()

        for view in ('round', 'fleet'):
            html = self.view_html(view)
            self.assertIn('class="rounds"', html, f'missing on {view}')
            self.assertIn('name="period"', html)

    def test_it_carries_the_view_so_the_tab_survives(self):
        """Changing the round on the fleet view must not drop you elsewhere."""
        self.submit(REAL_ARCHIVE.read_bytes())
        self.cache.rebuild()

        html = self.view_html('fleet')
        form = html.split('class="rounds"', 1)[1].split('</form>', 1)[0]
        self.assertIn('name="view" value="fleet"', form)

    def test_the_round_being_viewed_is_marked_and_offered(self):
        """Even when nothing has been submitted to it."""
        html = self.view_html('round', '2099-03')

        form = html.split('class="rounds"', 1)[1].split('</form>', 1)[0]
        self.assertIn('<option value="2099-03" selected>', form)

    def test_a_round_nobody_submitted_to_renders(self):
        """An empty round is a finding, not an error."""
        self.submit(REAL_ARCHIVE.read_bytes())
        self.cache.rebuild()

        html = self.view_html('round', '2099-03')

        self.assertIn('2099-03', html)
        self.assertNotIn('Internal server error', html)

    def test_selecting_a_round_reaches_it(self):
        self.submit(REAL_ARCHIVE.read_bytes())
        self.cache.rebuild()

        html = self.view_html('round', '2026-03')

        self.assertIn('Audit round <strong class="mono">2026-03</strong>', html)

    def test_a_closed_round_keeps_its_own_denominator(self):
        """The property that makes a historical figure stable.

        in_scope() takes the round's window, so an asset issued after a round
        is absent from it however the register grows afterwards. A regression
        here rewrites the past quietly, which is why it is pinned even though
        no code in this change touches it.

        Built on its own register rather than the harness one, whose rows are
        all valid from 2024 - against those, any assertion about scoping would
        pass by construction.
        """
        csv = self.storage / 'historical.csv'
        csv.parent.mkdir(parents=True, exist_ok=True)
        csv.write_text(
            'asset_id,serial,owner,model,class,status,owner_since,valid_from,'
            'valid_to,departure_reason\n'
            'TARI-00001,OLDONE,Long Serving,Laptop,linux,active,'
            '2024-01-01,2024-01-01,,\n'
            'TARI-00002,NEWONE,Joined Later,Laptop,linux,active,'
            '2026-08-10,2026-08-10,,\n'
            'TARI-00003,GONEONE,Left Us,Laptop,linux,active,'
            '2024-01-01,2024-01-01,2026-05-01,returned on leaving\n'
        )
        register = hb.AssetRegister(str(csv))
        register.load()

        march = hb.get_round_windows('2026-03', [3, 9], 4)
        september = hb.get_round_windows('2026-09', [3, 9], 4)
        in_march = {e['asset_id'] for e in register.in_scope(march[0], march[1])}
        in_september = {e['asset_id']
                        for e in register.in_scope(september[0], september[1])}

        # Issued in August: absent from the March round, present in September.
        self.assertNotIn('TARI-00002', in_march)
        self.assertIn('TARI-00002', in_september)

        # Left in May: still counted in the round it belonged to, gone from the
        # one after it. A departure must not erase the round it was part of.
        self.assertIn('TARI-00003', in_march)
        self.assertNotIn('TARI-00003', in_september)

        self.assertIn('TARI-00001', in_march)
        self.assertIn('TARI-00001', in_september)


# A register with enough shape to filter: two owners, three classes, an asset
# that left scope with a reason, a retired one, and a serial written with the
# separator the ISO tool uses so that searching for it without one has
# something to fail on.
FILTER_REGISTER_CSV = (
    'asset_id,serial,owner,model,class,status,owner_since,valid_from,valid_to,'
    'departure_reason\n'
    f'{REAL_ASSET_ID},{REAL_SERIAL},Wouter van der Toorren,LENOVO 21K9CTO1WW,'
    'linux,active,2024-01-01,2024-01-01,,\n'
    'TARI-00031,MP1Y-69AC,Pim Snel,MacBook Pro,macos,active,'
    '2024-01-01,2024-01-01,,\n'
    'TARI-00042,WINBOX01,Pim Snel,ThinkPad,windows,active,'
    '2024-01-01,2024-01-01,,\n'
    'TARI-00055,LEFTONE1,Richard van Os,Laptop,linux,active,'
    '2024-01-01,2024-01-01,2026-09-10,returned on leaving\n'
    'TARI-00066,GONEONE1,Richard van Os,Laptop,linux,retired,'
    '2024-01-01,2024-01-01,2025-01-01,end of life\n'
    'TARI-00099,NOSUCHSERIAL,Never Submitted,Some Laptop,linux,active,'
    '2024-01-01,2024-01-01,,\n'
)


class TestFilteringTheRoundView(ServerHarness):
    """Narrowing the round table without moving the round's figures.

    The register here is the harness one widened until every bucket the table
    builds has something in it, so that a filter has something to remove.
    """

    def setUp(self):
        super().setUp()
        csv_path = self.workdir / 'filter-assets.csv'
        csv_path.write_text(FILTER_REGISTER_CSV)
        register = hb.AssetRegister(str(csv_path))
        register.load()
        hb.ReportHandler.asset_register = register
        self.register = register

        self.submit(REAL_ARCHIVE.read_bytes())
        self.cache.rebuild()
        self.period = hb.get_audit_period(
            __import__('datetime').datetime.now(), self.config.audit_months)

    # -- helpers ---------------------------------------------------------

    def filtered_html(self, period=None, **terms):
        """The round view under one filter, as a dashboard user would see it."""
        from urllib.parse import urlencode
        params = [('view', 'round')]
        if period:
            params.append(('period', period))
        params += [(name, value) for name, value in terms.items()]
        credentials = b64encode(f'admin:{PASSWORD}'.encode()).decode()
        request = urllib.request.Request(
            f'http://127.0.0.1:{self.port}/?' + urlencode(params),
            headers={'Authorization': f'Basic {credentials}'},
        )
        with urllib.request.urlopen(request) as response:
            return response.read().decode()

    def assets_in_table(self, html):
        """The asset ids the per-asset table is showing."""
        table = html.split('<div class="tblwrap">', 1)
        if len(table) == 1:
            return set()
        return set(re.findall(r'<strong>(TARI-\d+)</strong>', table[1]))

    def figures(self, html):
        """The progress panel with only its navigation taken out.

        Every number stays - the headline, the meter widths, the key counts and
        each owner's tally. What goes is where the owner bars point and which
        one is marked, because those two are about the reader's view by design.
        Everything left is a statement about the round, and a filter that moved
        any of it would be putting a number on the page that depends on what
        the reader happened to be looking at.
        """
        self.assertIn('<div class="summary">', html)
        block = html.split('<div class="summary">', 1)[1].split('\n  </div>', 1)[0]
        self.assertIn('Progress', block)
        self.assertIn('By owner', block)
        return re.sub(r' href="[^"]*"', '', block).replace(' sel"', '"')

    def notice(self, html):
        """The filter notice, or '' when there is none."""
        if '<div class="alert filt">' not in html:
            return ''
        return html.split('<div class="alert filt">', 1)[1].split('</div>', 1)[0]

    # -- the acceptance criterion ----------------------------------------

    def test_the_figures_are_the_same_under_every_filter(self):
        """The reason this work needed stating rather than just doing.

        `1 of 6 assets scanned` is a compliance statement about the round. If a
        filter could recompute it, the number on the page would depend on what
        the reader was looking at - and somebody would eventually screenshot it
        into an audit file.
        """
        whole = self.figures(self.filtered_html())

        filters = [
            {'state': 'scanned'}, {'state': 'accounted'},
            {'state': 'outstanding'}, {'state': 'unexplained'},
            {'state': 'manual'}, {'state': 'retired'},
            {'owner': 'Pim Snel'}, {'owner': 'Never Submitted'},
            {'class': 'linux'}, {'class': 'windows'},
            {'q': 'TARI-00031'}, {'q': REAL_SERIAL},
            {'state': 'outstanding', 'owner': 'Pim Snel'},
            {'state': 'scanned', 'class': 'windows'},
        ]
        for terms in filters:
            with self.subTest(**terms):
                self.assertEqual(
                    self.figures(self.filtered_html(**terms)), whole,
                    f'the round\'s figures moved under {terms}')

    def test_the_headline_counts_the_round_not_the_view(self):
        """Stated separately, because it is the sentence people read."""
        whole = self.filtered_html()
        headline = re.search(r'of (\d+) assets scanned', whole).group(0)

        narrowed = self.filtered_html(state='outstanding', owner='Pim Snel')

        self.assertIn(headline, narrowed)
        self.assertEqual(self.assets_in_table(narrowed), {'TARI-00031'})

    def test_every_owner_stays_in_the_panel(self):
        """The panel is a call list for the round, not a legend for the table."""
        narrowed = self.filtered_html(owner='Pim Snel')

        for owner in ('Wouter van der Toorren', 'Pim Snel',
                      'Richard van Os', 'Never Submitted'):
            self.assertIn(owner, self.figures(narrowed))

    # -- narrowing -------------------------------------------------------

    def test_narrowing_by_state_shows_only_that_section(self):
        self.assertEqual(self.assets_in_table(self.filtered_html(state='scanned')),
                         {REAL_ASSET_ID})
        self.assertEqual(self.assets_in_table(self.filtered_html(state='manual')),
                         {'TARI-00042'})
        self.assertEqual(self.assets_in_table(self.filtered_html(state='retired')),
                         {'TARI-00066'})
        self.assertEqual(self.assets_in_table(self.filtered_html(state='outstanding')),
                         {'TARI-00031', 'TARI-00099'})

    def test_accounted_for_joins_the_exception_and_the_departure(self):
        """They read as one section in the table, so they are one state here.

        TARI-00055 left scope with a reason; TARI-00099 is excepted by an
        operator. Both are resolved without evidence.
        """
        hb.ReportHandler.exception_store.mark(
            'TARI-00099', self.period, 'no longer powered on', 'wtoorren')

        shown = self.assets_in_table(self.filtered_html(state='accounted'))

        self.assertEqual(shown, {'TARI-00055', 'TARI-00099'})

    def test_narrowing_by_owner(self):
        """Matched on the register's value, not on the proof-file slug."""
        shown = self.assets_in_table(self.filtered_html(owner='Pim Snel'))

        self.assertEqual(shown, {'TARI-00031', 'TARI-00042'})

    def test_owner_matching_ignores_case_but_not_identity(self):
        self.assertEqual(self.assets_in_table(self.filtered_html(owner='pim snel')),
                         {'TARI-00031', 'TARI-00042'})
        # owner_to_slug() would fold this to 'richard.os'; it is not identity.
        self.assertEqual(self.assets_in_table(self.filtered_html(owner='richard.os')),
                         set())

    def test_narrowing_by_class(self):
        """How somebody reads the part of the fleet that can submit today."""
        linux = self.assets_in_table(self.filtered_html(**{'class': 'linux'}))

        self.assertEqual(linux, {REAL_ASSET_ID, 'TARI-00055',
                                 'TARI-00066', 'TARI-00099'})
        self.assertNotIn('TARI-00042', linux)

    def test_terms_compose(self):
        both = self.assets_in_table(
            self.filtered_html(state='outstanding', **{'class': 'macos'}))

        self.assertEqual(both, {'TARI-00031'})

    # -- finding one asset ------------------------------------------------

    def test_find_by_asset_id_however_much_of_it_is_typed(self):
        for typed in ('TARI-00031', 'tari-00031', 'tari00031', '00031'):
            with self.subTest(typed=typed):
                self.assertEqual(self.assets_in_table(self.filtered_html(q=typed)),
                                 {'TARI-00031'})

    def test_find_by_serial_with_and_without_its_separators(self):
        """The register holds MP1Y-69AC; the machine reports MP1Y69AC.

        normalise_serial() uppercases and strips whitespace but leaves
        separators alone, so without folding them the two spellings are
        different strings and only one of them finds the asset.
        """
        for typed in ('MP1Y-69AC', 'MP1Y69AC', 'mp1y69ac'):
            with self.subTest(typed=typed):
                self.assertEqual(self.assets_in_table(self.filtered_html(q=typed)),
                                 {'TARI-00031'})

    def test_find_by_the_serial_of_a_scanned_asset(self):
        self.assertEqual(self.assets_in_table(self.filtered_html(q=REAL_SERIAL)),
                         {REAL_ASSET_ID})

    # -- saying what is hidden --------------------------------------------

    def test_the_notice_names_the_terms_and_the_hidden_count(self):
        html = self.filtered_html(state='outstanding', owner='Pim Snel')
        notice = self.notice(html)

        self.assertIn('outstanding', notice)
        self.assertIn('Pim Snel', notice)
        self.assertIn('Showing 1 of 6 listed assets', notice)
        self.assertIn('It hides 5.', notice)
        # The table's total and the round's denominator are different
        # numbers on purpose, and the notice has to say which is which.
        self.assertIn('is not the denominator above', notice)
        self.assertIn('of 4 assets scanned', html)

    def test_a_filter_matching_nothing_says_so_rather_than_reading_as_done(self):
        """An empty table under a filter and an empty round mean opposites."""
        html = self.filtered_html(owner='Nobody At All')

        self.assertIn('No assets match this filter', self.notice(html))
        self.assertEqual(self.assets_in_table(html), set())
        self.assertIn('No assets match this filter',
                      html.split('<div class="tblwrap">', 1)[1])
        self.assertNotIn('No assets in scope for this round', html)

    def test_a_filter_hiding_nothing_is_still_announced(self):
        """Or a shared address reads as the full picture."""
        every_state = '|'.join(key for key, _, _ in hb.ROUND_FILTER_STATES)
        self.assertTrue(every_state)  # the vocabulary exists to be complete

        html = self.filtered_html(q='TARI')

        self.assertNotEqual(self.notice(html), '')
        self.assertIn('It hides nothing', self.notice(html))

    def test_the_way_back_is_offered(self):
        html = self.filtered_html(state='outstanding')

        self.assertIn('Show the whole round', html)
        self.assertIn(f'/?view=round&amp;period={self.period}"', html)

    def test_no_notice_when_nothing_is_filtered(self):
        self.assertEqual(self.notice(self.filtered_html()), '')

    def test_an_unrecognised_state_is_reported_and_not_honoured(self):
        """A typo in an address should show the round, not an empty page."""
        html = self.filtered_html(state='outstandng')

        self.assertIn('Ignored an unrecognised state', html)
        self.assertEqual(self.notice(html), '')
        self.assertEqual(len(self.assets_in_table(html)), 6)

    # -- shareable ---------------------------------------------------------

    def test_the_address_carries_the_filter_and_the_control_shows_it(self):
        html = self.filtered_html(state='outstanding', owner='Pim Snel')
        form = html.split('<form class="filters"', 1)[1].split('</form>', 1)[0]

        self.assertIn('<option value="outstanding" selected>', form)
        self.assertIn('<option value="Pim Snel" selected>', form)

    def test_the_control_is_a_get_form_and_needs_no_scripting(self):
        """The legacy dashboard filtered by script and needed fixing twice."""
        html = self.filtered_html()
        form = html.split('<form class="filters"', 1)[1].split('</form>', 1)[0]

        self.assertIn('method="get"', form)
        self.assertNotIn('<script', html)
        self.assertNotIn('onchange', html)

    def test_a_filtered_link_to_a_closed_round(self):
        """The filter composes with the round, which the view already honours."""
        html = self.filtered_html(period='2026-03', state='outstanding')

        self.assertIn('Audit round <strong class="mono">2026-03</strong>', html)
        # Nothing was submitted in March, so everything active is outstanding.
        self.assertEqual(self.assets_in_table(html),
                         {REAL_ASSET_ID, 'TARI-00031', 'TARI-00055', 'TARI-00099'})

    def test_changing_the_round_keeps_the_filter(self):
        html = self.filtered_html(state='outstanding', owner='Pim Snel')
        selector = html.split('class="rounds"', 1)[1].split('</form>', 1)[0]

        self.assertIn('name="state" value="outstanding"', selector)
        self.assertIn('name="owner" value="Pim Snel"', selector)

    # -- the owner bars ----------------------------------------------------

    def test_the_owner_bars_link_to_that_owner(self):
        """They already look pressable and already carry the count."""
        panel = self.filtered_html().split('class="owners"', 1)[1]

        self.assertIn('owner=Pim+Snel', panel)
        self.assertIn('owner=Richard+van+Os', panel)

    def test_an_owner_bar_keeps_the_other_terms(self):
        panel = self.filtered_html(state='outstanding').split('class="owners"', 1)[1]

        self.assertIn('state=outstanding&amp;owner=Pim+Snel', panel)

    def test_the_owner_being_shown_is_marked(self):
        panel = self.filtered_html(owner='Pim Snel').split('class="owners"', 1)[1]

        marked = re.findall(r'class="owner [^"]*sel"[^>]*>\s*<span class="nm">([^<]*)',
                            panel)
        self.assertEqual(marked, ['Pim Snel'])


class TestNotesInTheRegister(unittest.TestCase):
    """A `#` line is a note, and the register loads around it.

    No server here: the register is read straight off disk, because what is
    under test is the file format rather than anything the dashboard does with
    it. The registers are written out in full rather than built from
    REGISTER_CSV, so that a note and the line it explains can be read together.
    """

    HEADER = ('asset_id,serial,owner,model,class,status,owner_since,'
              'valid_from,valid_to,departure_reason\n')
    ROW_23 = ('TARI-00023,PF50L2MR,Wouter van der Toorren,LENOVO 21K9CTO1WW,'
              'linux,active,2024-01-01,2024-01-01,,\n')
    ROW_31 = ('TARI-00031,YD063JGA,Elma Aker,ThinkPad,windows,active,'
              '2023-06-12,2023-06-12,,\n')

    def setUp(self):
        previous_level = hb.logger.level
        hb.logger.setLevel(logging.ERROR)
        self.addCleanup(hb.logger.setLevel, previous_level)

        self.workdir = Path(tempfile.mkdtemp(prefix='badgersbay-notes-'))
        self.addCleanup(shutil.rmtree, self.workdir, ignore_errors=True)

    def register(self, text):
        """Write a register and load it, returning the AssetRegister."""
        path = self.workdir / 'assets.csv'
        path.write_text(text)
        register = hb.AssetRegister(str(path))
        register.load()
        return register

    def test_a_note_above_the_header(self):
        """The case from the bean: the first line is read as the header.

        The real register ships as an agenix secret and is never seen in a
        diff, so the top of the file is exactly where somebody says what it is.
        """
        register = self.register(
            '# The asset register: the denominator compliance is measured\n'
            '# against. Keep it out of the repository.\n'
            + self.HEADER + self.ROW_23
        )

        self.assertEqual([row['asset_id'] for row in register.rows],
                         ['TARI-00023'])
        self.assertTrue(register.loaded)

    def test_a_note_between_rows_is_skipped(self):
        """And does not arrive as a row of its own."""
        register = self.register(
            self.HEADER + self.ROW_23
            + '# TARI-00031 carries the serial Win32_BIOS reports. The ISO\n'
              '# tool holds AC06CMEP, the suffix of the hostname - do not\n'
              '# "correct" this row to it, or it stops matching.\n'
            + self.ROW_31
        )

        self.assertEqual([row['asset_id'] for row in register.rows],
                         ['TARI-00023', 'TARI-00031'])
        self.assertEqual(register.rows[1]['serial'], 'YD063JGA')

    def test_an_indented_note_is_a_note(self):
        """So a note can sit under the row it belongs to."""
        register = self.register(
            self.HEADER + self.ROW_23 + '    # outside the denominator\n'
            + self.ROW_31
        )

        self.assertEqual(len(register.rows), 2)

    def test_a_hash_inside_a_field_is_not_a_note(self):
        """Only the first non-whitespace character decides."""
        register = self.register(
            self.HEADER
            + 'TARI-00023,PF50L2MR,Wouter van der Toorren,ThinkPad #2,'
              'linux,active,2024-01-01,2024-01-01,,\n'
        )

        self.assertEqual(register.rows[0]['model'], 'ThinkPad #2')

    def test_an_error_names_the_line_in_the_file(self):
        """The number has to lead to the line the maintainer opens.

        Every note shifts the rows down by one. A number counted off the parsed
        rows would drift further into the file the more notes somebody wrote,
        so commenting would be punished with a wrong error - worse than the
        refusal it replaces.
        """
        with self.assertRaises(hb.AssetRegisterError) as caught:
            self.register(
                '# two notes above the header\n'
                '# and this is the second\n'
                + self.HEADER + self.ROW_23
                + '# one more, which puts the bad row on line 6\n'
                + 'TARI-00031,YD063JGA,Elma Aker,ThinkPad,plan9,active,'
                  '2023-06-12,2023-06-12,,\n'
            )

        self.assertIn('row 6', str(caught.exception))
        self.assertIn('plan9', str(caught.exception))

    def test_an_unusable_header_quotes_the_line(self):
        """The bean's second complaint: the message listed columns that were there.

        A semicolon-separated export is the case that still reaches here now
        that a note cannot.
        """
        with self.assertRaises(hb.AssetRegisterError) as caught:
            self.register(
                '# exported from the workbook\n'
                'asset_id;serial;owner;model;class;status\n'
                'TARI-00023;PF50L2MR;Wouter van der Toorren;ThinkPad;linux;active\n'
            )

        message = str(caught.exception)
        self.assertIn('line 2', message)
        self.assertIn('asset_id;serial;owner;model;class;status', message)
        # The expected columns are still named: the gap between what was wanted
        # and what arrived is the diagnosis.
        self.assertIn('asset_id, class, owner, serial', message)

    def test_a_register_of_only_notes_says_it_has_no_header(self):
        """Rather than reporting every column as missing."""
        with self.assertRaises(hb.AssetRegisterError) as caught:
            self.register('# nothing here yet\n# but a plan to fill it in\n')

        self.assertIn('no header line', str(caught.exception))

    def test_the_example_register_loads_and_carries_notes(self):
        """assets.csv.example is the documentation, so it has to parse."""
        text = (HERE / 'assets.csv.example').read_text()
        register = self.register(text)

        self.assertTrue(register.loaded)
        self.assertTrue(register.rows)
        self.assertTrue([line for line in text.splitlines()
                         if line.lstrip().startswith('#')])


if __name__ == '__main__':
    unittest.main()
