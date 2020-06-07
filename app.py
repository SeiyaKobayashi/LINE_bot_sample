# app.py

import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    FollowEvent, MessageEvent, PostbackEvent,
    TextMessage, TextSendMessage, TemplateSendMessage,
    ButtonsTemplate, MessageAction, PostbackTemplateAction
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
                TextSendMessage(text='あなたのことをなんとお呼びすればよいですか？お名前またはニックネームを教えてください。')
            ]
        )


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    user = User.query.filter_by(line_id=line_bot_api.get_profile(event.source.user_id).user_id).first()

    if not user.name or not user.email or not user.password:     # If initial setup is not done
        if user.name == None:     # Ask name
            user.name = event.message.text
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text=event.message.text+'さん、こんばんは！'),
                    TextSendMessage(text='それでは、アカウントの作成をしていきましょう。よく使用するメールアドレスを入力してください。')
                ]
            )
        elif user.email == None:     # Ask email
            user.email = event.message.text
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text='メールアドレスを '+event.message.text+' に設定しました。'),
                    TextSendMessage(text='続いて、アカウントのパスワードを設定してください。')
                ]
            )
        elif user.password == None:     # Ask to set password
            user.password = event.message.text
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='パスワードを設定しました。\nこれで初期設定は完了です！\n\n\
                    今後の操作方法は以下をご確認ください。\n各種設定:「設定」と入力\n登録情報の参照:「履歴」と入力'
                )
            )
        db.session.commit()

    else:     # If initial setup is done
        if '設定' in event.message.text:
            msg_template = ButtonsTemplate(
                text='各種設定',
                actions=[
                    PostbackTemplateAction(
                        label='メールアドレス',
                        data='email'
                    ),
                    PostbackTemplateAction(
                        label='パスワード',
                        data='password'
                    ),
                    PostbackTemplateAction(
                        label='決済手段',
                        data='payment_method'
                    ),
                    PostbackTemplateAction(
                        label='住所',
                        data='address'
                    )
                ]
            )
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage(alt_text='settings template', template=msg_template)
            )
        elif '履歴' in event.message.text:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='名前: '+user.name+'\nEmail: '+user.email+'\nパスワード: '+user.password
                )
            )
        elif event.message.text == 'メールアドレスを変更する':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='名前: '+user.name+'\nEmail: '+user.email+'\nパスワード: '+user.password
                )
            )
        elif event.message.text == 'パスワードを変更する':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='名前: '+user.name+'\nEmail: '+user.email+'\nパスワード: '+user.password
                )
            )
        elif event.message.text == '決済手段を変更する':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='名前: '+user.name+'\nEmail: '+user.email+'\nパスワード: '+user.password
                )
            )
        elif event.message.text == '住所を変更する':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='名前: '+user.name+'\nEmail: '+user.email+'\nパスワード: '+user.password
                )
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=event.message.text)
            )


@handler.add(PostbackEvent)
def on_postback(event):
    if event.postback.data == 'email':
        msg_template = ButtonsTemplate(
            text='メールアドレスを変更しますか？',
            actions=[
                MessageAction(label='change_email', text='アドレスを変更する'),
                MessageAction(text='変更しない')
            ]
        )
    elif event.postback.data == 'password':
        msg_template = ButtonsTemplate(
            text='パスワードを変更しますか？',
            actions=[
                MessageAction(label='change_password', text='パスワードを変更する'),
                MessageAction(text='変更しない')
            ]
        )
    elif event.postback.data == 'payment_method':
        msg_template = ButtonsTemplate(
            text='決済手段を変更しますか？',
            actions=[
                MessageAction(label='change_payment_method', text='決済手段を変更する'),
                MessageAction(text='変更しない')
            ]
        )
    elif event.postback.data == 'address':
        msg_template = ButtonsTemplate(
            text='住所を変更しますか？',
            actions=[
                MessageAction(label='change_address', text='住所を変更する'),
                MessageAction(text='変更しない')
            ]
        )
    line_bot_api.reply_message(
        event.reply_token,
        TemplateSendMessage(alt_text='setting template', template=msg_template)
    )

if __name__ == "__main__":
    app.run()
