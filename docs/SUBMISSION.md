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
| 发布者 | 本人确认：个人，公开显示名 lihao10180419；平台身份认证待本人完成 |
| 能力 | 本机实验监测、等待时学习卡片、学习进度保存 |
| 执行 | `requires_local_executor: true`；Windows、Python、本机 CLI |

英文完整描述和默认提示已写入两份清单。内置卡片为中文入门示例，支持用户自行导入 JSON 卡片，不声明完整课程、多语言教学保证或远程作业支持。

## 已确认的发布设置

本人于 2026-11-12 确认个人发布，显示名使用 **lihao10180419**；面向**全部可用国家和地区**；插件**不收费、不涉及支付或购买**；保留当前图标、不另设品牌色。已在两份清单写入 `publication.countries: []`、`review.commerce: false` 及具体说明。完整决定见 [OWNER_DECISIONS.md](OWNER_DECISIONS.md)。

已按本人授权公开现有 GitHub 仓库及历史，开启 Issues，以仓库文档提供介绍、支持、[隐私政策](../plugins/experiment-learning/docs/PRIVACY.md)与[使用条款](../plugins/experiment-learning/docs/TERMS.md)。四个 HTTPS 页面均以无登录、无 Cookie、无令牌的请求读取到正确正文，并已写入两份清单，验证记录见 [PUBLIC_LINKS.md](PUBLIC_LINKS.md)。

发布资料字段已补齐；原生投递与实际安装验收已通过，见 [VERIFICATION.md](VERIFICATION.md)。本机执行的纯技能提交通道已按专门官方文档确认。上传包准备完成，后续由本人完成身份认证、导入核对、扫描和声明。空 listing_gaps 不代表身份验证或官方审核通过。

## 审查人员复现

本插件仅提供技能和本地脚本，无 MCP/App。按官方技能，不需要 MCP 的五正三负案例、演示视频或第三方测试账号；也没有为满足数量虚构这些材料。清单内提供自然语言 review prompts；本地实测见 [VERIFICATION.md](VERIFICATION.md)。

在兼容 Windows 上使用独立 profile 与单独 Codex 学习对话，按包内 SETUP 完成 `init`、`doctor`、`bind`、一次 `probe`。必须见到 `reply_confirmed`，不能把队列接受当成功。正常实验保留原命令与环境。明确的流程验收可运行 15 秒 simulate，使用该任务独立 `--test` 阈值，在真实进程确认后写 `waiting`；核对事件、回复时刻、实际 PID 和最终输出/退出码。不要对实际训练使用 `--test`。

预期边界：缺少 waiting、短任务、需审批/输入、暂停、免打扰均不应生成卡片；普通读文件不接入；远程 SSH 提交不可当作远程实验生命周期；停止学习不取消实验。队列失败时实验应继续。具体原生回复时延无法保证。

## 到官方平台前

专门的官方本机插件指南明确列出“没有 MCP 的插件”路径：纯技能调用本机程序时声明 requires_local_executor=true，按标准流程提交。本机 MCP 的合作方白名单限制不直接适用于这个无 MCP 包。平台仍可能就本机执行和队列/会话记录适配要求专项审查；技术归类并非获批。依据与审查说明见 [ELIGIBILITY.md](ELIGIBILITY.md)。

本人可先完成身份认证，再按[身份认证与送审步骤](IDENTITY_AND_SUBMISSION.md)进入官方平台、选正确组织，上传 ZIP，检查导入元数据、扫描与提示，亲自完成法律/政策声明，再提交审核。上传、提交、通过和公开发布是不同状态。本次没有在平台创建草稿、提交或发布。

官方依据：[送审流程](https://developers.openai.com/plugins/deploy/submission)、[本机插件](https://developers.openai.com/plugins/deploy/desktop-only)、[本机执行适用性说明](https://developers.openai.com/plugins/guides/submit-claude-plugin)。
