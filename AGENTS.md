# AGENTS.md

本文件面向后续在该仓库中工作的自动化编码工具，说明项目边界、常用命令和维护约定。

## 项目概览

- 项目类型：AstrBot 插件，Python 编写。
- 插件用途：查询《Street Fighter 6》Buckler 玩家主页中的玩家档案和对战统计。
- 插件入口：`main.py`。
- 页面请求与解析逻辑：`sf6_profile.py`。
- 用户配置：`_conf_schema.json`。
- 插件元数据：`metadata.yaml`。

## 当前功能

- `/绑定 <player_id>`：绑定当前聊天用户与 SF6 玩家 ID。
- `/查询 <player_id>`：查询指定玩家 ID。
- `/查询`：查询当前用户已绑定的玩家 ID。

查询结果包括玩家 ID、玩家名、段位、常用角色、常用角色段位、MR、总时长、排位赛时长、休闲赛时长、比赛间时长和排位对局场次。

## 发布文件

仓库应保持为可发布插件包，只保留运行和发布必需文件：

- `main.py`
- `sf6_profile.py`
- `_conf_schema.json`
- `metadata.yaml`
- `requirements.txt`
- `README.md`
- `LICENSE`
- `.gitignore`
- `AGENTS.md`

不要提交本地缓存、抓包样例、调试脚本、虚拟环境、SDK 文档镜像或临时输出。

## AstrBot 开发规则

- 插件类必须继承 `Star`。
- 在 `main.py` 中使用 `@register(...)` 注册插件。
- 指令处理函数保持 `self, event, ...` 形式，并使用 `AstrMessageEvent` 类型标注。
- 指令和事件监听使用 `astrbot.api.event.filter` 中的装饰器。
- 优先使用异步处理和异步 IO。
- 不使用 `requests`；网络请求使用 `httpx` 或 `aiohttp`。
- 日志使用 `from astrbot.api import logger`。
- 少量键值状态使用 AstrBot 存储 API。
- 大型运行时产物应放入 `data/plugin_data/{plugin_name}/`，不要写入源码目录。

## 解析与请求规则

- 优先解析 Buckler 页面中的 `__NEXT_DATA__` JSON。
- 页面结构变化时再使用 JSON 脚本或文本模式兜底。
- 解析逻辑要容忍缺失字段和嵌套结构变化。
- 空值统一显示为 `N/A`。
- 网络请求必须设置超时和明确请求头。
- 处理 401、403、404、5xx 和反爬页面，不要把底层异常直接暴露给用户。
- 日志中不要泄露 Cookie。

## 代码风格

- 导入顺序：标准库、第三方库、本地模块。
- 保持类型标注，公共函数和方法需要标明返回值。
- 业务逻辑放在辅助类或函数中，指令处理保持轻量。
- 捕获异常时先捕获具体异常，最后才使用兜底异常处理。
- 非必要不新增抽象，不做无关重构。
- 默认使用 ASCII 编辑代码；中文文档和用户提示可以使用中文。

## 常用命令

安装开发依赖：

```bash
pip install ruff pytest httpx
```

格式化和静态检查：

```bash
ruff format .
ruff check .
```

基础语法校验：

```bash
python -m compileall .
```

当前仓库没有提交测试目录。若后续修改解析逻辑，应新增针对 `sf6_profile.py` 的回归测试，并使用 Mock HTTP 保持测试稳定。

## 版本与元数据

- `metadata.yaml` 中的 `name` 保持 `astrbot_plugin_` 前缀。
- 用户可见行为变化时同步更新 `version`。
- `display_name`、`desc`、`author`、`repo` 应保持准确。
- README 的功能说明必须与 `main.py` 中的实际指令一致。

## Git 卫生

- 编辑范围保持聚焦。
- 不回滚无关改动。
- 不提交缓存、构建产物或本地环境文件。
- 提交说明应描述行为影响，而不只是文件差异。
