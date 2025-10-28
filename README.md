<div align="center">
<h1>✨ncatbot - GroupManager 插件✨</h1>

一个功能完善的 NcatBot 群组管理插件，提供自动审核、入群欢迎、禁言管理、头衔设置等全方位群管能力。


[![License](https://img.shields.io/badge/License-MIT_License-green.svg)](https://github.com/Sparrived/ncatbot-plugin-group-manager/blob/master/LICENSE)
[![ncatbot version](https://img.shields.io/badge/ncatbot->=4.2.9-blue.svg)](https://github.com/liyihao1110/ncatbot)
[![Version](https://img.shields.io/badge/version-1.0.6-orange.svg)](https://github.com/Sparrived/ncatbot-plugin-group-manager/releases)


</div>


---

## 🌟 功能亮点

- ✅ **自动欢迎** - 新成员进群自动发送欢迎消息，支持识别邀请人
- ✅ **离群提醒** - 记录群成员离开或被移除的场景，自动发送提示信息
- ✅ **智能审核** - 基于 QQ 等级的入群申请自动审核，防止小号进群，支持二次申请手动审核
- ✅ **禁言管理** - 支持对违规成员进行禁言处理，时长可自定义（1-1440分钟）
- ✅ **头衔设置** - 为群成员设置或清除专属头衔，彰显身份（需Bot为群主）
- ✅ **订阅机制** - 通过白名单限制插件作用范围，避免对未关注群组产生影响
- ✅ **权限检测** - 自动检测Bot权限，避免无权限操作导致的错误

## ⚙️ 配置项

配置文件位于 `data/GroupManager/GroupManager.yaml`

| 配置键 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `auto_approve.enabled` | `bool` | `true` | 是否启用自动审核逻辑。 |
| `auto_approve.min_qq_level` | `int` | `5` | 允许自动通过的最低 QQ 等级。低于此等级的用户会被自动拒绝并加入二次申请列表。 |
| `welcome_message` | `bool` | `true` | 新成员进群时是否发送欢迎语。 |
| `leave_message` | `bool` | `true` | 成员离群时是否发送提示。 |
| `subscribed_groups` | `List[str]` | `['123456789']` | 插件生效的群号白名单。只有在此列表中的群组才会处理事件和命令。 |

**配置示例:**
```yaml
auto_approve:
  enabled: true
  min_qq_level: 5
welcome_message: true
leave_message: true
subscribed_groups:
- '123456789'
- '987654321'
```

> **提示:** 配置文件可通过 NcatBot 的统一配置机制进行覆盖。建议使用 `/gm subscribe` 命令动态添加群组，避免手动修改配置后需要重启机器人。

## 🚀 快速开始

### 依赖要求

- Python >= 3.8
- NcatBot >= 4.2.9
- 无额外第三方依赖

### 使用 Git

```bash
git clone https://github.com/Sparrived/ncatbot-plugin-group-manager.git
cd ncatbot-plugin-group-manager
cp -r plugins/group_manager /path/to/your/ncatbot/plugins/
```

> 请将 `/path/to/your/ncatbot/plugins/` 替换为机器人实际的插件目录。

### 自主下载

1. 将本插件目录置于 `plugins/group_manager`。
2. 根据实际需要调整 `subscribed_groups` 等配置项（建议在群内使用指令调整，手动调整config需要重启机器人）。
3. 重启 NcatBot，插件将自动加载。

### 插件指令

> **注意事项:**
> - 所有指令仅限 NcatBot 管理员用户使用（`admin_group_filter` 限制）
> - 机器人需要有群管理员权限才能执行禁言等操作
> - 机器人需要有群主权限才能执行头衔设置操作
> - 支持 @ 用户来指定目标成员（在 `mute` 和 `prefix` 命令中）
> - 头衔设置仅在机器人为群主时可用，管理员权限无法设置头衔

| 指令 | 参数 | 说明 | 示例 |
| --- | --- | --- | --- |
| `/gm approve <qq号> [-d\|--deny]` | `qq号`：待处理成员 QQ<br>`-d/--deny`：拒绝申请 | 处理待审核的入群申请。不加 `-d` 则通过申请 | `/gm approve 123456789`<br>`/gm approve 123456789 -d` |
| `/gm mute <qq号\|@用户> [duration]` | `qq号/@用户`：目标成员<br>`duration`：禁言时长（分钟），默认 10，范围 1-1440 | 对指定成员执行禁言操作 | `/gm mute 123456789 30`<br>`/gm mute @某人 60` |
| `/gm prefix <qq号\|@用户> <头衔> [-c\|--clear]` | `qq号/@用户`：目标成员<br>`头衔`：要设置的专属头衔<br>`-c/--clear`：清除头衔 | 为指定成员设置或清除群专属头衔（**仅Bot为群主时可用**） | `/gm prefix 123456789 活跃成员`<br>`/gm prefix @某人 水群之王`<br>`/gm prefix 123456789 -c` |
| `/gm subscribe` | 无 | 订阅当前群的群管功能，使自动欢迎、自动审核等功能生效 | `/gm subscribe` |
| `/gm unsubscribe` | 无 | 取消当前群的订阅，插件对该群停止处理 | `/gm unsubscribe` |
| `/gm help` | 无 | 显示所有可用指令及其说明 | `/gm help` |



## 🧠 运作逻辑

### 订阅机制
- 插件在执行事件处理前，会先检查群组是否在 `subscribed_groups` 配置列表中
- 对于未订阅的群组，插件会跳过处理，同时在日志中输出调试信息
- 使用 `/gm subscribe` 可快速将当前群添加到白名单，无需重启机器人

### 入群审核流程
1. 接收到入群申请后，插件会调用平台接口获取申请人的 QQ 等级
2. 如果 QQ 等级低于配置的 `min_qq_level`，则自动拒绝并记录到二次申请列表
3. 对于二次申请的用户，插件会通知管理员手动审核
4. 管理员可使用 `/gm approve` 命令手动处理待审申请

### 权限检测机制
- **禁言功能**: 要求Bot具有管理员或群主权限，且不能对同级管理员或更高权限用户操作
- **头衔设置**: 要求Bot必须是群主，管理员权限无法设置头衔
- 执行前会自动检测权限，权限不足时会给出友好提示

### 消息通知
- **入群欢迎**: 新成员进群时自动 @ 欢迎，并标注邀请人（如果是邀请进群）
- **离群提醒**: 成员主动退群或被移除时发送通知，区分不同场景

## 🪵 日志与排错

插件使用 NcatBot 的统一日志系统，所有操作都会记录详细日志。

### 查看日志
```bash
# 日志文件位置
logs/bot.log.YYYY_MM_DD

# 筛选 GroupManager 相关日志
grep "GroupManager" logs/bot.log.2025_10_28
```

### 常见问题

**Q: 为什么指令没有响应？**
- 检查当前群是否已订阅（使用 `/gm subscribe`）
- 确认发送指令的用户是否在 NcatBot 的管理员列表中
- 查看日志确认是否有错误信息

**Q: 禁言/头衔设置失败？**
- 确保机器人账号具有群管理员权限（禁言功能）
- 确保机器人账号具有群主权限（头衔设置功能）
- 确认目标用户不是群主或其他管理员
- 管理员之间不能互相禁言

**Q: 自动审核不工作？**
- 检查 `auto_approve.enabled` 配置是否为 `true`
- 确认 `min_qq_level` 设置是否合理

## 🤝 贡献

欢迎通过 Issue 或 Pull Request 分享改进建议、提交补丁！

### 贡献指南
1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范
- 遵循 PEP 8 Python 代码风格
- 添加必要的注释和文档字符串
- 确保代码通过基本功能验证


## 🙏 致谢

感谢以下项目和贡献者：

- [NcatBot](https://github.com/liyihao1110/ncatbot) - 提供稳定易用的 OneBot11 Python SDK
- 社区测试者与维护者 - 提交 Issue、Pull Request 以及改进建议

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

<div align="center">

如果本插件帮助到了你，欢迎为项目点亮 ⭐ Star！

[报告问题](https://github.com/Sparrived/ncatbot-plugin-group-manager/issues) · [功能建议](https://github.com/Sparrived/ncatbot-plugin-group-manager/issues) · [查看发布](https://github.com/Sparrived/ncatbot-plugin-group-manager/releases)

</div>

