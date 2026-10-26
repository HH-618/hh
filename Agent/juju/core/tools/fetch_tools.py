import shutil
import subprocess
from urllib.parse import urlparse


CURL_TIMEOUT = 30
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _decode_output(data: bytes) -> str:
    for encoding in ("utf-8", "gbk", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def fetchweb(url):
    """获取指定网页的主要内容，并转换为 Markdown"""
    if not isinstance(url, str) or not url.strip():
        return "错误: 网页 URL 不能为空。"

    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        return "错误: 请提供有效的 http/https 网页 URL。"

    curl_path = shutil.which("curl")
    if not curl_path:
        return "错误: 未找到本地 curl 程序，请确认已安装 curl 并加入 PATH。"

    command = [
        curl_path,
        "-L",
        "--fail",
        "--silent",
        "--show-error",
        "--compressed",
        "--max-time",
        str(CURL_TIMEOUT),
        "--connect-timeout",
        "10",
        "--max-redirs",
        "5",
        "--proto",
        "=http,https",
        "--proto-redir",
        "=http,https",
        "-A",
        USER_AGENT,
        "-H",
        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "--",
        url,
    ]

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            timeout=CURL_TIMEOUT + 10,
        )
    except subprocess.TimeoutExpired:
        return f"错误: 获取网页超时（超过 {CURL_TIMEOUT} 秒）: {url}"
    except OSError as exc:
        return f"错误: 调用 curl 获取网页失败: {exc}"

    if process.returncode != 0:
        detail = _decode_output(process.stderr).strip()
        suffix = f": {detail}" if detail else ""
        return (
            f"错误: 获取网页失败（curl 退出码 {process.returncode}）"
            f"{suffix}，URL: {url}"
        )

    if not process.stdout or not process.stdout.strip():
        return f"错误: 网页返回内容为空: {url}"

    try:
        import trafilatura
    except ImportError:
        return (
            "错误: 未安装 trafilatura，无法提取网页正文。"
            "请先执行: py -m pip install trafilatura"
        )

    try:
        markdown = trafilatura.extract(
            process.stdout,
            url=url,
            output_format="markdown",
            include_comments=False,
            include_tables=True,
            include_links=True,
            include_formatting=True,
            with_metadata=True,
        )
    except Exception as exc:
        return f"错误: HTML 解析失败: {exc}，URL: {url}"

    if not markdown or not markdown.strip():
        return (
            "错误: 无法从网页提取正文内容。"
            "该页面可能由 JavaScript 动态渲染、需要登录，或不受支持。"
            f"URL: {url}"
        )

    return f"URL: {url}\n\n{markdown.strip()}"
