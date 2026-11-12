# Desktop execution eligibility inquiry

Draft for the owner to send through an existing OpenAI partner/support contact. This document has not been sent and is not evidence of eligibility approval.

We are preparing Experiment Learning v0.1.1, a Windows Codex skills-only plugin. Its core workflow uses a local Python standard-library process wrapper to preserve experiment execution, then delivers a short learning card to a separate, explicitly selected Codex conversation only when the experiment is live and the main agent marks a genuine wait.

The package declares `requires_local_executor: true`. It has no MCP server, app binding, OAuth service, maintainer-hosted backend or additional API key. Monitoring and optional Codex-open process detection do not call a model. Card delivery and an explicit connection probe use the user's installed `codex queue --thread --message --resume`; exact replies are confirmed in the selected thread's local JSONL record. The target must be separately bound and actually verified. It does not monitor arbitrary external terminals or remote scheduler jobs.

Users explicitly opt into a marked user/project AGENTS.md integration and, optionally, a current-user Windows Startup shortcut. A fresh installation is unbound and inactive. Data stays in a per-user local profile except the selected card/return messages sent through Codex. The monitor retains local experiment output and learning progress; its policy drafts describe retention and deletion. The software is MIT licensed.

Could you confirm whether this local-execution workflow is eligible for the public Plugins Directory for Codex, and whether it requires a desktop-specific review, allowlist or supported alternative to the current queue/history adapter? In particular, we would like confirmation before treating the separate learning conversation's automatically queued reminders as eligible directory behavior.

Source repository: https://github.com/lihao10180419/learning-when-waiting-for-experiment (currently private; grant access separately if requested). Package and verification records are available from the owner. No statement here implies approval or guaranteed future compatibility.
