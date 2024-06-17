import os

import yaml

import logger
from config.rms import RMSConfig, set_rms_config
from config.server import ServerConfig, set_server_config, get_server_config
from controller import serve


def __load_config():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with open('config/service.yaml', 'r') as yaml_file:
        conf_data = yaml.safe_load(yaml_file)
        logger.info(f"Loaded config: {conf_data}")
        server_conf = ServerConfig(**conf_data.get('server', {}))
        rms_conf = RMSConfig(**conf_data.get('rms', {}))
        set_server_config(server_conf)
        set_rms_config(rms_conf)


if __name__ == '__main__':
    __load_config()
    server_conf = get_server_config()
    logger_conf = server_conf.logger
    logger = logger.Logger(name=logger_conf.name, log_level=logger_conf.level, log_dir=logger_conf.log_dir)
    logger.set_global_logger(logger)
    serve(server_conf.port)

