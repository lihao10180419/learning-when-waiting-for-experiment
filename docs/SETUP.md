# 设置、迁移与卸载

## 手动设置

在仓库根目录的 PowerShell 中：

```powershell
$learningCli = Join-Path (Get-Location) 'plugins/experiment-learning/scripts/manage.py'
python $learningCli init
python $learningCli doctor
```

如果插件已安装到 Codex 缓存，由设置技能解析实际安装路径，不要照抄其他人的路径。`doctor` 只检查相关能力，不输出账号凭据。

创建一个独立、持久的 Codex 学习任务“实验间隙学习”。让它只解释卡片、保存学习上下文，不运行实验、不修改项目、不调用本助手。通过客户端支持的工具获取精确 UUID；当前主任务、CLI 的最后一个任务和手机 ChatGPT 对话不能相互混用。

把下面占位符替换成刚创建的学习 UUID：

```powershell
python $learningCli bind --thread 'LEARNING_THREAD_UUID'
python $learningCli probe
```

`probe` 会产生一次真实模型请求。收到 `reply_confirmed` 才完成连接验证；仅 `queued_accepted` 的退出码为 3，表示回复尚未验证。检查桌面应用是否正常运行、登录、联网，以及精确目标会话是否收到对应编号。不要无限重发。对当前不支持的历史格式，先保留未验证状态。

## 自动接入范围

用户明确选择所有本机项目时：

```powershell
python $learningCli integrate --scope user
python $learningCli start
```

这会在用户级 Codex `AGENTS.md`（有 override 时使用 override）追加本插件标记块，保留已有内容并备份。该目录可能需要正常的写入授权；没有额外的 hook 信任要求。

只接入一个项目：

```powershell
python $learningCli integrate --scope project --project 'YOUR_PROJECT_DIRECTORY'
python $learningCli start
```

它依赖 Codex 遵循说明启动实验和标记等待，不是 OS 层面的“所有实验自动探测”。已在运行的实验、外部终端和远程作业不接管。

## 打开 Codex 自动启动

按需执行：

```powershell
python $learningCli enable-autostart
```

它使用现有 Python 和 PowerShell，在当前用户 Startup 目录创建 `Codex Experiment Learning Plugin.lnk`，启动无窗口的本地监听器。监听每 5 秒读取进程元信息，不调用模型；检测新的 Codex 主进程后启动监测器。手动停止在同一进程会话内有效，完全退出再打开 Codex 才重新自动启动。暂停状态仍保留。

此选项会修改当前用户 Startup 目录，需相应写入授权。不会改变 PowerShell 执行策略；如果策略不允许运行脚本，保持手动 `start`，由用户按自己的系统策略处理。不会为安装而关闭 Codex 或重启实验。

目前匹配已验证的 Windows 打包版 Codex 应用路径。其他安装方式不保证识别。Windows 实际登录触发及完整应用退出重开需要在适合的时候自行复测，不把配置成功等同于这些场景均已实测。

## 配置、卡片与自定义 profile

`paths` 显示实际数据目录。默认 `%LOCALAPPDATA%/CodexExperimentLearning/`，包含 `config.json`、`cards.json` 和 `runtime/state.sqlite3`。插件更新不会覆盖它们；`init` 也不覆盖已有文件。

可在启动设置前选择自定义 profile：

```powershell
$env:EXPERIMENT_LEARNING_HOME = 'YOUR_PROFILE_DIRECTORY'
python $learningCli init
```

绑定后不允许把已有 profile 静默改投另一个 UUID，避免未完成队列进入错误会话。另一个目标使用新 profile。可选 Startup 快捷方式会显式保存选定 profile，不依赖设置终端的临时环境。

可修改等待阈值、UTC 固定偏移、免打扰起止小时和卡片。`quiet_start == quiet_end` 表示全天免打扰；本版不提供夏令时自动切换。`--test` 只改变指定模拟任务的阈值，不修改正常配置。

## 从之前的本机定制版迁移

1. 先停止旧监测器，并关闭旧的 Windows 自动启动入口。
2. 用旧安装自己的移除入口删除它在用户说明中的标记块；不要删除其他项目约定。
3. 安装本插件并运行新设置。不要直接上传旧 `runtime/`、日志、会话 UUID 或配置。
4. 卡片可由你主动复制。首版不自动迁移旧数据库/未完成队列，以免重复投递或混淆目标。

设置脚本发现目标说明中仍有旧版标记块时，会拒绝叠加集成。不要同时运行两个指向同一学习会话的监测器。

## 升级和卸载

升级前：`disable-autostart`、`stop`；安装新版本后重新运行设置以刷新集成与 Startup 的实际路径。数据目录保留。

卸载前运行：

```powershell
python $learningCli disable-autostart
python $learningCli stop
python $learningCli integrate --scope user --remove
codex plugin remove experiment-learning@experiment-learning-community
```

项目级集成按原来的项目路径移除。`--remove` 只删除本插件标记块。以上不会结束实验或删除学习进度；用户数据按需另行保留或自行清理。
