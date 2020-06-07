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
        TextSendMessage(
            [
                text='友達追加ありがとうございます！\niHack 公式LINE botです！',
                text='LINE botはあなたのことをなんとお呼びすればよいですか？\nお名前またはニックネームを教えてください。'
            ]
        )
    )


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    print(event)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='お名前を「'+event.message.text+'」と設定しました。')
    )


if __name__ == "__main__":
    app.run()
