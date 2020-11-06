#!/bin/python2.7
# -*- coding: utf-8 -*-

### pymm実行メインスクリプト ###

import configparser
import sys

from modules import color
from modules import logger
from modules import menu

reload(sys)
sys.setdefaultencoding("utf-8")

# ロガー生成
logger = logger.logger()

# メインプロセス
print ''
print color.pycolor.YELLOW + ' Welcome to Python Mail Manager.' + color.pycolor.END
print ''
menu.main_menu()
