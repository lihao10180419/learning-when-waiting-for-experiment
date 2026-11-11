"""Local Codex experiment-wait learning assistant. Python stdlib only."""
from __future__ import annotations

import argparse
import concurrent.futures
import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parent
from settings import DATA_HOME, CONFIG_PATH, CARDS_PATH, CODEX_STATE_HOME, load_config, load_cards
RUNTIME = DATA_HOME / "runtime"
DB = RUNTIME / "state.sqlite3"
CONFIG = load_config()
CARDS = load_cards()
LOCAL_TZ = timezone(timedelta(hours=CONFIG["utc_offset_hours"]))
TERMINAL = ("completed", "failed", "cancelled", "spawn_failed", "lost")


def uid(prefix):
    return prefix + "-" + uuid.uuid4().hex[:16]


def connect():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=10000")
    return db


def init():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS jobs(
          id TEXT PRIMARY KEY, origin TEXT, project TEXT, label TEXT, state TEXT,
          pid INTEGER, birth TEXT, started REAL, ended REAL, heartbeat REAL,
          expected REAL, test INTEGER, exit_code INTEGER, cancel INTEGER DEFAULT 0,
          wait_id TEXT, stdout_path TEXT, stderr_path TEXT);
        CREATE TABLE IF NOT EXISTS waits(
          id TEXT PRIMARY KEY,origin TEXT,state TEXT,created REAL,closed REAL,
          card_event TEXT,return_event TEXT);
        CREATE TABLE IF NOT EXISTS events(
          id TEXT PRIMARY KEY,at REAL,kind TEXT,job_id TEXT,wait_id TEXT,detail TEXT);
        CREATE TABLE IF NOT EXISTS deliveries(
          id TEXT PRIMARY KEY,dedupe TEXT UNIQUE,kind TEXT,status TEXT,
          created REAL,queued REAL,confirmed REAL,card_id TEXT,wait_id TEXT,
          message TEXT,reply TEXT,warning TEXT,queue_id TEXT);
        CREATE TABLE IF NOT EXISTS progress(
          card_id TEXT PRIMARY KEY,state TEXT,last_seen REAL,completed_at REAL);
        """)


def setting(db, key, default=None):
    row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row[0] if row else default


def set_setting(db, key, value):
    db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, str(value)))


def event(db, kind, job=None, wait=None, detail=None):
    event_id = uid("EV")
    db.execute("INSERT INTO events VALUES(?,?,?,?,?,?)",
               (event_id, time.time(), kind, job, wait, json.dumps(detail or {}, ensure_ascii=False)))
    return event_id


def process_birth(pid):
    """OS creation time and live status; avoids treating PID reuse as recovery."""
    if os.name == "nt":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return None
        try:
            creation, end, kernel_time, user = (wintypes.FILETIME() for _ in range(4))
            code = wintypes.DWORD()
            if not kernel.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(end), ctypes.byref(kernel_time), ctypes.byref(user)):
                return None
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value != 259:
                return None
            return str((creation.dwHighDateTime << 32) | creation.dwLowDateTime)
        finally:
            kernel.CloseHandle(handle)
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    except OSError:
        return None


def is_live(job):
    return (job["state"] == "running" and not job["cancel"] and job["birth"] is not None
            and process_birth(job["pid"]) == job["birth"]
            and time.time() - job["heartbeat"] < 8)


def safe_label(value):
    return "".join(c for c in value if c.isprintable())[:60]


def queue_delivery(db, dedupe, kind, text, wait=None, card=None):
    old = db.execute("SELECT id FROM deliveries WHERE dedupe=?", (dedupe,)).fetchone()
    if old:
        return old[0]
    delivery_id = uid("LRN")
    message = (f"[学习助手事件 {delivery_id}]\n只负责学习讲解，不调用工具，不运行实验，不触发助手。"
               f"请在回复中原样保留事件编号 {delivery_id}，供本地确认真实回复。\n{text}")
    db.execute("INSERT INTO deliveries(id,dedupe,kind,status,created,card_id,wait_id,message) VALUES(?,?,?,?,?,?,?,?)",
               (delivery_id, dedupe, kind, "pending", time.time(), card, wait, message))
    event(db, "notification_pending", wait=wait, detail={"delivery_id": delivery_id, "thread_id": CONFIG["thread_id"]})
    return delivery_id


def deliver(delivery_id):
    """One attempt. An unknown acceptance is never retried automatically."""
    with connect() as db:
        row = db.execute("SELECT * FROM deliveries WHERE id=?", (delivery_id,)).fetchone()
        if not row or row["status"] != "pending":
            return
        if row["kind"] == "card":
            wait = db.execute("SELECT * FROM waits WHERE id=?", (row["wait_id"],)).fetchone()
            jobs = db.execute("SELECT * FROM jobs WHERE wait_id=? AND state='running'", (row["wait_id"],)).fetchall()
            if (not wait or wait["state"] != "waiting" or not jobs
                    or not all(is_live(j) for j in jobs)
                    or not reminders_allowed(db, all(j["test"] for j in jobs))):
                db.execute("UPDATE deliveries SET status='suppressed',warning='Waiting ended or reminders disabled before submission.' WHERE id=?", (delivery_id,))
                event(db, "stale_card_suppressed", wait=row["wait_id"], detail={"delivery_id": delivery_id})
                return
        db.execute("UPDATE deliveries SET status='sending' WHERE id=?", (delivery_id,))
    try:
        if not CONFIG.get("thread_id"):
            raise ValueError("No learning thread configured")
        result = subprocess.run(
            [shutil.which("codex") or "codex", "queue", "--thread", CONFIG["thread_id"],
             "--message", row["message"], "--resume"],
            cwd=ROOT.parent, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=CONFIG["queue_timeout_seconds"],
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        # Preserve warnings, but never interpret a successful process exit as a reply.
        accepted = result.returncode == 0 and "Queued message " in result.stdout
        status = "queued_accepted" if accepted else "send_failed"
        queue_id = result.stdout.split("Queued message ", 1)[-1].split(" ", 1)[0] if accepted else None
        warning = result.stderr.strip()[:2000]
    except subprocess.TimeoutExpired:
        status, warning, queue_id = "acceptance_unknown", "Queue timed out; not retried to avoid duplicate messages.", None
    except (OSError, ValueError) as exc:
        status, warning, queue_id = "send_failed", type(exc).__name__, None
    with connect() as db:
        db.execute("UPDATE deliveries SET status=CASE WHEN status='reply_confirmed' THEN status ELSE ? END,queued=?,warning=?,queue_id=? WHERE id=?",
                   (status, time.time() if accepted_if_known(status) else None, warning, queue_id, delivery_id))
        event(db, "notification_" + status, wait=row["wait_id"], detail={"delivery_id": delivery_id})


def accepted_if_known(status):
    return status == "queued_accepted"


def control(db, action):
    if action == "pause":
        set_setting(db, "paused", "1")
    elif action == "resume":
        set_setting(db, "paused", "0")
        set_setting(db, "off_date", "")
    elif action == "today-off":
        set_setting(db, "off_date", datetime.now(LOCAL_TZ).date().isoformat())
    elif action == "done":
        row = db.execute("SELECT card_id FROM progress WHERE state='in_progress' ORDER BY last_seen DESC LIMIT 1").fetchone()
        if row:
            db.execute("UPDATE progress SET state='completed',completed_at=? WHERE card_id=?", (time.time(), row[0]))
    elif action == "later":
        set_setting(db, "snooze_until", time.time() + 15 * 60)
    event(db, "control_" + action)


def read_learning_messages(db):
    """Read the installed version's JSONL. No undocumented network endpoints."""
    path = setting(db, "rollout_path")
    if not path or not Path(path).exists():
        # Only inspect file names for the exact selected UUID, not other chats.
        home = CODEX_STATE_HOME / "sessions"
        found = list(home.rglob("*" + CONFIG["thread_id"] + "*.jsonl")) if home.exists() else []
        if not found:
            set_setting(db, "reader_health", "unavailable_reply_unverified")
            return
        path = str(found[-1])
        set_setting(db, "rollout_path", path)
    offset_text = setting(db, "rollout_offset")
    if offset_text is None:
        set_setting(db, "rollout_offset", Path(path).stat().st_size)
        set_setting(db, "reader_health", "ready")
        return
    offset = int(offset_text)
    if offset > Path(path).stat().st_size:
        set_setting(db, "reader_health", "history_changed_reply_unverified")
        return
    with open(path, "rb") as stream:
        stream.seek(offset)
        while True:
            start = stream.tell()
            line = stream.readline()
            if not line or not line.endswith(b"\n"):
                stream.seek(start)
                break
            try:
                item = json.loads(line)
            except ValueError:
                continue
            data = item.get("payload", {})
            if item.get("type") != "response_item" or data.get("type") != "message":
                continue
            text = "\n".join(c.get("text", "") for c in data.get("content", []) if isinstance(c, dict))
            if data.get("role") == "assistant" and data.get("phase") == "final_answer":
                for delivery in db.execute("SELECT id,card_id,wait_id FROM deliveries WHERE status IN ('sending','queued_accepted','acceptance_unknown','reply_unverified','send_failed')").fetchall():
                    if delivery["id"] not in text:
                        continue
                    db.execute("UPDATE deliveries SET status='reply_confirmed',confirmed=?,reply=? WHERE id=?", (time.time(), text, delivery["id"]))
                    tracked = db.execute("SELECT * FROM jobs WHERE wait_id=?", (delivery["wait_id"],)).fetchall()
                    event(db, "reply_confirmed", wait=delivery["wait_id"], detail={"delivery_id": delivery["id"],
                          "jobs_at_confirmation": [{"id": j["id"], "state": j["state"], "os_process_live": is_live(j)} for j in tracked]})
                    if delivery["card_id"]:
                        db.execute("INSERT INTO progress(card_id,state,last_seen) VALUES(?,'in_progress',?) ON CONFLICT(card_id) DO UPDATE SET last_seen=excluded.last_seen",
                                   (delivery["card_id"], time.time()))
            elif data.get("role") == "user":
                action = {"暂停": "pause", "恢复": "resume", "今日不再提醒": "today-off", "已学完": "done", "稍后学": "later"}.get(text.strip())
                if action:
                    control(db, action)
        set_setting(db, "rollout_offset", stream.tell())
        set_setting(db, "reader_health", "ready")


