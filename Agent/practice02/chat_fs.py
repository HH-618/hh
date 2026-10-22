import configparser
import json
import mimetypes
import os
import shutil
import subprocess
import time

from openai import OpenAI

config = configparser.ConfigParser()
config.read("config.ini")

client = OpenAI(
    base_url=config["llm"]["api_url"],
    api_key=config["llm"]["api_key"],
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "getdate",
            "description": "获取当前电脑的日期和时间",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "getcwd",
            "description": "获取当前工作目录的完整路径",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listdir",
            "description": "列出指定目录下的所有文件和子目录，目录名以 / 结尾",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "要列出的目录路径"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "getfiletype",
            "description": "获取指定文件的文件类型（扩展名和 MIME 类型）",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "readfile",
            "description": "读取指定纯文本文件的内容（不支持二进制文件）",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "createfile",
            "description": "在指定目录下根据文件名创建新文件，可指定初始内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "目标目录路径"},
                    "filename": {"type": "string", "description": "要创建的文件名"},
                    "content": {"type": "string", "description": "文件初始内容（可选）"},
                },
                "required": ["directory", "filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "editfile",
            "description": "编辑指定纯文本文件的内容，将整个文件覆盖为新的内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "新的完整内容"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "makedir",
            "description": "创建新目录（可包含多级路径）",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "要创建的目录路径"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "removedir",
            "description": "删除目录，非空目录连同其所有内容一起删除",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "要删除的目录路径"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "removefile",
            "description": "删除指定文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "要删除的文件路径"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rename",
            "description": "重命名文件或目录",
            "parameters": {
                "type": "object",
                "properties": {
                    "src": {"type": "string", "description": "原路径"},
                    "dst": {"type": "string", "description": "新路径"},
                },
                "required": ["src", "dst"],
            },
        },
    },
]


def getdate():
    """调用本地 date 命令获取当前日期和时间"""
    try:
        date_str = subprocess.run(
            ["cmd", "/c", "date", "/t"], capture_output=True, text=True
        ).stdout.strip()
        time_str = subprocess.run(
            ["cmd", "/c", "time", "/t"], capture_output=True, text=True
        ).stdout.strip()
        return f"{date_str} {time_str}"
    except Exception as e:
        return f"获取失败: {e}"


def getcwd():
    """获取当前工作目录"""
    return os.getcwd()


def listdir(path):
    """列出指定目录下的所有文件和子目录"""
    if not os.path.isdir(path):
        return f"错误: 目录不存在: {path}"
    try:
        entries = os.listdir(path)
    except OSError as e:
        return f"错误: {e}"
    lines = []
    for name in sorted(entries):
        full = os.path.join(path, name)
        lines.append(f"{name}/" if os.path.isdir(full) else name)
    return "\n".join(lines) if lines else "(空目录)"


def getfiletype(path):
    """获取指定文件的文件类型（扩展名和 MIME 类型）"""
    if not os.path.isfile(path):
        return f"错误: 文件不存在: {path}"
    ext = os.path.splitext(path)[1] or "(无扩展名)"
    mime, _ = mimetypes.guess_type(path)
    return f"{ext} ({mime or '未知类型'})"


def readfile(path):
    """读取指定纯文本文件的内容"""
    if not os.path.isfile(path):
        return f"错误: 文件不存在: {path}"
    content = None
    for enc in ("utf-8", "gbk"):
        try:
            with open(path, "r", encoding=enc) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue
        except OSError as e:
            return f"错误: {e}"
    if content is None:
        return "错误: 无法以纯文本方式读取（可能是二进制文件）"
    if len(content) > 100000:
        content = content[:100000] + "\n...(内容过长已截断)"
    return content


def createfile(directory, filename, content=""):
    """根据指定的目录和文件名创建新文件"""
    if not os.path.isdir(directory):
        return f"错误: 目录不存在: {directory}"
    path = os.path.join(directory, filename)
    if os.path.exists(path):
        return f"错误: 文件已存在: {path}"
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        return f"错误: {e}"
    return f"已创建文件: {path}"


def editfile(path, content):
    """编辑指定纯文本文件的内容（整文件覆盖）"""
    if not os.path.isfile(path):
        return f"错误: 文件不存在: {path}"
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        return f"错误: {e}"
    return f"已更新文件: {path}"


def makedir(path):
    """创建新目录"""
    if os.path.exists(path):
        return f"错误: 已存在: {path}"
    try:
        os.makedirs(path)
    except OSError as e:
        return f"错误: {e}"
    return f"已创建目录: {path}"


def removedir(path):
    """删除目录（非空目录连同其内容一起删除）"""
    if not os.path.isdir(path):
        return f"错误: 目录不存在: {path}"
    try:
        shutil.rmtree(path)
    except OSError as e:
        return f"错误: {e}"
    return f"已删除目录: {path}"


def removefile(path):
    """删除文件"""
    if not os.path.isfile(path):
        return f"错误: 文件不存在: {path}"
    try:
        os.remove(path)
    except OSError as e:
        return f"错误: {e}"
    return f"已删除文件: {path}"


def rename(src, dst):
    """重命名文件或目录"""
    if not os.path.exists(src):
        return f"错误: 源路径不存在: {src}"
    if os.path.exists(dst):
        return f"错误: 目标路径已存在: {dst}"
    try:
        os.rename(src, dst)
    except OSError as e:
        return f"错误: {e}"
    return f"已重命名: {src} -> {dst}"


TOOL_FUNCS = {
    "getdate": getdate,
    "getcwd": getcwd,
    "listdir": listdir,
    "getfiletype": getfiletype,
    "readfile": readfile,
    "createfile": createfile,
    "editfile": editfile,
    "makedir": makedir,
    "removedir": removedir,
    "removefile": removefile,
    "rename": rename,
}


def run_tool(name, arguments):
    func = TOOL_FUNCS.get(name)
    if func is None:
        return f"错误: 未知工具 {name}"
    try:
        args = json.loads(arguments) if arguments else {}
        result = func(**args)
    except json.JSONDecodeError as e:
        return f"错误: 参数解析失败: {e}"
    except TypeError as e:
        return f"错误: 参数不正确: {e}"
    except Exception as e:
        return f"错误: 执行失败: {e}"
    return result


messages = []

while True:
    user_msg = input("You: ")
    messages.append({"role": "user", "content": user_msg})
    try:
        while True:
            stream = client.chat.completions.create(
                model=config["llm"]["model_name"],
                messages=messages,
                tools=TOOLS,
                stream=True,
            )
            reply = ""
            tool_calls = {}
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    reply += delta.content
                    for char in delta.content:
                        print(char, end="", flush=True)
                        time.sleep(0.02)
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls:
                            tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                        if tc.id:
                            tool_calls[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls[idx]["name"] += tc.function.name
                            if tc.function.arguments:
                                tool_calls[idx]["arguments"] += tc.function.arguments
            if tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": reply or None,
                        "tool_calls": [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": tc["arguments"],
                                },
                            }
                            for tc in tool_calls.values()
                        ],
                    }
                )
                for tc in tool_calls.values():
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": run_tool(tc["name"], tc["arguments"]),
                        }
                    )
                continue
            messages.append({"role": "assistant", "content": reply})
            print()
            break
    except Exception as e:
        print(f"Error: {e}")
