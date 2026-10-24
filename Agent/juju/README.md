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
```

程序会自动从当前目录或 `Practice02/` 查找 `config.ini`。
