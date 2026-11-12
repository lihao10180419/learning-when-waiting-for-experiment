# 0.1.1 公共目录送审准备

准备依据：已安装的官方 Plugin Creator 0.1.28，`prepare-plugin-submission` 与 `update-plugin` 技能；检查了 listing、review-materials、plugin-packages 和 zip-requirements。以下为本地准备记录，不是 OpenAI 审核结果。

## 上传哪一个包

运行 `python tools/build_release.py`，生成：

- `dist/experiment-learning-v0.1.1-submission.zip`：公共目录上传候选，根目录直接包含 `plugin.json`，仅一个插件。
- `dist/experiment-learning-v0.1.1-source.zip`：完整 GitHub 源码，含本地 marketplace、测试与开发工具，不能代替送审包。
- 相应 SHA-256 文件与 `release-report.json`：完整性、实际 ZIP 清单与元数据检查结果。

送审包保留兼容清单，但不包含 `.app.json`、app 绑定、MCP 服务、hooks、marketplace、测试、第三方依赖、账号信息、用户配置、会话 UUID、数据库或日志。图标是原创书本与时钟图形，512px logo / 128px composer icon，MIT 许可。两个技能、脚本、设置/隐私/支持/条款文档与 LICENSE 都在包内。

## 商店文案草案

| 字段 | 当前草案 |
| --- | --- |
| 名称 | Experiment Learning（19 字符） |
| 副标题 | Learn while experiments run（27 字符） |
| 分类 | Productivity |
| 发布者 | 保留原作者 GitHub 标识；实际认证个人/企业名称待本人确认 |
| 能力 | 本机实验监测、等待时学习卡片、学习进度保存 |
| 执行 | `requires_local_executor: true`；Windows、Python、本机 CLI |

英文完整描述和默认提示已写入两份清单。内置卡片为中文入门示例，支持用户自行导入 JSON 卡片，不声明完整课程、多语言教学保证或远程作业支持。

## 必须补齐的发布事实

1. 本人确认认证个人/企业及希望显示的发布者名称。
2. 本人确认全部可用国家/地区，或指定国家代码。未知时不写 `countries`；只有明确选择全部才使用空数组。
3. 本人确认是否涉及支付/购买，涉及时说明内容与支付位置。未知时不代填 commerce 声明。
4. 本人审核 [隐私草案](../plugins/experiment-learning/docs/PRIVACY.md)、[支持草案](../plugins/experiment-learning/docs/SUPPORT.md)、[条款草案](../plugins/experiment-learning/docs/TERMS.md)，确认公开支持方式与实际数据实践。
5. 四个无须登录即可访问的 HTTPS 页面：插件介绍、支持、隐私政策、使用条款。当前仓库为私有，文件草案不算已发布页面。准备好页面后再由仓库所有者决定公开仓库或另行托管文档；不猜测 GitHub Pages 地址。真实访问并核对内容后才能写入四个 URL 字段。

这些事实仍待确认时，ZIP 可以通过结构检查，但**不能标为可直接送审**。`validate_release.py` 的 listing_gaps 不是完整的身份/法律审核，不推断任何已通过验证的事实。

## 审查人员复现

本插件仅提供技能和本地脚本，无 MCP/App。按官方技能，不需要 MCP 的五正三负案例、演示视频或第三方测试账号；也没有为满足数量虚构这些材料。清单内提供自然语言 review prompts；本地实测见 [VERIFICATION.md](VERIFICATION.md)。

在兼容 Windows 上使用独立 profile 与单独 Codex 学习对话，按包内 SETUP 完成 `init`、`doctor`、`bind`、一次 `probe`。必须见到 `reply_confirmed`，不能把队列接受当成功。正常实验保留原命令与环境。明确的流程验收可运行 15 秒 simulate，使用该任务独立 `--test` 阈值，在真实进程确认后写 `waiting`；核对事件、回复时刻、实际 PID 和最终输出/退出码。不要对实际训练使用 `--test`。

预期边界：缺少 waiting、短任务、需审批/输入、暂停、免打扰均不应生成卡片；普通读文件不接入；远程 SSH 提交不可当作远程实验生命周期；停止学习不取消实验。队列失败时实验应继续。具体原生回复时延无法保证。

## 到官方平台前

官方本机插件指南要求：核心依赖本机执行、文件系统/桌面应用或离线能力的插件，在提交前联系 OpenAI 确认产品适用范围。这是本项目的独立适用性问题，不能靠设置 `requires_local_executor` 或身份认证代替。给 OpenAI 的说明模板见 [ELIGIBILITY.md](ELIGIBILITY.md)。

技术与发布事实齐全、适用范围确认后，再由本人登录官方插件平台、选正确组织、完成身份验证；上传候选 ZIP，检查导入元数据、扫描与平台提示，亲自完成法律/政策声明，再提交审核。上传、提交、通过和公开发布是不同状态。本次没有在平台创建草稿、提交或发布。

官方依据：[送审流程](https://developers.openai.com/plugins/deploy/submission)、[本机插件](https://developers.openai.com/plugins/deploy/desktop-only)、[本机执行适用性说明](https://developers.openai.com/plugins/guides/submit-claude-plugin)。
