# app.py

import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    FollowEvent, MessageEvent, TextMessage, TextSendMessage,
    TemplateSendMessage, ButtonsTemplate
)
from __init__ import create_app
from models import db, User

app = create_app()

# Get chnnel secret and channel access token from environment
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

# Create instances
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header from request
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(FollowEvent)
def message_init(event):
    line_id = line_bot_api.get_profile(event.source.user_id).user_id
    db.session.add(User(line_id=line_id))
    db.session.commit()

    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text='友達追加ありがとうございます！\niHack 公式LINE botです！'),
            TextSendMessage(text='LINE botはあなたのことをなんとお呼びすればよいですか？\nお名前またはニックネームを教えてください。')
        ]
    )


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    user = User.query.filter_by(line_id=line_bot_api.get_profile(event.source.user_id).user_id).first()
    # name
    if user.init_step == 0:
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text='ありがとうございます。\nお名前を「'+event.message.text+'」と設定しました。'),
                TextSendMessage(text='続いて、アカウントの作成をしていきましょう。\nメールアドレスを入力してください。')
            ]
        )
    # email
    elif user.init_step == 1:
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text='メールアドレスを「'+event.message.text+'」に設定しました。'),
                TextSendMessage(text='続いて、アカウントのパスワードを設定してください。')
            ]
        )
    # password
    elif user.init_step == 2:
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text='パスワードを'+event.message.text+'」に設定しました。'),
                TextSendMessage(
                    text=
                        'これで初期設定は完了です！\n\n
                        このLINE botでは以下の設定や確認ができます。\n
                        各種設定を行いたい => 「設定」と入力\n
                        フィードバック => 「FB」と入力'
                )
            ]
        )


if __name__ == "__main__":
    app.run()
