from typing import Optional

from pydantic import BaseModel

import logger


class RequestConfig(BaseModel):
    timeout: int = 10
    delay: int = 3


class RMSApis(BaseModel):
    dock_ready: str
    dock_finish: str


class RMSConfig(BaseModel):
    request: RequestConfig
    host: str
    port: int
    apis: RMSApis


__rms_config: Optional[RMSConfig] = None


def set_rms_config(config: RMSConfig):
    global __rms_config
    logger.info(f"Setting RMS config: {config.dict()}")
    __rms_config = config


def get_rms_config() -> RMSConfig:
    global __rms_config
    if __rms_config is None:
        raise ValueError("RMS config not set")
    return __rms_config



