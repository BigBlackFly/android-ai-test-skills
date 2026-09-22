"""cleanup：证据与日志轮转，防 storage 无限膨胀。

每步 act/observe 都落全分辨率截图，长期不用必爆——定期跑或挂计划任务。
按**文件**自身 mtime 判断（目录 mtime 只在增删子项时变，按目录判会误删
正在写入的活跃证据）；当前会话的证据目录整目录跳过。

用法：
  python cleanup.py --days 7          # 删 7 天前的 evidence/ 与 logs/
  python cleanup.py --days 7 --dry    # 只报告将删什么
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    p = argparse.ArgumentParser(description="清理过期证据/日志")
    p.add_argument("--days", type=int, default=7, help="保留最近 N 天，默认 7")
    p.add_argument("--dry", action="store_true", help="只报告不删除")
    args = p.parse_args()

    cutoff = time.time() - args.days * 86400
    try:
        from db import current_session
        cur = current_session()
    except Exception:  # noqa: BLE001
        cur = None

    removed = kept = 0
    for name in ("evidence", "logs"):
        root = ROOT / "storage" / name
        if not root.is_dir():
            continue
        # 当前会话的证据目录整目录保护（跑一半被清掉=取证断链）
        protected = root / str(cur) if cur else None
        for f in list(root.rglob("*")):
            if not f.is_file():
                continue
            if protected and f.is_relative_to(protected):
                kept += 1
                continue
            if f.stat().st_mtime >= cutoff:
                kept += 1
                continue
            if args.dry:
                removed += 1
                print(f"[dry] 将删 {f.relative_to(ROOT)}")
                continue
            f.unlink(missing_ok=True)
            removed += 1
        # 顺手剪掉空目录（不含当前会话目录）
        if not args.dry:
            for d in sorted(root.rglob("*"), reverse=True):
                if d.is_dir() and d != protected and not any(d.iterdir()):
                    d.rmdir()
    print(f"清理完成：删除 {removed} 个文件，保留 {kept} 个（最近 {args.days} 天"
          + (f"；当前会话 {cur} 目录已保护" if cur else "") + "）")


if __name__ == "__main__":
    main()
