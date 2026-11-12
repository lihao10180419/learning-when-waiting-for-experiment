"""Setup, diagnose, verify and manage the installed experiment-learning plugin."""
from pathlib import Path
import argparse
from contextlib import closing
from datetime import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parent
from settings import CONFIG_PATH, CARDS_PATH, DATA_HOME, CODEX_STATE_HOME, initialize, load_config, save_config, paths, read_json, validate_cards
from codex_client import resolve_cli, backend_status

ENGINE_ACTIONS = {"run", "launch", "waiting", "busy", "attention", "result", "cancel", "start", "stop", "status", "pause", "resume", "today-off", "done", "later", "cleanup"}
START = "<!-- experiment-learning-plugin:start -->"
END = "<!-- experiment-learning-plugin:end -->"


def engine():
    import assistant
    assistant.init()
    return assistant


def bind(thread_id):
    thread = str(uuid.UUID(thread_id))
    if thread == os.environ.get("CODEX_THREAD_ID"):
        raise ValueError("Bind a separate learning thread, not the current main-project thread")
    config = load_config()
    if config.get("thread_id") and config["thread_id"] != thread:
        raise ValueError("This profile is already bound. Use a new EXPERIMENT_LEARNING_HOME for a different thread; existing queued messages cannot be moved.")
    a = engine()
    with a.connect() as db:
        if a.monitor_running(db):
            raise ValueError("Stop this profile's monitor before binding")
    config["thread_id"] = thread
    save_config(config)
    print(json.dumps({"thread_id": thread, "connection_verified": config.get("connection_verified", False), "next": "Run manage.py probe to verify an actual reply"}, ensure_ascii=False))


def probe(timeout, check_event=None):
    a = engine()
    if not a.CONFIG.get("thread_id"):
        raise ValueError("Bind a separate learning thread first")
    with a.connect() as db:
        if not check_event and a.monitor_running(db):
            raise ValueError("Stop the monitor before a connection probe")
        a.read_learning_messages(db)
        if check_event:
            selected = db.execute("SELECT kind FROM deliveries WHERE id=?", (check_event,)).fetchone()
            if not selected or selected["kind"] != "connection":
                raise ValueError("Select an existing connection probe from this profile")
            did = check_event
        else:
            did = a.queue_delivery(db, "connection:" + uuid.uuid4().hex, "connection", "连接测试。请只回复：学习窗口连接成功，并原样附上本事件编号。")
    if not check_event:
        a.deliver(did)
    deadline = time.monotonic() + timeout
    while True:
        with a.connect() as db:
            a.read_learning_messages(db)
            row = dict(db.execute("SELECT id,status,reply,warning FROM deliveries WHERE id=?", (did,)).fetchone())
        if row["status"] == "reply_confirmed":
            config = load_config()
            config.update(connection_verified=True, verified_at=time.time(), verified_event_id=did)
            save_config(config)
            print(json.dumps(row, ensure_ascii=False, indent=2))
            return 0
        if row["status"] == "send_failed" or check_event or time.monotonic() >= deadline:
            row["next"] = "Check this event again with probe --check-event ID; this never sends another message. For a resume warning, the target must be loaded or a supported local daemon must be available."
            print(json.dumps(row, ensure_ascii=False, indent=2))
            return 1 if row["status"] == "send_failed" else 3
        time.sleep(.25)


def instruction_block(config):
    executable = str(ROOT / "assistant.py").replace("\\", "/")
    selected_home = str(DATA_HOME).replace("\\", "/")
    return f'''{START}
## Experiment-wait learning (opt-in integration)

Assistant executable: `{executable}`. Profile: `{selected_home}`.
Use the `EXPERIMENT_LEARNING_HOME` environment variable for this profile when invoking the assistant, or its matching default profile. Learning-thread UUID: `{config['thread_id']}`. Never invoke this assistant from that learning thread.

For noninteractive local experiments expected to be long, automatically preserve the original interpreter, argument array, cwd and environment through `python <assistant> run --id JOB-<unique> --cwd <original-cwd> --label <safe-short-name> [--expected-seconds <known-total>] -- <executable> <original-arguments...>`. Do not classify experiments from command keywords alone. Ordinary file operations and short checks do not need wrapping.

For explicitly noninteractive background jobs use `launch` with the same arguments; it confirms the actual PID and captures local stdout/stderr. After termination, `result --run JOB-ID --follow` returns captured streams and the original exit code. Keep `run` for tasks that need stdin.

Only after the OS confirms the experiment running AND the main Codex is actually waiting for results, with no pending approval, input or other work, write `waiting --run JOB-ID [OTHER-JOB-ID ...]`. Before doing other work write `busy --run JOB-ID`; when permission, input or human handling is needed write `attention --run JOB-ID`. These markers never cancel the experiment. No waiting marker means no learning card. Do not use --test on real jobs.

Known total runtime >=600s plus >=30s stable execution, or unknown total runtime plus >=180s actual execution, can qualify for learning. Never invent remaining time. A local wrapper cannot treat SSH submission completion as completion of a remote job. Do not restart or guess-attach existing experiments.

Use `status` to inspect state. Respect Pause and Stop; do not restart a manually stopped monitor in the same app session. An explicitly enabled local desktop-open watcher may start it on the next Codex process session. Pause/Stop never terminate experiments. Only use `cancel --run JOB-ID` for an explicit cancellation request.
{END}'''


