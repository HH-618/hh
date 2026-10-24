import configparser
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMSettings:
    api_url: str
    api_key: str
    model_name: str


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
