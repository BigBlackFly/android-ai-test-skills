"""act：动一下。执行单个动作后自动回传动作后画面（= act + observe 一次完成）。

用法：
  python act.py tap --x 540 --y 1200 --via rid=com.app:id/btn_ok --why "提交表单" --name case172/step02
  python act.py longclick --x 540 --y 1200 --name ...
  python act.py input --x 540 --y 1200 --text "你好" --via text="确定" --name ...
  python act.py input --x 540 --y 1200 --text "追加内容" --no-click --append --name ...
  python act.py swipe --from 540,2000 --to 540,800 --dur 300 --watch text="允许" --name ...
  python act.py back --why "关闭二级页" --name ...
  python act.py home --name ...
  python act.py key --code 4 --name ...        # 4=BACK 3=HOME（一般用 back/home 即可）

语义说明：
- input 默认会先 click 目标坐标聚焦输入框（AI 已点过输入框时加 --no-click 避免
  双击副作用）；默认 clear=True 覆盖已有内容，追加用 --append。
- --watch：动作后监听瞬态弹窗并立即点击（tap/longclick/input/swipe 均支持），
  多候选用 | 分隔；决策在挂载时完成，弹窗出现亚秒级响应，不经 AI。
- --via 定位依据溯源（链路卡提炼靠它）；--why 本步理由（时间轴展示）。
- --settle 动作后稳定窗口毫秒数（默认 600）。异步渲染页（联网解析等）AI 应
  按知识卡经验加大，而不是靠反复 observe 轮询堆证据。
"""
from __future__ import annotations

import argparse
import time
from datetime import datetime

from common import (add_common_args, add_common_args_all_subcommands, capture,
                    connect, emit, evidence_paths, fail, guard_terminated,
                    log_auto, rel, summarize_xml)


def xy(v: str) -> tuple[int, int]:
    a, b = v.split(",")
    return int(a), int(b)


def parse_selector(spec: str) -> dict:
    """watch/选择器规格 → u2 查询参数。支持 rid=/text=/desc=。"""
    for prefix, key in (("rid=", "resourceId"), ("text=", "text"), ("desc=", "description")):
        if spec.startswith(prefix):
            return {key: spec[len(prefix):]}
    raise SystemExit(f"选择器规格不支持: {spec}（支持 rid=/text=/desc=）")


def check_crash(d, package: str | None, evidence_dir) -> dict | None:
    """崩溃检测（分级 + 20s 上下文取证）委托给 logcat.detect。

    ⚠️ evidence_dir 必须传当前步骤证据目录，否则 crash.log 不会落盘、
    崩溃取证就是空承诺（本注释为修过的真实事故留）。

    ⚠️ target 不能只用"当前前台包"：**被测 App 崩溃后前台会回落到桌面**，
    此时 foreground=com.zui.launcher、崩溃 process=com.zui.calendar，
    按前台包分类必然判成 other（"不影响判定"）→ 崩溃被放过。
    故优先用会话声明的被测包（首个 observe 回填的 session.package），
    前台包仅在会话未记录时兜底。
    """
    related: list[str] = []
    target = package
    try:
        from db import current_session, get_db
        sid = current_session()
        if sid:
            related = get_db().get_related(sid)
            sess_pkg = get_db().get_session_package(sid)
            if sess_pkg:
                target = sess_pkg
    except Exception:  # noqa: BLE001
        pass
    from logcat import detect as detect_crash
    return detect_crash(d, target, related, evidence_dir)


