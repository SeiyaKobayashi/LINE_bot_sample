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
    if User.query.filter_by(line_id=line_id).first():     # If user account already exists (i.e., past user)
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text='友達再追加ありがとうございます！'),
            ]
        )
    else:     # If new user
        db.session.add(User(line_id=line_id))
        db.session.commit()

        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text='友達追加ありがとうございます！'),
                TextSendMessage(text='あなたのことをなんとお呼びすればよいですか？\nお名前またはニックネームを教えてください。')
            ]
        )


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    print('event:', event)
    user = User.query.filter_by(line_id=line_bot_api.get_profile(event.source.user_id).user_id).first()
    if init_step <= 3:     # If initial setup is done
        if user.init_step == 0:     # Ask name
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text=event.message.text+'さん、こんばんは！'),
                    TextSendMessage(text='それでは、アカウントの作成をしていきましょう。\nよく使用するメールアドレスを入力してください。')
                ]
            )
        elif user.init_step == 1:     # Ask email
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text='メールアドレスを '+event.message.text+' に設定しました。'),
                    TextSendMessage(text='続いて、アカウントのパスワードを設定してください。')
                ]
            )
        elif user.init_step == 2:     # Ask to set password
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='これで初期設定は完了です！\n\n今後の操作方法は以下をご確認ください。\n各種設定: 「設定」と入力'
                )
            )
        user.init_step += 1
        db.session.commit()
    else:     # If initial setup is not done
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='こんばんは。'
            )
        )

if __name__ == "__main__":
    app.run()
