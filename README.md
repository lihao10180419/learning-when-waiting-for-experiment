# Learning When Waiting for Experiments

**Turn verified experiment waits into short learning sessions in a separate Codex conversation.**

[中文说明](README.zh-CN.md) · [Setup](docs/SETUP.md) · [Privacy](docs/PRIVACY.md) · [License](LICENSE)

This Windows Codex plugin runs a small local process monitor. When an experiment is actually running and the main Codex explicitly marks that it is waiting for results, the monitor sends one short learning card to your separately bound learning thread. Completion, failure or a request for human handling can send you back to the project.

**Background monitoring uses zero model tokens.** Card delivery, learning replies and the explicit connection probe use your signed-in Codex account's quota. No extra API key, cloud service or Python dependency is required.

```text
Start experiment → confirm process → main agent marks waiting
                 → wait threshold → separate learning card
                 → experiment completes/fails → return reminder
```

## Install

Requirements: **Windows 10/11, Python 3.10+, a signed-in Codex desktop app, and a CLI supporting `codex queue`**. The original native delivery was tested with CLI `0.167.0-alpha.3.2`; other versions must pass their own connection probe. macOS, Linux and remote job monitoring are not supported by this release.

```powershell
codex plugin marketplace add https://github.com/lihao10180419/learning-when-waiting-for-experiment.git
codex plugin add experiment-learning@experiment-learning-community
```

Start a new Codex conversation and request:

> Use $experiment-learning-setup to set up a separate learning thread, verify a real reply, and integrate the assistant into my local projects. Also enable startup when I open Codex.

Installation makes the skills available; setup binds your own UUID and opts into project integration and startup. A private repository requires Git access. Availability of custom marketplaces can depend on the client and workspace policy. GitHub distribution does not imply listing or approval in OpenAI's public Plugins Directory.

For a local checkout:

```powershell
git clone https://github.com/lihao10180419/learning-when-waiting-for-experiment.git
cd learning-when-waiting-for-experiment
codex plugin marketplace add .
codex plugin add experiment-learning@experiment-learning-community
```

This CLI version uses `plugin add`; check `codex plugin --help` if your version differs. Detailed manual setup and uninstall commands are in [SETUP.md](docs/SETUP.md).

## How waiting is detected

- Known total runtime of at least 10 minutes: eligible after 30 stable seconds.
- Unknown duration: eligible after 3 actual minutes, with remaining time explicitly unknown.
- Both cases also require a live PID with its original creation identity, a fresh wrapper heartbeat and an explicit main-agent waiting marker.
- Pending approval, no actual process, missing/conflicting waiting state, pause and quiet hours suppress learning.
- Only wrap eligible local experiments. Already running jobs are left alone; SSH submission exit is not remote-job completion.

Automatic integration uses an opt-in marked `AGENTS.md` block. It covers Codex starts that follow those instructions, not arbitrary commands in every terminal. No tool hooks are installed. Pausing/stopping the assistant never cancels an experiment.

## Cards, progress and startup

Three editable **flow-test cards** are included; they are not a prescribed curriculum. Cards contain a title, suggested duration, explanation, example, question and answer. The initial request and response omit the answer; ask the native learning conversation to explain it when ready. Only explicit completion advances progress.

User state lives outside the plugin cache in `%LOCALAPPDATA%/CodexExperimentLearning/`. Change the profile with `EXPERIMENT_LEARNING_HOME`. Edit `cards.json` and `config.json` there. Default quiet hours are 23:00–08:00 at UTC+8; the fixed UTC offset and hours are configurable.

Optional desktop-open startup creates one current-user Windows Startup shortcut. A local watcher checks every five seconds and starts the monitor once per new Codex process session. Manual Stop is respected for that session; Pause remains saved. No model is polled in either background process.

## Honest delivery state

`pending → sending → queued_accepted → reply_confirmed`

Failures can be `send_failed`, `acceptance_unknown`, `reply_unverified` or `suppressed`. A successful queue command, including one with a failed-resume warning, is **not proof of a reply**. Ambiguous sends are not endlessly retried. The current reply reader supports the tested local JSONL history format; other history formats need verification. Keep the desktop app running and online for model replies; detection and local state recording work offline. Phone and operating-system toast delivery are not promised.

## Develop and verify

```powershell
python -m unittest discover -s tests -v
python tools/validate_release.py
python tools/build_release.py
```

Tests use isolated profiles and make no model calls. The source prototype received real native replies during a 15-second simulation; public-package verification and limits are recorded in [VERIFICATION.md](docs/VERIFICATION.md). Upgrades and optional Windows startup registration require rerunning setup to refresh installed paths while preserving user data.

MIT © 2026 lihao10180419 and contributors.

Packaging follows the [official OpenAI plugin guide](https://developers.openai.com/plugins/build/plugins); command and hook behavior should be checked against the installed CLI and [official CLI reference](https://learn.chatgpt.com/docs/cli/reference).
