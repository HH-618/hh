import subprocess


CLI_TIMEOUT = 30
MAX_STREAM_CHARS = 10000


def _decode_output(data):
    """尽量按 UTF-8、GBK 或 GB18030 解码子进程输出"""
    if not data:
        return ""

    for encoding in ("utf-8", "gbk", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _format_stream(name, data):
    """格式化 stdout/stderr，并截断过长的输出"""
    text = _decode_output(data)
    if not text:
        return f"{name}: (空)"

    if len(text) > MAX_STREAM_CHARS:
        omitted = len(text) - MAX_STREAM_CHARS
        text = text[:MAX_STREAM_CHARS]
        marker = (
            f"\n...(输出已截断：仅显示前 {MAX_STREAM_CHARS} 个字符，"
            f"省略 {omitted} 个字符)"
        )
        return f"{name}:\n{text}{marker}"

    return f"{name}:\n{text}"


def _format_result(command, args, exit_code, stdout, stderr):
    return "\n".join(
        [
            f"命令: {command}",
            f"参数: {args!r}",
            f"退出码: {exit_code}",
            _format_stream("标准输出", stdout),
            _format_stream("标准错误", stderr),
        ]
    )


def RunCli(command, args=None):
    """执行本地命令行程序，并返回 stdout、stderr 和退出码"""
    if not isinstance(command, str) or not command.strip():
        return "错误: command 必须是非空字符串。"

    command = command.strip()
    if args is None:
        args = []
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        return "错误: args 必须是字符串列表。"

    try:
        process = subprocess.run(
            [command, *args],
            capture_output=True,
            timeout=CLI_TIMEOUT,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        return _format_result(
            command,
            args,
            f"无（执行超过 {CLI_TIMEOUT} 秒，进程已终止）",
            exc.stdout or b"",
            exc.stderr or b"",
        )
    except FileNotFoundError:
        return f"错误: 未找到命令或程序: {command}"
    except PermissionError as exc:
        return f"错误: 没有权限执行命令 {command}: {exc}"
    except ValueError as exc:
        return f"错误: 命令参数无效: {exc}"
    except OSError as exc:
        return f"错误: 启动命令失败: {exc}"

    return _format_result(
        command,
        args,
        process.returncode,
        process.stdout,
        process.stderr,
    )
