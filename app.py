# app.py

import os
from datetime import datetime
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


def setGreeting(hour):
    if 5 <= hour and hour <= 9:
        return 'おはようございます！'
    elif 10 <= hour and hour <= 18:
        return 'こんにちは！'
    else:
        return 'こんばんは！'


@handler.add(FollowEvent)
def message_init(event):

    greeting = setGreeting(datetime.fromtimestamp(event.timestamp/1000).time().hour)

    try:
        User.query.filter_by(line_id=line_bot_api.get_profile(event.source.user_id).user_id).first()
    except:     # If new user
        db.session.add(User(line_id=line_id))
        db.session.commit()

        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(
                    text=greeting + '友達追加ありがとうございます！'
                ),
                TextSendMessage(
                    text='botはあなたのことをなんとお呼びすればよいですか？お名前またはニックネームを教えてください。'
                )
            ]
        )
    else:     # If user account already exists (i.e., past user)
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(
                    text=user.name + 'さん、' + greeting + '\n友達再追加ありがとうございます！'
                ),
                TextSendMessage(
                    text='操作方法を再度ご確認ください。\n1.登録情報の確認 =>「履歴」と入力\n2. 各種設定の変更 =>「設定」と入力\n3. 使い方の確認 =>「使い方」と入力\n'
                )
            ]
        )


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):

    user = User.query.filter_by(line_id=line_bot_api.get_profile(event.source.user_id).user_id).first()
    greeting = setGreeting(datetime.fromtimestamp(event.timestamp/1000).time().hour)

    if not user.name or not user.email or not user.password:     # If initial setup is not done
        if user.name == None:     # Ask name
            user.name = event.message.text
            db.session.commit()
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text=user.name + 'さん、' + greeting),
                    TextSendMessage(text='それでは、アカウントの設定をしていきましょう！よく使用するメールアドレスを入力してください。')
                ]
            )
        elif user.email == None:     # Ask email
            user.email = event.message.text
            db.session.commit()
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text='メールアドレスを ' + user.email + ' に設定しました。'),
                    TextSendMessage(text='続いて、アカウントのパスワードを設定してください。')
                ]
            )
        elif user.password == None:     # Ask to set password
            user.password = event.message.text
            db.session.commit()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='パスワードを設定しました。これで初期設定は完了です！\n\n今後の操作方法は以下をご確認ください。\n1.登録情報の確認 =>「履歴」と入力\n2. 各種設定の変更 =>「設定」と入力\n3. 使い方の確認 =>「使い方」と入力\n'
                )
            )

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
        # WIP starts (should use LIFF)
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
        # WIP ends
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
                MessageAction(label='はい', text='メールアドレスを変更する'),
                MessageAction(label='いいえ', text='変更しない')
            ]
        )
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='メールアドレスを変更しますか？', template=msg_template)
        )
    elif event.postback.data == 'password':
        msg_template = ButtonsTemplate(
            text='パスワードを変更しますか？',
            actions=[
                MessageAction(label='はい', text='パスワードを変更する'),
                MessageAction(label='いいえ', text='変更しない')
            ]
        )
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='パスワードを変更しますか？', template=msg_template)
        )
    elif event.postback.data == 'payment_method':
        msg_template = ButtonsTemplate(
            text='決済手段を変更しますか？',
            actions=[
                MessageAction(label='はい', text='決済手段を変更する'),
                MessageAction(label='いいえ', text='変更しない')
            ]
        )
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='決済手段を変更しますか？', template=msg_template)
        )
    elif event.postback.data == 'address':
        msg_template = ButtonsTemplate(
            text='住所を変更しますか？',
            actions=[
                MessageAction(label='はい', text='住所を変更する'),
                MessageAction(label='いいえ', text='変更しない')
            ]
        )
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='住所を変更しますか？', template=msg_template)
        )


if __name__ == "__main__":
    app.run()
