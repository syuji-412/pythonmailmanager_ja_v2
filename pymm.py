#!/usr/bin/python
# -*- coding: utf-8 -*-

### pymm実行メインスクリプト ###

import configparser

from modules import color
from modules import logger
from modules import menu


# ロガー生成
logger = logger.logger()

# メインプロセス
print ''
print color.pycolor.YELLOW + ' Welcome to Python Mail Manager.' + color.pycolor.END
print ''
menu.main_menu()
