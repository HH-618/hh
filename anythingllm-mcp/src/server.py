import os
import re

import httpx
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

load_dotenv()

BASE_URL = os.getenv("ANYTHINGLLM_BASE_URL", "http://localhost:3001").rstrip("/")
API_KEY = os.getenv("ANYTHINGLLM_API_KEY", "")
WORKSPACE_SLUG = os.getenv("WORKSPACE_SLUG", "")
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))

mcp = MCPServer("anythingllm-mcp", version="0.1.0")


@mcp.tool()
async def ask_workspace_knowledge(question: str) -> str:
    """使用固定的 AnythingLLM 单个工作区的知识库回答问题，仅基于该工作区内容作答。"""
    if not WORKSPACE_SLUG or not API_KEY:
        raise RuntimeError("请先在 .env 中配置 WORKSPACE_SLUG 和 ANYTHINGLLM_API_KEY")

    url = f"{BASE_URL}/api/v1/workspace/{WORKSPACE_SLUG}/chat"
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"message": question, "mode": "query"},
        )
        resp.raise_for_status()
        data = resp.json()

    return re.sub(r"<think>.*?</think>", "", data.get("textResponse") or "", flags=re.S).strip()


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=MCP_HOST,
        port=MCP_PORT,
        stateless_http=True,
        json_response=True,
    )
