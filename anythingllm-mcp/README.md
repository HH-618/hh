# anythingllm-mcp

极简 MCP Server：**MCP 2026-07-28 + Streamable HTTP**，只做一件事——
从**唯一一个指定的 AnythingLLM 工作区**提取信息并进行 AI 回答。

## 结构

```
anythingllm-mcp/
├── .env              # 配置（已 gitignore）
├── .env.example      # 配置模板
├── pyproject.toml
├── README.md
├── src/server.py     # 唯一源码：1 个 tool + HTTP 传输
└── test_client.py    # 冒烟测试脚本
```

## 1. 配置

复制模板并填写：

```bash
copy .env.example .env
```

```env
ANYTHINGLLM_BASE_URL=http://localhost:3001
ANYTHINGLLM_API_KEY=<你的 AnythingLLM API Key>
WORKSPACE_SLUG=<唯一工作区的 slug>
MCP_HOST=127.0.0.1
MCP_PORT=8000
```

获取 `WORKSPACE_SLUG`（只取一个固定值）：

```bash
curl -H "Authorization: Bearer <API_KEY>" http://localhost:3001/api/v1/workspaces
```

## 2. 安装

```bash
py -3 -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## 3. 启动

```bash
python src/server.py
```

- MCP 端点：`http://127.0.0.1:8000/mcp`
- 传输：**Streamable HTTP**（非 stdio）
- 协议：2026-07-28（同时兼容 2025-11-25 及更早的老客户端握手）

## 4. 工具

| 工具 | 入参 | 说明 |
|---|---|---|
| `ask_workspace_knowledge` | `{"question": "string"}` | 用固定工作区的知识库回答问题，返回纯文本答案 |

内部调用 AnythingLLM：
`POST {ANYTHINGLLM_BASE_URL}/api/v1/workspace/{WORKSPACE_SLUG}/chat`，body `{"message": ..., "mode": "query"}`，
取响应中的 `textResponse`（并去掉模型的 `<think>` 思考块）。

## 5. 冒烟测试

```bash
python test_client.py "你的问题"
```

会依次验证：2026-07-28 的 `server/discover` → `tools/list` → `tools/call`，以及老协议客户端兼容性。

## 6. 接入 MCP 客户端

```json
{
  "mcpServers": {
    "anythingllm": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```
