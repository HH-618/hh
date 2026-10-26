# Juju

Juju 是从 `Practice02/chat_fs.py` 重构而来的 AI 助手，采用 **core + UI 分离** 的模块化、分层架构，便于未来扩展到 Web/Desktop/Mobile 等多前端。

## 目录结构

```
juju/
├── core/           # 核心业务逻辑（UI 无关）
│   ├── config/     # 配置加载（config.ini）
│   ├── llm/        # LLM 客户端与聊天引擎
│   ├── tools/      # 工具 schema 与文件系统工具实现
│   └── agent/      # Agent 服务层（统一对外接口）
├── tui/            # Textual TUI 界面
│   ├── app/        # 应用入口
│   ├── screens/    # 屏幕
│   ├── widgets/    # 自定义组件（预留）
│   └── styles/     # 样式
├── web/            # 未来 Web 前端（预留）
├── desktop/        # 未来 Desktop 前端（预留）
└── mobile/         # 未来 Mobile 前端（预留）
```

## 使用方式

### CLI 模式
```bash
py -m juju.cli
```

### TUI 模式（Textual）
```bash
py -m juju.tui_main
```

## 配置
需要 `config.ini`，格式同 `Practice02/config.ini`：
```ini
[llm]
api_url = http://127.0.0.1:1234/v1
api_key = lm-studio
model_name = qwen/qwen3-4b

[search]
baidu_api_key = <百度千帆 API Key>
# 可选配置
# api_url = https://qianfan.baidubce.com/v2/ai_search/chat/completions
# model = ernie-4.5-turbo-32k
# top_k = 10
# timeout = 30
```

程序会自动从当前目录、`juju/` 或 `Practice02/` 等位置查找 `config.ini`。

## 网络搜索

Agent 内置 `searchweb` 工具，通过 Function Calling 调用百度千帆「智能搜索生成」API。
`searchweb` 接收搜索关键词或问题 `query`，返回搜索摘要以及参考来源的标题、URL 等信息。
需要在 `config.ini` 的 `[search]` 小节配置 `baidu_api_key`；未配置或请求失败时，工具会以清晰的错误信息返回给 LLM。

## 网页正文读取

Agent 内置 `fetchweb` 工具，接收网页 URL，通过本地 `curl` 下载 HTML，再使用 `trafilatura`
提取正文并转换为 Markdown，保留标题、段落、列表、表格和链接。
需要本地已安装 `curl`，并安装 Python 包 `trafilatura`：

```bash
py -m pip install trafilatura
```

`fetchweb` 会自动处理访问失败、超时、HTML 解析失败和正文无法提取等情况，并通过工具结果返回错误信息。

## 执行本地 CLI

Agent 内置 `RunCli` 工具，接收程序名称 `command` 和参数列表 `args`，使用 `subprocess`
以参数列表方式执行命令（`shell=False`），并返回标准输出、标准错误和退出码。
默认执行超时为 30 秒；stdout 和 stderr 分别超过 10000 个字符时会截断，并明确标注截断情况。

示例工具参数：

```json
{"command": "py", "args": ["--version"]}
```

`RunCli` 暂不提供命令白名单、黑名单或审批机制。命令会以运行 Juju 的当前用户权限执行，
仅应在受控教学实验环境中使用。
