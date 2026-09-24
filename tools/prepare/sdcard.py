"""清理用户使用设备过程中产生的文件，并预置 skill 内的测试图片和视频。

清理对象包括图片、视频、下载文件及测试残留；保留 /sdcard/Android 及其内容。
应用数据与权限保持原状。

开会话后由测试 Agent 按准备文档显式调用，结果记入当前会话。
入口：python tools/prepare --serial <serial> sdcard init|clear
也可供其他模块调用：clear(serial)、init(serial)。
"""
from pathlib import Path, PurePosixPath
import os
import re
import shlex
import stat
import subprocess

MEDIA_DIR = Path(__file__).resolve().parents[2] / "media-resources"
PROTECTED_FOLDERS = ["Android"]
EMPTY_FOLDERS = (
    "Alarms", "Audiobooks", "Download", "DCIM", "Documents", "Music",
    "Movies", "Notifications", "Podcasts", "Pictures", "Ringtones", "Recordings",
)
MEDIA_SUFFIXES = {
    "images": {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic"},
    "videos": {".mp4", ".mkv", ".webm", ".mov", ".3gp"},
}

# 相对素材目录的文件名 → 相对设备 sdcard 根目录的专用目标。
MEDIA_TARGETS = {
    "images/课程表1.png": "Pictures/课程表1.png",
    "images/课程表2.png": "Pictures/课程表2.png",
}


class SDCardError(RuntimeError):
    """文件操作异常，由准备入口返回并记入当前会话。"""


class SDCard:
    def __init__(self, adb_run, media_dir=None):
        # 由调用方绑定设备 serial，所有命令（包括 push）使用同一设备。
        self._adb_run = adb_run
        self.media_dir = Path(media_dir) if media_dir is not None else MEDIA_DIR
        self._root = None
        self._user = None

    def _run(self, *args, timeout=30):
        try:
            result = self._adb_run(*args, timeout=timeout, text=False)
        except (OSError, subprocess.SubprocessError) as exc:
            raise SDCardError(f"ADB 执行失败: {exc}") from exc
        if result.returncode:
            message = (result.stderr or result.stdout or b"").decode("utf-8", "replace")
            raise SDCardError(
                f"ADB 退出码 {result.returncode}: {message.strip()[:1500]}")
        return result.stdout or b""

    def _shell(self, *args, timeout=30):
        # adb 会将 shell 后的参数再次拼接；将参数引用成一个远端命令，
        # 防止文件名中的空格、引号、$()、分号在设备 shell 上被解释。
        return self._run("shell", shlex.join(args), timeout=timeout)

    def _text(self, *args, timeout=30):
        try:
            return self._shell(*args, timeout=timeout).decode("utf-8").strip()
        except UnicodeError as exc:
            raise SDCardError("ADB 返回了无法解析的 UTF-8 输出") from exc

    def _prepare_device(self):
        root = self._text("readlink", "-f", "/sdcard")
        match = re.fullmatch(r"/storage/emulated/([0-9]+)", root)
        if not match:
            raise SDCardError(f"拒绝清理未知的 /sdcard 实际路径: {root!r}")
        user = match.group(1)
        if self._text("am", "get-current-user") != user:
            raise SDCardError("/sdcard 与当前 Android 用户不一致，未执行清理")
        self._shell("test", "-d", root)
        self._root, self._user = root, user

    def _entries(self, directory):
        raw = self._shell("find", directory, "-mindepth", "1", "-maxdepth", "1", "-print0")
        if raw and not raw.endswith(b"\0"):
            raise SDCardError(f"目录清单不完整: {directory}")
        try:
            entries = [p.decode("utf-8") for p in raw.split(b"\0") if p]
        except UnicodeError as exc:
            raise SDCardError(f"目录包含无法解析的文件名: {directory}") from exc
        for entry in entries:
            # 不接受 find 输出中的根目录、..、越界条目或不规范路径。
            path = PurePosixPath(entry)
            if (str(path.parent) != directory or str(path) != entry
                    or path.name in (".", "..") or ".." in path.parts):
                raise SDCardError(f"拒绝清理越界目录条目: {entry!r}")
        return entries

    def _real_directory(self, path):
        self._shell("test", "!", "-L", path)
        self._shell("test", "-d", path)
        if self._text("readlink", "-f", path) != path:
            raise SDCardError(f"拒绝进入重定向目录: {path}")

    def _clear_files(self):
        # 删除前先完成目录检查及计划；不通过 glob 清理，包含隐藏文件。
        targets = []
        protected_directories = {PurePosixPath(self._root, name) for name in PROTECTED_FOLDERS}
        kept_directories = {PurePosixPath(self._root, name) for name in EMPTY_FOLDERS}

        def collect(directory):
            for path in self._entries(directory):
                entry = PurePosixPath(path)
                if entry in protected_directories:
                    continue
                if entry in kept_directories:
                    self._real_directory(path)
                    collect(path)
                else:
                    targets.append(path)

        collect(self._root)
        for path in targets:
            # rm 删除链接本身，不跟随它；受保护目录从不作为删除目标。
            self._shell("rm", "-rf", "--", path, timeout=120)
        # 系统可能立即重建缓存；清理后不要求目录持续为空。
        for name in EMPTY_FOLDERS:
            if name not in PROTECTED_FOLDERS:
                self._shell("mkdir", "-p", f"{self._root}/{name}")

    def _scan(self):
        # 尝试刷新媒体索引，执行异常由准备入口记录。
        self._shell(
            "content", "call", "--user", self._user, "--uri", "content://media",
            "--method", "scan_volume", "--arg", "external_primary", timeout=120)

    def _local_files(self):
        files = {}
        try:
            if self.media_dir.is_symlink() or not self.media_dir.is_dir():
                raise SDCardError(f"素材目录不存在或为链接: {self.media_dir}")
            root = self.media_dir.resolve()
            for folder, suffixes in MEDIA_SUFFIXES.items():
                base = root / folder
                if base.is_symlink() or base.resolve() != base or not base.is_dir():
                    raise SDCardError(f"缺少素材目录或目录为链接: {base}")
                count = 0
                for current, dirs, names in os.walk(
                        base, followlinks=False, onerror=self._walk_error):
                    for name in dirs + names:
                        path = Path(current) / name
                        if path.is_symlink() or path.resolve() != path:
                            raise SDCardError(f"素材路径越界或为链接: {path}")
                    for name in names:
                        path = Path(current) / name
                        if path.suffix.lower() not in suffixes or not stat.S_ISREG(path.stat().st_mode):
                            raise SDCardError(f"不支持的素材文件: {path}")
                        # 在清理设备前完整读取，尽早发现空文件、权限和读取错误。
                        size = 0
                        with path.open("rb") as stream:
                            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                                size += len(chunk)
                        if not size:
                            raise SDCardError(f"素材文件为空: {path}")
                        files[path.relative_to(root).as_posix()] = (path, size)
                        count += 1
                if not count:
                    raise SDCardError(f"素材目录为空: {base}")
        except OSError as exc:
            raise SDCardError(f"读取本地素材失败: {exc}") from exc
        return dict(sorted(files.items()))

    @staticmethod
    def _walk_error(error):
        raise error

    def _push_media(self, files):
        targets = {
            relative: PurePosixPath(
                self._root, MEDIA_TARGETS.get(relative, f"media-resources/{relative}"))
            for relative in files
        }
        # 同目录下的多个文件只创建一次父目录。
        parents = {str(target.parent) for target in targets.values()}
        for parent in sorted(parents):
            self._shell("mkdir", "-p", parent)
        for relative, (source, _) in files.items():
            self._run("push", str(source), str(targets[relative]), timeout=120)

    def clear(self):
        """清理设备使用过程中产生的用户文件并刷新媒体索引，不依赖本地素材。"""
        self._prepare_device()
        self._clear_files()
        self._scan()
        return {"files": 0, "bytes": 0}

    def init(self):
        """清理后推送 images/videos；先检查本机素材，再触碰设备。"""
        files = self._local_files()
        self._prepare_device()
        self._clear_files()
        self._push_media(files)
        self._scan()
        return {"files": len(files), "bytes": sum(size for _, size in files.values())}


def _prepare(serial, *, initialize):
    """显式执行文件准备，返回实际结果，并沿用当前会话的 INFO 事件。"""
    from common import log_auto

    action = "sdcard_init" if initialize else "sdcard_clear"
    entry = {"action": action, "serial": serial, "status": "INFO", "ok": False,
             "detail": f"{action} 已完成", "data": {}}

    def adb_run(*args, timeout=30, text=False):
        return subprocess.run(["adb", "-s", serial, *args],
                              capture_output=True, timeout=timeout, text=text)

    try:
        if not serial or not serial.strip():
            raise SDCardError("必须显式指定设备 serial，文件准备未执行")
        worker = SDCard(adb_run)
        entry["data"] = worker.init() if initialize else worker.clear()
        entry["ok"] = True
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        entry["error"] = str(exc)
        entry["detail"] = f"{action} 执行异常: {exc}"

    log_auto("preparation", "preparation " + action, entry["detail"], entry)
    result = {"ok": entry["ok"], "action": action, "serial": serial,
              "status": "INFO", "steps": [entry]}
    if "error" in entry:
        result["error"] = entry["error"]
    return result


def clear(serial):
    """清理用户文件并刷新媒体索引，返回结果并记录当前会话。"""
    return _prepare(serial, initialize=False)


def init(serial):
    """清理用户文件并预置测试媒体，返回结果并记录当前会话。"""
    return _prepare(serial, initialize=True)
