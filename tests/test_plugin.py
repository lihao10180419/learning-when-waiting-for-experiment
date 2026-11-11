"""Offline tests: real child processes, isolated profiles, no real queue calls."""
from pathlib import Path
import importlib
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


if __name__ == "__main__":
    unittest.main()
