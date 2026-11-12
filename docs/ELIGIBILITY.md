# Desktop-only submission route — v0.1.1

Reviewed against official OpenAI documentation on 12 November 2026. This package fits the documented **skills-only, desktop execution** submission format. This establishes the technical submission route, not OpenAI approval of the plugin's behavior or publication.

The dedicated [desktop-only guide, Plugins without an MCP server](https://developers.openai.com/plugins/deploy/desktop-only#plugins-without-an-mcp-server) instructs skills-only packages that call local programs to declare `extensions.com.openai.requires_local_executor: true` and follow the standard submission flow. The compatibility manifest uses the same flag at its root. Both declarations are present here.

The guide's partner/organization allowlist prerequisite applies to **local MCP submissions**. This package has no MCP server or configuration, so that prerequisite is not imposed merely because Python scripts execute locally. If the portal rejects the local-executor field or raises an access issue, retain the exact error and organization ID and contact OpenAI. Do not remove the flag to disguise the dependency.

The broader [migration guide](https://developers.openai.com/plugins/guides/submit-claude-plugin) warns that local execution, filesystem/application access or inbound-message workflows can need product-specific review. The native queue/history adapter is therefore described explicitly below. The dedicated no-MCP path does not waive review or guarantee approval. It does not establish a separate advance whitelist prerequisite for this no-MCP package.

## Reviewer implementation brief

We are preparing Experiment Learning v0.1.1, a Windows Codex skills-only plugin. Its core workflow uses a local Python standard-library process wrapper to preserve experiment execution, then delivers a short learning card to a separate, explicitly selected Codex conversation only when the experiment is live and the main agent marks a genuine wait.

The package declares `requires_local_executor: true`. It has no MCP server, app binding, OAuth service, maintainer-hosted backend or additional API key. Monitoring and optional Codex-open process detection do not call a model. Card delivery and an explicit connection probe use the user's installed `codex queue --thread --message --resume`; exact replies are confirmed in the selected thread's local JSONL record. The target must be separately bound and actually verified. It does not monitor arbitrary external terminals or remote scheduler jobs.

Users explicitly opt into a marked user/project AGENTS.md integration and, optionally, a current-user Windows Startup shortcut. A fresh installation is unbound and inactive. Data stays in a per-user local profile except the selected card/return messages sent through Codex. The monitor retains local experiment output and learning progress; its published policy describes retention and deletion. The software is MIT licensed. A complete native CLI and reachable local daemon are explicit prerequisites; service startup is an explicit user action, never a polling action.

Clean-profile delivery and an actual temporary local-plugin installation have been tested. A card reply was confirmed 11.084 seconds into a live 15-second process, the completion reminder was confirmed, and a failed child preserved exit code 7 and both output streams while generating a confirmed native return reminder. See [VERIFICATION.md](VERIFICATION.md).

Public source: [learning-when-waiting-for-experiment](https://github.com/lihao10180419/learning-when-waiting-for-experiment). The owner selected individual publisher lihao10180419, all available countries/regions and no commerce. Identity verification, organization access, automated scans and owner attestations remain Portal steps. See [IDENTITY_AND_SUBMISSION.md](IDENTITY_AND_SUBMISSION.md).
