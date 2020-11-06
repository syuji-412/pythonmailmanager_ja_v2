#!/bin/python2.7
# -*- coding: utf-8 -*-

### 各種メニュー定義スクリプト ###

# モジュールインポート
import configparser
import os
import sys

from . import color
from . import logger
from . import pop
from . import pop_tsv
from . import send
from . import send_tsv


# ロガー生成
logger = logger.logger()

# メインメニュー関数
def main_menu():
    # 設定ファイル読込
    config = configparser.ConfigParser()
    config.read('pymm.conf.ini')

    # メインメニュー表示
    print ''
    print ' +-------------------------+'
    print ' |      メインメニュー     |'
    print ' +-------------------------+'
    print '   1. メール送信'
    print '   2. メール受信'
    print '   3. 終了'
    print ''
    menu = raw_input(color.pycolor.CYAN + ' メニュー番号を選択: ' + color.pycolor.END)

    if menu == '1':
        send_menu()
    elif menu == '2':
        pop_menu()
    elif menu == '3':
        print color.pycolor.BLUE + ' Exit pymm. Bye...' + color.pycolor.END
        sys.exit()
    else:
        print color.pycolor.RED + ' エラー： 選択された番号が正しくありません。1,2,3のいずれかを指定してください。' + color.pycolor.END
        print ''
        main_menu()


# 送信メニュー関数
def send_menu():
    # 設定ファイル読込
    config = configparser.ConfigParser()
    config.read('pymm.conf.ini')

    print ' ================================= '
    print ' 対象ドメイン一覧.'
    for i in config['send_domains']['domain_list'].split(','):
        print '  - ' + i
    print ''
    print ' +----------------------+'
    print ' |     送信メニュー     |'
    print ' +----------------------+'
    print '   1. TSVファイルを読み込んで送信'
    print '   2. 個別に送信'
    print '   3. 送信メニューを終了（メインメニューに戻る）'
    print '   9. pymmを終了'
    print ''
    menu = raw_input(color.pycolor.CYAN + ' メニュー番号を選択: ' + color.pycolor.END)

    if menu == '1':
        print ''
        send_from_tsv()
    elif menu == '2':
        print ''
        send_indivisually()
    elif menu == '3':
        print color.pycolor.BLUE + ' Exit send menu. Bye...' + color.pycolor.END
        print ''
        main_menu()
    elif menu == '9':
        print color.pycolor.BLUE + ' Exit pymm. Bye...' + color.pycolor.END
        print ''
        sys.exit()
    else:
        print color.pycolor.RED + ' エラー： 選択された番号が正しくありません。1,2,3,9のいずれかを指定してください。' + color.pycolor.END
        print ''
        send_menu()
    

# TSV送信関数
def send_from_tsv():
    # 設定ファイル読込
    config = configparser.ConfigParser()
    config.read('pymm.conf.ini')

    tsv_file = ''
    while os.path.isfile(tsv_file) == False:
        tsv_file = raw_input(color.pycolor.CYAN + ' TSVファイルを指定（指定しない場合は "send.tsv" または "q" でTSVから送信を中止）: ' + color.pycolor.END)

        if tsv_file == '':
            tsv_file = config['tsv']['tsv_base_path'] + 'send.tsv'
        elif tsv_file == 'q':
            print color.pycolor.BLUE + ' Exit send from TSV. Bye...' + color.pycolor.END
            print ''
            send_menu()
        else:
            tsv_file = config['tsv']['tsv_base_path'] + tsv_file

        if os.path.isfile(tsv_file) == False:
            print color.pycolor.RED + ' エラー： 指定されたTSVファイルが見つかりません。' + color.pycolor.END
    print ''
    logger.debug('TSV file is ' + str(tsv_file))
    send_tsv.send_mail(tsv_file)
    send_menu()
    

# 個別送信関数
def send_indivisually():
    # 設定ファイル読込
    config = configparser.ConfigParser()
    config.read('pymm.conf.ini')

    print ' Supported domains.'
    for i in config['send_domains']['domain_list'].split(','):
        print '  - ' + i
    print ''
    print ''
    print color.pycolor.CYAN + ' メールを送信するドメインを指定（指定しない場合はサポートされている全てのドメイン）.' + color.pycolor.END
    specified_domains = raw_input(color.pycolor.CYAN + ' カンマ区切りで複数のドメインを指定可能: ' + color.pycolor.END)

    if specified_domains == '':
        specified_domains = config['send_domains']['domain_list']
    logger.debug('specified_domains is ' + str(specified_domains))
    
    # 1つでもサポートされていないドメインが入っていたら再入力
    for specified_domain in specified_domains.split(','):
        if specified_domain not in config['send_domains']['domain_list'].split(','):
            print color.pycolor.RED + ' エラー： "' + specified_domain + '" はサポートされていません。' + color.pycolor.END
            send_indivisually()

    # send_mail関数呼び出しに渡す引数の生成
    send_list = []
    for domain in specified_domains.split(','):
        print color.pycolor.GREEN + ' ['+domain+']'+ color.pycolor.END
        mail_from = raw_input(' 送信元アドレス（デフォルトは "' + config['send_default_account'][domain].split(',')[0].split(':')[0] + '"）: ')

        if mail_from == '':
            mail_from = config['send_default_account'][domain].split(',')[0].split(':')[0]
            password = config['send_default_account'][domain].split(',')[0].split(':')[1]
        else:
            password = raw_input(' パスワード: ')

        rcpt_to = raw_input(' 送信先アドレス（デフォルトは "' + config['send_default_account'][domain].split(',')[1] + '"）: ')

        if rcpt_to == '':
            rcpt_to = config['send_default_account'][domain].split(',')[1]
        send_list.append([mail_from,password,rcpt_to,config['send_domain_ips'][mail_from.split('@')[1]]])
    logger.debug('send_list is ' + str(send_list))

    subject = raw_input(' 件名: ')
    body = raw_input(' 本文: ')

    send.send_mail(send_list, subject, body)
    send_menu()


