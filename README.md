# Street Tracker

Street Tracker 是一个用于 AstrBot 的《Street Fighter 6》玩家信息查询插件。插件会访问 Capcom Buckler 玩家主页，解析玩家档案与对战统计，并通过聊天指令返回结果。

## 功能

- `/查询 <player_id>`：按玩家 ID 查询 SF6 玩家信息。
- `/绑定 <player_id>`：把当前聊天用户绑定到一个玩家 ID，之后可以直接使用 `/查询`。
- 使用 AstrBot 插件配置中的 Cookie 进行鉴权请求。
- 优先解析 Buckler 页面中的 `__NEXT_DATA__` 数据，页面结构变化时会尝试备用解析逻辑。

## 查询结果

当前返回以下信息：

- 玩家 ID
- 玩家名
- 段位
- 常用角色
- 常用角色段位
- 大师分 MR
- 总时长
- 排位赛时长
- 休闲赛时长
- 比赛间时长
- 排位对局场次

缺失或无法解析的字段会显示为 `N/A`。

## 安装

1. 将本仓库放入 AstrBot 的插件目录，例如：

   ```bash
   cd AstrBot/data/plugins
   git clone https://github.com/zihang-huang/astrbot_plugin_street_tracker
   ```

2. 在 AstrBot WebUI 中重载插件，或重启 AstrBot。
3. 在插件配置页面填写 `sf6_cookie`。
4. 在聊天中发送 `/查询 <player_id>` 测试查询。

依赖由 AstrBot 根据 `requirements.txt` 安装，目前仅需要：

```text
httpx>=0.27.0
```

## 配置

配置文件由 `_conf_schema.json` 声明，可直接在 AstrBot WebUI 中编辑。

| 配置项 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `sf6_cookie` | 是 | 空 | 登录 `streetfighter.com` 后从浏览器复制的完整 Cookie 请求头内容。 |
| `user_agent` | 否 | 内置浏览器 UA | 自定义请求使用的 User-Agent。通常保持为空即可。 |
| `request_timeout_seconds` | 否 | `20` | 请求 Buckler 页面时的超时时间，单位为秒。 |

Cookie 属于敏感信息，请不要发到群聊、日志、截图或公开 Issue 中。如果查询提示 Cookie 失效，请重新登录 Buckler 后更新配置。

## 使用

直接查询指定玩家：

```text
/查询 1234567890
```

绑定当前用户：

```text
/绑定 1234567890
```

绑定后查询：

```text
/查询
```

## 常见问题

### 提示 Cookie 无效或已过期

请重新登录 Street Fighter 6 Buckler 官网，复制新的 Cookie 并更新插件配置。Buckler 的登录态可能会过期，过期后插件无法继续查询。

### 提示无法解析玩家数据

通常表示 Buckler 页面结构发生变化、目标页面返回异常内容，或 Capcom 临时调整了页面数据。可以先确认玩家 ID 是否正确，再查看 AstrBot 日志。

### 查询速度较慢或失败

插件会实时请求 Buckler 页面，网络质量、Capcom 服务状态和反爬限制都会影响结果。可以适当调大 `request_timeout_seconds`。

## 文件说明

仓库中与插件运行直接相关的核心文件：

- `main.py`：AstrBot 插件入口与指令处理。
- `sf6_profile.py`：Buckler 页面请求、解析和字段标准化。
- `_conf_schema.json`：AstrBot WebUI 配置声明。
- `metadata.yaml`：插件市场元数据。
- `requirements.txt`：插件依赖。
- `README.md`：中文使用说明。
- `LICENSE`：开源许可证。

## 开发校验

提交前建议运行：

```bash
ruff format .
ruff check .
python -m compileall .
```