def watch_and_click(d, stages: list[list[str]], timeout_ms: int,
                    per_stage_ms: int = 2500) -> dict:
    """瞬态弹窗确定性响应：在 UiAutomator 层轮询匹配即点（亚秒级）。

    用于权限框等**出现几秒就消失**的弹窗——决策在挂载时已完成，工具只负责快。

    ⚠️ 系统权限框约 6s 未点击会自动消失（Android 通用机制）。
    所以绝不能用"点一下 → observe 看看 → 再决定点哪"的节奏：
    一次 observe（截图 2.4MB + dump）就足以吃掉整个窗口（真实事故：
    168 用例的图库权限框就是这样丢的，最后权限没授上、选择器打不开）。

    支持**多阶段**：`stages=[stage1_specs, stage2_specs, ...]`
    典型场景是"App 自己的提示框 → 系统权限框"两段式：
    stage1 命中并点掉后，继续等 stage2，直到所有阶段处理完或超时。

    参数 `stages` 为二维列表（每阶段一组候选，阶段内用 | 分隔）。
    返回 {"clicked": [...每次点中的 spec...], "waited_ms":..., "missed_stage": idx}
    """
    t_start = time.time()
    all_deadline = t_start + timeout_ms / 1000
    clicked: list[dict] = []
    for idx, specs in enumerate(stages):
        selectors = [(s, parse_selector(s)) for s in specs]
        # 每阶段给一个较短的窗口；但总时长不超过 all_deadline
        stage_deadline = min(all_deadline, time.time() + per_stage_ms / 1000)
        hit = False
        while time.time() < stage_deadline:
            for spec, sel in selectors:
                try:
                    obj = d(**sel)
                    if obj.exists:
                        obj.click()
                        clicked.append({"stage": idx, "spec": spec,
                                        "waited_ms": round((time.time() - t_start) * 1000)})
                        hit = True
                        break
                except Exception:  # noqa: BLE001
                    pass
            if hit:
                break
            time.sleep(0.15)
        if not hit:
            # 该阶段没出现：可能本来就没有（如权限已授予），交给 AI 判断，不算致命
            return {"clicked": clicked, "missed_stage": idx,
                    "missed_specs": specs,
                    "waited_ms": round((time.time() - t_start) * 1000)}
        time.sleep(0.25)   # 让下一个弹窗有时间渲染
    return {"clicked": clicked, "missed_stage": None,
            "waited_ms": round((time.time() - t_start) * 1000)}


