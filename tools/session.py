"""session：测试会话生命周期。开会话后，observe/act/read 自动把每次调用
作为事件写入当前会话；AI 只需在断言时记 finding、结束时 finish。

用法：
  python session.py start --title "日历新建课程表" --input "用户口述的用例原文..."
  python session.py finding --status PASS --expect "出现新建成功toast" --actual "OCR读到'创建成功'"
  python session.py finish --status PASS --summary "3/4 PASS，1 BLOCKED(无图库权限)"
  python session.py list
  python session.py current
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from common import knowledge_hint
from db import ROOT, STATUSES, clear_current, current_session, get_db, set_current

# Windows 控制台默认 GBK，中文/特殊符号会炸 → 全部 CLI 输出强制 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def maybe_file(v: str) -> str:
    """`@路径` → 读 UTF-8 文件内容作为值。

    中文长文本直接放命令行参数，在部分终端/管道里会被 GBK 双重解码
    （旧 skill 的 GBK 事故同族）；用例口述这种长文本一律建议走 @文件。
    """
    if v and v.startswith("@"):
        return Path(v[1:]).read_text(encoding="utf-8")
    return v


def export_runbook(db, session_id: int, out: str | None) -> str:
    """把会话事件流提炼成"可回放链路卡"——v2 形态的规划缓存。

    内容原则（对齐 SKILL.md 跨设备规则）：
    - 带 --via 的动作 → 记录**定位意图**（rid/text），这是缓存键，换设备可重定位；
    - 无 --via 的动作 → 只记坐标并标 ⚠️（机型绑定，回放前必须现场校准）；
    - 中间的 observe 摘要为检查点（断言依据），不复制节点列表。

    两个真实痛点（回放时才知道）：
    1. **权限分支意图必须记**：否则回放时不知道该声明 grant 还是 deny，
       权限框会走错分支 —— 从事件流的 `perm_intent_set` / perm 事件还原。
    2. **`rid=button1` 是有歧义的定位**：同一个 rid 在不同弹窗里是不同按钮
       （首次说明框的"同意"、提示框的"知道了"、权限框的"允许/拒绝"）。
       故额外记下**点击时屏幕上的弹窗标题 + 实际命中按钮文本**，回放据此判断。
    """
    import xml.etree.ElementTree as ET

    s = db.get_session(session_id)
    if not s:
        raise SystemExit(f"会话 #{session_id} 不存在")
    pkg = s.get("package") or "unknown"
    safe = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", s.get("title") or f"session{session_id}")[:40]
    path = Path(out) if out else ROOT / "knowledge" / "_runs" / pkg / f"{session_id}_{safe}.md"

    def dialog_context(evidence_rel: str | None, prev_intent: str | None) -> str:
        """取"动作发生时屏幕上的弹窗标题"，用于消解 rid 歧义。

        ⚠️ 难点：act 落盘的 dump 是**动作之后**的画面，弹窗可能已被点掉。
        所以策略是：只有当 dump 里确实存在**弹窗特征**（AlertDialog 类节点 /
        已知弹窗 rid）时才取标题；否则返回空——**宁可不写，也不写错的**。
        （早期版本无脑取第一个 title 节点，把页面标题当弹窗标题，误导回放。）
        """
        if not evidence_rel:
            return ""
        try:
            xml = (ROOT / evidence_rel).with_name("dump.xml")
            if not xml.is_file():
                return ""
            root = ET.fromstring(xml.read_text(encoding="utf-8"))
            # 弹窗特征：AlertDialog/弹窗容器类名，或弹窗专用 rid
            DIALOG_CLS = ("AlertDialog", "Dialog", "PopupWindow")
            DIALOG_RID_HINT = ("alertTitle", "parentPanel", "buttonPanel",
                               "button1", "button2", "customPanel")
            for el in root.iter("node"):
                a = el.attrib
                cls = a.get("class", "")
                rid = a.get("resource-id", "")
                pkg = a.get("package", "")
                is_dialog = (any(d in cls for d in DIALOG_CLS)
                             or any(h in rid for h in DIALOG_RID_HINT))
                # 系统权限框额外识别（它的包名不是被测 App）
                if "permissioncontroller" in pkg:
                    is_dialog = True
                if not is_dialog:
                    continue
                # 在弹窗容器内找标题/正文
                for sub in el.iter("node"):
                    sa = sub.attrib
                    srid = sa.get("resource-id", "")
                    if srid.endswith(("alertTitle", "message", "dialog_title")):
                        t = (sa.get("text") or "").strip()
                        if t:
                            return t
            return ""
        except Exception:  # noqa: BLE001
            return ""

    lines = [
        f"# 链路：{s.get('title') or session_id}",
        "",
        f"- 来源会话: #{session_id}（{s.get('status')}，{s.get('started_at')}）",
        f"- 包名: {pkg}",
        f"- 设备: {s.get('device') or '未记录'}",
        "- 用例口述:",
        "",
        "```",
        s.get("user_input") or "（未记录）",
        "```",
        "",
        "## 步骤",
        "",
    ]
    n = 0
    cur_intent: str | None = None       # 当前生效的权限意图（跟随事件流）
    pending_decl: str | None = None     # 由独立 perm-intent 事件声明、待挂到下一个 act
    last_ck: str | None = None          # 上一条检查点的 activity（用于去重连续重复）
    ck_dup = 0                          # 连续重复计数
    # 误操作关键词：命中的步骤要标"回放可跳过"，否则回放者会照做一次多余的往返
    _DETOUR = ("误点", "误操作", "绕行", "点错", "走错")
    for e in s["events"]:
        data = json.loads(e["data_json"] or "{}")

        # 权限意图：独立声明的事件（挂到下一个 act 上展示），或 act 顺带声明
        if e["kind"] == "perm":
            m = re.search(r"(grant|deny)", e["detail"] or "")
            if m:
                cur_intent = m.group(1)
                pending_decl = m.group(1)     # 标记"下一步是新声明的"
            continue
        if isinstance(data.get("perm_intent_set"), dict):
            cur_intent = data["perm_intent_set"].get("action")

        if e["kind"] == "act":
            n += 1
            act_data = data.get("action", {})
            via = act_data.get("via")
            why = act_data.get("why")
            loc = f"定位 `{via}`" if via else "⚠️坐标直点（回放前现场校准）"

            # 意图声明（两种来源）：顺带声明 or 上一条 perm-intent 命令
            declared = pending_decl
            pi_perm = ""
            if isinstance(data.get("perm_intent_set"), dict):
                declared = data["perm_intent_set"]["action"]
                pi_perm = data["perm_intent_set"].get("permission") or ""
            if declared:
                loc += (f" ｜ 🎯**声明**权限意图 `{declared}`"
                        + (f"（{pi_perm}）" if pi_perm else ""))
                pending_decl = None               # 只标一次

            line = f"{n}. **{e['tool']}** {loc}"
            if why:
                line += f" —— {why}"

            # 误操作步骤：AI 如实记进 --why（好习惯），但回放者不该照做一遍多余的往返。
            # 弯路本身常有含义（如"排序后前 2 个不是节行"），故保留该步 + 标注可跳过。
            if why and any(k in why for k in _DETOUR):
                line += "\n   - ↩️ **误操作/弯路，回放可跳过**（保留以示当时的定位教训）"

            # 消解 rid 歧义：只在确认是弹窗时才记标题
            title = dialog_context(e.get("evidence"), cur_intent)
            if title:
                line += f"\n   - 🪟 弹窗：「{title}」"

            # 权限框的实际响应
            perm = data.get("permission") or {}
            if perm.get("clicks"):
                got = ", ".join(c["text"] for c in perm["clicks"])
                line += f"\n   - 🔐 权限弹窗自动响应：{got}"
            elif perm.get("detected"):
                line += f"\n   - 🔐 权限弹窗出现但未点击（可见：{perm.get('buttons')}）"

            if cur_intent and not declared:
                line += f"\n   - 权限意图（延续）：{cur_intent}"

            # ── 检查点：act 本身就带 activity（动作后的画面），直接当检查点用 ──
            # ⚠️ 这样「验证类步骤」不必再补一次独立 observe ——
            # `act --full` 一次调用就同时给了动作 + 全量节点，检查点照样有。
            # 只有"纯验证步"（该步没有 act）才需要单独 observe。
            ck = f"activity={data.get('activity')}" if data.get("activity") else ""
            if ck:
                if ck == last_ck:
                    ck_dup += 1
                    if ck_dup == 1 and any("👁" in x for x in lines[-6:]):
                        line += f"\n   - 👁 {ck}（与前一步相同，连续重复核对）"
                else:
                    last_ck, ck_dup = ck, 0
                    line += f"\n   - 👁 检查点：{ck}"
            lines.append(line)
        elif e["kind"] == "read":
            lines.append(f"   - 🔍 {e['tool']}：{e['detail']}")
        elif e["kind"] == "observe":
            ck = f"activity={data.get('activity')}"
            if ck == last_ck:
                # 连续重复的检查点（AI 习惯性"再看一眼"）不重复落行，只累计计数。
                # ⚠️ 只去重**连续**重复：跨步骤绕一圈回到同一页是有信息量的，不能全局去重。
                # ⚠️ 也不能让重复看起来像"刻意三重断言"——那等于把坏习惯教给回放者。
                ck_dup += 1
                if ck_dup == 1:
                    lines.append(f"   - 👁 检查点：{ck}（AI 当时在此页连续重复核对）")
            else:
                last_ck, ck_dup = ck, 0
                lines.append(f"   - 👁 检查点：{ck}")
        elif e["kind"] == "state":
            lines.append(f"   - ⚙️ {e['detail']}")
    if s.get("summary"):
        lines += ["", "## 结论", "", s["summary"]]
    lines += ["", "## 回放说明",
              "",
              "- 按步骤逐条执行，**每步核对返回**；任一步失配（元素找不到/状态不符）",
              "  → 回退完整 observe→决策流程，跑通后重新 export 覆盖本卡。",
              "- 权限准备与分支操作按当前用例和 SKILL 执行。",
              "- 带 🪟 的步骤说明当时是弹窗操作，`rid=button1` 之类**不能盲目复用**，",
              "  要按弹窗标题确认当前是哪一层弹窗。",
              "- 坐标为当次实测，⚠️ 标记的步骤回放前必须先 observe 校准。",
              "", f"> 提炼自会话 #{session_id}；回放失配 → 回退全流程并更新本卡。"]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def run_case_cmd(db, args) -> None:
    """用例库子命令：add/list/show/update/save（从会话提升）。"""
    if args.ccmd == "add":
        cid = db.add_case(maybe_file(args.title), maybe_file(args.input),
                          args.package)
        print(json.dumps({"ok": True, "case_id": cid,
                          "hint": "复跑：session.py start --case " + str(cid)},
                         ensure_ascii=False))
    elif args.ccmd == "list":
        cases = db.list_cases()
        print(json.dumps(cases, ensure_ascii=False, indent=2))
    elif args.ccmd == "show":
        c = db.get_case(args.id)
        if not c:
            raise SystemExit(f"用例 #{args.id} 不存在")
        print(json.dumps(c, ensure_ascii=False, indent=2))
    elif args.ccmd == "update":
        ok = db.update_case(args.id,
                            maybe_file(args.title) if args.title else None,
                            maybe_file(args.input) if args.input else None,
                            args.package)
        print(json.dumps({"ok": ok}, ensure_ascii=False))
    elif args.ccmd == "save":
        s = db.get_session(args.session)
        if not s:
            raise SystemExit(f"会话 #{args.session} 不存在")
        if not (s.get("user_input") or "").strip():
            raise SystemExit("该会话没有口述用例文本，无法提升")
        title = maybe_file(args.title) if args.title else (s.get("title") or f"会话{args.session}用例")
        if s.get("case_id"):
            db.update_case(s["case_id"], title=title, user_input=s["user_input"])
            cid = s["case_id"]
            action = "updated"
        else:
            cid = db.add_case(title, s["user_input"], s.get("package"))
            action = "created"
        print(json.dumps({"ok": True, "case_id": cid, "action": action,
                          "hint": "复跑：session.py start --case " + str(cid)},
                         ensure_ascii=False))


def main() -> None:
    p = argparse.ArgumentParser(description="测试会话生命周期")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("start")
    s.add_argument("--title", default=None)
    s.add_argument("--input", default=None, help="用户口述的用例原文（追溯锚点）")
    s.add_argument("--case", type=int, default=None, dest="case_id",
                   help="引用用例库：自动带出标题与用例文本，无需重复输入")
    s.add_argument("--device", default=None)
    s.add_argument("--diag", action="store_true",
                   help="标记为验证/调试会话：不进「测试记录」库、不计入仪表盘成功率。"
                        "用于工具自检、探针验证等非正式测试的跑动")
    s.add_argument("--package", default=None,
                   help="被测包名（强烈建议显式声明）：崩溃分级的 target 依据。"
                        "不声明则靠首个 observe 回填前台包——但被测 App 崩溃后"
                        "前台会回落到桌面，会把被测包崩溃误判成 other")
    s.add_argument("--related", default="",
                   help="关联包（逗号分隔），其崩溃同样按 BLOCKED 处理；"
                        "权限框宿主默认已含")

    s = sub.add_parser("finding")
    s.add_argument("--status", required=True, choices=STATUSES)
    s.add_argument("--expect", default="")
    s.add_argument("--actual", default="")
    s.add_argument("--note", default="")
    s.add_argument("--id", type=int, default=None,
                   help="记录到指定会话（暂停/等待中的会话用 --id）")

    s = sub.add_parser("finish")
    s.add_argument("--status", required=True, choices=STATUSES)
    s.add_argument("--summary", default="")
    s.add_argument("--package", default=None)
    s.add_argument("--no-runbook", action="store_true", dest="no_runbook",
                   help="PASS 时默认自动沉淀链路卡；加此参数跳过")
    s.add_argument("--id", type=int, default=None,
                   help="收尾指定会话（暂停/等待中的会话已解绑，须用 --id）")

    s = sub.add_parser("pause", help="遇阻暂停或向用户提问（中间态，记录保留可续跑）")
    s.add_argument("--reason", required=True, help="为什么停：卡在哪、试过什么")
    s.add_argument("--ask", action="store_true",
                   help="同时向用户提问（状态=waiting 而非 paused）")

    s = sub.add_parser("resume", help="恢复暂停/等待中的会话")
    s.add_argument("--id", type=int, required=True)
    s.add_argument("--note", default="", help="用户的答复或恢复原因，随事件入库")

    c = sub.add_parser("case", help="正式用例库：口述用例的沉淀与复用")
    csub = c.add_subparsers(dest="ccmd", required=True)
    ca = csub.add_parser("add")
    ca.add_argument("--title", required=True)
    ca.add_argument("--input", required=True)
    ca.add_argument("--package", default=None)
    csub.add_parser("list")
    cs = csub.add_parser("show")
    cs.add_argument("--id", type=int, required=True)
    cu = csub.add_parser("update")
    cu.add_argument("--id", type=int, required=True)
    cu.add_argument("--title", default=None)
    cu.add_argument("--input", default=None)
    cu.add_argument("--package", default=None)
    cv = csub.add_parser("save", help="把会话的口述用例提升为正式用例（首次跑新用例后用）")
    cv.add_argument("--session", type=int, required=True)
    cv.add_argument("--title", default=None, help="缺省沿用会话标题")

    s = sub.add_parser("perm-intent",
                       help="声明/查看/清除权限响应意图（act/observe 遇到权限弹窗时按此自动响应）")
    s.add_argument("--action", default=None, choices=["grant", "deny"],
                   help="遇到权限弹窗点【同意】(grant) 还是【拒绝】(deny)")
    s.add_argument("--perm", default="",
                   help="权限类型标记（如 media_images/camera/location），仅用于记录")
    s.add_argument("--clear", action="store_true", help="清除意图（分支测完就清）")
    s.add_argument("--show", action="store_true", help="只查看当前意图")
    s.add_argument("--id", type=int, default=None, help="指定会话（默认当前）")

    s = sub.add_parser("export", help="把会话事件流提炼成可回放链路卡（规划缓存）")
    s.add_argument("--id", type=int, required=True)
    s.add_argument("--out", default=None, help="输出路径，默认 knowledge/_runs/<包名>/<id>_<标题>.md")

    sub.add_parser("list")
    sub.add_parser("current")
    sub.add_parser("abandon", help="放弃当前会话（不写结论，仅解绑）")

    args = p.parse_args()
    db = get_db()

    if args.cmd == "start":
        case = db.get_case(args.case_id) if args.case_id else None
        if args.case_id and not case:
            raise SystemExit(f"用例 #{args.case_id} 不存在，session.py case list 查看")
        title = maybe_file(args.title) if args.title else (case["title"] if case else None)
        user_input = maybe_file(args.input) if args.input else (case["input"] if case else None)
        if not title or not user_input:
            raise SystemExit("需要 --case <id>（复用库中用例）或 --title/--input（新用例，"
                             "中文长文本用 @文件）")
        sid = db.start_session(title, user_input, args.device, case_id=args.case_id,
                               kind="diag" if args.diag else "test")
        set_current(sid)
        if args.package:
            # 显式声明优先：首个 observe 的 backfill 不会覆盖已有值
            db.set_package(sid, args.package)
        related = [x.strip() for x in args.related.split(",") if x.strip()]
        if related:
            db.set_related(sid, related)
        # 扩 logcat 缓冲区防冲（-G 5M）+ 清 crash 缓冲区归因；设备不在也不影响建会话
        from common import try_connect
        d = try_connect(args.device)
        # 将设备的 sdcard 初始化到一个相对干净的状态，并预置一些测试资源文件
        import sdcard
        sdcard.init(args.device)
        if d is not None:
            notes = []
            for cmd, okmsg in (("logcat -G 5M", "logcat 缓冲区已扩到 5M"),
                               ("logcat -b crash -c", "crash 缓冲区已清空")):
                try:
                    d.shell(cmd)
                    notes.append(okmsg)
                except Exception:
                    notes.append(f"{cmd} 失败（可手动 logcat.py setup / clear）")
            device_note = "；".join(notes)
        else:
            device_note = "设备未连接（连上后手动跑 logcat.py setup + logcat.py clear）"
        for stale in (ROOT / "storage").glob(".crash_seen_*"):
            stale.unlink(missing_ok=True)
        out = {"ok": True, "session_id": sid, "related": related,
               "note": f"后续 observe/act/read 自动记入本会话；{device_note}"}
        # 知识卡浮现：有卡就提示路径 + 小节索引（只提示一次，见 common.knowledge_hint）
        hint = knowledge_hint(args.package or (case["package"] if case else None))
        if hint:
            out["knowledge_hint"] = hint
            # 只要发出了 hint 就落标记（无卡包也有 system_card 提示，同样别重复发）
            db.mark_knowledge_shown(sid)
        print(json.dumps(out, ensure_ascii=False))
    elif args.cmd == "finding":
        sid = args.id if getattr(args, "id", None) else current_session()
        if not sid:
            raise SystemExit("没有进行中的会话，先 session.py start（或用 --id 指定）")
        fid = db.add_finding(sid, args.status, maybe_file(args.expect),
                             maybe_file(args.actual), maybe_file(args.note))
        print(json.dumps({"ok": fid is not None, "finding_id": fid}, ensure_ascii=False))
    elif args.cmd == "pause":
        sid = current_session()
        if not sid:
            raise SystemExit("没有进行中的会话")
        status = "waiting" if args.ask else "paused"
        db.set_session_status(sid, status)
        db.log_event(sid, "ask" if args.ask else "pause",
                     f"session {'ask' if args.ask else 'pause'}",
                     maybe_file(args.reason))
        clear_current()
        print(json.dumps({"ok": True, "session_id": sid, "status": status,
                          "note": ("把问题抛给用户，答复后用 resume --id 恢复"
                                   if args.ask else "已暂停；resume 续跑或 finish 收尾")},
                         ensure_ascii=False))
    elif args.cmd == "resume":
        # resume 也用于"崩溃终止后人工确认继续"：必须清除终态，否则工具仍拒绝执行。
        # ⚠️ 顺序要紧：先校验理由，**通过后才清终态**。
        # 曾经先 clear 再校验，导致"无理由被拒"的那次调用已把终态抹掉，
        # 第二次不带理由的 resume 反而放行（真实 bug）。
        was_terminated = db.get_termination(args.id)
        note = maybe_file(args.note) if args.note else ""
        if was_terminated and not note:
            raise SystemExit(
                f"会话 #{args.id} 因崩溃被终止，继续执行必须给出理由："
                f"resume --id {args.id} --note \"为什么可以继续（如已确认偶发、已恢复前置）\"")
        db.clear_termination(args.id)
        db.set_session_status(args.id, "running")
        set_current(args.id)
        if note:
            db.log_event(args.id, "note", "session resume", note)
        out = {"ok": True, "session_id": args.id, "status": "running"}
        if was_terminated:
            out["note"] = "已清除崩溃终态，会话恢复运行"
            out["was_terminated"] = True
            out["terminate_reason"] = was_terminated
        print(json.dumps(out, ensure_ascii=False))
    elif args.cmd == "finish":
        sid = args.id if getattr(args, "id", None) else current_session()
        if not sid:
            raise SystemExit("没有进行中的会话（暂停/等待中的会话用 --id 指定）")
        ok = db.finish_session(sid, args.status, maybe_file(args.summary), args.package)
        clear_current()
        crash_n = db.count_crash_events(sid)
        stats = db.finding_stats(sid)
        fail_n = stats.get("FAIL", 0)
        summary = maybe_file(args.summary)
        self_check = []
        if args.status == "PASS" and fail_n:
            self_check.append(f"⚠️ 存在 {fail_n} 条 FAIL 断言，结论不能是 PASS")
        if args.status == "FAIL" and not fail_n:
            self_check.append("⚠️ 结论 FAIL 但没有任何 FAIL 断言——补 finding，"
                              "或改用 BLOCKED（测不下去）/ ERROR（环境异常）")
        if args.status == "BLOCKED" and not crash_n and not summary.strip():
            self_check.append("⚠️ BLOCKED 需要归因（崩溃/前置不满足/找不到控件且人确认）"
                              "——summary 为空且无崩溃记录")
        if not stats and args.status in ("PASS", "FAIL"):
            self_check.append("⚠️ 没有任何断言记录，PASS/FAIL 结论缺乏依据")
        # bug1 修复：会话没有关联用例时主动提示入库。
        # 用例不会自动进库（什么时候沉淀是人的决定），但**必须提醒**，
        # 否则跑完的用例悄悄丢掉、仪表盘/用例库永远是旧的。
        case_hint = None
        row = db.get_session(sid) or {}
        if not row.get("case_id") and (row.get("user_input") or "").strip():
            case_hint = (f"本会话尚未进入用例库。沉淀为正式用例："
                         f"python session.py case save --session {sid}")
        # 崩溃终止过的会话：结论必须是 BLOCKED，否则与工具给出的终止理由矛盾
        term_reason = db.get_termination(sid)
        if term_reason and args.status != "BLOCKED":
            self_check.append(
                f"⚠️ 本会话因崩溃/ANR 被终止，结论应为 BLOCKED（当前 {args.status}）")

        # PASS 自动沉淀链路卡（回放缓存）。
        # 只在 PASS 时做：失败会话的链路没有回放价值，导出反而污染知识库。
        # 有 FAIL 断言时自检会告警、结论通常会被改掉，这里以传入的 status 为准。
        runbook_path = None
        if args.status == "PASS" and not fail_n and not getattr(args, "no_runbook", False):
            try:
                runbook_path = export_runbook(db, sid, None)
            except Exception as e:  # noqa: BLE001
                self_check.append(f"⚠️ 链路卡自动导出失败：{e}")

        out = {"ok": ok, "session_id": sid, "crash_events": crash_n,
               "findings": stats, "self_check": self_check,
               "case_hint": case_hint,
               "hint": (f"本会话有 {crash_n} 个崩溃事件——若涉及被测/关联包，"
                        "结论应为 BLOCKED 且报告需附 crash.log 证据路径；"
                        "无关包崩溃仅需在报告中说明")
               if crash_n else "无崩溃事件"}
        if runbook_path:
            out["runbook"] = runbook_path
            out["note"] = "已自动沉淀链路卡（复跑时按卡逐步执行，失配则回退全流程）"
        print(json.dumps(out, ensure_ascii=False))
    elif args.cmd == "case":
        run_case_cmd(db, args)
    elif args.cmd == "abandon":
        clear_current()
        print(json.dumps({"ok": True}, ensure_ascii=False))
    elif args.cmd == "perm-intent":
        sid = args.id if getattr(args, "id", None) else current_session()
        if not sid:
            raise SystemExit("没有进行中的会话（或用 --id 指定）")
        if args.clear:
            db.clear_perm_intent(sid)
            print(json.dumps({"ok": True, "session_id": sid, "intent": None,
                              "note": "权限意图已清除"}, ensure_ascii=False))
        elif args.show or not args.action:
            cur = db.get_perm_intent(sid)
            print(json.dumps({"ok": True, "session_id": sid, "intent": cur,
                              "hint": "声明：perm-intent --action grant|deny [--perm 类型]"
                              } if cur else {
                                  "ok": True, "session_id": sid, "intent": None,
                                  "hint": "当前无意图：遇到权限弹窗只会记录、不会点击"},
                             ensure_ascii=False))
        else:
            ok = db.set_perm_intent(sid, args.action, args.perm)
            db.log_event(sid, "perm", "perm-intent",
                         f"权限意图: {args.action}"
                         + (f"（{args.perm}）" if args.perm else ""))
            print(json.dumps({"ok": ok, "session_id": sid,
                              "intent": {"action": args.action, "permission": args.perm},
                              "hint": (f"后续 act/observe 遇到权限弹窗将自动点"
                                       f"【{'同意' if args.action == 'grant' else '拒绝'}】"
                                       f"；分支测完请 perm-intent --clear")},
                             ensure_ascii=False))
    elif args.cmd == "export":
        path = export_runbook(db, args.id, args.out)
        print(json.dumps({"ok": True, "path": path}, ensure_ascii=False))
    elif args.cmd == "list":
        print(json.dumps(db.list_sessions(20), ensure_ascii=False, indent=2))
    elif args.cmd == "current":
        print(json.dumps({"session_id": current_session()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
