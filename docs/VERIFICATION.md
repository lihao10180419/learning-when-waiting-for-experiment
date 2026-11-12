# Verification for v0.1.1

Verified on Windows with Python 3.14.7 and Codex CLI 0.167.0-alpha.3.2. The plugin runtime uses only the Python standard library.

## Public package checks

`python -X utf8 -W error::ResourceWarning -m unittest discover -s tests -v`: **17 tests passed** in 24.724 seconds, using separate per-test profiles and no real model messages. Run on 12 November 2026; no unclosed SQLite connection warnings remained.

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

Both bundled skills passed the skill-creator validator. Its optional PyYAML validation dependency was placed only in an ignored local test directory; it is not a plugin runtime dependency and is not shipped.

The installed Codex CLI recognized `experiment-learning@experiment-learning-community`, version `0.1.1`, as an available plugin after temporary local marketplace registration. The returned entry was installed=false, enabled=false. The temporary registration was removed. This check did not install the plugin, modify active project integration or call a model.

The release validator checks manifest consistency, marketplace paths, skill entrypoints, JSON/Python syntax, listing text limits, icon references/dimensions, local-executor declaration, absence of app bindings/hooks and inactive defaults. It scans the explicit publication allowlist for literal user-home paths, session UUIDs, credential-like tokens and private state files. A separate upload ZIP contains only the self-contained plugin. The actual ZIP is reopened, CRC-tested, extracted for metadata inspection, and every member's SHA-256 compared against the validated source inventory. These are project-local preflight checks, not OpenAI server-side ingestion or approval.

## Fresh-profile native probe — blocked

The first v0.1.1 submission candidate was extracted to a new isolated profile. `init`, `doctor` and `bind` succeeded using the existing installed Python/CLI. One real native `probe` was submitted. After 60 seconds it remained **queued_accepted**, with no matching assistant reply. The CLI warned that it could not resume the target because there was no running local daemon; an official app read reported the exact target **notLoaded**. The matching history contained no new test reply.

No resend was made, the profile remained unverified, its own monitor was stopped, and the 15-second native simulation was **not run** because the required probe had not passed. No existing monitor, watcher, daemon, global instructions or experiments were changed. This is a real failed verification, not a native success claim. The subsequent no-resend recheck improvement is fixture-tested; a native success with the final candidate is still unverified.

The [official queue reference](https://learn.chatgpt.com/docs/developer-commands#codex-queue) confirms that `--resume` needs a running local daemon or selected server; a failed resume can still exit successfully. A desktop process alone is insufficient for an unloaded learning target. Restore the exact target using a supported client path or arrange a supported local daemon, then recheck the existing event. Directory eligibility of this local delivery/history adapter remains a separate OpenAI confirmation item.

## Native delivery evidence and its scope

Before packaging, the source prototype was tested against a real separate native Codex learning task. In one 15-second local simulation, a full learning reply was confirmed about 8.3 seconds after process start, with an immediate OS identity check showing the experiment still running. Another final card request, with the answer omitted from the visible request, was confirmed before its 15-second process ended. Success and failure return reminders, stdout/stderr and exit code 7 were also checked.

Some early native replies arrived after the short simulation ended. Queue warnings and reply latency were retained as failures for those individual timings, rather than treated as delivery success. No private thread IDs, local session files, screenshots or machine-specific logs are included here.

The public package introduces per-user profiles and fresh binding. Its fresh-profile native attempt is recorded above and did not pass. Every new installation must pass its own `probe`; the prototype's historical success cannot verify a different UUID, account, client state or storage format.

## Not verified or not supported

- Installation by unrelated accounts from the GitHub marketplace, or public-directory submission/approval.
- Full Windows logout/login or a forced desktop-app restart for the packaged release. Startup registration was syntax-checked; the original watcher identified the running app. Existing work was not interrupted for a restart test.
- macOS/Linux deployment, remote SSH/scheduler job state, GPU training or large model downloads.
- Other local history formats, full concurrency/restart pressure testing, phone pairing or OS toast delivery.

The owner subsequently authorized public source distribution. The repository was changed to public with Issues enabled; anonymous HTTPS reads of all four listing destinations returned expected content, recorded in PUBLIC_LINKS.md. This publication change does not resolve the native probe or imply directory approval.
