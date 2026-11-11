# Experiment Learning plugin

Windows-only local experiment-wait monitor, native Codex learning thread and optional desktop-open watcher. Monitoring and app detection make no model calls; actual native delivery and the explicit connection probe use account quota.

Entry point: `python scripts/manage.py`. First run `init` and `doctor`, bind a **separate** persistent Codex thread with `bind --thread UUID`, then run one `probe`. Continue only after `reply_confirmed`. `queued_accepted` is not proof of a reply. Never bind the main project or a mobile ChatGPT conversation.

Use `integrate --scope user` only when the user requests all-project integration, or `integrate --scope project --project PATH` for one project. Existing instructions are preserved and backed up. Then `start` the monitor. `enable-autostart` is optional and creates a current-user Startup shortcut; `disable-autostart` removes this plugin's verified shortcut and exits the watcher. Neither stops experiments.

Runtime commands: `run`, `launch`, `waiting`, `busy`, `attention`, `result`, `cancel`, `status`, `pause`, `resume`, `today-off`, `done`, `later`, `stop`. The experiment's original executable, argument array, cwd and environment must be preserved. Only explicitly noninteractive experiments may use `launch`. Write `waiting` only after the OS confirms the real process and the main agent genuinely waits for results.

User data defaults to `%LOCALAPPDATA%/CodexExperimentLearning/`; set `EXPERIMENT_LEARNING_HOME` before running a command for another profile. Content and progress stay outside the plugin cache. Built-in cards are flow tests. First presentation omits answers. Only explicit completion advances progress.

Known >=10-minute tasks qualify after 30 stable seconds; unknown durations qualify after 3 actual minutes. Missing markers, pending approvals/input, quiet hours and pause suppress learning. `--test` changes thresholds only for a designated simulation. No remote job monitoring, arbitrary-terminal process scanning, user-idle API, phone guarantee or tool hooks are provided.

Local JSONL reply reading is version-specific. Ambiguous queue sends are not retried automatically. Stop and disable optional startup before uninstalling/upgrading; remove only this plugin's marked integration using `integrate --scope user --remove` or the matching project scope. Rerun setup after upgrades to refresh executable paths. Data is retained.

MIT licensed. Repository documentation: https://github.com/lihao10180419/learning-when-waiting-for-experiment