def main() -> None:
    p = argparse.ArgumentParser(description="act：执行动作并回传动作后画面")
    # --settle / --perm-action / --perm 已在 add_common_args 里定义
    add_common_args(p)
    sub = p.add_subparsers(dest="action", required=True)

    for name in ("tap", "longclick"):
        s = sub.add_parser(name)
        s.add_argument("--x", type=int, required=True)
        s.add_argument("--y", type=int, required=True)
        s.add_argument("--via", default=None, help="定位依据，如 rid=... 或 text=...")
        s.add_argument("--why", default=None, help="这一步的理由（入库展示在时间轴）")
        s.add_argument("--watch", default=None,
                       help="动作后监听瞬态弹窗并立即点击，多个候选用 | 分隔。"
                            "如 rid=com.android.permissioncontroller:id/permission_allow_button|text=允许")
        s.add_argument("--watch-timeout", type=int, default=8000, dest="watch_timeout",
                       help="watch 总窗口毫秒数，默认 8000（系统权限框约 6s 自行消失，必须一次处理完）")

    s = sub.add_parser("input")
    s.add_argument("--x", type=int, required=True)
    s.add_argument("--y", type=int, required=True)
    s.add_argument("--text", required=True)
    s.add_argument("--via", default=None)
    s.add_argument("--why", default=None)
    s.add_argument("--watch", default=None)
    s.add_argument("--watch-timeout", type=int, default=8000, dest="watch_timeout", help="watch 总窗口毫秒（系统权限框约6s自行消失）")
    s.add_argument("--no-click", action="store_true", dest="no_click",
                   help="不先点击聚焦（AI 已点过输入框时用，避免双击副作用）")
    s.add_argument("--append", action="store_true",
                   help="追加到已有内容（默认覆盖 clear=True）")

    s = sub.add_parser("swipe")
    s.add_argument("--from", dest="src", required=True, help="x1,y1")
    s.add_argument("--to", dest="dst", required=True, help="x2,y2")
    s.add_argument("--dur", type=int, default=300, help="毫秒，默认 300")
    s.add_argument("--via", default=None)
    s.add_argument("--why", default=None)
    s.add_argument("--watch", default=None)
    s.add_argument("--watch-timeout", type=int, default=8000, dest="watch_timeout", help="watch 总窗口毫秒（系统权限框约6s自行消失）")

    for name in ("back", "home"):
        s = sub.add_parser(name)
        s.add_argument("--why", default=None, help="这一步的理由（入库展示在时间轴）")

    s = sub.add_parser("key")
    s.add_argument("--code", type=int, required=True)
    s.add_argument("--why", default=None)

    # 让 --serial/--dir/--name 在子命令前后都能写（两种位置解析后合并）
    add_common_args_all_subcommands(p)
    args = p.parse_args()
    guard_terminated(f"act {args.action}")   # 会话已因崩溃终止 → 拒绝执行
    via = getattr(args, "via", None)
    why = getattr(args, "why", None)

    # 顺带声明权限意图（在动作之前生效，这样本次动作触发的弹窗就能被接住）
    perm_inline = None
    if getattr(args, "perm_action", None):
        try:
            from db import current_session, get_db
            si = current_session()
            if si:
                get_db().set_perm_intent(si, args.perm_action, args.perm or "")
                perm_inline = {"action": args.perm_action, "permission": args.perm or ""}
        except Exception:  # noqa: BLE001
            pass

    try:
        d = connect(args.serial)
    except Exception as e:  # noqa: BLE001
        fail(f"设备连接失败: {e}")

    t0 = time.perf_counter()
    started_at = datetime.now().isoformat(timespec="milliseconds")
    try:
        if args.action in ("tap", "longclick"):
            (d.long_click if args.action == "longclick" else d.click)(args.x, args.y)
            action = {"type": args.action, "x": args.x, "y": args.y}
        elif args.action == "input":
            if not args.no_click:
                d.click(args.x, args.y)
                time.sleep(0.3)
            d.send_keys(args.text, clear=not args.append)
            action = {"type": "input", "x": args.x, "y": args.y, "text": args.text,
                      "mode": "append" if args.append else "overwrite"}
        elif args.action == "swipe":
            x1, y1 = xy(args.src)
            x2, y2 = xy(args.dst)
            d.swipe(x1, y1, x2, y2, args.dur / 1000)
            action = {"type": "swipe", "from": [x1, y1], "to": [x2, y2], "dur_ms": args.dur}
        elif args.action == "back":
            d.press("back")
            action = {"type": "back"}
        elif args.action == "home":
            d.press("home")
            action = {"type": "home"}
        else:
            d.shell(f"input keyevent {args.code}")
            action = {"type": "key", "code": args.code}
    except Exception as e:  # noqa: BLE001
        fail(f"动作执行失败: {e}")

    time.sleep(args.settle / 1000)  # 稳定窗口（--settle 可调），画面是否稳定由 AI 按 after 判断

    png, xml, meta = evidence_paths(args.dir, args.name)
    # ⚠️ 必须按 action 分支求值：字典字面量会**同时**求值所有 value，
    # 而 tap 没有 args.text / swipe 没有 args.x / back 没有 args.code
    # → AttributeError 让除 input 外的所有动作在采集阶段直接崩（真实事故）。
    if args.action in ("tap", "longclick"):
        detail = f"{'点击' if args.action == 'tap' else '长按'} ({args.x},{args.y})"
    elif args.action == "input":
        detail = (f"输入 {args.text!r}"
                  + ("（追加）" if getattr(args, "append", False) else ""))
    elif args.action == "swipe":
        detail = f"滑动 {args.src} → {args.dst}"
    elif args.action == "back":
        detail = "返回"
    elif args.action == "home":
        detail = "回到桌面"
    else:
        detail = f"keyevent {args.code}"
    if via:
        detail += f" via {via}"
        action["via"] = via
    if why:
        action["why"] = why

    # watch 在 capture 之前：瞬态弹窗的窗口期不能浪费在一次 dump 上。
    # ⚠️ 系统权限框约 6s 自动消失，必须先挂 watch 再让动作执行完，
    # 绝不能用"点一下 → observe → 再点"的节奏（会丢掉整个窗口）。
    watch_result = None
    watch_spec = getattr(args, "watch", None)
    if watch_spec:
        # 多阶段语法：阶段之间用 ";;" 分隔，阶段内候选用 "|" 分隔。
        # 例：--watch "text=知道了;;rid=...permission_allow_all_button|text=允许"
        #     （先点 App 提示框"知道了"，再点系统权限框"全部允许"）
        stages = [[s for s in stage.split("|") if s.strip()]
                  for stage in watch_spec.split(";;") if stage.strip()]
        watch_result = watch_and_click(d, stages,
                                       getattr(args, "watch_timeout", 8000))
        got = watch_result.get("clicked") or []
        if got:
            detail += " · watch命中 " + ", ".join(
                f"[阶段{c['stage'] + 1}]{c['spec']}" for c in got)
        if watch_result.get("missed_stage") is not None:
            detail += (f" · watch阶段{watch_result['missed_stage'] + 1}未出现"
                       f"（候选 {watch_result.get('missed_specs')}）")

    # 权限弹窗：按会话级意图自动响应（放在 capture 之前，别浪费 6s 窗口）。
    # 意图由 AI 事先声明；**未声明时默认 grant（同意）**——见 perm.DEFAULT_ACTION。
    perm_result = None
    try:
        from db import current_session, get_db
        si = current_session()
        intent = get_db().get_perm_intent(si) if si else None
        import perm as _perm
        perm_result = _perm.handle(d, intent["action"] if intent else None)
    except Exception as e:  # noqa: BLE001
        perm_result = {"error": str(e)}
    if perm_result and perm_result.get("detected"):
        clk = ", ".join(c["text"] for c in perm_result.get("clicks") or [])
        src = "（默认）" if perm_result.get("action_source") == "default" else ""
        detail += f" · 权限弹窗({perm_result.get('activity')})"
        if clk:
            detail += f" 已自动点击: {clk} {src}".rstrip()
        elif perm_result.get("unmatched"):
            detail += f" 未匹配可点按钮，可见: {perm_result.get('buttons')}"
        else:
            detail += " 未点击"

    try:
        info = capture(d, png, xml, meta,
                       extra={"action": action, **({"watch": watch_result} if watch_result else {})})
    except Exception as e:  # noqa: BLE001
        fail(f"动作已执行但采集失败: {e} | action={action}")

    # 崩溃自动检测（分级 + 20s 上下文取证，crash.log 落在当前步骤证据目录）
    failure = None
    crash = check_crash(d, info.get("package"), png.parent)
    alert = None
    if crash and crash.get("new"):
        from logcat import verdict as crash_verdict
        v = crash_verdict(crash)
        entry = crash.get("entry") or {}
        scope = crash.get("scope")
        info["crash_detected"] = True
        info["crash"] = {"scope": scope, "type": entry.get("type"),
                         "process": entry.get("process"), "time": entry.get("time"),
                         "log_path": crash.get("log_path")}
        detail += f" · ⚠️{v['message']}"
        if v["blocked"]:
            alert = v["message"]
            # 崩溃一次即终止：写会话终态（工具层硬拦截后续动作），
            # 并置 blocked 标记，AI 必须立即 finish 而不再继续
            info["blocked"] = True
            failure = {"blocked": True, "scope": scope,
                       "type": entry.get("type"), "process": entry.get("process"),
                       "reason": v["message"]}
            try:
                from db import current_session, get_db
                sid = current_session()
                if sid:
                    get_db().terminate_session(sid, v["message"])
            except Exception:  # noqa: BLE001
                pass

    duration_ms = round((time.perf_counter() - t0) * 1000)

    # ⚠️ 事件必须在**补齐 perm/watch 等附加字段之后**再落库：
    # 这些字段是链路卡回放的关键（🎯 权限意图声明、🔐 权限框响应），
    # 若在组装前落库，卡里就只剩裸动作，回放者不知道当时声明了什么意图（真实缺陷）。
    if watch_result:
        info = {**info, "watch": watch_result}
    if perm_inline:
        info = {**info, "perm_intent_set": perm_inline}
    if perm_result and perm_result.get("detected"):
        info = {**info, "permission": perm_result}
    log_auto("act", f"act {args.action}", detail, info, rel(png), duration_ms, started_at)

    nodes = summarize_xml(xml.read_text(encoding="utf-8"),
                          mode="full" if getattr(args, "full", False) else "nav",
                          fg_package=None if getattr(args, "no_filter", False)
                          else info.get("package"))
    payload = {
        "action": action,
        **info,
        "evidence": {"png": str(png), "xml": str(xml), "meta": str(meta)},
        "nodes": nodes,
        "nodes_count": len(nodes),
        "nodes_mode": "full" if getattr(args, "full", False) else "nav",
        "hint": ("核对 after 画面是否变化再规划下一步；"
                 "nodes 为导航模式（仅可点节点）。需要按文字断言页面内容时"
                 "加 --full 重取；toast 等浮层不在 nodes 里，用 read.py OCR"),
    }
    if perm_inline:
        payload["perm_intent_set"] = perm_inline
        detail = (f"[意图:{perm_inline['action']}"
                  + (f"/{perm_inline['permission']}" if perm_inline["permission"] else "")
                  + "] " + detail)
    if alert:
        payload["alert"] = alert
    if perm_result and perm_result.get("detected"):
        payload["permission"] = perm_result
        if not (perm_result.get("clicks") or []):
            payload["permission_hint"] = (
                "检测到系统权限弹窗但**没有自动点击**：弹窗里没有可匹配的按钮"
                f"（可见 {perm_result.get('buttons')}）。"
                "若是要测「拒绝」路径，用 perm-intent --action deny 后重触发；"
                "否则看 buttons 自己决定点哪个。")
    if failure:
        # 硬性终止信号：AI 必须立即 finish(BLOCKED)，不要再发下一个 act
        payload["terminate"] = True
        payload["terminate_reason"] = failure["reason"]
        payload["hint"] = ("⛔ 检测到被测/关联包崩溃 → 立即停止执行："
                           "session.py finding --status BLOCKED ... 然后 "
                           "session.py finish --status BLOCKED ...；不要继续下一步")
    emit(True, payload)


if __name__ == "__main__":
    main()