def integrate(scope, project=None, remove=False):
    if scope == "user":
        target = CODEX_STATE_HOME / ("AGENTS.override.md" if (CODEX_STATE_HOME / "AGENTS.override.md").exists() else "AGENTS.md")
    else:
        if not project:
            raise ValueError("Project integration requires --project PATH")
        project_root = Path(project).expanduser().resolve()
        if not project_root.is_dir():
            raise ValueError("Project directory does not exist")
        target = project_root / "AGENTS.md"
    before = target.read_bytes() if target.exists() else b""
    text = before.decode("utf-8-sig")
    if "<!-- experiment-wait-learning:start -->" in text:
        raise ValueError("A legacy one-off learning assistant is already integrated. Stop/disable that installation and remove its own marked block before migrating.")
    if (START in text) != (END in text):
        raise ValueError("Incomplete marked block; existing instructions were not changed")
    config = load_config()
    if not remove and not config.get("connection_verified"):
        raise ValueError("Verify the target connection before installing automatic project instructions")
    if START in text:
        start, end = text.index(START), text.index(END) + len(END)
        updated = text[:start] + ("" if remove else instruction_block(config)) + text[end:]
    elif remove:
        updated = text
    else:
        updated = text + ("\n\n" if text else "") + instruction_block(config) + "\n"
    if updated != text:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            backup = target.with_name(target.name + ".experiment-learning-backup-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
            shutil.copy2(target, backup)
        bom = b"\xef\xbb\xbf" if before.startswith(b"\xef\xbb\xbf") else b""
        target.write_bytes(bom + updated.encode("utf-8"))
    print(json.dumps({"target": str(target), "installed": not remove, "changed": updated != text,
                      "previous_sha256": hashlib.sha256(before).hexdigest()}, ensure_ascii=False))


def doctor():
    config = load_config()
    binary = resolve_cli(config)
    report = {"platform": sys.platform, "python": sys.version.split()[0], "paths": paths(),
              "thread_bound": bool(config.get("thread_id")), "connection_verified": config.get("connection_verified", False),
              "codex_found": bool(shutil.which(binary)), "codex_executable": binary, "queue_supported": False}
    if report["codex_found"]:
        for command, key in (([binary, "--version"], "codex_version"), ([binary, "queue", "--help"], "queue_help")):
            completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=12)
            if key == "codex_version":
                report[key] = completed.stdout.strip()
            else:
                report["queue_supported"] = completed.returncode == 0 and all(flag in completed.stdout for flag in ("--thread", "--message", "--resume"))
    report["local_daemon"] = backend_status(binary)
    report["real_reply_still_required"] = True
    report["supported_platform"] = os.name == "nt"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["supported_platform"] and report["queue_supported"] and report["local_daemon"]["reachable"] else 1


