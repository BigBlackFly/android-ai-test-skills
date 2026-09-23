#!/usr/bin/env python3
"""本地 Web 测试台（v2）：测试会话时间线 + 知识库编辑。
零依赖：Python 标准库 http.server。

启动:  python webui.py [--port 8900]
访问:  http://127.0.0.1:8900
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from db import get_db  # noqa: E402

WEBUI_DIR = ROOT / "webui"
STORAGE_DIR = ROOT / "storage"
KNOWLEDGE_DIR = ROOT / "knowledge"
MD_NAME_RE = re.compile(r"^[\w\u4e00-\u9fff.\-]+\.md$")

# ── 视觉模型配置（OpenAI 兼容多模态通道，vision.py 消费）────────────
VISION_KEYS = ("base_url", "model", "api_key")


def _load_vision() -> dict:
    conf = {k: "" for k in VISION_KEYS}
    fp = STORAGE_DIR / "vision.json"
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for k in VISION_KEYS:
                conf[k] = str(data.get(k) or "")
    except (OSError, ValueError):
        pass
    return conf


def _save_vision(conf: dict) -> None:
    STORAGE_DIR.mkdir(exist_ok=True)
    (STORAGE_DIR / "vision.json").write_text(
        json.dumps(conf, ensure_ascii=False, indent=2), encoding="utf-8")


def _mask(s: str) -> str:
    """api_key 脱敏回显：只留首 4 与末 4 位。GET 绝不能返回明文。"""
    if not s:
        return ""
    if len(s) <= 8:
        return "*" * len(s)
    return s[:4] + "*" * (len(s) - 8) + s[-4:]


# 1x1 透明 PNG：视觉连通性测试用最小图，不依赖本地证据文件
_TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00"
    b"\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _test_vision() -> dict:
    """用已保存的配置做一次真实连通性验证（不发真图，只验鉴权+模型可用）。"""
    import base64
    import time
    import urllib.error
    import urllib.request

    conf = _load_vision()
    base = (conf.get("base_url") or "").rstrip("/")
    model = conf.get("model") or ""
    key = conf.get("api_key") or ""
    if not (base and model and key):
        return {"ok": False, "error": "配置不完整（base_url / model / api_key 均必填）"}

    b64 = base64.b64encode(_TINY_PNG).decode()
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "回复两个字：可用"},
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]}],
        "max_tokens": 20,
    }).encode()
    req = urllib.request.Request(
        base + "/chat/completions", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        ms = round((time.time() - t0) * 1000)
        text = data["choices"][0]["message"]["content"]
        return {"ok": True, "latency_ms": ms, "model": model,
                "reply": str(text)[:200],
                "usage": data.get("usage"),
                "hint": "连通成功：鉴权与模型均可用"}
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:300]
        except Exception:  # noqa: BLE001
            pass
        return {"ok": False, "error": f"HTTP {e.code} {e.reason}", "detail": detail,
                "hint": "401/403 多为 api_key 错误；404 多为 base_url 少了或多了 /v1"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {e}",
                "hint": "网络不可达或 base_url 写错（需含 http(s):// 与 /v1 前缀，视服务而定）"}

MIME = {".html": "text/html", ".js": "application/javascript",
        ".css": "text/css", ".png": "image/png", ".xml": "text/xml",
        ".json": "application/json", ".md": "text/markdown", ".log": "text/plain"}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json")

    def _static(self, relpath: str):
        fp = (WEBUI_DIR / relpath).resolve()
        # is_relative_to 而非 startswith：字符串前缀会放过同前缀兄弟目录
        if not fp.is_relative_to(WEBUI_DIR) or not fp.is_file():
            return self._json({"error": "not found"}, 404)
        self._send(200, fp.read_bytes(), MIME.get(fp.suffix, "application/octet-stream"))

    def _replay(self, sid: int):
        """回放数据：把会话里有截图的事件串成"帧"。

        每帧 = {evidence(图片), x/y(点击坐标，仅动作有), size(原图尺寸),
                kind, action, via, why, detail, ts}

        ⚠️ **坐标换算交给前端按百分比做**：这里给的是**原图坐标系**的 x/y 和
        size，前端用 `left = x/size_w*100%` 定位 —— 这样图片无论被 CSS
        缩放成多大，圆点都不会偏。
        """
        s = get_db().get_session(sid)
        if not s:
            return self._json({"error": "not found"}, 404)

        frames = []
        for e in s.get("events") or []:
            ev = e.get("evidence")
            if not ev:
                continue
            try:
                j = json.loads(e.get("data_json") or "{}")
            except ValueError:
                j = {}
            act = j.get("action") or {}
            size = j.get("size") or []
            # action 字段可能没存（历史数据），从 detail 首段回退（如"点击 (x,y) via ..."）
            action = act.get("action") or ""
            if not action and e.get("detail"):
                action = str(e["detail"]).split(" ")[0]
            frames.append({
                "seq": e.get("seq"),
                "kind": e.get("kind"),
                "evidence": ev,
                "x": act.get("x"),
                "y": act.get("y"),
                "size": size if len(size) == 2 else None,
                "action": action,
                "via": act.get("via") or "",
                "why": act.get("why") or "",
                "detail": e.get("detail") or "",
                # 图还在不在（被 cleanup 轮转/误删后为 False）
                "ok": (ROOT / ev).is_file(),
            })

        missing = sum(1 for f in frames if not f["ok"])
        return self._json({
            "session_id": sid,
            "title": s.get("title") or f"会话 #{sid}",
            "status": s.get("status"),
            "frames": frames,
            "total": len(frames),
            "missing": missing,
            # 一张可用的图都没有 → 前端把回放入口置灰
            "playable": any(f["ok"] for f in frames),
        })

    def _storage_file(self, relpath: str):
        """伺服 storage 下的证据文件。

        ⚠️ 事件流里的 evidence 字段来自 common.rel()，是**项目根相对**路径
        （形如 `storage/evidence/.../shot.png`），而本函数历史上按
        **storage 相对**解析 → 拼成 storage/storage/... 恒 404（真实事故：
        记录里所有截图全空白）。故先按 storage 相对试，未命中再按项目根相对试。
        """
        candidates = [STORAGE_DIR / relpath]
        p = Path(relpath)
        if p.parts and p.parts[0] == STORAGE_DIR.name:
            candidates.append(ROOT / p)
        for fp in candidates:
            fp = fp.resolve()
            # is_relative_to 而非 startswith：字符串前缀会放过同前缀兄弟目录
            if fp.is_relative_to(STORAGE_DIR) and fp.is_file():
                return self._send(200, fp.read_bytes(),
                                  MIME.get(fp.suffix, "application/octet-stream"))
        return self._json({"error": "not found"}, 404)

    # ── GET ─────────────────────────────────────────────────────
    def do_GET(self):  # noqa: N802
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._static("index.html")
        if path.startswith("/static/"):
            return self._static(path[len("/static/"):])
        if path.startswith("/files/"):
            return self._storage_file(urllib.parse.unquote(path[len("/files/"):]))

        if path == "/api/sessions":
            # 默认只看正式测试记录；?all=1 追加**验证/调试**会话。
            # ⚠️ mock（占位/构造数据）**永不出现**——与 session_kind_counts()
            # 口径一致，否则"显示全部"会漏出 mock 而计数里又没有它。
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            show_all = qs.get("all", ["0"])[0] in ("1", "true")
            db = get_db()
            sessions = db.list_sessions(
                include=("test", "diag") if show_all else None,
                kind=None if show_all else "test")
            return self._json({"sessions": sessions,
                               "stats": db.session_stats(),
                               "kinds": db.session_kind_counts()})

        if path == "/api/vision":
            conf = _load_vision()
            conf["api_key_masked"] = _mask(conf.pop("api_key"))
            return self._json(conf)

        if path == "/api/modules":
            return self._json({"modules": get_db().module_stats()})

        if path == "/api/dashboard":
            db = get_db()
            return self._json({"overview": db.case_overview(),
                               "modules": db.module_stats(),
                               "recent": db.run_stats(3),
                               "sessions": db.session_stats()})

        if path == "/api/cases":
            return self._json({"items": get_db().list_cases()})

        m = re.match(r"^/api/cases/(\d+)$", path)
        if m:
            c = get_db().get_case(int(m.group(1)))
            return self._json(c if c else {"error": "not found"}, 200 if c else 404)

        m = re.match(r"^/api/sessions/(\d+)/replay$", path)
        if m:
            return self._replay(int(m.group(1)))

        m = re.match(r"^/api/sessions/(\d+)$", path)
        if m:
            s = get_db().get_session(int(m.group(1)))
            return self._json(s if s else {"error": "not found"},
                              200 if s else 404)

        if path == "/api/knowledge":
            items = []
            if KNOWLEDGE_DIR.is_dir():
                for fp in sorted(KNOWLEDGE_DIR.glob("*.md")):
                    st = fp.stat()
                    items.append({"name": fp.name, "size": st.st_size,
                                  "mtime": datetime.fromtimestamp(st.st_mtime)
                                  .isoformat(timespec="seconds")})
            return self._json({"items": items})

        m = re.match(r"^/api/knowledge/(.+\.md)$", path)
        if m:
            name = urllib.parse.unquote(m.group(1))
            if not MD_NAME_RE.match(name):
                return self._json({"error": "bad name"}, 400)
            fp = KNOWLEDGE_DIR / name
            if not fp.is_file():
                return self._json({"error": "not found"}, 404)
            return self._json({"name": name, "content": fp.read_text(encoding="utf-8")})

        return self._json({"error": "not found"}, 404)

    # ── POST ────────────────────────────────────────────────────
    def do_POST(self):  # noqa: N802
        path = urllib.parse.urlparse(self.path).path

        if path == "/api/vision":
            length = int(self.headers.get("Content-Length") or 0)
            try:
                data = json.loads(self.rfile.read(length).decode("utf-8"))
            except ValueError:
                return self._json({"error": "bad body"}, 400)
            conf = _load_vision()
            for k in VISION_KEYS:
                v = str(data.get(k) or "").strip()
                # api_key 留空 = 保留原值（避免只想改 model 却清掉密钥）
                if v or not (k == "api_key" and conf["api_key"]):
                    conf[k] = v
            _save_vision(conf)
            return self._json({"ok": True})

        if path == "/api/vision/test":
            return self._json(_test_vision())

        m = re.match(r"^/api/cases/(\d+)/kind$", path)
        if m:
            length = int(self.headers.get("Content-Length") or 0)
            try:
                data = json.loads(self.rfile.read(length).decode("utf-8"))
            except ValueError:
                return self._json({"error": "bad body"}, 400)
            ok = get_db().set_case_kind(int(m.group(1)), str(data.get("kind") or ""))
            return self._json({"ok": ok}, 200 if ok else 400)

        m = re.match(r"^/api/sessions/(\d+)/kind$", path)
        if m:
            length = int(self.headers.get("Content-Length") or 0)
            try:
                data = json.loads(self.rfile.read(length).decode("utf-8"))
            except ValueError:
                return self._json({"error": "bad body"}, 400)
            ok = get_db().set_session_kind(int(m.group(1)), str(data.get("kind") or ""))
            return self._json({"ok": ok}, 200 if ok else 400)

        if path == "/api/cases":
            length = int(self.headers.get("Content-Length") or 0)
            try:
                data = json.loads(self.rfile.read(length).decode("utf-8"))
            except ValueError:
                return self._json({"error": "bad body"}, 400)
            title = str(data.get("title") or "").strip()
            inp = str(data.get("input") or "").strip()
            if not (title and inp):
                return self._json({"ok": False,
                                   "error": "标题与用例原文均必填"}, 400)
            cid = get_db().add_case(title, inp,
                                    str(data.get("package") or "").strip() or None)
            return self._json({"ok": True, "case_id": cid})

        m = re.match(r"^/api/cases/(\d+)$", path)
        if m:
            length = int(self.headers.get("Content-Length") or 0)
            try:
                data = json.loads(self.rfile.read(length).decode("utf-8"))
            except ValueError:
                return self._json({"error": "bad body"}, 400)
            ok = get_db().update_case(int(m.group(1)),
                                      data.get("title") or None,
                                      data.get("input") or None,
                                      data.get("package") or None)
            return self._json({"ok": ok})

        m = re.match(r"^/api/knowledge/(.+\.md)$", path)
        if not m:
            return self._json({"error": "not found"}, 404)
        name = urllib.parse.unquote(m.group(1))
        if not MD_NAME_RE.match(name):
            return self._json({"error": "bad name"}, 400)
        length = int(self.headers.get("Content-Length") or 0)
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            content = data["content"]
            if not isinstance(content, str):
                raise ValueError
        except (ValueError, KeyError):
            return self._json({"error": "bad body"}, 400)
        KNOWLEDGE_DIR.mkdir(exist_ok=True)
        (KNOWLEDGE_DIR / name).write_text(content, encoding="utf-8")
        return self._json({"ok": True})

    def do_DELETE(self):  # noqa: N802
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        path = urllib.parse.urlparse(self.path).path
        m = re.match(r"^/api/cases/(\d+)$", path)
        if m:
            ok = get_db().delete_case(int(m.group(1)))
            return self._json({"ok": ok}, 200 if ok else 404)
        m = re.match(r"^/api/sessions/(\d+)$", path)
        if m:
            # 默认连带删除磁盘证据；?evidence=0 只删库记录
            keep_ev = qs.get("evidence", ["1"])[0] in ("0", "false")
            r = get_db().delete_session(int(m.group(1)), remove_evidence=not keep_ev)
            return self._json(r, 200 if r.get("ok") else 404)
        return self._json({"error": "not found"}, 404)

    def log_message(self, *a):  # 静默访问日志
        pass


def main():
    ap = argparse.ArgumentParser(description="Android AI 测试台")
    ap.add_argument("--port", type=int, default=8900)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print("⚠️ 警告：绑定非回环地址——Web UI 无鉴权，知识库 POST 接口可被"
              "同网段任意改写，仅限可信内网短时使用！")
    print(f"测试台: http://{args.host}:{args.port}")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
