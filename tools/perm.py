"""perm：系统权限弹窗的检测与响应（确定性，不依赖 AI 现场决策）。

设计参考 AiAgentTest 的 set_permission_intent 体系，解决一个硬约束：

    **系统权限框约 6 秒未点击会自动消失**（Android 通用机制），
    而"该同意还是该拒绝"需要读懂用例语义（慢）。
    决策与执行必须解耦——AI 事先声明意图（session.py perm-intent），
    工具在动作时按意图秒级响应。

匹配规则（rid 优先，与文案/语言无关）：
  grant：permission_allow_all_button(全量) > foreground_only > allow
  deny ：只认 permission_deny_button，**绝不点** deny_and_dont_ask_again
         （点了会设 don't-ask-again，导致后续"授予"分支弹窗不再出现）
不匹配的按钮（如"选择照片"部分媒体、"前往设置"）一律不点，交回 AI。
"""
from __future__ import annotations

import re
import time

# 系统权限弹窗的 activity 标记（大小写不敏感）
ACTIVITY_MARKERS = ("permissioncontroller", "grantpermissionsactivity")

# rid → 优先级（数字越小越优先）。grant 时优先"最小够用"的授权范围：
# 全量授权(1) 优先于 前台(2) 优先于 基本/单次(2 同级按出现顺序)
_GRANT_RID_SCORES = {
    "permission_allow_all_button": 1,            # 媒体「全部允许」
    "permission_allow_always_button": 1,         # 「始终允许」
    "permission_allow_foreground_only_button": 2,
    "permission_allow_button": 2,
    "permission_allow_one_time_button": 2,
}
_DENY_RID = "permission_deny_button"
_DONT_ASK_AGAIN_RID = "permission_deny_and_dont_ask_again_button"

# 文案兜底（非标准 OEM / 自定义 rid）
_GRANT_TEXTS = ("仅在使用中允许", "仅本次使用时允许", "始终允许", "全部允许",
                "允许访问所有照片", "允许", "同意", "Allow")
_DENY_TEXTS = ("拒绝", "不允许", "禁止", "Deny", "Don't allow")

# 明令排除：这些文案/rid 永不自动点
_EXCLUDE_TEXTS = ("选择照片", "仅选择照片", "允许访问所选照片", "前往设置",
                  "拒绝并不再询问", "拒绝且不再询问")
_EXCLUDE_RID_PARTS = (_DONT_ASK_AGAIN_RID, "dont_ask_again",
                      "permission_allow_selected_button")


def is_permission_activity(activity: str | None) -> bool:
    a = (activity or "").lower()
    return any(m in a for m in ACTIVITY_MARKERS)


