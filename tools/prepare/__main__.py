"""准备工具统一入口：python tools/prepare --serial <serial> ...。"""
import argparse
from pathlib import Path
import sys

# 目录入口可从任意工作目录执行；复用 tools 中的现有会话与事件底座。
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import emit
from prepare import permissions, sdcard


def _serial(parser, *, default=argparse.SUPPRESS):
    parser.add_argument("--serial", default=default,
                        help="必填，显式指定与当前会话一致的设备 serial")


def main() -> int:
    parser = argparse.ArgumentParser(description="prepare：执行前环境准备，结果记入当前会话")
    _serial(parser, default=None)
    commands = parser.add_subparsers(dest="command", required=True)

    files = commands.add_parser("sdcard", help="设备用户文件准备（保留 Android 目录）")
    _serial(files)
    actions = files.add_subparsers(dest="action", required=True)
    for name, help_text in (("init", "清理用户文件、预置素材并刷新媒体索引"),
                            ("clear", "只清理用户文件并刷新媒体索引")):
        action = actions.add_parser(name, help=help_text)
        _serial(action)

    grant = commands.add_parser("grant-all", help="提前授予 App 申请的全部运行时权限")
    _serial(grant)
    grant.add_argument("--package", required=True, help="已确定的单个 App 包名")

    args = parser.parse_args()
    if not args.serial or not args.serial.strip():
        parser.error("必须通过 --serial 显式指定设备")
    if args.command == "sdcard":
        result = sdcard.init(args.serial) if args.action == "init" else sdcard.clear(args.serial)
    else:
        result = permissions.prepare(args.serial, args.package)
    emit(result["ok"], result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
