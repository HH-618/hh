import json
import socket
import urllib.error
import urllib.request

from juju.core.config import load_search_settings


# 记录当前进程内确认无权限使用的模型，避免每次搜索都重复失败一次
_unavailable_models = set()


def _extract_error_detail(text):
    """从 API 错误响应中提取可读的错误信息"""
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        data = None

    if isinstance(data, dict):
        parts = []
        code = data.get("code", data.get("error_code"))
        message = data.get("message") or data.get("msg")
        error = data.get("error")
        if isinstance(error, dict):
            code = code or error.get("code")
            message = message or error.get("message")
        elif error and not message:
            message = str(error)
        request_id = data.get("requestId") or data.get("request_id")
        if code not in (None, ""):
            parts.append(f"错误码: {code}")
        if message:
            parts.append(f"错误信息: {message}")
        if request_id:
            parts.append(f"请求 ID: {request_id}")
        if parts:
            return "，" + "，".join(parts)

    text = (text or "").strip()
    return f"，响应内容: {text[:500]}" if text else ""


def _is_model_permission_error(data):
    """判断是否是当前 API Key 无权使用指定模型的错误"""
    if not isinstance(data, dict):
        return False
    code = str(data.get("code") or "").lower()
    message = str(data.get("message") or "").lower()
    return code == "invalid_appid" or "appid" in message


def _api_error(data):
    """返回 API 错误描述；没有错误时返回空字符串"""
    if not isinstance(data, dict):
        return ""
    code = data.get("code")
    if code not in (None, "", 0, "0", 200, "200"):
        return _extract_error_detail(json.dumps(data, ensure_ascii=False))
    if data.get("error") and not data.get("choices") and not data.get("references"):
        return _extract_error_detail(json.dumps(data, ensure_ascii=False))
    return ""


def _clean_text(value):
    return " ".join(str(value or "").split())


def _single_line(value):
    """将多行内容压缩为一行输出"""
    return " ".join(str(value or "").split())


def _format_reference_summary(references, max_items=5, max_chars=4000):
    """当 API 未返回模型摘要时，用参考网页片段整理一份搜索摘要"""
    lines = []
    total = 0
    for ref in references or []:
        if not isinstance(ref, dict):
            continue
        content = _clean_text(ref.get("content") or ref.get("abstract"))
        if not content:
            continue
        title = _clean_text(ref.get("title") or ref.get("web_anchor"))
        content = content[:500]
        line = f"[{len(lines) + 1}] {title + '：' if title else ''}{content}"
        if lines and total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line)
        if len(lines) >= max_items:
            break
    return "\n".join(lines)


def _format_sources(references):
    """整理参考来源的标题、URL 等信息"""
    lines = []
    seen_urls = set()
    for ref in references or []:
        if not isinstance(ref, dict):
            continue
        url = str(ref.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        title = _clean_text(ref.get("title") or ref.get("web_anchor")) or url
        extra = []
        if ref.get("web_anchor"):
            extra.append(_clean_text(ref["web_anchor"]))
        if ref.get("date"):
            extra.append(_clean_text(ref["date"]))
        suffix = f"（{'，'.join(extra)}）" if extra else ""
        lines.append(f"[{len(lines) + 1}] {title}{suffix}\n    URL: {url}")
    return "\n".join(lines)


def _format_response(data):
    choices = data.get("choices") or []
    summary = ""
    if choices and isinstance(choices[0], dict):
        message = choices[0].get("message") or {}
        if isinstance(message, dict):
            summary = str(message.get("content") or "").strip()

    references = data.get("references") or []
    if not summary:
        summary = _format_reference_summary(references)

    sources = _format_sources(references)

    parts = []
    if summary:
        label = "搜索摘要：" if choices else "搜索摘要（根据参考网页内容整理）："
        parts.append(f"{label}\n{summary}")
    if sources:
        parts.append(f"参考来源：\n{sources}")
    if not parts:
        return "搜索完成，但未获取到摘要或参考来源。请尝试更换关键词后重试。"
    return _single_line("\n\n".join(parts))


def _execute_request(settings, payload):
    """执行 HTTP 请求，返回 (解析后的数据, HTTP 状态码, 原始文本, 错误信息)"""
    request = urllib.request.Request(
        settings.api_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=settings.timeout) as response:
            raw = response.read()
            status = getattr(response, "status", 200)
    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read()
        except Exception:
            raw = b""
        status = exc.code
    except (TimeoutError, socket.timeout):
        return None, None, "", (
            f"错误: 搜索 API 请求超时（超过 {settings.timeout:g} 秒），请稍后重试。"
        )
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return None, None, "", (
                f"错误: 搜索 API 请求超时（超过 {settings.timeout:g} 秒），请稍后重试。"
            )
        return None, None, "", f"错误: 无法连接搜索 API，网络请求失败: {reason}"
    except OSError as exc:
        return None, None, "", f"错误: 网络请求失败: {exc}"

    text = raw.decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except ValueError:
        if status is not None and not 200 <= status < 300:
            return None, status, text, (
                f"错误: 搜索 API 请求失败（HTTP {status}）"
                f"{_extract_error_detail(text)}"
            )
        return None, status, text, (
            f"错误: 搜索 API 返回了无法解析的数据（HTTP {status}）"
            f"{_extract_error_detail(text)}"
        )
    if not isinstance(data, dict):
        return None, status, text, f"错误: 搜索 API 返回格式异常（HTTP {status}）。"
    return data, status, text, ""


def _build_payload(query, settings, use_model=True):
    payload = {
        "messages": [{"role": "user", "content": query}],
        "stream": False,
        "search_source": "baidu_search_v2",
        "resource_type_filter": [{"type": "web", "top_k": settings.top_k}],
        "search_mode": "required",
        "enable_deep_search": False,
    }
    if use_model and settings.model_name:
        payload["model"] = settings.model_name
    return payload


def searchweb(query):
    """通过百度千帆智能搜索生成 API 搜索互联网最新信息"""
    if not isinstance(query, str) or not query.strip():
        return "错误: 搜索关键词不能为空。"

    settings = load_search_settings()
    if not settings.api_key:
        return (
            "错误: 未配置百度千帆搜索 API Key。"
            "请在 juju/config.ini 的 [search] 小节设置 baidu_api_key。"
        )

    query = query.strip()
    use_model = (
        bool(settings.model_name)
        and settings.model_name not in _unavailable_models
    )
    payload = _build_payload(query, settings, use_model=use_model)
    data, status, text, error = _execute_request(settings, payload)

    # 某些 API Key 只有搜索权限、没有模型权限（invalid_appId）。
    # 此时自动退回到“百度搜索”模式，并使用参考网页片段整理摘要。
    if data is not None and _is_model_permission_error(data):
        if settings.model_name:
            _unavailable_models.add(settings.model_name)
        payload = _build_payload(query, settings, use_model=False)
        data, status, text, error = _execute_request(settings, payload)

    if error:
        return error

    api_error = _api_error(data)
    if api_error:
        return f"错误: 百度千帆搜索 API 返回错误{api_error}"

    if status is not None and not 200 <= status < 300:
        return f"错误: 搜索 API 请求失败（HTTP {status}）{_extract_error_detail(text)}"

    return _format_response(data)
