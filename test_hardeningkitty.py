#!/usr/bin/env python3
"""Windows submissions and their HardeningKitty report.

The requirement set for class `windows` is sysinfo and hardening, and hardening
is met by the HardeningKitty result the Windows client sends as
hardeningkitty.csv. Until the server recognised that file, every Windows
submission was recorded without it and so as incomplete. These tests submit a
Windows archive to a real server, and repair records stored before the fix.

The archive is built here rather than taken from a real machine: it carries the
same file names, the byte order marks and CRLF the Windows client writes, and
the header HardeningKitty produces, without a person's serial and username.

    python3 -m unittest test_hardeningkitty -v
"""

import json
import logging
import unittest

import honeybadger_server as hb
from test_asset_inventory import ServerHarness, repack

WINDOWS_SERIAL = 'WINTEST01'
WINDOWS_ASSET_ID = 'TARI-00077'

BOM = b'\xef\xbb\xbf'
HARDENINGKITTY_CSV = (
    BOM
    + b'"ID","Category","Name","Severity","Result","Recommended","TestResult","SeverityFinding"\r\n'
    + b'"1000","Account Policies","Account lockout duration","Low","0","15","Failed","Low"\r\n'
    + b'"1100","User Rights","Access this computer from the network","Passed","x","x","Passed","Passed"\r\n'
)
DIR = 'output-WINTEST01-tester-28-09-2026'


def windows_archive(hardeningkitty=HARDENINGKITTY_CSV):
    """A Windows client archive, as the client writes it."""
    members = {
        f'{DIR}/fastfetch.json': BOM + json.dumps({
            'user': 'tester', 'hostname': 'WINTEST01', 'os': 'Windows 11 x86_64',
            'host': '82H8 (IdeaPad 3 15ITL6)', 'kernel': '10.0.26200.9457',
        }).encode(),
        f'{DIR}/hardware-serial.txt': BOM + f'{WINDOWS_SERIAL}\r\n'.encode(),
        f'{DIR}/hardware-serial-source.txt': BOM + b'wmi:Win32_BIOS\r\n',
        f'{DIR}/bitlocker_result.txt': BOM + b'Fully encrypted\r\n',
    }
    if hardeningkitty is not None:
        members[f'{DIR}/hardeningkitty.csv'] = hardeningkitty
    return repack(members)


class WindowsHarness(ServerHarness):
    """The shared harness, with a register that holds a Windows asset."""

    def setUp(self):
        super().setUp()
        register_path = self.workdir / 'assets.csv'
        register_path.write_text(
            'asset_id,serial,owner,model,class,status,owner_since,valid_from,valid_to,'
            'departure_reason\n'
            f'{WINDOWS_ASSET_ID},{WINDOWS_SERIAL},Test Owner,Lenovo IdeaPad 3,'
            'windows,active,2024-01-01,2024-01-01,,\n'
        )
        register = hb.AssetRegister(str(register_path), state_dir=self.workdir)
        register.load()
        hb.ReportHandler.asset_register = register

    def records(self):
        """Every submission.json under submissions/, as (dir, document)."""
        found = []
        for meta in sorted((self.storage / 'submissions').glob('*/*/submission.json')):
            found.append((meta.parent, json.loads(meta.read_text())))
        return found


