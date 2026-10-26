import configparser
import os
from dataclasses import dataclass
from typing import Optional


DEFAULT_SEARCH_API_URL = "https://qianfan.baidubce.com/v2/ai_search/chat/completions"
DEFAULT_SEARCH_MODEL = "ernie-4.5-turbo-32k"


@dataclass
class LLMSettings:
    api_url: str
    api_key: str
    model_name: str


@dataclass
class SearchSettings:
    api_key: str = ""
    api_url: str = DEFAULT_SEARCH_API_URL
    model_name: str = DEFAULT_SEARCH_MODEL
    top_k: int = 10
    timeout: float = 30.0


@dataclass
class Settings:
    llm: LLMSettings


def load_settings(config_path: Optional[str] = None) -> Settings:
    if config_path is None:
        candidates = [
            os.path.join(os.getcwd(), "config.ini"),
            os.path.join(os.getcwd(), "juju", "config.ini"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "Practice02", "config.ini"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Practice02", "config.ini"),
            r"E:\LLM\Agent\Practice02\config.ini",
            r"E:\LLM\Agent\juju\config.ini",
            r"E:\LLM\Agent\config.ini",
        ]
        for c in candidates:
            c = os.path.normpath(c)
            if os.path.exists(c):
                config_path = c
                break
        if config_path is None:
            config_path = os.path.join(os.getcwd(), "config.ini")
    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")

    if "llm" not in config:
        for c in [
            r"E:\LLM\Agent\Practice02\config.ini",
            r"E:\LLM\Agent\juju\config.ini",
            r"E:\LLM\Agent\config.ini",
            os.path.join(os.getcwd(), "config.ini"),
        ]:
            c = os.path.normpath(c)
            if os.path.exists(c):
                config.read(c, encoding="utf-8")
                if "llm" in config:
                    break

    llm = LLMSettings(
        api_url=config["llm"]["api_url"],
        api_key=config["llm"]["api_key"],
        model_name=config["llm"]["model_name"],
    )
    return Settings(llm=llm)


def _search_config_candidates(config_path: Optional[str] = None):
    """返回搜索配置可能所在的 config.ini 路径，按优先级排列"""
    if config_path is not None:
        return [os.path.normpath(config_path)]

    cwd = os.getcwd()
    package_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    agent_root = os.path.dirname(package_root)
    candidates = [
        os.path.join(cwd, "config.ini"),
        os.path.join(cwd, "juju", "config.ini"),
        os.path.join(package_root, "config.ini"),
        os.path.join(agent_root, "juju", "config.ini"),
        os.path.join(agent_root, "config.ini"),
        os.path.join(agent_root, "Practice02", "config.ini"),
    ]

    paths = []
    seen = set()
    for path in candidates:
        path = os.path.normpath(path)
        if path in seen:
            continue
        seen.add(path)
        paths.append(path)
    return paths


def _read_config_file(path: str) -> Optional[configparser.ConfigParser]:
    config = configparser.ConfigParser(interpolation=None)
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            config.read_file(f)
    except (OSError, UnicodeDecodeError, configparser.Error):
        return None
    return config


def _parse_int(value, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def _parse_float(value, default: float, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def load_search_settings(config_path: Optional[str] = None) -> SearchSettings:
    """从 config.ini 的 [search] 小节读取百度千帆搜索配置

    缺少 [search] 小节或 baidu_api_key 时返回空 api_key，由调用方给出提示。
    """
    for path in _search_config_candidates(config_path):
        if not os.path.isfile(path):
            continue
        config = _read_config_file(path)
        if config is None or not config.has_section("search"):
            continue

        section = config["search"]
        api_key = section.get("baidu_api_key", "").strip()
        if not api_key:
            continue

        api_url = section.get("api_url", "").strip() or DEFAULT_SEARCH_API_URL
        model_name = (
            section.get("model", "").strip()
            or section.get("model_name", "").strip()
            or DEFAULT_SEARCH_MODEL
        )
        return SearchSettings(
            api_key=api_key,
            api_url=api_url,
            model_name=model_name,
            top_k=_parse_int(section.get("top_k"), 10, 1, 50),
            timeout=_parse_float(section.get("timeout"), 30.0, 1.0, 120.0),
        )

    return SearchSettings()
