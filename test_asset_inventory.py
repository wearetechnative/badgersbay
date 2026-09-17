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
            'finding': '3 kwetsbare packages gevonden',
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
        self.assertIn('title="3 kwetsbare packages gevonden"', cell)
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
            'finding': 'niet vastgesteld - geen sessie-informatie beschikbaar',
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
        self.assertIn('niet vastgesteld - geen sessie-informatie beschikbaar', row)
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


if __name__ == '__main__':
    unittest.main()
