# 实验等待学习助手

**长实验真正运行、主项目明确等待时，在独立 Codex 对话中插空学习。**

[English](README.md) · [完整设置](docs/SETUP.md) · [隐私与数据](docs/PRIVACY.md) · [MIT 许可](LICENSE)

本地程序负责确认实验进程、计时、检查等待状态和保存进度。符合条件后，它向你自己的“实验间隙学习”会话投递一张短卡片；实验完成、失败或需要人工处理时，提醒返回项目。

**24 小时后台监测也不消耗模型 token。** 只有投递、学习问答和你主动执行的连接测试使用现有 Codex 额度。无需新增 API key、付费服务或 Python 依赖。

## 安装

当前支持 Windows 10/11、Python 3.10+、已登录的 Codex 桌面应用，以及提供 `queue` 的 Codex CLI。原型实测版本为 `0.167.0-alpha.3.2`；其他版本必须通过自己的连接测试。当前不支持 macOS/Linux 或远程调度作业。

```powershell
codex plugin marketplace add https://github.com/lihao10180419/learning-when-waiting-for-experiment.git
codex plugin add experiment-learning@experiment-learning-community
```

安装后新开一个 Codex 对话，输入：

> 使用 $experiment-learning-setup 配置实验等待学习助手：创建独立学习对话，验证真实回复，接入我的本机项目，并启用打开 Codex 时自动启动。

插件安装负责加载技能；绑定会话、全项目说明和 Windows 自动启动由设置流程按你的选择完成。私有 GitHub 仓库需要 Git 访问权限。连接了 GitHub 不代表命令行 Git 已自动获得访问权限。客户端和工作区策略也可能限制自定义 marketplace。

本项目通过 GitHub marketplace 分发，不代表已上架或通过官方公共插件目录审核。

## 日常使用

按正常方式让 Codex 做项目。已授权集成的 Codex 会把耗时本机实验交给包装器，在进程真实启动且自己确实等待结果后写入等待标记。不会靠命令里出现 `train` 或 `python`、高 CPU、或者执行前事件就推断你空闲。

- 已知预计总时长至少 10 分钟，稳定运行 30 秒后才可能推送。
- 预计未知时，实际运行 3 分钟后才可能推送，并注明剩余时长未知。
- 没有等待标记、进程未运行、正在授权/输入、暂停或免打扰时不推送。
- 默认 UTC+8 的 23:00—08:00 免打扰，可修改。没有固定时刻的每日学习提醒。
- 同一主会话的一个连续等待时段只生成一个卡片事件。多轮等待可以继续提醒；优先继续未学完的卡片。

自动接入依赖明确授权后追加的 `AGENTS.md` 标记块，覆盖遵循约定的 Codex 启动，不是扫描所有终端进程。已在运行的实验不重启接管。SSH 命令结束不等于远程实验结束。

## 学习内容与控制

内置三张“入门示例”卡片。可用 `cards validate` 检查自己的课程，再用 `cards import --file PATH` 导入；导入备份旧卡片并拒绝无效先修关系。卡片和程序分离，可在用户目录的 `cards.json` 编辑。首次请求和回复都不提前提供答案；在原生学习对话说“显示答案”再由 Codex 解释。

只有你明确说“已学完”才推进；收到卡片只记录为 `in_progress`。支持 `暂停`、`恢复`、`今日不再提醒`、`稍后学`，也有对应命令行控制。文字控制需要监测器运行并支持当前会话记录格式。

配置、进度和本地实验输出默认在 `%LOCALAPPDATA%/CodexExperimentLearning/`，不会写入插件缓存或跟随仓库上传。使用 `EXPERIMENT_LEARNING_HOME` 可设置独立 profile。

可选“打开 Codex 自动启动”：Windows 登录后静默运行本地监听器，约每 5 秒检查一次应用进程，在新的 Codex 进程会话开始时拉起监测器。手动停止后本次会话内不反复拉起；下次完全退出再打开时恢复。暂停状态不会被清除。停止助手不会终止实验。

## 送达状态

排队接受与真实回复分开记录。即使 `queue` 退出码为 0，也需要从精确学习 UUID 的会话记录确认回复。接受状态不明不无限重发，未收到回复不伪装成功。

本版读取经过验证的本地 JSONL 会话格式；分页或升级后的其他格式需要重新验证。监测和记录可以离线，原生模型回复需要联网；未承诺手机当前 ChatGPT 对话或系统横幅通知。

## 开发、升级与移除

```powershell
python -m unittest discover -s tests -v
python tools/validate_release.py
python tools/build_release.py
```

测试使用隔离目录，不投递模型消息。完整接入、卸载、升级与从旧版本迁移见 [设置说明](docs/SETUP.md)，验证范围见 [验收说明](docs/VERIFICATION.md)。升级前先关闭旧版本自动启动，升级后重新设置以刷新插件路径；用户数据保留。

MIT © 2026 lihao10180419 and contributors。

0.1.1 分别提供源码 ZIP 和仅含一个插件的公共目录上传候选 ZIP。发布者已确认个人显示名 lihao10180419、全部可用地区和不涉及插件收费；原生投递验收、公开链接验证及本机插件适用性仍须核对。详细材料见[送审准备](docs/SUBMISSION.md)。