class TestSubmission(WindowsHarness):

    def test_a_windows_archive_is_recorded_complete(self):
        status, body = self.submit(windows_archive(), hostname='WINTEST01', username='tester')
        self.assertEqual(status, 200, body)
        self.assertEqual(body['asset_id'], WINDOWS_ASSET_ID)

        (record_dir, record), = self.records()
        self.assertEqual(record['reports'], ['fastfetch', 'hardeningkitty'])
        # Stored as the bytes that arrived, BOM and CRLF included.
        self.assertEqual((record_dir / 'hardeningkitty.csv').read_bytes(), HARDENINGKITTY_CSV)
        self.assertEqual(hb.evaluate_completeness('windows', record['reports']), (True, []))
        self.assertNotIn('hardeningkitty.csv',
                         [u['file'].rsplit('/', 1)[-1] for u in body['unrecognised']])

    def test_a_csv_that_is_not_a_hardeningkitty_result_is_unrecognised(self):
        status, body = self.submit(windows_archive(b'name,value\r\nfoo,1\r\n'),
                                   hostname='WINTEST01', username='tester')
        self.assertIn(status, (200, 207), body)

        (record_dir, record), = self.records()
        self.assertEqual(record['reports'], ['fastfetch'])
        self.assertFalse((record_dir / 'hardeningkitty.csv').exists())
        reasons = {u['file'].rsplit('/', 1)[-1]: u['reason'] for u in body['unrecognised']}
        self.assertIn('Not a HardeningKitty result', reasons['hardeningkitty.csv'])


class TestRepair(WindowsHarness):

    def stored_as_before_the_fix(self):
        """A Windows record as the server wrote it before it knew the report."""
        status, body = self.submit(windows_archive(), hostname='WINTEST01', username='tester')
        self.assertEqual(status, 200, body)
        (record_dir, record), = self.records()
        record['reports'] = ['fastfetch']
        (record_dir / 'submission.json').write_text(json.dumps(record, indent=2))
        (record_dir / 'hardeningkitty.csv').unlink()
        return record_dir, record

    def test_a_stored_windows_record_is_repaired_once(self):
        record_dir, before = self.stored_as_before_the_fix()

        with self.assertLogs(hb.logger, level=logging.INFO) as logs:
            repaired = hb.repair_hardeningkitty_records(self.storage)
        self.assertEqual(repaired, [record_dir])
        self.assertTrue(any(str(record_dir) in line for line in logs.output))

        after = json.loads((record_dir / 'submission.json').read_text())
        self.assertEqual(after['reports'], ['fastfetch', 'hardeningkitty'])
        # Nothing else in the record moves.
        self.assertEqual({k: v for k, v in after.items() if k != 'reports'},
                         {k: v for k, v in before.items() if k != 'reports'})
        self.assertEqual((record_dir / 'hardeningkitty.csv').read_bytes(), HARDENINGKITTY_CSV)
        self.assertFalse((record_dir / 'submission.json.tmp').exists())

    def test_a_second_start_finds_nothing_to_repair(self):
        record_dir, _ = self.stored_as_before_the_fix()
        hb.repair_hardeningkitty_records(self.storage)
        first = (record_dir / 'submission.json').read_bytes()

        self.assertEqual(hb.repair_hardeningkitty_records(self.storage), [])
        self.assertEqual((record_dir / 'submission.json').read_bytes(), first)

    def test_records_without_the_report_are_left_alone(self):
        # A Windows archive that carries no HardeningKitty report.
        status, _ = self.submit(windows_archive(hardeningkitty=None),
                                hostname='WINTEST01', username='tester')
        self.assertEqual(status, 200)
        (windows_dir, _), = self.records()
        windows_before = (windows_dir / 'submission.json').read_bytes()

        # And a Linux record, which is never a candidate.
        linux_dir = self.storage / 'submissions' / 'LINUX01' / '2026-09-17T10-00-00'
        linux_dir.mkdir(parents=True)
        (linux_dir / 'submission.json').write_text(json.dumps({
            'class': 'linux', 'os_type': 'NixOS 26.05 (Yarara)',
            'reports': ['fastfetch', 'lynis'], 'evidence': 'missing.tar.gz',
        }, indent=2))
        linux_before = (linux_dir / 'submission.json').read_bytes()

        self.assertEqual(hb.repair_hardeningkitty_records(self.storage), [])
        self.assertEqual((windows_dir / 'submission.json').read_bytes(), windows_before)
        self.assertEqual((linux_dir / 'submission.json').read_bytes(), linux_before)


if __name__ == '__main__':
    unittest.main()
