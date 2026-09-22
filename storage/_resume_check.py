# -*- coding: utf-8 -*-
"""决定性实验：resume 的清终态时序（子进程输出按 GBK 容错解码）。"""
import subprocess
import sys

sys.path.insert(0, "tools")
from db import current_session, get_db, set_current  # noqa: E402

db = get_db()
sid = db.start_session("resume-timing-test", "t")
set_current(sid)
db.terminate_session(sid, "FATAL EXCEPTION test")
print("step1 terminated=", db.get_termination(sid))


def run_resume(*extra):
    r = subprocess.run([sys.executable, "tools/session.py", "resume",
                        "--id", str(sid), *extra], capture_output=True)
    out = r.stdout.decode("utf-8", errors="replace").strip()
    err = r.stderr.decode("gbk", errors="replace").strip()
    return r.returncode, out, err


# 无 note 的 resume：预期拒绝（exit 1）
rc, out, err = run_resume()
print("step2 refused=", rc == 1, "| stderr=", err[:60])
print("step3 terminated_after_refusal=", db.get_termination(sid))
print("step4 current_after_refusal=", current_session())

# 有 note 的 resume：预期解锁
rc, out, err = run_resume("--note", "confirmed ok")
print("step5 resume_ok=", rc == 0, "| out=", out[:80])
print("step6 terminated_after_note_resume=", db.get_termination(sid))

# 清理
db._conn().execute("DELETE FROM events WHERE session_id=?", (sid,))
db._conn().execute("DELETE FROM sessions WHERE id=?", (sid,))
db._conn().commit()
if current_session() == sid:
    from db import clear_current
    clear_current()
print("DONE")
