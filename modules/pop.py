#!/bin/python2.7
# -*- coding: utf-8 -*-


# モジュールインポート
import configparser
import csv
import sys
import re
import telnetlib

from . import color
from . import logger


# ロガー定義
logger = logger.logger()


# コマンド実行時レスポンスチェック関数
# 応答コードに応じて True/False を返す
#
# 応答コード +OK~  : Trueを返す
# 応答コード -ERR~ : Falseを返す
# EOFError例外     : Falseを返す
def check_return(response):
    try:
        if re.match('\+OK.*', response):
            print response.strip()
            return True

        elif re.match('\-ERR.*', response):
            print response.strip()
            return False

    except EOFError:
        print 'サーバーから応答がありません。正常性を確認してください。'
        return False


### メイン処理 ###
def pop(pop_info_list):
    # 設定ファイル読込
    config = configparser.ConfigParser()
    config.read('pymm.conf.ini')

    pop_success = 0
    pop_failed = 0
    success = 0
    failed = 0
    message_count = 0

    logger.info('Start mail pop process indivisually.')
    port = config['pop_default']['server_port']
    logger.debug('common parameter [port: ' + str(port) + '].')

    for pop_info in pop_info_list:
        username = pop_info[0]
        password = pop_info[1]
        server = pop_info[2]

        try:
            tn = telnetlib.Telnet(server, int(port))
        
        except:
            print color.pycolor.RED + 'サーバーに接続できませんでした。サーバーの正常性を確認するか正しいIP/ポートを指定してください。' + color.pycolor.END
            sys.exit()
        
        result = tn.expect([b'(\+OK|\-ERR).*\r\n'])[2].decode()
        if check_return(result):
            print '-> user ' + username
            tn.write(b'user ' + username.encode() + b'\r\n')
        
            result = tn.expect([b'(\+OK|\-ERR).*\r\n'])[2].decode()
        
            if check_return(result):
                print '-> pass ' + password
                tn.write(b'pass ' + password.encode() + b'\r\n')
                result = tn.expect([b'(\+OK|\-ERR).*\r\n'])[2].decode()
                
                if check_return(result):
                    print '-> list'
                    tn.write(b'list\r\n')
        
                    result = tn.expect([b'(\+OK|\-ERR).*\r\n'])[2].decode()
        
                    # LISTした結果からメールの数を取得
                    if check_return(result):
                        message_count = int(re.search('\+OK.*', result).group().split()[1])
        
                    result = tn.read_until(b'.\r\n').decode()
                    print result
        
                    if message_count == 0:
                        pass
                    
                    else:
                        # 全メールを繰り返し取得
                        for i in range(1, message_count+1):
                            print '-> retr ' + str(i)
                            tn.write(b'retr ' + str(i).encode() + b'\r\n')
                            try:
                                result = tn.read_until(b'\r\n.\r\n').decode()
                                print color.pycolor.YELLOW + '========== Message ID: ' + str(i) + ' ==========' + color.pycolor.END
                                print result
                                print ''
                                print ''
                                pop_success += 1
        
                            except:
                                print 'POP Error. skip...'
                                pop_failed += 1
                                continue
        
                        # 全メール削除処理
                        all_delete = raw_input(color.pycolor.RED + '全てのメールを削除しますか？（y/n）: ' + color.pycolor.END)
                        if all_delete == 'y':
                            print 'deleting.....'
                            for i in range(1, message_count+1):
                                tn.write(b'dele ' + str(i).encode() + b'\r\n')
                                result = tn.expect([b'(\+OK|\-ERR).*\r\n'])[2].decode()
                                if check_return(result):
                                    pass
                                else:
                                    print result
        
                            tn.write(b'list\r\n')
                            result = tn.read_until(b'.\r\n').decode()
        
                            if int(re.search('\+OK.*', result).group().split()[1]) == 0:
                                print color.pycolor.GREEN + '全てのメールが削除されました。' + color.pycolor.END
                            else:
                                print color.pycolor.GREEN + 'いくつかメールが残っています。' + color.pycolor.END
        
                        elif all_delete == 'n':
                            print color.pycolor.GREEN + '削除せずに終了します。' + color.pycolor.END
        
                        else:
                            print color.pycolor.GREEN + '"y" または "n" を指定してください。 削除せずに終了します。' + color.pycolor.END
                    
                    print '-> quit'
                    tn.write(b'quit\r\n')
                    result = tn.expect([b'(\+OK|\-ERR).*\r\n'])[2].decode()
        
                    # なぜか削除後のresultには「.\r\n」が先頭に入ってしまう問題に対する対処
                    if '.\r\n' in result:
                        result = result.replace('.\r\n','')
        
                    if check_return(result):
                        tn.close()
                        success += 1
                    else:
                        print result
                        failed += 1
                else:
                    print result
                    failed += 1
            else:
                print result
                failed += 1
        else:
            print result
            failed += 1
    
    logger.info('End mail pop process indivisually.')
    
    print ''
    print ''
    print '========== Mail POP Summary =========='
    print ''
    print ' Receive Status'
    print '     total message: ' + str(message_count)
    print '     pop success: ' + str(pop_success)
    print '     pop failed : ' + str(pop_failed)
    print ''
    print ' Execute Status'
    print color.pycolor.CYAN + '     Success: ' + color.pycolor.END + str(success)
    print color.pycolor.RED + '     Failed: ' + color.pycolor.END + str(failed)
    print ''
    print ' Total Processed Count: ' + str(success + failed)
    print '======================================'
