# Verification for v0.1.0

Verified on Windows with Python 3.14.7 and Codex CLI 0.167.0-alpha.3.2. The plugin runtime uses only the Python standard library.

## Public package checks

`python -m unittest discover -s tests -v`: **11 tests passed**, using separate per-test profiles and no real model messages.

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

Both bundled skills passed the skill-creator validator. Its optional PyYAML validation dependency was placed only in an ignored local test directory; it is not a plugin runtime dependency and is not shipped.

The installed Codex CLI recognized `experiment-learning@experiment-learning-community`, version `0.1.0`, as an available plugin after temporary local marketplace registration. The temporary registration was removed. This check did not install the plugin, modify active project integration or call a model.

The release validator checks manifest consistency, marketplace paths, skill entrypoints, Python syntax and inactive defaults. It scans the explicit publication allowlist for literal user-home paths, session UUIDs, credential-like tokens and private state files. The ZIP is made from that same allowlist and its integrity is checked.

## Native delivery evidence and its scope

Before packaging, the source prototype was tested against a real separate native Codex learning task. In one 15-second local simulation, a full learning reply was confirmed about 8.3 seconds after process start, with an immediate OS identity check showing the experiment still running. Another final card request, with the answer omitted from the visible request, was confirmed before its 15-second process ended. Success and failure return reminders, stdout/stderr and exit code 7 were also checked.

Some early native replies arrived after the short simulation ended. Queue warnings and reply latency were retained as failures for those individual timings, rather than treated as delivery success. No private thread IDs, local session files, screenshots or machine-specific logs are included here.

The public package introduces per-user profiles and fresh binding. It has not sent a new model-backed message using another person's installation. Every new installation must pass its own `probe`; the prototype's success cannot verify a different UUID, account, client or storage format.

## Not verified or not supported

- Installation by unrelated accounts from the GitHub marketplace, or public-directory submission/approval.
- Full Windows logout/login or a forced desktop-app restart for the packaged release. Startup registration was syntax-checked; the original watcher identified the running app. Existing work was not interrupted for a restart test.
- macOS/Linux deployment, remote SSH/scheduler job state, GPU training or large model downloads.
- Other local history formats, full concurrency/restart pressure testing, phone pairing or OS toast delivery.

GitHub repository upload is source distribution. Keeping it private limits installation to accounts with Git access; making it public is a separate owner choice.