def choose_card(db, budget):
    states = {row["card_id"]: row["state"] for row in db.execute("SELECT * FROM progress")}
    previous = db.execute("SELECT card_id FROM progress WHERE state='in_progress' ORDER BY last_seen DESC LIMIT 1").fetchone()
    if previous:
        return next((c for c in CARDS if c["id"] == previous[0]), None), True
    for card in CARDS:
        if card["minutes"] <= budget and states.get(card["id"]) != "completed" and all(states.get(p) == "completed" for p in card["prerequisites"]):
            return card, False
    return None, False


def reminders_allowed(db, test):
    if setting(db, "paused", "0") == "1":
        return False
    if setting(db, "off_date", "") == datetime.now(LOCAL_TZ).date().isoformat():
        return False
    if float(setting(db, "snooze_until", "0")) > time.time():
        return False
    hour = datetime.now(LOCAL_TZ).hour
    start, end = CONFIG["quiet_start"], CONFIG["quiet_end"]
    quiet = start <= hour < end if start < end else hour >= start or hour < end
    return test or not quiet


def tick(db):
    now = time.time()
    for job in db.execute("SELECT * FROM jobs WHERE state='running'").fetchall():
        if now - job["heartbeat"] > 10 and not is_live(job):
            db.execute("UPDATE jobs SET state='lost',ended=? WHERE id=?", (now, job["id"]))
            event(db, "monitor_lost", job["id"], job["wait_id"])
    for wait in db.execute("SELECT * FROM waits WHERE state IN ('waiting','attention')").fetchall():
        jobs = db.execute("SELECT * FROM jobs WHERE wait_id=?", (wait["id"],)).fetchall()
        if not jobs:
            continue
        active = [j for j in jobs if j["state"] == "running"]
        failed = any(j["state"] in ("failed", "spawn_failed", "lost", "cancelled") for j in jobs)
        needs_return = wait["state"] == "attention" or failed or not active
        if needs_return:
            if not wait["return_event"] and (wait["card_event"] or failed or wait["state"] == "attention") and reminders_allowed(db, all(j["test"] for j in jobs)):
                outcome = "需要你处理，请返回主项目" if wait["state"] == "attention" else ("实验失败、取消或监测中断，请返回主项目查看输出和退出码" if failed else "实验已完成，请返回主项目")
                states = "；".join(f"{j['label']}：{j['state']}，退出码 {j['exit_code']}" for j in jobs)
                did = queue_delivery(db, "return:" + wait["id"], "return", outcome + "。\n" + states + "\n保留未完成学习内容，不自动标记已学完。", wait["id"])
                db.execute("UPDATE waits SET return_event=? WHERE id=?", (did, wait["id"]))
            db.execute("UPDATE waits SET state='closed',closed=? WHERE id=?", (now, wait["id"]))
            event(db, "wait_closed", wait=wait["id"])
            continue
        if wait["card_event"]:
            continue
        # All registered running jobs in this origin must belong to the explicit wait.
        conflict = db.execute("SELECT 1 FROM jobs WHERE origin=? AND state='running' AND (wait_id IS NULL OR wait_id!=?)", (wait["origin"], wait["id"])).fetchone()
        if conflict or not all(is_live(j) for j in active):
            continue
        eligible = []
        for job in active:
            elapsed = now - job["started"]
            stable, minimum, unknown = (2, 10, 3) if job["test"] else (CONFIG["stable_seconds"], CONFIG["expected_min_seconds"], CONFIG["unknown_seconds"])
            if (job["expected"] is not None and job["expected"] >= minimum and elapsed >= stable) or (job["expected"] is None and elapsed >= unknown):
                eligible.append(job)
        if not eligible or not reminders_allowed(db, all(j["test"] for j in eligible)):
            continue
        test = all(j["test"] for j in eligible)
        unknown = any(j["expected"] is None for j in eligible)
        remaining = max((j["expected"] or 0) - (now - j["started"]) for j in eligible)
        if not unknown and not test and remaining < 300:
            continue
        budget = 5 if unknown or test or remaining < 600 else (10 if remaining < 1200 else 20)
        card, resume = choose_card(db, budget)
        labels = "、".join(j["label"] for j in active)
        timing = "剩余时长未知，可随时中断" if unknown else ("秒级流程测试，非真实学习时长" if test else f"按任务配置估计约剩余 {int(remaining / 60)} 分钟，可随时中断")
        if card:
            # Queue requests themselves are visible in the native conversation.
            # Never put the answer in the first visible request either.
            material = {k: card[k] for k in ("topic", "minutes", "explanation", "example", "question")}
            text = (f"实验已确认运行，主项目明确进入等待。{labels}。{timing}。\n"
                    + ("继续上次未完成内容。\n" if resume else "学习卡片（流程测试）。\n")
                    + "请直接展示标题、建议用时、核心解释、例子和自测题。原样保留标题与自测题，首次不要作答。"
                    + "用户回复‘显示答案’时再解释自测题答案；‘已学完’才推进。可回复：暂停／恢复／今日不再提醒／稍后学。\n"
                    + json.dumps(material, ensure_ascii=False))
        else:
            text = "实验等待已确认。当前没有符合先修条件的可用卡片，请用户补充学习目录。不要自行生成课程。"
        did = queue_delivery(db, "card:" + wait["id"], "card", text, wait["id"], card["id"] if card else None)
        db.execute("UPDATE waits SET card_event=? WHERE id=?", (did, wait["id"]))
        event(db, "card_triggered_while_running", wait=wait["id"], detail={"delivery_id": did, "jobs": [j["id"] for j in active], "test": test})


