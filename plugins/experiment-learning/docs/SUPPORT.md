# Support — Experiment Learning

Updated 12 November 2026. For installation problems, bug reports, feature requests or privacy questions, use the project's [GitHub Issues](https://github.com/lihao10180419/learning-when-waiting-for-experiment/issues). A GitHub account is needed to post an issue; this support page and existing public issues can be read without signing in.

For setup, migration, all-project integration, startup and uninstalling, read [SETUP.md](SETUP.md). For data handling and deletion, read [PRIVACY.md](PRIVACY.md). Runtime code and these documents are maintained in [learning-when-waiting-for-experiment](https://github.com/lihao10180419/learning-when-waiting-for-experiment) by individual publisher `lihao10180419`. OpenAI identity verification and public-directory review are separate processes.

When reporting a problem, include the plugin version, Windows/Python/Codex CLI versions, action taken, actual delivery state and a short redacted error. `doctor` checks local prerequisites and `status` shows monitor state. Read their output before sharing it: paths, job labels and thread identifiers can identify your workspace. Do not post account credentials, complete `config.json`, session JSONL, databases or experiment logs. No support response-time commitment is made by this version.

`queued_accepted` means accepted for queueing; it does not prove the learning conversation replied. Keep the signed-in desktop app running and online, confirm the exact separate target and inspect that event. `acceptance_unknown` must be inspected before any manual resend. Avoid repeating probes indefinitely.

If editable card material is broken, `cards validate` explains validation failures and `cards import --file PATH` can replace it after the monitor is stopped, preserving a local backup. `stop` remains available even if configuration or cards are malformed. Disabling startup turns off this profile's watcher first; a changed or unverified shortcut is retained for manual inspection.

The supported target is Windows with Python 3.10+ and a Codex CLI providing `queue --thread --message --resume`. Exact JSONL history reading and packaged-app detection depend on the installed client. Remote jobs, external-terminal discovery, phone delivery and other operating systems are outside this release's supported workflow.
