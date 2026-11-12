# Data and privacy — v0.1.1

Updated 12 November 2026. Experiment Learning is maintained by individual publisher `lihao10180419`. Support and privacy questions can be raised through the project's [GitHub Issues](https://github.com/lihao10180419/learning-when-waiting-for-experiment/issues). This policy describes the packaged implementation; OpenAI and GitHub provide their own services under their respective policies.

The monitor and desktop-open watcher are local Python programs. They do not poll an LLM, collect browser cookies, access private chat APIs, or need a separate API key.

The local profile stores the selected learning-thread UUID, configuration and editable card content. Its SQLite database stores job IDs, project working directories, short labels, PIDs and process creation identities, timestamps, exit codes, local output paths, wait markers, notification IDs, sent card/return messages, matched learning replies and learning progress. Full child stdout/stderr and wrapper/monitor diagnostic logs remain on disk; these can contain sensitive experiment output. Startup receipts contain the installed script path, profile path and shortcut hash. Optional integration also writes the selected profile path and thread UUID into the chosen local Codex instructions, with a backup.

For model delivery, the plugin sends card material (initially without the answer), event IDs, short project-supplied labels, timing/wait information, result/exit-code summaries and an explicit probe request to the separately bound Codex thread through installed `codex queue`. The plugin does not add full experiment commands, argument arrays, environment variables or captured experiment output to these requests. Choose labels and card text that you are comfortable sending to Codex; user-written card text or labels can themselves contain sensitive data.

Codex replies require network access and use the signed-in account's quota. The connection probe also requests one reply. Monitoring, app detection and progress recording do not themselves request model inference. Account and service data handling remains governed by the applicable Codex/OpenAI settings and terms.

The native reply adapter reads new messages in the exact selected thread's local JSONL record to match event IDs and recognize explicit control messages. Matched assistant replies are stored in the profile. Filename lookup scans the session directory for that exact UUID; other conversation contents are not read for topic selection. The watcher reads local process names, paths and creation identities to recognize the Codex desktop session. Other history formats and future storage migrations must be verified separately.

The repository and release archive exclude user configuration, session UUIDs, databases, logs, absolute user workstation paths and the original prototype's local reports. Default `thread_id` is null. A fresh installation does not start monitoring or install Windows startup entries until explicitly configured.

Optional Windows Startup registration creates a current-user shortcut pointing to the installed watcher and selected profile. Disabling startup removes only the verified owned shortcut; uninstalling does not erase user data automatically. See [SETUP.md](SETUP.md).

## Recipients and services

This version has no maintainer-operated backend, analytics endpoint, advertising tracker or automatic upload of the profile. The plugin maintainer does not receive local monitoring records through the plugin. Model-backed requests and replies are processed by the user's Codex/OpenAI service under that account's applicable settings and terms. GitHub handles repository downloads and any support issues the user chooses to post under its own policies. Public support issues are public when the repository is public; never attach credentials, full session records or experiment data.

## Retention and user controls

There is no automatic retention limit. Configuration, card backups, database records, sent/replied learning text, progress and diagnostics stay locally until the user removes them. `cleanup --older-than-days 7` explicitly removes output directories and wrapper logs for finished jobs older than seven days; it leaves active jobs, the database, progress and monitor logs in place. A minimum of one day is enforced. It does not delete Codex conversation history or GitHub issues.

Use `paths` to locate your profile. Pause/Stop suppress monitoring without cancelling experiments; disable optional startup and remove the plugin's instruction block when uninstalling. After all jobs using that profile have ended and its monitor/watcher have stopped, the user can back up or delete that profile directory to remove its local records. Delete any instruction backups separately if they contain paths or thread IDs. Data already sent to Codex or posted on GitHub must be managed using the respective service's controls.

Support and privacy questions: see [SUPPORT.md](SUPPORT.md). Changes to these practices must be reflected in this policy before a changed version is submitted. The repository publisher handle is not a claim that OpenAI identity verification or directory approval has been completed.
