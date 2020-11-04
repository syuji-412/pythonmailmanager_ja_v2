#!/usr/bin/python
# -*- coding: utf-8 -*-

# モジュールインポート
import csv
import pprint
import sys
import re
import telnetlib

from . import color
from . import logger

# ロガー定義
logger = logger.logger()

# グローバル変数定義
pop_success = 0
pop_failed = 0
success = 0
failed = 0
message_count = 0
total_message_count = 0


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
        logger.error('Server response is empty. Please check the server health.')
        print 'サーバーから応答がありません。正常性を確認してください。'
        return False


### メイン処理 ###
def pop_mail(tsv_file):
    global pop_success
    global pop_failed
    global success
    global failed
    global message_count
    global total_message_count

    logger.info('Start mail pop process from TSV file.')
    with open(tsv_file, encoding='utf-8') as f:
        for cols in csv.reader(f, delimiter='\t'):
        
            # ローカル変数定義
            server = cols[0]
            port = cols[1]
            username = cols[2]
            password = cols[3]
    
            logger.info('Variable is [server: ' + server + ', port: ' + str(port) + ', username: ' + username + ', password: '  + password + '].')
            print ''
            print color.pycolor.YELLOW + '=*=*=*=*=*=*=*=*=*=*= ' + username + ' =*=*=*=*=*=*=*=*=*=*=' + color.pycolor.END
            try:
                tn = telnetlib.Telnet(server, port)
            
            except:
                logger.error('Failed connect to server. Please check the server health or specify correct IP/Port.')
                print color.pycolor.RED + 'サーバーに接続できませんでした。正常性を確認するか正しいIP/ポートを指定してください。' + color.pycolor.END
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
                            total_message_count = message_count + total_message_count
    
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
                                    print 'POP エラー。 スキップします...'
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
    logger.info('End mail pop process from TSV file.')
    
    
    print ''
    print ''
    print '========== Mail POP Summary =========='
    print ''
    print ' Receive Status'
    print '     total message: ' + str(total_message_count)
    print '     pop success: ' + str(pop_success)
    print '     pop failed : ' + str(pop_failed)
    print ''
    print ' Execute Status'
    print color.pycolor.CYAN + '     Success: ' + color.pycolor.END + str(success)
    print color.pycolor.RED + '     Failed: ' + color.pycolor.END + str(failed)
    print ''
    print ' Total Processed Count: ' + str(success + failed)
    print '======================================'
