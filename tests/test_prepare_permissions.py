"""准备目录批量授权回归：模拟设备、隔离 SQLite，验证入口与记录归属。"""
from pathlib import Path
import contextlib
import io
import json
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import db
from prepare import permissions
from prepare import __main__ as prepare_cli

PACKAGE = "com.example.app"


def response(output="", exit_code=0):
    return SimpleNamespace(output=output, exit_code=exit_code)


class PermissionPreparationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="prepare-permissions-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.database = db.SessionDB(self.root / "sessions.db")
        self.addCleanup(self.database._conn().close)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(db, "_DB", self.database))
        self.stack.enter_context(patch.object(db, "CURRENT_FILE", self.root / "current_session"))
        self.device = Mock()
        self.connect = self.stack.enter_context(patch.object(permissions, "connect", return_value=self.device))

    def cli(self, args):
        output = io.StringIO()
        with patch.object(sys, "argv", ["prepare", *args]), contextlib.redirect_stdout(output):
            code = prepare_cli.main()
        return code, json.loads(output.getvalue())

    def test_bulk_grant_keeps_command_result_semantics(self):
        for command, expected in ((response(), True), (response("", 1), False),
                                  (response("Failure [package not found]"), False),
                                  (response("Error: permission denied"), False)):
            with self.subTest(command=command):
                d = Mock()
                d.shell.return_value = command
                result = permissions.grant_all(d, PACKAGE)
                self.assertIs(result["ok"], expected)
                self.assertEqual(result["output"], command.output)
                self.assertEqual(result["exit_code"], command.exit_code)
                d.shell.assert_called_once_with(["pm", "grant", "--all-permissions", PACKAGE])

    def test_invalid_package_never_runs_shell(self):
        for package in ("", " ", "com.a; reboot", "--all-permissions"):
            with self.subTest(package=package):
                d = Mock()
                with self.assertRaises(ValueError):
                    permissions.grant_all(d, package)
                d.shell.assert_not_called()

    def test_cli_serial_positions_and_result_recording(self):
        previous = self.database.start_session("previous", "fixture", "SERIAL")
        current = self.database.start_session("current", "fixture", "SERIAL")
        db.set_current(current)
        for args in (["--serial", "SERIAL", "grant-all", "--package", PACKAGE],
                     ["grant-all", "--package", PACKAGE, "--serial", "SERIAL"]):
            for command in (response(), response("Failure [not allowed]")):
                with self.subTest(args=args, output=command.output):
                    self.device.shell.return_value = command
                    code, result = self.cli(args)
                    self.assertEqual(code, 0 if not command.output else 1)
                    self.assertEqual(result["serial"], "SERIAL")
                    self.assertTrue(result["all_permissions"])
                    self.connect.assert_called_with("SERIAL")
                    self.device.shell.assert_called_with(["pm", "grant", "--all-permissions", PACKAGE])
                    record = self.database.get_session(current)
                    event = record["events"][-1]
                    self.assertEqual(event["kind"], "preparation")
                    self.assertEqual(event["tool"], "prepare grant-all")
                    self.assertEqual(json.loads(event["data_json"]), result)
                    self.assertEqual(record["status"], "running")
        self.assertEqual(self.database.get_session(previous)["events"], [])
        self.assertEqual(len(self.database.get_session(current)["events"]), 4)

    def test_invalid_cli_arguments_never_connect(self):
        for args in (["grant-all", "--package", PACKAGE],
                     ["--serial", "SERIAL", "grant-all"],
                     ["--serial", "SERIAL", "grant-all", "--package", PACKAGE, "--perm", "camera"],
                     ["--serial", " ", "grant-all", "--package", PACKAGE]):
            with self.subTest(args=args), patch.object(sys, "argv", ["prepare", *args]), \
                    contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    prepare_cli.main()
                self.assertEqual(error.exception.code, 2)
        self.connect.assert_not_called()

    def test_connection_failure_is_recorded(self):
        current = self.database.start_session("connection failure", "fixture", "SERIAL")
        db.set_current(current)
        self.connect.side_effect = RuntimeError("device unavailable")
        code, result = self.cli(["--serial", "SERIAL", "grant-all", "--package", PACKAGE])
        self.assertEqual(code, 1)
        self.assertEqual(result["error"], "device unavailable")
        self.assertFalse(result["ok"])
        self.assertEqual(json.loads(self.database.get_session(current)["events"][0]["data_json"]), result)
        self.device.shell.assert_not_called()

    def test_directory_entry_from_another_working_directory(self):
        entry = Path(__file__).resolve().parents[1] / "tools" / "prepare"
        for args, expected in ((["--help"], 0), (["sdcard", "init", "--help"], 0),
                               (["grant-all", "--help"], 0),
                               (["grant-all", "--package", PACKAGE], 2)):
            with self.subTest(args=args):
                result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(entry), *args],
                                        cwd=self.root, capture_output=True, text=True, encoding="utf-8", timeout=15)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertIn("usage:", result.stdout + result.stderr)
        self.assertFalse((self.root / "storage").exists())


if __name__ == "__main__":
    unittest.main()
