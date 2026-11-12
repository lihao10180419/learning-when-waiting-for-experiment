---
name: experiment-learning-setup
description: Set up or repair this Windows Codex experiment-wait learning plugin, bind a separate learning thread, verify a real reply, or configure project integration and desktop-open startup.
---

The plugin CLI is `../../scripts/manage.py`, relative to this skill folder. Resolve the actual installed path; do not invent a workstation path. Use the installed Python and argument arrays. No API key or additional paid service is required.

1. Run `manage.py doctor` and `manage.py init`. This release supports Windows with a Codex CLI offering `queue --thread --message --resume`. Read reported paths; user configuration, cards and progress are outside the plugin cache.
2. Create or select a separate persistent Codex learning task titled **实验间隙学习**. Use the client's official create/read task tools if present; otherwise guide one manual creation and obtain its exact UUID from that task's local `CODEX_THREAD_ID`. Never use the main project thread, `--last`, a guessed ID, or a mobile ChatGPT conversation.
3. Give the learning task this role: explain short supplied cards, keep the first presentation free of answers, explain the answer only when asked, and never launch experiments, modify projects or call this assistant. Verify the selected task's identity through the client.
4. Run `manage.py bind --thread UUID`, then `manage.py probe`. A probe uses account quota once to request a unique test reply. Success requires `reply_confirmed`, not exit code 0 or `queued_accepted`. If it remains queued, report that state and stop automatic setup until the target's actual reply can be verified. Use `probe --check-event EVENT` to recheck that existing request without sending another one. If resume warns that no daemon is available, explain that an unloaded target needs a supported running daemon or normal client restoration; the desktop process alone does not guarantee delivery. Do not restart the app or alter daemon services just to make a probe pass, and do not repeatedly submit the probe.
5. Honor the requested scope. If the user asks to integrate all projects, run `manage.py integrate --scope user`; for one project use `--scope project --project PATH`. These commands append only a marked block, preserve other instructions and make backups. They do not edit `config.toml`. Resolve any required write approval through the normal tool mechanism. Without a requested scope, ask which scope they want before this change.
6. Start the monitor with `manage.py start`. Enable Windows desktop-open startup only when requested, using `manage.py enable-autostart`. It adds one current-user Startup shortcut and a local watcher. Do not change PowerShell execution policy or bypass hook trust; no hooks are required.

Report the exact selected thread, real connection status, selected scope and startup choice. Local monitoring and app detection make no model calls; native card delivery and questions use the signed-in account's quota. Do not promise phone delivery or automatic monitoring of external terminals or remote jobs.

For migration, card import, custom profiles and uninstalling, read the packaged `../../docs/SETUP.md`. Read `../../docs/PRIVACY.md` for data handling. These files are inside the installed plugin; no repository checkout is required. Preserve existing live experiments and never restart them to attach monitoring.
