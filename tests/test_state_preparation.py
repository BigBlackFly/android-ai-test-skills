"""状态工具的离线回归；不连接设备，不写入真实会话或数据库。

仅验证命令结果处理和 CLI 兼容性，不作为真机验收。直接执行本文件。
"""
from pathlib import Path
import contextlib
import io
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import state

PACKAGE = "com.example.app"
CAMERA = "android.permission.CAMERA"


def response(output="", exit_code=0):
    return SimpleNamespace(output=output, exit_code=exit_code)


class StateTests(unittest.TestCase):
    def test_bulk_grant_uses_only_command_result(self):
        for command, expected in [
            (response(), True),
            (response("", 1), False),
            (response("Failure [package not found]"), False),
            (response("Error: permission denied"), False),
        ]:
            with self.subTest(command=command):
                d = Mock()
                d.shell.return_value = command
                result = state.grant_all(d, PACKAGE)
                self.assertIs(result["ok"], expected)
                self.assertEqual(result["output"], command.output)
                self.assertEqual(result["exit_code"], command.exit_code)
                d.shell.assert_called_once_with(["pm", "grant", "--all-permissions", PACKAGE])

    def test_package_required_and_single_bulk_mutually_exclusive(self):
        for args in [
            ["grant", "--all-permissions"],
            ["grant", "--package", PACKAGE],
            ["grant", "--package", PACKAGE, "--perm", "camera", "--all-permissions"],
            ["revoke", "--package", PACKAGE, "--all-permissions"],
        ]:
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()):
                with patch.object(sys, "argv", ["state.py", *args]), patch.object(state, "connect") as connect:
                    with self.assertRaises(SystemExit) as error:
                        state.main()
                    self.assertEqual(error.exception.code, 2)
                    connect.assert_not_called()

    def test_invalid_bulk_package_never_runs_shell(self):
        for package in ("", " ", "com.a; reboot", "--all-permissions"):
            with self.subTest(package=package):
                d = Mock()
                with self.assertRaises(ValueError):
                    state.grant_all(d, package)
                d.shell.assert_not_called()

    def run_main(self, args, device, serial=None):
        with (
            patch.object(sys, "argv", ["state.py", *args]),
            patch.object(state, "connect", return_value=device) as connect,
            patch.object(state, "log_auto") as logged,
            patch.object(state, "emit") as emitted,
        ):
            state.main()
            connect.assert_called_once_with(serial)
            self.assertTrue(logged.called)
            return emitted.call_args.args, logged.call_args.args

    def test_bulk_cli_serial_and_recorded_result(self):
        for args in [
            ["--serial", "SERIAL", "grant", "--package", PACKAGE, "--all-permissions"],
            ["grant", "--package", PACKAGE, "--all-permissions", "--serial", "SERIAL"],
        ]:
            with self.subTest(args=args):
                d = Mock()
                d.shell.return_value = response()
                (ok, payload), logged = self.run_main(args, d, serial="SERIAL")
                self.assertTrue(ok)
                self.assertTrue(payload["all_permissions"])
                self.assertEqual(logged[:2], ("state", "state grant"))
                self.assertEqual(logged[3], payload)

    def test_existing_cli_calls_remain_compatible(self):
        for command, extra, outputs, key, expected in [
            ("grant", ["--perm", "camera"], [response(), response(f"{CAMERA}: granted=true")], "perm", CAMERA),
            ("revoke", ["--perm", CAMERA], [response(), response(f"{CAMERA}: granted=false")], "perm", CAMERA),
            ("clear", [], [response("Success")], "output", "Success"),
            ("start", [], [], "started", PACKAGE),
            ("start", ["--activity", ".MainActivity"], [], "started", f"{PACKAGE}/.MainActivity"),
            ("stop", [], [], "stopped", PACKAGE),
        ]:
            with self.subTest(command=command, extra=extra):
                d = Mock()
                d.shell.side_effect = outputs
                (ok, payload), _ = self.run_main([command, "--package", PACKAGE, *extra], d)
                self.assertTrue(ok)
                self.assertEqual(payload[key], expected)
                if command in ("grant", "revoke"):
                    self.assertEqual(d.shell.call_args_list[0].args[0], f"pm {command} {PACKAGE} {CAMERA}")
                    self.assertEqual(d.shell.call_count, 2)
                elif command == "clear":
                    d.shell.assert_called_once_with(f"pm clear {PACKAGE}")
                elif command == "start":
                    d.app_start.assert_called_once_with(PACKAGE, ".MainActivity") if extra else d.app_start.assert_called_once_with(PACKAGE)
                else:
                    d.app_stop.assert_called_once_with(PACKAGE)


if __name__ == "__main__":
    unittest.main()
