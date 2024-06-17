from typing import Optional

from pydantic import BaseModel

import logger


class LoggerConfig(BaseModel):
    name: str
    level: str = "INFO"
    log_dir: str = "rms-log"


class ServerConfig(BaseModel):
    port: Optional[int] = 10001
    logger: LoggerConfig


__server_config: Optional[ServerConfig] = None


def set_server_config(config: ServerConfig):
    global __server_config
    logger.info(f"Setting server config: {config.dict()}")
    __server_config = config


def get_server_config() -> ServerConfig:
    global __server_config
    if __server_config is None:
        raise ValueError("Server config not set")
    return __server_config
