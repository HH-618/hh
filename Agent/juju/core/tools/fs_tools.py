import json
import mimetypes
import os
import shutil
import subprocess

from .cli_tools import RunCli
from .fetch_tools import fetchweb
from .schemas import get_tools_schema
from .search_tools import searchweb


TOOLS = get_tools_schema()


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
    "searchweb": searchweb,
    "fetchweb": fetchweb,
    "RunCli": RunCli,
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
