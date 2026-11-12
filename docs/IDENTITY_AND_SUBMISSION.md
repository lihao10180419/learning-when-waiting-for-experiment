# 本人身份认证与后续送审

核对日期：2026-11-12。个人发布者已选择公开名称 `lihao10180419`；本文件没有替本人完成身份验证或接受平台法律/政策声明。

## 现在可以完成的个人认证

1. 登录 [OpenAI Platform](https://platform.openai.com/)，使用将拥有并提交插件的账号。
2. 打开[组织常规设置](https://platform.openai.com/settings/organization/general)，确认当前选中的组织正确。后续在插件平台使用同一个组织；插件属于该组织，不属于 GitHub 登录状态本身。
3. 找到身份验证区域，选择 **Individual／个人验证**。按该页面要求填写真实资料，并由本人完成证件、拍摄或其他验证步骤；具体要求以当时页面为准。
4. 等待验证状态通过。保留页面显示的认证身份，后续上传时选择它。目录展示名由平台选定的认证身份决定；若平台显示为认证姓名，不能仅靠 ZIP 的 GitHub 昵称覆盖。需要改公开清单时再同步更新，不在公开仓库写入身份证件资料。
5. 若无法找到入口，先核对所选组织及自身权限。提交者需为组织所有者，或拥有 **Apps Management Write**。把具体页面提示或错误文字带回即可继续排查。

官方依据：[提交权限与发布身份](https://developers.openai.com/plugins/deploy/submission#confirm-access-and-publishing-identity)。

## 投递验收通过之后

1. 打开[插件提交平台](https://platform.openai.com/plugins)，确认同一组织/项目。
2. 选择 **Upload new or existing plugin**；若界面先要求插件类型，选择 **Skills only**。选择本人已验证的 Developer identity。
3. 上传 `dist/experiment-learning-v0.1.1-submission.zip`。不要上传带 marketplace 和测试工具的 source ZIP。
4. 在 **Metadata & Skills** 核对版本、两个技能、图标、四个 URL、个人开发者身份、全部可用地区和不涉及支付的声明。等待必需扫描完成；如有问题，使用 **Copy issues** 取得完整错误文本，再修改 ZIP。
5. 资料和扫描通过后，由本人完成当时页面要求的法律/政策声明，再点 **Submit for review**。上传只创建草稿，提交审核和通过后公开发布是后续不同步骤。

这款插件无 MCP，不需要搭建远程服务器、OAuth、域名挑战、MCP 测试账号或演示视频。它按纯技能且需桌面执行的路径提交，清单已声明 `requires_local_executor: true`。若平台报该字段不允许，保留错误码和组织 ID，通过官方 OpenAI 联系人确认该组织的提交权限；不要通过删除标记来隐藏本机执行依赖。

官方依据：[本机执行的纯技能插件](https://developers.openai.com/plugins/deploy/desktop-only#plugins-without-an-mcp-server)、[提交全流程](https://developers.openai.com/plugins/deploy/submission)。最终是否获批由平台审核决定。
