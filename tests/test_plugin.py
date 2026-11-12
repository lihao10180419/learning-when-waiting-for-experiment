"""Offline tests: real child processes, isolated profiles, no real queue calls."""
from pathlib import Path
import importlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "experiment-learning" / "scripts"
ARTIFACTS = ROOT / ".test-artifacts"
ARTIFACTS.mkdir(exist_ok=True)
sys.path.insert(0, str(SCRIPTS))


class PluginTests(unittest.TestCase):
    def setUp(self):
        self.profile = Path(tempfile.mkdtemp(prefix="profile-", dir=ARTIFACTS)).resolve()
        self.assertEqual(self.profile.parent, ARTIFACTS.resolve())
        self.env_before = os.environ.get("EXPERIMENT_LEARNING_HOME")
        os.environ["EXPERIMENT_LEARNING_HOME"] = str(self.profile)
        import settings, assistant, codex_autostart, manage
        self.s = importlib.reload(settings)
        self.s.initialize()
        self.a = importlib.reload(assistant)
        self.w = importlib.reload(codex_autostart)
        self.m = importlib.reload(manage)
        self.a.init()
        self.a.CODEX_STATE_HOME = self.profile / "codex-fixtures"
        self.jobs = []

    def tearDown(self):
        for job in self.jobs:
            with self.a.connect() as db:
                row = db.execute("SELECT state FROM jobs WHERE id=?", (job,)).fetchone()
            if row and row[0] == "running":
                self.cli("cancel", "--run", job)
                self.cli("result", "--run", job, "--follow")
        if self.env_before is None:
            os.environ.pop("EXPERIMENT_LEARNING_HOME", None)
        else:
            os.environ["EXPERIMENT_LEARNING_HOME"] = self.env_before

    def cli(self, *args):
        return subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "manage.py"), *args], cwd=ROOT,
                              capture_output=True, encoding="utf-8", errors="replace", timeout=25)

    def launch(self, seconds, expected=15):
        job = "JOB-" + uuid.uuid4().hex[:12]
        args = ["launch", "--id", job, "--origin", "offline-test-main", "--test"]
        if expected is not None:
            args += ["--expected-seconds", str(expected)]
        args += ["--", sys.executable, "-u", str(SCRIPTS / "simulate.py"), "--seconds", str(seconds)]
        result = self.cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["process_confirmed"])
        self.jobs.append(job)
        return job

    def cards(self):
        with self.a.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM deliveries WHERE kind='card'")]

    def tick(self):
        with self.a.connect() as db:
            self.a.tick(db)

    def test_fresh_profile_is_unbound_and_initialization_preserves_edits(self):
        config = self.s.load_config()
        self.assertIsNone(config["thread_id"])
        self.assertFalse(config["connection_verified"])
        self.assertFalse(config["auto_start_on_codex_open"])
        config["quiet_start"] = 21
        self.s.save_config(config)
        before = self.s.CONFIG_PATH.read_bytes()
        self.s.initialize()
        self.assertEqual(before, self.s.CONFIG_PATH.read_bytes())
        with self.assertRaises(ValueError):
            self.a.start()

    def test_actual_running_process_and_wait_marker_create_one_card(self):
        before = self.s.CONFIG_PATH.read_bytes()
        job = self.launch(5)
        self.tick()
        self.assertEqual(self.cards(), [])
        marked = self.cli("waiting", "--run", job)
        self.assertEqual(marked.returncode, 0, marked.stderr)
        time.sleep(2.1)
        self.tick()
        self.tick()
        cards = self.cards()
        self.assertEqual(len(cards), 1)
        with self.a.connect() as db:
            running = db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone()
        self.assertTrue(self.a.is_live(running))
        self.assertNotIn('"answer"', cards[0]["message"])
        self.assertNotIn(self.a.CARDS[0]["answer"], cards[0]["message"])
        finished = self.cli("result", "--run", job, "--follow")
        self.assertEqual(finished.returncode, 0)
        self.tick()
        with patch.object(self.a.subprocess, "run", side_effect=AssertionError("No queue for an ended wait")):
            self.a.deliver(cards[0]["id"])
        with self.a.connect() as db:
            self.assertEqual(db.execute("SELECT status FROM deliveries WHERE id=?", (cards[0]["id"],)).fetchone()[0], "suppressed")
        self.assertEqual(before, self.s.CONFIG_PATH.read_bytes())

    def test_short_task_does_not_create_a_learning_card(self):
        job = self.launch(1)
        self.cli("waiting", "--run", job)
        finished = self.cli("result", "--run", job, "--follow")
        self.assertEqual(finished.returncode, 0)
        self.tick()
        self.assertEqual(self.cards(), [])

    def test_cancel_with_existing_wait_marker_does_not_push_learning(self):
        job = self.launch(10)
        self.assertEqual(self.cli("waiting", "--run", job).returncode, 0)
        self.assertEqual(self.cli("cancel", "--run", job).returncode, 0)
        self.tick()
        self.assertEqual(self.cards(), [])
        self.assertEqual(self.cli("result", "--run", job, "--follow").returncode, 130)
        self.tick()
        self.assertEqual(self.cards(), [])

    def test_spawn_failure_cannot_be_marked_waiting(self):
        job = "JOB-" + uuid.uuid4().hex[:12]
        result = self.cli("run", "--id", job, "--origin", "offline-test-main", "--", "no-such-executable-experiment-test")
        self.assertEqual(result.returncode, 127)
        self.assertEqual(self.cli("waiting", "--run", job).returncode, 2)
        self.tick()
        self.assertEqual(self.cards(), [])

    def test_argument_array_cwd_environment_streams_and_exit_code(self):
        os.environ["EXPERIMENT_TEST_SENTINEL"] = "sentinel with spaces"
        job = "JOB-" + uuid.uuid4().hex[:12]
        program = "import json,os,sys; print(json.dumps({'args':sys.argv[1:],'cwd':os.getcwd(),'env':os.environ.get('EXPERIMENT_TEST_SENTINEL')})); print('stderr sentinel',file=sys.stderr); sys.exit(7)"
        arguments = ["a b", '"quoted"', "$()", "; & echo never-executed"]
        result = self.cli("run", "--id", job, "--origin", "offline-test-main", "--cwd", str(self.profile), "--", sys.executable, "-c", program, *arguments)
        self.assertEqual(result.returncode, 7)
        output = json.loads(result.stdout)
        self.assertEqual(output["args"], arguments)
        self.assertEqual(Path(output["cwd"]).resolve(), self.profile)
        self.assertEqual(output["env"], "sentinel with spaces")
        with self.a.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone()
        self.assertEqual(Path(row["stdout_path"]).read_text(encoding="utf-8"), result.stdout)
        self.assertEqual(Path(row["stderr_path"]).read_text(encoding="utf-8"), result.stderr)
        os.environ.pop("EXPERIMENT_TEST_SENTINEL", None)

    def test_queue_failure_does_not_stop_experiment(self):
        with self.a.connect() as db:
            did = self.a.queue_delivery(db, "fault", "connection", "offline transport test")
        self.a.CONFIG["thread_id"] = str(uuid.uuid4())
        with patch.object(self.a.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", "simulated queue failure")):
            self.a.deliver(did)
        with self.a.connect() as db:
            self.assertEqual(db.execute("SELECT status FROM deliveries WHERE id=?", (did,)).fetchone()[0], "send_failed")
        result = self.cli("run", "--id", "JOB-fault", "--origin", "offline-test-main", "--", sys.executable, "-c", "import sys;print('experiment ran');sys.exit(7)")
        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stdout.strip(), "experiment ran")

    def test_jsonl_real_reply_state_is_distinct_from_queue_acceptance(self):
        fixture = self.profile / "thread-fixture.jsonl"
        fixture.write_bytes(b"")
        with self.a.connect() as db:
            self.a.set_setting(db, "rollout_path", fixture)
            self.a.read_learning_messages(db)
            did = self.a.queue_delivery(db, "fixture", "card", "fixture", card=self.a.CARDS[0]["id"])
            db.execute("UPDATE deliveries SET status='queued_accepted',queued=? WHERE id=?", (time.time(), did))
        with self.a.connect() as db:
            self.a.read_learning_messages(db)
            self.assertEqual(db.execute("SELECT status FROM deliveries WHERE id=?", (did,)).fetchone()[0], "queued_accepted")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM progress").fetchone()[0], 0)
        def append(role, body):
            value = {"type":"response_item","payload":{"type":"message","role":role,"phase":"final_answer" if role=="assistant" else None,"content":[{"type":"output_text" if role=="assistant" else "input_text","text":body}]}}
            with fixture.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(value, ensure_ascii=False)+"\n")
        append("assistant", "fixture card reply " + did)
        with self.a.connect() as db:
            self.a.read_learning_messages(db)
            self.assertEqual(db.execute("SELECT status FROM deliveries WHERE id=?", (did,)).fetchone()[0], "reply_confirmed")
            self.assertEqual(db.execute("SELECT state FROM progress").fetchone()[0], "in_progress")
        append("user", "已学完")
        with self.a.connect() as db:
            self.a.read_learning_messages(db)
        with self.a.connect() as db:
            self.assertEqual(db.execute("SELECT state FROM progress").fetchone()[0], "completed")

    def test_late_probe_reply_can_verify_without_another_model_message(self):
        config = self.s.load_config()
        config["thread_id"] = str(uuid.uuid4())
        self.s.save_config(config)
        self.a.CONFIG.update(config)
        fixture = self.profile / "probe-fixture.jsonl"
        fixture.write_bytes(b"")
        with self.a.connect() as db:
            self.a.set_setting(db, "rollout_path", fixture)
            self.a.read_learning_messages(db)
            did = self.a.queue_delivery(db, "late-probe", "connection", "probe fixture")
            db.execute("UPDATE deliveries SET status='queued_accepted' WHERE id=?", (did,))
        with patch.object(self.m, "engine", return_value=self.a), patch.object(self.a, "deliver", side_effect=AssertionError("Recheck must not send")), patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(self.m.probe(1, did), 3)
            self.assertFalse(self.s.load_config()["connection_verified"])
            fixture.write_text(json.dumps({"type":"response_item","payload":{"type":"message","role":"assistant","phase":"final_answer","content":[{"type":"output_text","text":"confirmed " + did}]}})+"\n",encoding="utf-8")
            self.assertEqual(self.m.probe(1, did), 0)
            self.assertTrue(self.s.load_config()["connection_verified"])
            self.assertEqual(self.s.load_config()["verified_event_id"], did)

    def test_integration_preserves_other_instructions_and_is_idempotent(self):
        project = self.profile / "project"
        project.mkdir()
        target = project / "AGENTS.md"
        original = b"\xef\xbb\xbfUser instructions\r\nKeep these lines.\r\n"
        target.write_bytes(original)
        config = self.s.load_config()
        config.update(thread_id=str(uuid.uuid4()), connection_verified=True)
        self.s.save_config(config)
        self.m.integrate("project", str(project))
        first = target.read_bytes()
        self.assertTrue(first.startswith(original))
        self.m.integrate("project", str(project))
        self.assertEqual(first, target.read_bytes())
        self.m.integrate("project", str(project), remove=True)
        self.assertTrue(target.read_bytes().startswith(original))
        self.assertNotIn(self.m.START.encode(), target.read_bytes())

    def test_learning_thread_cannot_be_the_main_thread_or_launch_experiments(self):
        thread = str(uuid.uuid4())
        with patch.dict(os.environ, {"CODEX_THREAD_ID": thread}):
            with self.assertRaises(ValueError):
                self.m.bind(thread)
        self.a.CONFIG["thread_id"] = thread
        from argparse import Namespace
        with self.assertRaises(ValueError):
            self.a.run(Namespace(command=[sys.executable,"-c","print('must not run')"], origin=thread))

    def test_desktop_session_gate_respects_manual_stop_and_restarts(self):
        gate = self.w.SessionGate()
        frames = [[], ["one:born-A"], ["one:born-A"], [], ["one:born-B"], ["one:born-B"]]
        self.assertEqual([gate.should_start(frame) for frame in frames], [False,True,False,False,True,False])
        restarted = self.w.SessionGate(["one:born-B"])
        self.assertFalse(restarted.should_start(["one:born-B"]))
        self.assertFalse(self.w.desktop_path(r"C:\Program Files\WindowsApps\OpenAI.ChatGPT_1.0\app\ChatGPT.exe"))

    def test_cards_reject_missing_prerequisites_cycles_and_invalid_duration(self):
        original = self.s.load_cards()
        for mutation in ("missing", "cycle", "boolean", "infinite", "blank", "duplicate"):
            cards = json.loads(json.dumps(original))
            if mutation == "missing":
                cards[0]["prerequisites"] = ["not-a-card"]
            elif mutation == "cycle":
                cards[0]["prerequisites"] = [cards[-1]["id"]]
                cards[-1]["prerequisites"] = [cards[0]["id"]]
            elif mutation == "boolean":
                cards[0]["minutes"] = True
            elif mutation == "infinite":
                cards[0]["minutes"] = float("inf")
            elif mutation == "blank":
                cards[0]["explanation"] = "  "
            else:
                cards.append(dict(cards[0]))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.s.validate_cards(cards)
        self.assertEqual(self.s.validate_cards(original), original)

    def test_validated_card_import_repairs_broken_material_and_preserves_backup(self):
        broken = b'{"accidental":"edit"}'
        self.s.CARDS_PATH.write_bytes(broken)
        source = self.profile / "my-course.json"
        course = json.loads(self.s.DEFAULT_CARDS.read_text(encoding="utf-8"))
        course[0]["topic"] = "My own course"
        source.write_text(json.dumps(course), encoding="utf-8")
        failed = self.cli("cards", "validate")
        self.assertEqual(failed.returncode, 2)
        status = self.cli("status")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertTrue(json.loads(status.stdout)["cards_error"])
        imported = self.cli("cards", "import", "--file", str(source))
        self.assertEqual(imported.returncode, 0, imported.stderr)
        self.assertEqual(json.loads(imported.stdout)["card_count"], len(course))
        self.assertEqual(self.s.load_cards()[0]["topic"], "My own course")
        self.assertEqual(next(self.profile.glob("cards.backup-*.json")).read_bytes(), broken)

    def test_stop_remains_available_with_broken_configuration_and_cards(self):
        self.s.CONFIG_PATH.write_text("not JSON", encoding="utf-8")
        self.s.CARDS_PATH.write_text("not JSON", encoding="utf-8")
        stopped = self.cli("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        with self.a.connect() as db:
            self.assertEqual(self.a.setting(db, "stop_requested"), "1")

    def test_disable_revokes_profile_even_if_shortcut_has_changed(self):
        config = self.s.load_config()
        config.update(auto_start_on_codex_open=True, autostart_watcher_on_windows_logon=True)
        self.s.save_config(config)
        startup = self.profile / "Startup"
        startup.mkdir()
        target = startup / "Codex Experiment Learning Plugin.lnk"
        target.write_bytes(b"somebody changed this shortcut")
        receipt = {"shortcut": str(target), "shortcut_sha256": "invalid-old-hash"}
        (self.a.RUNTIME / "autostart-install.json").write_text(json.dumps(receipt), encoding="utf-8")
        with patch.object(self.w, "startup_folder", return_value=startup):
            self.assertEqual(self.w.disable(), 1)
        self.assertFalse(self.s.load_config()["auto_start_on_codex_open"])
        self.assertFalse(self.s.load_config()["autostart_watcher_on_windows_logon"])
        self.assertEqual(target.read_bytes(), b"somebody changed this shortcut")

    def test_cleanup_deletes_only_old_finished_output_and_keeps_progress(self):
        old = self.launch(1)
        self.assertEqual(self.cli("result", "--run", old, "--follow").returncode, 0)
        live = self.launch(5)
        with self.a.connect() as db:
            db.execute("UPDATE jobs SET ended=? WHERE id=?", (time.time()-3*86400, old))
            db.execute("INSERT OR REPLACE INTO progress(card_id,state,last_seen,completed_at) VALUES(?,?,?,?)",
                       (self.a.CARDS[0]["id"], "completed", time.time(), time.time()))
        wrapper = self.a.RUNTIME / (old + "-wrapper.log")
        self.assertTrue(wrapper.is_file())
        result = self.cli("cleanup", "--older-than-days", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.a.RUNTIME / "runs" / old).exists())
        self.assertFalse(wrapper.exists())
        self.assertTrue((self.a.RUNTIME / "runs" / live).is_dir())
        with self.a.connect() as db:
            self.assertEqual(db.execute("SELECT state FROM progress").fetchone()[0], "completed")


if __name__ == "__main__":
    unittest.main()
