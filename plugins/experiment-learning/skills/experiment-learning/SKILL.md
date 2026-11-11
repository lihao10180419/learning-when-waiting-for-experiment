---
name: experiment-learning
description: Use the configured Windows learning assistant when starting a long local noninteractive experiment and genuinely waiting for its results. Also handle pause, resume and learning-progress controls. Do not treat ordinary short checks or remote SSH submission as a long local experiment.
---

Use `../../scripts/manage.py` relative to this skill folder. Resolve the installed path. Inspect `status` once as part of the project task; do not poll a model to monitor experiments. The configured learning UUID belongs to a separate task. If the current thread is that learning task, do not run experiments or invoke this assistant.

- Preserve the original interpreter, argument array, cwd and environment. For a semantic candidate such as training or evaluation, wrap with `run --id JOB-UNIQUE --cwd ORIGINAL --label SAFE-SHORT-NAME [--expected-seconds KNOWN-TOTAL] -- EXECUTABLE ARGS...`. Do not infer suitability from keywords or CPU alone.
- `run` preserves stdin, streams and exit status. Only explicitly noninteractive jobs may use detached `launch`. It returns an OS-confirmed PID and local output paths; `result --run JOB --follow` returns output and the original exit code.
- After actual process startup, mark `waiting --run JOB [OTHER-JOB ...]` only when the main agent is actually waiting for results and there is no approval, input request or other active work. Missing or conflicting markers suppress learning. Mark `busy` before doing other work; mark `attention` when the user must return. Neither cancels a job.
- Default thresholds: known total >=10 minutes with >=30 seconds stable runtime, or unknown total after 3 actual minutes. The monitor checks OS process creation identity and wrapper heartbeat. Leave expected duration unspecified when unknown. Never use `--test` on real tasks.
- Learning cards have prerequisites and persistent progress. A sent card is only in progress; use `done` only for the user's explicit completion. Controls: `pause`, `resume`, `today-off`, `later`. Native exact text controls are implemented through the local thread reader; report reader limitations honestly.
- Stop/Pause never terminate experiments. Respect manual Stop in the current application instance. The optional watcher can start the monitor on the next complete Codex relaunch. Cancel only on an explicit user request.

No model calls occur during background monitoring. Native card replies and learning questions require network access and use the account's quota. Queue acceptance, ambiguous acceptance and confirmed replies are different states; never retry ambiguous sends indefinitely. A local SSH PID is not the remote training job. Do not restart existing jobs or claim global process detection, idle-user detection or phone synchronization.

If setup is missing, keep project work moving and explain how to invoke `$experiment-learning-setup`; do not silently modify global instructions, add startup entries or fabricate connection success.
