#!/usr/bin/python

### logger定義スクリプト ###

# モジュールインポート
import configparser
import logging

# ベース設定定義関数
def logger():
    # ログ設定読み出し
    config = configparser.ConfigParser()
    config.read('pymm.conf.ini')
    if config['logging']['log_level'] == 'DEBUG':
        log_level = logging.DEBUG
    elif config['logging']['log_level'] == 'INFO':
        log_level = logging.INFO
    elif config['logging']['log_level'] == 'WARNING':
        log_level = logging.WARNING
    elif config['logging']['log_level'] == 'ERROR':
        log_level = logging.ERROR
    elif config['logging']['log_level'] == 'CRITICAL':
        log_level = logging.CRITICAL

    logging.basicConfig(filename=config['logging']['config_file'],
                        level = log_level,
                        datefmt='%Y/%m/%d %H:%M:%S',
                        format='%(asctime)s [%(module)s/%(funcName)s][%(levelname)s]: %(message)s')
    logger = logging.getLogger(__name__)

    return logger
