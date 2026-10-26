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
        {
            "type": "function",
            "function": {
                "name": "searchweb",
                "description": "使用百度千帆智能搜索生成 API 搜索互联网，获取最新的网络信息和参考来源。当需要查询实时新闻、最新动态、事实性资料或本地知识无法回答的问题时使用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词或需要联网回答的问题",
                        }
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "fetchweb",
                "description": "获取指定网页的主要内容。使用本地 curl 下载网页 HTML，再用 trafilatura 提取正文并转换为 Markdown，保留标题、段落、列表、表格和链接，去除导航栏、广告和页脚。适合读取文章、文档或搜索结果中的网页。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "要获取的网页完整 URL，必须以 http:// 或 https:// 开头",
                        }
                    },
                    "required": ["url"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "RunCli",
                "description": "执行本地已安装的命令行程序（CLI）。command 是单个程序名称或可执行文件路径，args 是传给程序的参数列表。工具会返回 stdout、stderr 和退出码，可用于运行编译器、解释器、版本控制、系统信息等命令，并根据结果决定下一步操作。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "要执行的程序名称或路径，例如 py、git、node、curl 或完整可执行文件路径",
                        },
                        "args": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "传给程序的参数列表，例如 [\"--version\"] 或 [\"status\", \"--short\"]；没有参数时传空列表 []",
                        },
                    },
                    "required": ["command", "args"],
                },
            },
        },
    ]