def serve():
    if not CONFIG.get("thread_id") or not CONFIG.get("connection_verified"):
        raise ValueError("A verified learning thread is required")
    import msvcrt
    lock = open(RUNTIME / "monitor.lock", "a+b")
    lock.seek(0)
    if not lock.read(1):
        lock.write(b"0")
        lock.flush()
    lock.seek(0)
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        print("Monitor already running.")
        return 0
    with connect() as db:
        set_setting(db, "monitor_pid", os.getpid())
        set_setting(db, "monitor_birth", process_birth(os.getpid()))
        set_setting(db, "stop_requested", "0")
        # A crash during submission has ambiguous acceptance; do not replay it.
        db.execute("UPDATE deliveries SET status='acceptance_unknown',warning='Monitor restarted during queue submission; no automatic resend.' WHERE status='sending'")
        event(db, "monitor_started")
    submitted = {}
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        while True:
            try:
                with connect() as db:
                    if setting(db, "stop_requested", "0") == "1":
                        break
                    read_learning_messages(db)
                    tick(db)
                    db.execute("UPDATE deliveries SET status='reply_unverified' WHERE status='queued_accepted' AND queued < ?", (time.time() - CONFIG["reply_timeout_seconds"],))
                    pending = [r[0] for r in db.execute("SELECT id FROM deliveries WHERE status='pending' ORDER BY created")]
                    set_setting(db, "monitor_heartbeat", time.time())
                for did in pending:
                    if did not in submitted:
                        submitted[did] = executor.submit(deliver, did)
            except Exception as exc:
                # Monitor failure must never stop or restart an experiment.
                print("Monitor tick:", type(exc).__name__, str(exc), flush=True)
            time.sleep(CONFIG["poll_seconds"])
    finally:
        executor.shutdown(wait=True)
        with connect() as db:
            set_setting(db, "monitor_heartbeat", "0")
            event(db, "monitor_stopped")
        lock.close()
    return 0