def set_cli(executable):
    selected = resolve_cli({"codex_executable": executable})
    config = load_config()
    a = engine()
    with a.connect() as db:
        if a.monitor_running(db):
            raise ValueError("Stop this profile's monitor before changing its CLI; experiments keep running")
    version = subprocess.run([selected, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=12)
    help_result = subprocess.run([selected, "queue", "--help"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=12)
    if version.returncode or "codex-cli " not in version.stdout or help_result.returncode or not all(flag in help_result.stdout for flag in ("--thread", "--message", "--resume")):
        raise ValueError("Selected executable does not provide the required Codex CLI queue interface")
    config.update(codex_executable=selected, connection_verified=False)
    config.pop("verified_at", None)
    config.pop("verified_event_id", None)
    save_config(config)
    print(json.dumps({"codex_executable": selected, "version": version.stdout.strip(), "connection_verified": False,
                      "next": "Check backend status/start, then verify a real probe"}, ensure_ascii=False))
    return 0


def backend(action):
    config = load_config()
    binary = resolve_cli(config)
    if action == "status":
        status = backend_status(binary)
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0 if status["reachable"] else 1
    if config.get("thread_id") and config["thread_id"] == os.environ.get("CODEX_THREAD_ID"):
        raise ValueError("Do not start backend services from the learning thread")
    # Explicit user action only. The monitor and watcher never start/restart a
    # Codex daemon. This command is idempotent and never invokes stop/update.
    result = subprocess.run([binary, "app-server", "daemon", "start"], timeout=60)
    return result.returncode


def cards(action, source=None):
    initialize()
    selected = Path(source).expanduser().resolve() if source else CARDS_PATH
    material = validate_cards(read_json(selected))
    if action == "import":
        a = engine()
        with a.connect() as db:
            if a.monitor_running(db):
                raise ValueError("Stop this profile's monitor before importing cards; experiments keep running")
        backup = CARDS_PATH.with_name("cards.backup-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".json")
        shutil.copy2(CARDS_PATH, backup)
        temporary = CARDS_PATH.with_suffix(".tmp")
        temporary.write_text(json.dumps(material, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        temporary.replace(CARDS_PATH)
    print(json.dumps({"valid": True, "card_count": len(material), "imported": action == "import"}, ensure_ascii=False))
    return 0


def main():
    # Stop remains available even after a user accidentally breaks config/cards.
    # This flag never signals or cancels the experiment workers.
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        import sqlite3
        database = DATA_HOME / "runtime" / "state.sqlite3"
        if database.exists():
            with closing(sqlite3.connect(database, timeout=10)) as db, db:
                db.execute("INSERT OR REPLACE INTO settings VALUES('stop_requested','1')")
        print("Monitor stop requested; experiments keep running.")
        return 0
    if len(sys.argv) > 1 and sys.argv[1] in ENGINE_ACTIONS:
        return subprocess.call([sys.executable, "-X", "utf8", str(ROOT / "assistant.py"), *sys.argv[1:]])
    p = argparse.ArgumentParser(description=__doc__)
    subs = p.add_subparsers(dest="command", required=True)
    for name in ("init", "paths", "doctor", "enable-autostart", "disable-autostart"):
        subs.add_parser(name)
    q = subs.add_parser("bind")
    q.add_argument("--thread", required=True)
    q = subs.add_parser("set-cli", help="Select an existing complete native Codex CLI for this profile")
    q.add_argument("--executable", required=True)
    q = subs.add_parser("backend", help="Local-only diagnostics, or an explicitly requested daemon start")
    q.add_argument("backend_action", choices=("status", "start"))
    q = subs.add_parser("probe", help="One explicit model-backed connection test; accepted queue is not a confirmed reply")
    q.add_argument("--timeout", type=float, default=60)
    q.add_argument("--check-event", help="Read an existing probe result without sending another model message")
    q = subs.add_parser("integrate")
    q.add_argument("--scope", choices=("user", "project"), required=True)
    q.add_argument("--project")
    q.add_argument("--remove", action="store_true")
    q = subs.add_parser("cards", help="Validate or import user-authored JSON cards without calling a model")
    cq = q.add_subparsers(dest="cards_action", required=True)
    cq.add_parser("validate").add_argument("--file")
    cq.add_parser("import").add_argument("--file", required=True)
    args = p.parse_args()
    if args.command == "paths":
        print(json.dumps(paths(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "init":
        initialize()
        print(json.dumps(paths(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "doctor":
        return doctor()
    if args.command == "set-cli":
        return set_cli(args.executable)
    if args.command == "backend":
        return backend(args.backend_action)
    if args.command == "bind":
        initialize()
        bind(args.thread)
        return 0
    if args.command == "probe":
        if not 0 < args.timeout <= 300:
            raise ValueError("Probe timeout must be >0 and <=300 seconds")
        return probe(args.timeout, args.check_event)
    if args.command == "integrate":
        integrate(args.scope, args.project, args.remove)
        return 0
    if args.command == "cards":
        return cards(args.cards_action, args.file)
    if args.command == "disable-autostart":
        from codex_autostart import disable
        return disable()
    if args.command == "enable-autostart":
        config = load_config()
        if not config.get("connection_verified"):
            raise ValueError("Verify the learning thread before enabling automatic startup")
        if os.name != "nt":
            raise ValueError("Autostart is supported on Windows only")
        return subprocess.call(["powershell.exe", "-NoProfile", "-File", str(ROOT / "install_autostart.ps1")])
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
