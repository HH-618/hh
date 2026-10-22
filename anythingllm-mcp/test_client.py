"""MCP 2026-07-28 (Streamable HTTP) 冒烟测试。

用法: python test_client.py "问题"
"""

import json
import sys

import httpx

URL = "http://127.0.0.1:8000/mcp"
MODERN_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "MCP-Protocol-Version": "2026-07-28",
}
META = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientCapabilities": {},
}


def modern(method: str, params: dict, rid: int = 1):
    headers = {**MODERN_HEADERS, "Mcp-Method": method}
    if "name" in params:
        headers["Mcp-Name"] = params["name"]
    body = {"jsonrpc": "2.0", "id": rid, "method": method, "params": {**params, "_meta": META}}
    r = httpx.post(URL, json=body, headers=headers, timeout=300)
    return r.status_code, r.json()


def legacy(question: str):
    """老协议（2025-11-25）客户端：initialize -> notifications/initialized -> tools/call"""
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    with httpx.Client(timeout=300) as c:
        init = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "smoke", "version": "1.0"},
            },
        }
        r = c.post(URL, json=init, headers=headers)
        sid = r.headers.get("mcp-session-id")
        print("[legacy] initialize ->", r.json().get("result", {}).get("protocolVersion"))
        if sid:
            headers["mcp-session-id"] = sid
        c.post(
            URL,
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
            headers=headers,
        )
        r = c.post(
            URL,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "ask_workspace_knowledge", "arguments": {"question": question}},
            },
            headers=headers,
        )
        return r.status_code, r.json()


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "hh.txt 里写了什么？"

    print("[2026] discover:", json.dumps(modern("server/discover", {})[1]["result"]["supportedVersions"]))
    status, data = modern("tools/list", {}, 2)
    print("[2026] tools:", [t["name"] for t in data["result"]["tools"]])

    status, data = modern(
        "tools/call",
        {"name": "ask_workspace_knowledge", "arguments": {"question": question}},
        3,
    )
    print(f"[2026] tools/call -> {status}")
    print("[2026] answer:", data.get("result", {}).get("content", [{}])[0].get("text", data))

    status, data = legacy(question)
    print(f"[legacy] tools/call -> {status}")
    print("[legacy] answer:", data.get("result", {}).get("content", [{}])[0].get("text", data))
