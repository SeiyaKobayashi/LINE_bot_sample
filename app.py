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

    user = User.query.filter_by(line_id=line_bot_api.get_profile(event.source.user_id).user_id).first()
    greeting = setGreeting(datetime.fromtimestamp(event.timestamp // 1000).time().hour)

    if user:     # If user account already exists (i.e., past user)
        if not user.name:
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(
                        text=greeting + '友達再追加ありがとうございます！'
                    ),
                    TextSendMessage(
                        text='このボットは、あなたのことをなんとお呼びすればいいですか？お名前またはニックネームを教えてください。',
                        quickReply={
                            'items': [
                                {
                                    "type": "action",
                                    "action": {
                                      "type": "message",
                                      "label": line_bot_api.get_profile(event.source.user_id).display_name + "に設定する",
                                      "text": line_bot_api.get_profile(event.source.user_id).display_name
                                    }
                                }
                            ]
                        }
                    )
                ]
            )
        elif not user.email:
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(
                        text=user.name + 'さん、' + greeting + '\n友達再追加ありがとうございます！'
                    ),
                    TextSendMessage(
                        text='まだメールアドレスが登録されていないようです。頻繁に使用するメールアドレスを入力してください。'
                    )
                ]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(
                        text=user.name + 'さん、' + greeting + '\n友達再追加ありがとうございます！'
                    ),
                    TextSendMessage(text='基本操作は画面下のメニューから行なってください。')
                ]
            )
    else:     # If new user
        db.session.add(User(line_id=line_bot_api.get_profile(event.source.user_id).user_id))
        db.session.commit()

        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(
                    text=greeting + '友達追加ありがとうございます！'
                ),
                TextSendMessage(
                    text='このボットは、あなたのことをなんとお呼びすればいいですか？お名前またはニックネームを教えてください。',
                    quickReply={
                        'items': [
                            {
                                "type": "action",
                                "action": {
                                  "type": "message",
                                  "label": line_bot_api.get_profile(event.source.user_id).display_name + "に設定する",
                                  "text": line_bot_api.get_profile(event.source.user_id).display_name
                                }
                            }
                        ]
                    }
                )
            ]
        )


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):

    user = User.query.filter_by(line_id=line_bot_api.get_profile(event.source.user_id).user_id).first()
    greeting = setGreeting(datetime.fromtimestamp(event.timestamp // 1000).time().hour)

    if not user.name:
        user.name = event.message.text
        db.session.commit()

        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text=user.name + 'さん、はじめまして！'),
                TextSendMessage(text='続いて、頻繁に使用するメールアドレスを教えてください。')
            ]
        )
    elif not user.email:
        # WIP: Check if it matches email registered on EC Force
        if '@' not in event.message.text or len(event.message.text) < 4:
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text='有効なメールアドレスではないようです。もう一度入力してください。'),
                ]
            )
        else:
            user.email = event.message.text
            db.session.commit()

            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text='メールアドレスを ' + user.email + ' に設定しました。'),
                    TextSendMessage(text='初期設定は以上となります。今後の基本操作は画面下のメニューから行なってください。')
                ]
            )
    else:
        if event.message.text == '設定変更':
            setting_template = ButtonsTemplate(
                text='変更したい項目をタップしてください',
                actions=[
                    PostbackTemplateAction(
                        label='メールアドレス',
                        data='email'
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
                TemplateSendMessage(alt_text='設定変更', template=setting_template)
            )
        elif event.message.text == '登録情報':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=user.name+'さんの登録情報は以下の通りです。\n\nLINE ID: '+user.line_id+'\nEmail: '+user.email+'\n決済手段: '+(user.payment if user.payment else '設定されていません')+'\n住所: '+(user.address if user.address else '設定されていません')
                )
            )
        elif event.message.text == 'フィードバック':
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text='製品・サービスに関するフィードバックの入力をお願い致します。'),
                    TextSendMessage(
                        text='【質問①】\n\n明日からこの製品が使えなくなるとしたら、どう感じますか?',
                        quickReply={
                            'items': [
                                {
                                    "type": "action",
                                    "action": {
                                      "type": "postback",
                                      "label": "とても残念に思う",
                                      "text": "とても残念に思う",
                                      "data": "qid=1&ans=1"
                                    }
                                },
                                {
                                    "type": "action",
                                    "action": {
                                      "type": "postback",
                                      "label": "どちらかといえば残念に思う",
                                      "text": "どちらかといえば残念に思う",
                                      "data": "qid=1&ans=2"
                                    }
                                },
                                {
                                    "type": "action",
                                    "action": {
                                      "type": "postback",
                                      "label": "どちらでもない",
                                      "text": "どちらでもない",
                                      "data": "qid=1&ans=3"
                                    }
                                },
                                {
                                    "type": "action",
                                    "action": {
                                      "type": "postback",
                                      "label": "どちらかといえば残念に思わない",
                                      "text": "どちらかといえば残念に思わない",
                                      "data": "qid=1&ans=4"
                                    }
                                },
                                {
                                    "type": "action",
                                    "action": {
                                      "type": "postback",
                                      "label": "全く残念に思わない",
                                      "text": "全く残念に思わない",
                                      "data": "qid=1&ans=5"
                                    }
                                }
                            ]
                        }
                    )
                ]
            )
        # WIP: no need of templates
        elif (event.message.text == 'メールアドレスを変更する') or (event.message.text == '決済手段を変更する') or (event.message.text == '住所を変更する'):
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(
                        text='以下のリンクより、各種設定を行なってください。'
                    ),
                    TextSendMessage(
                        text='https://liff.line.me/1654318751-43AoOjrg'
                    )
                ]
            )
        elif event.message.text == '変更しない':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='変更を取りやめました。')
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='会話機能は現在開発中です...')
            )


def generateMsgTemplate(event, keyword):
    msg_template = ButtonsTemplate(
        text=keyword + 'を変更しますか？',
        actions=[
            MessageAction(label='はい', text=keyword + 'を変更する'),
            MessageAction(label='いいえ', text='変更しない')
        ]
    )
    line_bot_api.reply_message(
        event.reply_token,
        TemplateSendMessage(alt_text=keyword + 'を変更しますか？', template=msg_template)
    )


@handler.add(PostbackEvent)
def on_postback(event):
    if event.postback.data == 'email':
        generateMsgTemplate(event, 'メールアドレス')
    elif event.postback.data == 'payment_method':
        generateMsgTemplate(event, '決済手段')
    elif event.postback.data == 'address':
        generateMsgTemplate(event, '住所')
    else:
        if '&' in event.postback.data and event.postback.data.split('&')[0] == 'qid=1':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=event.postback.data.split('&')[1])
            )


if __name__ == "__main__":
    app.run()