def _bounds_center(bounds: str) -> tuple[int, int] | None:
    m = re.search(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]", bounds or "")
    if not m:
        return None
    x1, y1, x2, y2 = map(int, m.groups())
    return ((x1 + x2) // 2, (y1 + y2) // 2)


def list_buttons(xml_text: str) -> list[dict]:
    """从 UI 树里取出权限弹窗中"可见且有文字"的可点按钮。"""
    import xml.etree.ElementTree as ET
    out: list[dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out
    for el in root.iter("node"):
        a = el.attrib
        if a.get("clickable") != "true":
            continue
        text = (a.get("text") or "").strip()
        if not text:
            continue
        c = _bounds_center(a.get("bounds", ""))
        if not c:
            continue
        out.append({"text": text, "rid": a.get("resource-id", ""),
                    "center": list(c)})
    return out


def _excluded(btn: dict) -> bool:
    if any(x in btn["text"] for x in _EXCLUDE_TEXTS):
        return True
    rid = btn["rid"]
    return any(p in rid for p in _EXCLUDE_RID_PARTS)


def match_button(buttons: list[dict], action: str) -> dict | None:
    """按 action 选目标按钮。返回按钮 dict 或 None（不匹配则交回 AI）。"""
    cands = [b for b in buttons if not _excluded(b)]
    if not cands:
        return None

    if action == "deny":
        # 只认精确的"拒绝"rid；文案兜底也只认 _DENY_TEXTS
        for b in cands:
            if b["rid"].endswith(_DENY_RID):
                return b
        for b in cands:
            if b["text"] in _DENY_TEXTS:
                return b
        return None

    # grant：rid 命中的按下标打分取最优；都没命中再文案兜底
    best, best_score = None, None
    for b in cands:
        for key, score in _GRANT_RID_SCORES.items():
            if b["rid"].endswith(key) and (best_score is None or score < best_score):
                best, best_score = b, score
                break
    if best:
        return best
    for t in _GRANT_TEXTS:
        for b in cands:
            if b["text"] == t:
                return b
    return None


def detect(d, timeout_s: float = 0.8, interval_s: float = 0.2) -> dict | None:
    """有界轮询检测权限弹窗。

    返回 {"activity":..., "buttons":[...]} 或 None；只读不点。

    ⚠️ 默认窗口刻意取小（0.8s）：**屏幕上没有权限弹窗时也要空等到 deadline**，
    而每步 act/observe 都会调用一次 —— 3s 的默认值等于每步白等 3 秒。
    权限弹窗是**动作的直接结果**，渲染延迟 100~300ms，0.8s 已经足够；
    确实慢的设备用 timeout_s 显式加大（handle 的第二轮用 2s 兜底）。
    """
    deadline = time.time() + max(0.0, min(timeout_s, 8.0))
    while True:
        try:
            cur = d.app_current() or {}
            act = cur.get("activity") or ""
            if is_permission_activity(act):
                btns = list_buttons(d.dump_hierarchy())
                # activity 对了但还没渲染出按钮时继续等
                if btns:
                    return {"activity": act, "buttons": btns, "package": cur.get("package")}
        except Exception:  # noqa: BLE001
            pass
        if time.time() >= deadline:
            return None
        time.sleep(interval_s)


# 未声明意图时的默认动作。
# 规则（人明确要求）：**默认同意**——大多数 GUI 用例测的是"功能能不能用"，
# 授权只是通往功能的前置，不是被测对象；默认不点会让权限框 6 秒后自行消失，
# 后续步骤全部走不下去。
# 例外：用例明确要测"拒绝路径"时，用 session.py perm-intent --action deny 覆盖。
DEFAULT_ACTION = "grant"


def handle(d, action: str | None = None, timeout_s: float = 0.8,
           chain_max: int = 5, observe_only: bool = False) -> dict:
    """检测并按 action 处理权限弹窗（含链式多弹窗）。

    action=None → 用 DEFAULT_ACTION（grant，默认同意）。
    observe_only=True → 只检测不点击（调试/仅取证时用）。
    返回 {"detected","handled","clicks":[{text,rid,center}],"dialog_count",...}
    """
    result = {"detected": False, "handled": False, "clicks": [],
              "dialog_count": 0, "activity": None, "buttons": []}
    if not observe_only:
        result["action"] = action or DEFAULT_ACTION
        result["action_source"] = "declared" if action else "default"
    # ⚠️ 防重复点击同一个弹窗：链式循环本意是接住"连弹多个"，
    # 但若某次点击没能关掉弹窗（按钮无响应/被遮挡），循环会**反复点同一个按钮**
    # （实测 chain_max=5 时同一按钮被点 5 次）。用 (activity, 按钮文本) 去重。
    clicked_sig: set[tuple] = set()
    for i in range(max(1, chain_max)):
        info = detect(d, timeout_s=timeout_s if i == 0 else 2.0)
        if not info:
            break
        result["detected"] = True
        result["dialog_count"] = i + 1
        result["activity"] = info["activity"]
        result["buttons"] = [b["text"] for b in info["buttons"]]
        if observe_only:
            break                       # 只看不点
        btn = match_button(info["buttons"], action or DEFAULT_ACTION)
        if not btn:
            result["unmatched"] = True  # 弹窗在，但没有可点的匹配项 → 交回 AI
            break
        sig = (info["activity"], btn["text"])
        if sig in clicked_sig:
            # 同一个弹窗还没消失 → 不要再点，交回 AI（可能按钮无响应）
            result["stuck"] = True
            break
        clicked_sig.add(sig)
        try:
            d.click(*btn["center"])
            result["clicks"].append({"text": btn["text"], "rid": btn["rid"],
                                     "center": btn["center"]})
            result["handled"] = True
            time.sleep(0.3)             # 给下一个弹窗留渲染时间
        except Exception as e:  # noqa: BLE001
            result["click_error"] = str(e)
            break
    return result
