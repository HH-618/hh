from typing import List, Dict, Any


def get_tools_schema() -> List[Dict[str, Any]]:
    return [
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
