"""执行前批量授权；沿用系统命令及返回判据，结果记入当前会话。"""
import re

from common import connect, log_auto


def _command_ok(response) -> bool:
    return response.exit_code == 0 and not re.search(
        r"(?im)^\s*(?:Error\b|Failure\b|Exception\b|java\.)", response.output or "")


def grant_all(d, pkg: str) -> dict:
    """调用系统命令批量授权，返回命令执行结果。"""
    # 缺包名会使原生命令作用于全部包；校验只用于批量授权。
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*", pkg):
        raise ValueError("必须提供已确定的单个包名；包名不明时跳过准备")
    response = d.shell(["pm", "grant", "--all-permissions", pkg])
    ok = _command_ok(response)
    return {"cmd": "grant", "package": pkg, "user": 0, "all_permissions": True,
            "output": (response.output or "").strip(), "exit_code": response.exit_code,
            "ok": ok,
            "hint": "批量授权命令执行成功。" if ok else "批量授权命令失败，请检查 output。"}


def prepare(serial: str, package: str) -> dict:
    """为指定设备和 App 批量授权，返回并记录实际执行结果。"""
    result = {"ok": False, "action": "grant_all", "serial": serial,
              "package": package, "status": "INFO"}
    try:
        if not serial or not serial.strip():
            raise ValueError("必须显式指定设备 serial，批量授权未执行")
        device = connect(serial)
        result.update(grant_all(device, package))
    except Exception as exc:
        result["error"] = str(exc)
    outcome = "执行成功" if result["ok"] else "执行失败"
    detail = f"批量授权 {package} → {outcome}"
    if "error" in result:
        detail += ": " + result["error"]
    log_auto("preparation", "prepare grant-all", detail, result)
    return result
