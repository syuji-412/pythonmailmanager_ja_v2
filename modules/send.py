#!/usr/bin/python
# -*- coding: utf-8 -*-

# モジュールインポート
import base64
import configparser
import sys
import re
import telnetlib

from . import color
from . import logger
from . import smtp_auth


# ロガー定義
logger = logger.logger()


# コマンド実行時レスポンスチェック関数
# 応答コード応じて True/False を返す
#
# 応答コード2XX or 3XX : Trueを返す
# 応答コード4XX or 5XX : Falseを返す
# EOFError例外         : Falseを返す
def check_return(response):
    try:
        if re.match('2\d\d.*\r\n', response) or re.match('3\d\d.*\r\n', response):
            print response.strip()
            return True

        elif re.match('4\d\d.*\r\n', response):
            print '一時エラー。 エラーメッセージ： ' + response.strip()
            print 'しばらく待ってから再度接続してください。'
            return False

        elif re.match('5\d\d.*\r\n', response):
            print 'システムエラー。 エラーメッセージ： ' + response.strip()
            print 'エラー内容を確認してください。'
            return False

    except EOFError:
        logger.error('Server response is empty. Please check the server health.')
        print 'サーバーから応答がありません。正常性を確認してください。'
        return False


### メイン処理 ###
def send_mail(sending_info_list, subject, body):
    # 設定ファイル読込
    config = configparser.ConfigParser()
    config.read('pymm.conf.ini')

    success = 0
    failed = 0
    auth_noauth = 0
    auth_plain = 0
    auth_login = 0
    auth_cram_md5 = 0
    auth_digest_md5 = 0

    logger.info('Start mail sending process indivisually.')

    port = config['send_default']['server_port']
    subject = subject
    body = body
    auth_method = config['send_default']['auth_method']
    logger.debug('common parameter [port: ' + str(port) + ', Auth method: ' + auth_method + ', Subject: ' + subject + ', Body: ' + body + '].')

    for sending_info in sending_info_list:
        username = sending_info[0]
        password = sending_info[1]
        rcpt_to = sending_info[2]
        server = sending_info[3]

        for server_address in sending_info[3].split(','):
            logger.debug('send paramater [From address(username): ' + username + ', password: ' + password + ', To address: ' + rcpt_to + ', Server: ' + str(server) + '].')
            print color.pycolor.YELLOW + '=*=*=*=*=*=*=*=*=*=*= ' + username + '_' + server_address + ' =*=*=*=*=*=*=*=*=*=*=' + color.pycolor.END

            try:
                tn = telnetlib.Telnet(server_address, port)
            
            except:
                logger.error('Failed connect to server. Please check the server health or specify correct IP/Port.')
                print color.pycolor.RED + 'サーバーに接続できませんでした。正常性を確認するか正しいIP/ポートを指定してください。' + color.pycolor.END
                sys.exit()
            
            result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
            if check_return(result):
                if auth_method == 'NOAUTH':
                    print '-> helo ' + username.split('@')[1]
                    tn.write(b'helo ' + username.split('@')[1].encode() + b'\r\n')
            
                    result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
            
                else:
                    print '-> ehlo ' + username.split('@')[1]
                    tn.write(b'ehlo ' + username.split('@')[1].encode() + b'\r\n')
            
                    result = tn.read_until(b'250 DSN\r\n').decode()
            
            if check_return(result):
                # PLAIN認証
                if auth_method == 'PLAIN':
                    logger.debug('auth method is "' + auth_method + '".')
                    auth_plain += 1
                    print '-> auth PLAIN'
                    tn.write(b'auth PLAIN\r\n')
                    result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
                    if check_return(result):
                        print '-> ' + smtp_auth.make_plain(username, password)
                        tn.write(smtp_auth.make_plain(username, password).encode() + b'\r\n')
                        result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
                    else:
                        print result
                        failed += 1
            
                # LOGIN認証
                elif auth_method == 'LOGIN':
                    logger.debug('auth method is "' + auth_method + '".')
                    auth_login += 1
                    print '-> auth LOGIN'
                    tn.write(b'auth LOGIN\r\n')
                    result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
                    if check_return(result):
                        print '-> ' + base64.b64encode(username.encode()).decode()
                        tn.write(base64.b64encode(username.encode()) + b'\r\n')
                        result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
                        if check_return(result):
                            print '-> ' + base64.b64encode(password.encode()).decode()
                            tn.write(base64.b64encode(password.encode()) + b'\r\n')
                            result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
                        else:
                            print result
                            failed += 1
            
                # CRAM-MD5認証
                elif auth_method == 'CRAM-MD5':
                    logger.debug('auth method is "' + auth_method + '".')
                    auth_cram_md5 += 1
                    print '-> auth CRAM-MD5'
                    tn.write(b'auth CRAM-MD5\r\n')
                    result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
                    if check_return(result):
                        print '-> ' + smtp_auth.cram_md5_response(username, password, result.strip())
                        tn.write(smtp_auth.cram_md5_response(username, password, result.strip()).encode() + b'\r\n')
                        result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
                    else:
                        print result
                        failed += 1
            
                # DIGEST-MD5認証
                elif auth_method == 'DIGEST-MD5':
                    logger.debug('auth method is "' + auth_method + '".')
                    auth_digest_md5 += 1
                    print '-> auth DIGEST-MD5'
                    tn.write(b'auth DIGEST-MD5\r\n')
                    result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
                    if check_return(result):
                        print '-> ' + smtp_auth.digest_md5_response(server_address, username, password, smtp_auth.make_cnonce(), result.strip())
                        tn.write(smtp_auth.digest_md5_response(server_address, username, password, smtp_auth.make_cnonce(), result.strip()).encode() + b'\r\n')
                        result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
                        if check_return(result):
                            print '-> '
                            tn.write(b'\r\n')
                            result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
                    else:
                        print result
                        failed += 1
            
                # 認証なし
                elif auth_method == 'NOAUTH':
                    logger.debug('auth method is "' + auth_method + '".')
                    auth_noauth += 1
                    pass
            
                # 認証メソッドエラー
                else:
                    result = '535 5.7.8 Error: authentication failed: Invalid authentication mechanism'
            else:
                logger.error('Internal Server Error. Server is not working.')
                print 'システムエラー： サーバーが応答していません。'
                failed += 1
            
            # メール送信処理
            if check_return(result):
                logger.info(auth_method + ' authentication success.')
                print '-> mail from: ' + username
                tn.write(b'mail from: ' + username.encode() + b'\r\n')
            
                result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
                if check_return(result):
                    print '-> rcpt to: ' + rcpt_to
                    tn.write(b'rcpt to: ' + rcpt_to.encode() + b'\r\n')
            
                    result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
                    if check_return(result):
                        print '-> DATA'
                        tn.write(b'DATA\r\n')
            
                        result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
                        if check_return(result):
                            print '-> From: ' + username
                            tn.write(b'From: ' + username.encode() + b'\r\n')
                            print '-> To: ' + rcpt_to
                            tn.write(b'To: ' + rcpt_to.encode() + b'\r\n')
                            print '-> Subject: ' + subject
                            tn.write(b'Subject: ' + subject.encode() + b'\r\n')
                            print '-> '
                            tn.write(b'\r\n')
                            print '-> ' + body
                            tn.write(body.encode() + b'\r\n')
                            print '-> .'
                            tn.write(b'.\r\n')
            
                            result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
                            if check_return(result):
                                print '-> quit'
                                tn.write(b'quit\r\n')
            
                                result = tn.expect([b'[2345]\d\d.*\r\n'])[2].decode()
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
            else:
                print result
                failed += 1
    logger.info('End mail sending process indivisually.')

    print ''
    print ''
    print '========== Mail Sending Summary =========='
    print ''
    print ' Authentication Method'
    print '     NOAUTH    : ' + str(auth_noauth)
    print '     PLAIN     : ' + str(auth_plain)
    print '     LOGIN     : ' + str(auth_login)
    print '     CRAM-MD5  : ' + str(auth_cram_md5)
    print '     DIGEST-MD5: ' + str(auth_digest_md5)
    print ''
    print ' Execute Status'
    print color.pycolor.CYAN + '     Success: ' + color.pycolor.END + str(success)
    print color.pycolor.RED + '     Failed : ' + color.pycolor.END + str(failed)
    print ''
    print ' Total Processed Count: ' + str(success + failed)
    print '=========================================='
