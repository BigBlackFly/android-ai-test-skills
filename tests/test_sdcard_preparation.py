"""文件准备 CLI 与会话归属的离线回归；临时 SQLite + 模拟 ADB，不连接设备。"""
from pathlib import Path
import contextlib
import io
import json
import shlex
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import common
import db
from prepare import sdcard
from prepare import __main__ as prepare_cli
import session


class ModulePathTests(unittest.TestCase):
    def test_media_directory_still_points_to_project_assets(self):
        self.assertEqual(sdcard.MEDIA_DIR, Path(__file__).resolve().parents[1] / "media-resources")


class PreparationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="sdcard-regression-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.media = self.root / "media-resources"
        for relative, content in (("images/课程表1.png", b"image"),
                                  ("videos/sample.mp4", b"video")):
            path = self.media / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        self.database = db.SessionDB(self.root / "storage" / "sessions.db")
        self.addCleanup(self.database._conn().close)
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(db, "_DB", self.database))
        stack.enter_context(patch.object(db, "CURRENT_FILE", self.root / "storage" / "current_session"))
        stack.enter_context(patch.object(session, "ROOT", self.root))
        stack.enter_context(patch.object(sdcard, "MEDIA_DIR", self.media))
        self.device = Mock()
        self.connection = stack.enter_context(patch.object(common, "try_connect", return_value=self.device))
        self.adb = stack.enter_context(patch.object(sdcard.subprocess, "run", side_effect=self.fake_adb))
        self.commands = []
        self.device_root = "/storage/emulated/0"
        self.scan_error = False

    def fake_adb(self, command, **kwargs):
        self.assertEqual(command[:3], ["adb", "-s", "SERIAL"])
        self.commands.append(command)
        output = b""
        if command[3] == "shell":
            args = shlex.split(command[4])
            if args[:2] == ["readlink", "-f"]:
                output = (self.device_root if args[2] == "/sdcard" else args[2]).encode()
            elif args == ["am", "get-current-user"]:
                output = b"0"
            elif args[0] == "find":
                entries = {
                    "/storage/emulated/0": ["Android", "Pictures", "old.txt", ".cache"],
                    "/storage/emulated/0/Pictures": ["old image.png"],
                }[args[1]]
                output = b"".join((args[1] + "/" + name).encode() + bytes([0]) for name in entries)
            elif args[0] == "content" and self.scan_error:
                return SimpleNamespace(returncode=1, stdout=b"", stderr=b"scan failed")
        return SimpleNamespace(returncode=0, stdout=output, stderr=b"")

    def cli(self, args):
        output = io.StringIO()
        with patch.object(sys, "argv", ["prepare", *args]), contextlib.redirect_stdout(output):
            code = prepare_cli.main()
        return code, json.loads(output.getvalue())

    def shell_commands(self):
        return [shlex.split(command[4]) for command in self.commands if command[3] == "shell"]

    def new_session(self, title):
        return self.database.start_session(title, "offline fixture", "SERIAL")

    def test_init_preserves_android_pushes_media_and_records_current_session(self):
        old = self.new_session("previous")
        current = self.new_session("current")
        db.set_current(current)
        code, result = self.cli(["--serial", "SERIAL", "sdcard", "init"])
        self.assertEqual(code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["steps"][0]["data"], {"files": 2, "bytes": 10})
        removals = [command[-1] for command in self.shell_commands() if command[0] == "rm"]
        self.assertEqual(set(removals), {"/storage/emulated/0/Pictures/old image.png",
                                        "/storage/emulated/0/old.txt", "/storage/emulated/0/.cache"})
        pushes = [command for command in self.commands if command[3] == "push"]
        self.assertEqual({command[-1] for command in pushes},
                         {"/storage/emulated/0/Pictures/课程表1.png",
                          "/storage/emulated/0/media-resources/videos/sample.mp4"})
        self.assertEqual(self.shell_commands()[-1][0], "content")
        self.assertEqual(self.database.get_session(old)["events"], [])
        events = self.database.get_session(current)["events"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["kind"], "preparation")
        self.assertEqual(json.loads(events[0]["data_json"]), result["steps"][0])

    def test_clear_does_not_read_or_push_local_media(self):
        with patch.object(sdcard, "MEDIA_DIR", self.root / "missing"):
            code, result = self.cli(["sdcard", "clear", "--serial", "SERIAL"])
        self.assertEqual(code, 0)
        self.assertEqual(result["action"], "sdcard_clear")
        self.assertEqual(result["steps"][0]["data"], {"files": 0, "bytes": 0})
        self.assertFalse(any(command[3] == "push" for command in self.commands))
        self.assertEqual(self.shell_commands()[-1][0], "content")

    def test_serial_before_and_after_subcommand(self):
        for action in ("init", "clear"):
            for args in (["--serial", "SERIAL", "sdcard", action],
                         ["sdcard", "--serial", "SERIAL", action],
                         ["sdcard", action, "--serial", "SERIAL"]):
                with self.subTest(args=args):
                    code, result = self.cli(args)
                    self.assertEqual(code, 0)
                    self.assertEqual(result["serial"], "SERIAL")
                    self.assertEqual(result["action"], "sdcard_" + action)

    def test_missing_serial_and_help_never_touch_adb(self):
        for args, expected in ((["sdcard", "init"], 2), (["sdcard", "clear", "--serial", " "], 2),
                               (["--help"], 0), (["sdcard", "init", "--help"], 0),
                               (["sdcard", "clear", "--help"], 0)):
            with self.subTest(args=args), contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()), \
                    patch.object(sys, "argv", ["prepare", *args]):
                with self.assertRaises(SystemExit) as error:
                    prepare_cli.main()
                self.assertEqual(error.exception.code, expected)
        self.adb.assert_not_called()

    def test_missing_assets_stop_before_device_operations(self):
        with patch.object(sdcard, "MEDIA_DIR", self.root / "missing"):
            code, result = self.cli(["sdcard", "init", "--serial", "SERIAL"])
        self.assertEqual(code, 1)
        self.assertFalse(result["ok"])
        self.assertIn("素材目录", result["error"])
        self.adb.assert_not_called()

    def test_invalid_device_root_never_deletes_or_pushes(self):
        self.device_root = "/unexpected"
        code, result = self.cli(["sdcard", "clear", "--serial", "SERIAL"])
        self.assertEqual(code, 1)
        self.assertIn("拒绝清理", result["error"])
        self.assertEqual(len(self.commands), 1)

    def test_scan_failure_is_returned_and_recorded_without_finishing_session(self):
        current = self.new_session("scan failure")
        db.set_current(current)
        self.scan_error = True
        code, result = self.cli(["sdcard", "clear", "--serial", "SERIAL"])
        self.assertEqual(code, 1)
        self.assertFalse(result["ok"])
        self.assertIn("scan failed", result["error"])
        record = self.database.get_session(current)
        self.assertEqual(record["status"], "running")
        self.assertEqual(db.current_session(), current)
        self.assertEqual(json.loads(record["events"][0]["data_json"]), result["steps"][0])

    def test_adb_timeout_returns_failure(self):
        self.adb.side_effect = subprocess.TimeoutExpired("adb", 30)
        code, result = self.cli(["sdcard", "clear", "--serial", "SERIAL"])
        self.assertEqual(code, 1)
        self.assertFalse(result["ok"])
        self.assertIn("ADB 执行失败", result["error"])

    def test_library_missing_serial_returns_failure_without_adb(self):
        for action in (sdcard.init, sdcard.clear):
            with self.subTest(action=action.__name__):
                result = action(None)
                self.assertFalse(result["ok"])
                self.assertEqual(result["status"], "INFO")
                self.assertIn("serial", result["error"])
        self.adb.assert_not_called()

    def test_standalone_preparation_does_not_create_a_session(self):
        code, result = self.cli(["sdcard", "clear", "--serial", "SERIAL"])
        self.assertEqual(code, 0)
        self.assertTrue(result["ok"])
        self.assertIsNone(db.current_session())
        count = self.database._conn().execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        self.assertEqual(count, 0)

    def test_session_start_and_resume_never_prepare_files(self):
        case_id = self.database.add_case("case", "offline fixture", "com.example.app")
        modes = (["--title", "normal", "--input", "fixture"],
                 ["--title", "diag", "--input", "fixture", "--diag"],
                 ["--case", str(case_id)])
        with patch.object(sdcard, "init") as initialize, patch.object(sdcard, "clear") as clear:
            for device in (None, self.device):
                self.connection.return_value = device
                for mode in modes:
                    with self.subTest(mode=mode, connected=device is not None):
                        args = ["session.py", "start", *mode, "--device", "SERIAL", "--package", "com.example.app"]
                        output = io.StringIO()
                        with patch.object(sys, "argv", args), contextlib.redirect_stdout(output):
                            session.main()
                        current = json.loads(output.getvalue())["session_id"]
                        self.assertEqual(db.current_session(), current)
                        self.assertEqual(self.database.get_session(current)["events"], [])
                        with patch.object(sys, "argv", ["session.py", "resume", "--id", str(current)]), \
                                contextlib.redirect_stdout(io.StringIO()):
                            session.main()
                        self.assertEqual(db.current_session(), current)
            initialize.assert_not_called()
            clear.assert_not_called()
        self.adb.assert_not_called()
        self.assertTrue(self.device.shell.called)
        self.assertEqual({call.args[0] for call in self.device.shell.call_args_list},
                         {"logcat -G 5M", "logcat -b crash -c"})


if __name__ == "__main__":
    unittest.main()
