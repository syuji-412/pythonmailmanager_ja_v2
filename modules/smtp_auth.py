#!/usr/bin/python
# -*- coding: utf-8 -*-

### 認証メソッド定義スクリプト ###

# モジュールインポート
import base64
import hashlib
import hmac
import random
import string

from . import logger

# ロガー定義
logger = logger.logger()


# PLAINレスポンス生成関数
def make_plain(username, password):
    logger.info('Start making plain response. Variable is [' + username + ', ' + password + ']')
    pre_response = '{}\x00{}\x00{}'.format(username, username, password)
    logger.info('plain response is "' + str(base64.b64encode(pre_response.encode()).decode()) + '".')
    return base64.b64encode(pre_response.encode()).decode()


# CRAM-MD5レスポンス生成関数
#
# レスポンス生成シーケンス
# 1. チャレンジコードをレスポンスから抜き出す（返ってきたレスポンス「334 hogehoge」をそのまま渡す）
#    ex: PDEyMjUwNDIzODcyNjY5MDYuMTU5ODUzNzI4M0Bva2luYXdhLWFsbGluPg== 
#
# 2. チャレンジコードをbase64でデコード
#    ex: <1225042387266906.1234537283@smtp.example.jp>
#
# 3. パスワードをキーとして2でデコードした文字列をハッシュ化
#    ex: 2e1da7ad7dc73c1d9077d70feccaed1b
#
# 4. <ユーザー名+空白+3でハッシュ化した文字列>をbase64エンコードしてレスポンスを生成
#    ex: dGVzdHNlcnZpY2UwMUB0ZXN0LmNlbnRvczguanAgMmUxZGE3YWQ3ZGM3M2MxZDkwNzdkNzBmZWNjYWVkMWI=
def cram_md5_response(username, password, challenge):
    logger.info('Start making cram-md5 response. Variable is [' + username + '. ' + password + '. ' + challenge + ']')
    challenge_code = challenge.strip().split()[1]
    challenge_decode = base64.b64decode(challenge_code.encode()).decode()
    challenge_hash = hmac.new(password.encode(), challenge_decode.encode('utf-8'), hashlib.md5).hexdigest()
    challenge_response = base64.b64encode(username.encode() + ' '.encode() + challenge_hash.encode()).decode()

    logger.info('cram-md5 response is "' + str(challenge_response) + '".')
    return challenge_response


# DIGEST-MD5レスポンス生成関数
#
# レスポンス生成シーケンス
# 1. チャレンジコードをレスポンスから抜き出す
# 2. 抜き出したチャレンジコードをデコードして各種値を取り出す
# 3. A1文字列を計算
# 4. A2文字列を計算
# 5. レスポンス文字列を計算
# 6. 各種値とレスポンス文字列を埋め込んだ文字列をbase64エンコードしてレスポンスを生成
def digest_md5_response(server, username, password, cnonce, challenge):
    logger.info('Start making digest-md5 response. Variable is [' + server + ', ' + username + ', ' + password + ', ' + cnonce + ', ' + challenge + ']')
    challenge_code = challenge.strip().split()[1]
    challenge_decode = base64.b64decode(challenge_code.encode()).decode()
    logger.debug('decoded challenge code is "' + str(challenge_decode) + '".')
    challenge_decode_list = challenge_decode.split(',')

    pre_dict = []
    for i in challenge_decode_list:
        pre_dict.append(tuple(i.replace('"', '').split('=',1)))
    challenge_param = dict(pre_dict)

    realm = challenge_param['realm']
    qop = challenge_param['qop']
    nonce = challenge_param['nonce']
    cnonce = cnonce
    uri = 'smtp/' + str(server) + '/'
    logger.debug('variable is [realm: ' + realm + ', qop: ' + qop + ', nonce: ' + nonce + ', cnonce: ' + cnonce + ', uri: ' + uri + '].')

    pre_a1 = hashlib.md5(username.encode() + ":".encode() + realm.encode() + ":".encode() + password.encode())

    # A1文字列を計算
    a1 = hashlib.md5(pre_a1.digest() + ":".encode()
                     + nonce.encode() + ":".encode()
                     + cnonce.encode()).hexdigest()
    logger.debug('A1 = "' + str(a1) + '".')

    # A2文字列を計算
    a2 = hashlib.md5(b'AUTHENTICATE:' + uri.encode()).hexdigest()
    logger.debug('A2 = "' + str(a2) + '".')

    # response文字列を計算
    response = hashlib.md5(a1.encode() + ":".encode()
                           + nonce.encode() + ":".encode()
                           + "00000001".encode() + ":".encode()
                           + cnonce.encode() + ":".encode()
                           + qop.encode() + ":".encode()
                           + a2.encode()).hexdigest()

    pre_response = 'username="{user}",realm="{realm}",nonce="{nonce}",nc=00000001,cnonce="{cnonce}",digest-uri="{uri}",response={response},qop={qop}'.format(user=username,realm=realm,nonce=nonce,cnonce=cnonce,uri=uri,response=response,qop=qop)

    logger.info('digest-md5 response is "' + str(base64.b64encode(pre_response.encode()).decode()) + '".')
    return base64.b64encode(pre_response.encode()).decode()


# cnonce生成関数
def make_cnonce():
    return ''.join([random.choice(string.ascii_letters + string.digits) for i in range(16)])
