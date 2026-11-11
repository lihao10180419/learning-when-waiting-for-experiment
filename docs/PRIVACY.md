# Data and privacy

The monitor and desktop-open watcher are local Python programs. They do not poll an LLM, collect browser cookies, access private chat APIs, or need a separate API key.

The monitor stores job IDs, process creation identities, timestamps, status, local output paths, wait markers, notification IDs and learning progress in a per-user SQLite database. Full child stdout/stderr are preserved locally because they are part of experiment behavior; they may contain sensitive experiment output and should be handled like the experiment's own logs.

Only card material, event IDs, a short project-supplied label and a result/exit-code summary are sent to the separately bound Codex thread through the installed `codex queue` interface. Full experiment commands, argument arrays and data are not placed in learning requests. Choose labels that do not contain secrets.

Codex replies require network access and use the signed-in account's quota. The connection probe also requests one reply. Monitoring, app detection and progress recording do not themselves request model inference. Account and service data handling remains governed by the applicable Codex/OpenAI settings and terms.

The native reply adapter reads the exact selected thread's local JSONL record, including user control messages. It does not read arbitrary conversation contents to infer what to teach. Filename lookup may scan the session directory to locate that exact UUID. Other history formats and future storage migrations must be verified separately.

The repository and release archive exclude user configuration, session UUIDs, databases, logs, absolute user workstation paths and the original prototype's local reports. Default `thread_id` is null. A fresh installation does not start monitoring or install Windows startup entries until explicitly configured.

Optional Windows Startup registration creates a current-user shortcut pointing to the installed watcher and selected profile. Disabling startup removes only the verified owned shortcut; uninstalling does not erase user data automatically. See [SETUP.md](SETUP.md).
