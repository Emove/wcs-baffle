import json
import time
from threading import Thread
from typing import Dict

import requests

import logger
from config.rms import get_rms_config


def submit_delay_callback(delay: int, callback_url: str, callback_params: Dict[str, str]):
    th = Thread(target=__delay_callback, args=(ip, delay, callback_url, callback_params), daemon=True)
    th.start()


def __delay_callback(delay: int, callback_url: str, callback_params: Dict[str, str]):
    while True:
        try:
            time.sleep(delay)
            if __request_rms(ip, callback_url, callback_params):
                return
        except Exception:
            logger.exception(f"delay callback error, delay: {delay}, callback_url: {callback_url}, "
                             f"callback_params: {callback_params}")


def __request_rms(url: str, params: Dict[str, str]) -> bool:
    logger.info(f"request RMS, url: {url}, params: {params}")
    conf = get_rms_config()
    resp = requests.post(url=url, data=json.dumps(params), headers={"Content-Type": "application/json"},
                         timeout=conf.request.timeout)
    if resp.ok:
        logger.info(f"request RMS succeed, url: {url}, params: {params}, resp: {resp.text}")
        resp_content = json.loads(resp.text)
        if resp_content.get("code") == 0:
            return True
    logger.error(f"request RMS error, url: {url}, params: {json.dumps(params)}, resp: {resp.text}")
    return False
