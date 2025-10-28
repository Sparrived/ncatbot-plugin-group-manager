<div align="center">
<h1>✨ncatbot - GroupManager 插件✨</h1>

一个基于 NcatBot 的群组管理插件，提供自动审核、入群欢迎、离群提醒等能力。


<a><img src="https://img.shields.io/badge/License-MiT_License-green.svg"></a>
<a><img src="https://img.shields.io/badge/ncatbot->=4.2.9-blue.svg"></a>


</p>

</div>


---

## 功能亮点

- 自动欢迎新成员，支持识别邀请人。
- 记录群成员离开或被移除的场景，自动发送提示信息。
- 针对入群请求提供基础自动审核（按 QQ 等级过滤）。
- 通过订阅列表限制插件执行范围，避免对未关注群组产生影响。

## 配置项

| 配置键 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `auto_approve.enabled` | `bool` | `true` | 是否启用自动审核逻辑。 |
| `auto_approve.min_qq_level` | `int` | `5` | 允许自动通过的最低 QQ 等级。 |
| `welcome_message` | `bool` | `true` | 新成员进群时是否发送欢迎语。 |
| `leave_message` | `bool` | `true` | 成员离群时是否发送提示。 |
| `subscribed_groups` | `List[str]` | `['123456789']` | 插件生效的群号白名单。 |

> 配置文件可通过 NcatBot 的统一配置机制进行覆盖，或在插件初始化时动态更新。

## 快速开始

1. 将本插件目录置于 `plugins/group_manager`（或自定义插件目录）。
2. 在机器人配置中启用 `GroupManager` 插件。
3. 根据实际需要调整 `subscribed_groups` 等配置项。
4. 重启或热加载插件后，即可在群组中体验自动化管理体验。


## 运作逻辑

- 插件在执行事件处理前，会先检查群组是否在 `subscribed_groups` 中。
- 对于未通过检查的群组事件，插件会跳过处理，同时在日志中输出调试信息。
- 入群请求会调用平台接口获取申请人的QQ等级，并根据配置给出处理结果。

## 日志与排错

- 如需排查，可在 NcatBot 的日志目录下查看近期日志文件，关注 `GroupManager` 关键字。
- 若需更详细的输出，可调整机器人全局日志等级或为插件单独配置。

## 贡献

欢迎通过 Issue 或 Pull Request 分享改进建议、提交补丁。提交前请确保：

- 已执行必要的 lint／格式化工具。
- 在支持的场景下完成基本功能验证。


## 致谢

感谢以下项目和贡献者：

- [NcatBot](https://github.com/liyihao1110/ncatbot)：提供稳定易用的 OneBot11 Python SDK。
- 社区测试者与维护者：提交 Issue、Pull Request 以及改进建议。

如果本插件帮助到了你，欢迎为相关项目点亮 Star 或提交反馈，让生态更加繁荣。