def monitor_running(db):
    pid, birth = setting(db, "monitor_pid"), setting(db, "monitor_birth")
    return bool(pid and birth and process_birth(int(pid)) == birth and time.time() - float(setting(db, "monitor_heartbeat", "0")) < 5)


def start():
    if os.name != "nt":
        raise ValueError("This release supports Windows only")
    if not CONFIG.get("thread_id"):
        raise ValueError("No learning thread bound. Run manage.py bind --thread UUID, then manage.py probe.")
    if not CONFIG.get("connection_verified"):
        raise ValueError("Connection is not verified. Run manage.py probe and confirm a real reply before starting.")
    with connect() as db:
        if monitor_running(db):
            print("监测器已运行；学习窗口 UUID：", CONFIG["thread_id"])
            return 0
    with open(RUNTIME / "monitor.log", "ab", buffering=0) as log:
        subprocess.Popen([sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "serve"], cwd=ROOT.parent,
                         stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                         creationflags=(subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == "nt" else 0)
    for _ in range(50):
        time.sleep(.1)
        with connect() as db:
            if monitor_running(db):
                print("监测器已启动；原生学习窗口：实验间隙学习；UUID：", CONFIG["thread_id"])
                return 0
    print("监测器未能确认启动，请检查 runtime/monitor.log。", file=sys.stderr)
    return 1


def stop_child(child, birth):
    if child.poll() is not None or process_birth(child.pid) != birth:
        return
    if os.name == "nt":
        subprocess.run(["taskkill.exe", "/PID", str(child.pid), "/T", "/F"], capture_output=True,
                       creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
    else:
        child.terminate()
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        child.kill()


def run(args):
    if not args.command:
        raise ValueError("Missing executable and argument array after --")
    origin = args.origin or os.environ.get("CODEX_THREAD_ID")
    if not origin:
        raise ValueError("Missing --origin or CODEX_THREAD_ID; cannot attach an explicit wait safely")
    if origin == CONFIG["thread_id"]:
        raise ValueError("Learning thread may not run experiments (recursion excluded)")
    command = args.command[1:] if args.command[0] == "--" else args.command
    run_id = args.id or uid("JOB")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", run_id):
        raise ValueError("Run id must contain only ASCII letters, digits, underscores or hyphens")
    logs = RUNTIME / "runs" / run_id
    logs.mkdir(parents=True, exist_ok=False)
    stdout_path, stderr_path = logs / "stdout.log", logs / "stderr.log"
    with connect() as db:
        db.execute("INSERT INTO jobs(id,origin,project,label,state,expected,test,stdout_path,stderr_path) VALUES(?,?,?,?,?,?,?,?,?)",
                   (run_id, origin, str(Path(args.cwd).resolve()), safe_label(args.label), "spawning", args.expected_seconds,
                    int(args.test), str(stdout_path), str(stderr_path)))
        event(db, "spawn_requested", job=run_id)
    interrupted = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: interrupted.set())
    try:
        child = subprocess.Popen(command, cwd=args.cwd, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
    except OSError as exc:
        with connect() as db:
            db.execute("UPDATE jobs SET state='spawn_failed',ended=?,exit_code=127 WHERE id=?", (time.time(), run_id))
            event(db, "spawn_failed", job=run_id, detail={"error_type": type(exc).__name__})
        print(f"实验启动失败 {run_id}: {exc}", file=sys.stderr)
        return 127
    birth = process_birth(child.pid)
    started = time.time()
    with connect() as db:
        db.execute("UPDATE jobs SET state='running',pid=?,birth=?,started=?,heartbeat=? WHERE id=?", (child.pid, birth, started, started, run_id))
        event(db, "process_started", job=run_id, detail={"pid": child.pid, "birth": birth})
    if args.id is None:
        print("学习助手实验 ID:", run_id, file=sys.stderr, flush=True)

    def tee(source, destination, path):
        with open(path, "wb", buffering=0) as log:
            while block := source.read1(65536):
                log.write(block)
                try:
                    destination.buffer.write(block)
                    destination.buffer.flush()
                except (BrokenPipeError, OSError, AttributeError):
                    pass

    threads = [threading.Thread(target=tee, args=(child.stdout, sys.stdout, stdout_path)),
               threading.Thread(target=tee, args=(child.stderr, sys.stderr, stderr_path))]
    for thread in threads:
        thread.start()
    cancelled = False
    try:
        while child.poll() is None:
            try:
                with connect() as db:
                    db.execute("UPDATE jobs SET heartbeat=? WHERE id=?", (time.time(), run_id))
                    cancel = db.execute("SELECT cancel FROM jobs WHERE id=?", (run_id,)).fetchone()[0]
            except sqlite3.Error:
                cancel = False
            if interrupted.is_set() or cancel:
                cancelled = True
                stop_child(child, birth)
                break
            time.sleep(.1)
        actual_exit = child.wait()
    finally:
        for thread in threads:
            thread.join()
    exit_code = 130 if cancelled else actual_exit
    state = "cancelled" if cancelled else ("completed" if exit_code == 0 else "failed")
    try:
        with connect() as db:
            db.execute("UPDATE jobs SET state=?,ended=?,exit_code=?,heartbeat=? WHERE id=?", (state, time.time(), exit_code, time.time(), run_id))
            event(db, state, job=run_id, detail={"exit_code": exit_code, "child_exit_code": actual_exit})
    except sqlite3.Error:
        print("监测状态保存失败；以下仍返回实验真实退出码。", file=sys.stderr)
    return exit_code


def launch(args):
    """Explicit detached mode for noninteractive jobs; foreground run keeps stdin."""
    run_id = args.id or uid("JOB")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", run_id):
        raise ValueError("Unsafe run id")
    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command:
        raise ValueError("Missing experiment argument array")
    worker = [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "run", "--id", run_id,
              "--cwd", args.cwd, "--label", args.label]
    if args.origin:
        worker += ["--origin", args.origin]
    if args.expected_seconds is not None:
        worker += ["--expected-seconds", str(args.expected_seconds)]
    if args.test:
        worker += ["--test"]
    worker += ["--", *command]
    with open(RUNTIME / f"{run_id}-wrapper.log", "ab", buffering=0) as log:
        proc = subprocess.Popen(worker, cwd=ROOT.parent, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                creationflags=(subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == "nt" else 0)
    for _ in range(100):
        with connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (run_id,)).fetchone()
        if row and row["state"] != "spawning":
            print(json.dumps({"run_id": run_id, "state": row["state"], "pid": row["pid"],
                              "process_confirmed": is_live(row), "exit_code": row["exit_code"]}, ensure_ascii=False))
            return 0 if row["state"] != "spawn_failed" else 127
        if proc.poll() is not None:
            print("包装器未能启动，请检查本地 wrapper.log。", file=sys.stderr)
            return proc.returncode
        time.sleep(.05)
    print("未能确认实验进程启动，不写入等待标记。", file=sys.stderr)
    return 2


def result(args):
    while True:
        with connect() as db:
            job = db.execute("SELECT * FROM jobs WHERE id=?", (args.run,)).fetchone()
        if job is None:
            raise ValueError("Unknown run id")
        if job["state"] in TERMINAL:
            break
        if not args.follow:
            print(json.dumps({"run_id": job["id"], "state": job["state"]}))
            return 3
        time.sleep(.2)
    for name, stream in (("stdout_path", sys.stdout), ("stderr_path", sys.stderr)):
        path = Path(job[name])
        if path.exists():
            stream.buffer.write(path.read_bytes())
            stream.buffer.flush()
    return job["exit_code"] if job["exit_code"] is not None else 125


def mark_wait(args):
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        jobs = [db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone() for job_id in args.run]
        if not jobs or any(j is None or not is_live(j) for j in jobs):
            print("未确认进程正在运行，拒绝写入等待标记。", file=sys.stderr)
            return 2
        origins = {j["origin"] for j in jobs}
        if len(origins) != 1:
            raise ValueError("One waiting mark must refer to one main Codex thread")
        origin = origins.pop()
        previous = db.execute("SELECT id FROM waits WHERE origin=? AND state='waiting' ORDER BY created DESC LIMIT 1", (origin,)).fetchone()
        wait_id = previous[0] if previous else uid("WAIT")
        if not previous:
            db.execute("INSERT INTO waits(id,origin,state,created) VALUES(?,?,'waiting',?)", (wait_id, origin, time.time()))
        for job in jobs:
            db.execute("UPDATE jobs SET wait_id=? WHERE id=?", (wait_id, job["id"]))
        event(db, "explicit_main_wait", wait=wait_id, detail={"jobs": args.run})
    print(wait_id)
    return 0


def status():
    from codex_autostart import status as autostart_status
    with connect() as db:
        result = {"monitor_running": monitor_running(db), "thread_id": CONFIG["thread_id"],
                  "codex_open_autostart": autostart_status(),
                  "reader_health": setting(db, "reader_health", "not_started"),
                  "paused": setting(db, "paused", "0") == "1", "off_date": setting(db, "off_date", ""),
                  "jobs": [dict(r) for r in db.execute("SELECT id,label,state,pid,started,ended,exit_code,wait_id,test FROM jobs ORDER BY rowid DESC LIMIT 15")],
                  "deliveries": [dict(r) for r in db.execute("SELECT id,kind,status,created,queued,confirmed,wait_id,warning FROM deliveries ORDER BY created DESC LIMIT 15")],
                  "progress": [dict(r) for r in db.execute("SELECT * FROM progress")]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main():
    init()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("start", "serve", "stop", "status", "pause", "resume", "today-off", "done", "later"):
        sub.add_parser(name)
    for name in ("run", "launch"):
        p = sub.add_parser(name, help="Run an argument array; launch is detached and noninteractive")
        p.add_argument("--id")
        p.add_argument("--origin")
        p.add_argument("--label", default="本机实验")
        p.add_argument("--cwd", default=str(Path.cwd()))
        p.add_argument("--expected-seconds", type=float)
        p.add_argument("--test", action="store_true", help="Only this job uses 2/3-second test thresholds and bypasses quiet hours")
        p.add_argument("command", nargs=argparse.REMAINDER)
    p = sub.add_parser("result")
    p.add_argument("--run", required=True)
    p.add_argument("--follow", action="store_true")
    p = sub.add_parser("waiting", help="Main agent's explicit waiting-for-results mark, AFTER process started")
    p.add_argument("--run", nargs="+", required=True)
    for name in ("attention", "busy", "cancel"):
        p = sub.add_parser(name)
        p.add_argument("--run", required=True)
    p = sub.add_parser("cleanup", help="Delete only old local run output; never running jobs or progress")
    p.add_argument("--older-than-days", type=int, default=7)
    args = parser.parse_args()
    if args.action == "start":
        return start()
    if args.action == "serve":
        return serve()
    if args.action == "run":
        return run(args)
    if args.action == "launch":
        return launch(args)
    if args.action == "result":
        return result(args)
    if args.action == "waiting":
        return mark_wait(args)
    if args.action == "status":
        return status()
    if args.action in ("attention", "busy", "cancel"):
        with connect() as db:
            job = db.execute("SELECT * FROM jobs WHERE id=?", (args.run,)).fetchone()
            if not job:
                raise ValueError("Unknown run id")
            if args.action == "cancel":
                db.execute("UPDATE jobs SET cancel=1 WHERE id=? AND state='running'", (args.run,))
            elif job["wait_id"]:
                db.execute("UPDATE waits SET state=? WHERE id=?", ("attention" if args.action == "attention" else "suspended", job["wait_id"]))
            event(db, args.action, job=job["id"], wait=job["wait_id"])
        return 0
    if args.action == "cleanup":
        if args.older_than_days < 1:
            raise ValueError("Minimum retention is one day")
        with connect() as db:
            rows = db.execute("SELECT id FROM jobs WHERE state IN ('completed','failed','cancelled','spawn_failed','lost') AND ended < ?", (time.time()-args.older_than_days*86400,)).fetchall()
            allowed_root = (RUNTIME / "runs").resolve()
            for row in rows:
                target = (allowed_root / row[0]).resolve()
                if target.parent != allowed_root:
                    raise ValueError("Unsafe cleanup path")
                if target.exists():
                    shutil.rmtree(target)
            print(f"已清理 {len(rows)} 个旧实验的输出目录；进度和事件保留。")
        return 0
    with connect() as db:
        if args.action == "stop":
            set_setting(db, "stop_requested", "1")
            print("已请求停止监测器；实验继续运行。")
        else:
            control(db, args.action)
            print("已保存：", args.action)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, sqlite3.Error) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
