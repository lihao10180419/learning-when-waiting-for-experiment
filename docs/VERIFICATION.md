# Verification for v0.1.1

Verified on Windows with Python 3.14.7, complete native Codex CLI **0.167.2** and local daemon **0.167.2**. The desktop-provided CLI **0.167.0-alpha.3.2** was also used for local catalog/install commands. The plugin runtime uses only the Python standard library.

## Public package checks

`python -X utf8 -W error::ResourceWarning -m unittest discover -s tests -v`: **20 tests passed** in 25.049 seconds, using separate per-test profiles and no real model messages. Run on 12 November 2026; no unclosed SQLite connection warnings remained.

- A real child process plus an explicit wait creates one card event while the process is still live; repeated monitor ticks do not create another.
- A running process without a wait marker does not create a card.
- A short child process does not create a learning card.
- Cancellation with an existing wait marker does not create a card and returns 130.
- Startup failure returns 127 and cannot be marked waiting.
- Arguments containing spaces, quotes and shell metacharacters arrive unchanged as arguments; cwd, environment, stdout, stderr and exit code 7 are preserved.
- A simulated queue transport failure is recorded while a real experiment still runs and returns 7.
- A local JSONL adapter fixture distinguishes accepted queue state from an actual assistant reply; only an explicit completion control advances progress.
- Fresh profiles are unbound, unverified and inactive. Initialization preserves user edits; unverified monitoring is refused.
- Learning-thread recursion is refused.
- Project instruction integration preserves existing content/line endings and is idempotent. App-session gating respects manual Stop and distinguishes new process identities.
- Card validation rejects missing prerequisite IDs, cycles, duplicate IDs, empty text, boolean/infinite durations. Validated import repairs malformed material and preserves its previous bytes in a backup.
- Stop works even with broken configuration/cards. Disabling startup revokes profile flags while retaining a changed, unverified shortcut.
- Explicit cleanup removes only old finished-job output/wrapper logs, leaving active output and progress in place.
- A late probe reply can complete verification using `probe --check-event` without submitting another model message; this is covered with a local JSONL fixture.
- Selecting a native CLI preserves the target and requires a fresh probe. Queue messages remain literal arguments with no shell invocation.
- Backend diagnostics require an actual running response, handle unavailable/malformed responses and never send a queue message.
- Explicit backend startup uses only idempotent daemon start, rejects the learning thread, and rejects Windows command-script wrappers as a native executable.

Both bundled skills passed the skill-creator validator. Its optional PyYAML validation dependency was placed only in an ignored local test directory; it is not a plugin runtime dependency and is not shipped.

The installed Codex CLI recognized `experiment-learning@experiment-learning-community`, version `0.1.1`, as an available plugin after temporary local marketplace registration. The returned entry was installed=false, enabled=false. The temporary registration was removed. This check did not install the plugin, modify active project integration or call a model.

The release validator checks manifest consistency, marketplace paths, skill entrypoints, JSON/Python syntax, listing text limits, icon references/dimensions, local-executor declaration, absence of app bindings/hooks and inactive defaults. It scans the explicit publication allowlist for literal user-home paths, session UUIDs, credential-like tokens and private state files. A separate upload ZIP contains only the self-contained plugin. The actual ZIP is reopened, CRC-tested, extracted for metadata inspection, and every member's SHA-256 compared against the validated source inventory. These are project-local preflight checks, not OpenAI server-side ingestion or approval.

## Initial failed probe and resolved prerequisite

The first v0.1.1 submission candidate was extracted to a new isolated profile. `init`, `doctor` and `bind` succeeded using the existing installed Python/CLI. One real native `probe` was submitted. After 60 seconds it remained **queued_accepted**, with no matching assistant reply. The CLI warned that it could not resume the target because there was no running local daemon; an official app read reported the exact target **notLoaded**. The matching history contained no new test reply.

That original attempt was not resent; its profile remained unverified and stopped. Its 15-second simulation was **not run** because its probe had not passed. This failure is retained independently of the later successful run.

The [official queue reference](https://learn.chatgpt.com/docs/developer-commands#codex-queue) confirms that resume needs a running local daemon or selected server; a failed resume can still exit successfully. Further diagnosis found that the desktop-bundled CLI could not install a daemon because it lacked a complete local package. A pinned official npm CLI 0.167.2 was installed in an ignored test directory, without replacing PATH or the desktop CLI; its explicit daemon start prepared the managed per-user backend. The desktop app and existing experiments were not restarted. The backend remains available under Codex management; test monitors were stopped separately.

## Successful native acceptance from the rebuilt ZIP

The updated ZIP was extracted to another fresh profile. Its selected complete CLI passed doctor, and a new probe returned **reply_confirmed** after the missing prerequisite had been resolved.

- A real 15-second local simulation was launched and OS-confirmed before waiting.
- Exactly one card event was created. Its real final reply was confirmed **11.084 seconds** after process start; the immediate OS process-identity check still reported the original child live.
- The request and actual reply were inspected: title, suggested time, explanation, example and original self-test question were present; the self-test answer was withheld.
- The child exited **0**, stdout was preserved, and its completion/return reminder reached **reply_confirmed**.
- The test monitor was stopped. Global integration, the desktop app and existing experiments were not modified by the run.

Execution-code hashes and sanitized results are recorded in [NATIVE_ACCEPTANCE.json](NATIVE_ACCEPTANCE.json). Private paths, UUIDs, session records and raw logs are excluded from public sources.

## Actual plugin installation and native failure return

The plugin was temporarily installed through the real Codex CLI from the local marketplace. **All 24 installed files** matched the prepared plugin source, including both skills. The installed cache entrypoint, using the separate verified profile, passed doctor and ran a real one-second simulation with requested exit code **7**.

Original stdout and stderr were preserved, result-follow returned **7**, and the failed-job return reminder reached **reply_confirmed**. Its monitor was stopped. The plugin and marketplace registration created for this test were removed; existing integrations, data and backend were retained. This verifies local installer/cache execution, not public-directory ingestion or an unrelated user's environment.

## Native delivery evidence and its scope

Before packaging, the source prototype was tested against a real separate native Codex learning task. In one 15-second local simulation, a full learning reply was confirmed about 8.3 seconds after process start, with an immediate OS identity check showing the experiment still running. Another final card request, with the answer omitted from the visible request, was confirmed before its 15-second process ended. Success and failure return reminders, stdout/stderr and exit code 7 were also checked.

Some early native replies arrived after the short simulation ended. Queue warnings and reply latency were retained as failures for those individual timings, rather than treated as delivery success. No private thread IDs, local session files, screenshots or machine-specific logs are included here.

The initial package failure and subsequent successful acceptance are recorded separately above. Every new installation must pass its own probe; these results cannot verify another UUID, account, client state or storage format.

## Not verified or not supported

- Installation by unrelated accounts from the public GitHub marketplace, or public-directory submission/approval. Local CLI installation was tested as described above.
- Full Windows logout/login or a forced desktop-app restart for the packaged release. Startup registration was syntax-checked; the original watcher identified the running app. Existing work was not interrupted for a restart test.
- macOS/Linux deployment, remote SSH/scheduler job state, GPU training or large model downloads.
- Other local history formats, full concurrency/restart pressure testing, phone pairing or OS toast delivery.

The repository is public with Issues enabled; anonymous reads of all four listing destinations returned expected content, recorded in PUBLIC_LINKS.md. The documented Desktop-only skills route is described in ELIGIBILITY.md. None of these local checks imply directory approval.