# 受信メニュー関数
def pop_menu():
    # 設定ファイル読込
    config = configparser.ConfigParser()
    config.read('pymm.conf.ini')
    
    print ' ================================= '
    print ' 対象ドメイン一覧'
    for i in config['pop_domains']['domain_list'].split(','):
        print '  - ' + i
    print ''
    print ' +---------------------+'
    print ' |     受信メニュー    |'
    print ' +---------------------+'
    print '   1. TSVを読み込んで受信'
    print '   2. 個別に読み込んで受信'
    print '   3. 受信メニューを終了（メインメニューに戻る）'
    print '   9. pymmを終了'
    print ''
    menu = raw_input(color.pycolor.CYAN + ' メニュー番号を選択: ' + color.pycolor.END)

    if menu == '1':
        print ''
        pop_from_tsv()
    elif menu == '2':
        print ''
        pop_indivisually()
    elif menu == '3':
        print color.pycolor.BLUE + ' Exit send menu. Bye...' + color.pycolor.END
        print ''
        main_menu()
    elif menu == '9':
        print color.pycolor.BLUE + ' Exit pymm. Bye...' + color.pycolor.END
        print ''
        sys.exit()
    else:
        print color.pycolor.RED + ' エラー： 選択された番号が正しくありません。1,2,3,9のいずれかを指定してください。' + color.pycolor.END
        print ''
        send_menu()


# TSV受信関数
def pop_from_tsv(): 
    # 設定ファイル読込
    config = configparser.ConfigParser()
    config.read('pymm.conf.ini')

    tsv_file = ''
    while os.path.isfile(tsv_file) == False:
        tsv_file = raw_input(color.pycolor.CYAN + ' TSVファイルを指定（指定しない場合は "pop.tsv" または "q" TSVから受信を中止）: ' + color.pycolor.END)

        if tsv_file == '': 
            tsv_file = config['tsv']['tsv_base_path'] + 'pop.tsv'
        elif tsv_file == 'q':
            print color.pycolor.BLUE + ' Exit pop from TSV. Bye...' + color.pycolor.END
            print ''
            pop_menu()
        else:
            tsv_file = config['tsv']['tsv_base_path'] + tsv_file

        if os.path.isfile(tsv_file) == False:
            print color.pycolor.RED + ' エラー： 指定されたTSVファイルが見つかりません。' + color.pycolor.END

    print ''
    logger.debug('TSV file is ' + str(tsv_file))
    pop_tsv.pop_mail(tsv_file)
    pop_menu()


# 個別受信関数
def pop_indivisually():
    # 設定ファイル読込
    config = configparser.ConfigParser()
    config.read('pymm.conf.ini')

    print ' Supported domains.'
    for i in config['pop_domains']['domain_list'].split(','):
        print '  - ' + i
    print ''
    print ''
    print color.pycolor.CYAN + ' メールを受信するドメインを指定（指定しない場合はサポートされている全てのドメイン）.' + color.pycolor.END
    specified_domains = raw_input(color.pycolor.CYAN + ' カンマ区切りで複数のドメインを指定可能: ' + color.pycolor.END)

    if specified_domains == '':
        specified_domains = config['pop_domains']['domain_list']
    logger.debug('specified_domains is ' + str(specified_domains))

    # 1つでもサポートされていないドメインが入っていたら再入力
    for specified_domain in specified_domains.split(','):
        if specified_domain not in config['pop_domains']['domain_list'].split(','):
            print color.pycolor.RED + ' エラー： "' + specified_domain + '" はサポートされていません。' + color.pycolor.END
            pop_indivisually()

    # pop関数に渡す引数の生成
    pop_list = []
    for domain in specified_domains.split(','):
        print color.pycolor.GREEN + ' ['+domain+']'+ color.pycolor.END
        username = raw_input(' ユーザー名(デフォルトは "' + config['pop_default_account'][domain].split(':')[0] + '"): ')

        if username == '':
            username = config['pop_default_account'][domain].split(':')[0]
            password = config['pop_default_account'][domain].split(':')[1]
        else:
            password = raw_input(' パスワード: ')
        pop_list.append([username,password,config['pop_domain_ips'][username.split('@')[1]]])

    print ''
    logger.debug('pop_list is ' + str(pop_list))
    pop.pop(pop_list)
    pop_menu()
