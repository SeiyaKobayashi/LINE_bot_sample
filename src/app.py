# -*- coding: utf-8 -*-
# app.py

import os
import json
from datetime import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    FollowEvent, MessageEvent, PostbackEvent,
    TextMessage, LocationMessage, TextSendMessage, TemplateSendMessage,
    MessageAction, PostbackAction, PostbackTemplateAction, LocationAction,
    ButtonsTemplate, QuickReply, QuickReplyButton,
)
from src import create_app
from src.models import db, User
from src.weather import parse_address, fetch_weather_driver

app = create_app()

# Get chnnel secret and channel access token from environment
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

# Create instances
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# WIP: separate this data as a different file (e.g., JSON)
MSGS_IGNORED = [
    'とても残念に思う', 'どちらかといえば残念に思う', 'どちらでもない', 'どちらかといえば残念に思わない', '全く残念に思わない',
    'サプリの効果が感じられた', '1日分のサプリが小分けになっている', 'デザインが好き', 'サプリ診断が役立った', 'LINE Botが便利', '特になし',
    '価格を下げる', 'サプリの配合を変える', '購入後のサポート体制を整える', 'オンにする', 'オフにする', 'すべてみる', '9時', '12時', '15時',
    '18時', '21時', '0時', '3時', '6時'
]
FB_QUESTIONS_NUM = 3
fb_questions = {
    1: '【質問①】\n\n明日からこの製品が使えなくなるとしたら、どう感じますか?',
    2: '【質問②】\n\nこの製品を使ってみて良かった点を教えてください。',
    3: '【質問③】\n\nこの製品をより良くするためには何が必要だと感じますか?'
}
fb_options = {
    1: [('とても残念に思う', 1), ('どちらかといえば残念に思う', 2), ('どちらでもない', 3), ('どちらかといえば残念に思わない', 4), ('全く残念に思わない', 5)],
    2: [('サプリの効果が感じられた', 1), ('1日分のサプリが小分けになっている', 2), ('デザインが好き', 3), ('サプリ診断が役立った', 4), ('LINE Botが便利', 5), ('特になし', 6)],
    3: [('価格を下げる', 1), ('サプリの配合を変える', 2), ('購入後のサポート体制を整える', 3), ('特になし', 4)]
}


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
            items = [
                QuickReplyButton(
                    action=MessageAction(
                        label=line_bot_api.get_profile(event.source.user_id).display_name + "に設定する",
                        text=line_bot_api.get_profile(event.source.user_id).display_name
                    )
                )
            ]
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(
                        text=greeting + '友達再追加ありがとうございます！'
                    ),
                    TextSendMessage(
                        text='このボットは、あなたのことをなんとお呼びすればいいですか？お名前またはニックネームを教えてください。',
                        quick_reply=QuickReply(items=items)
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
        db.session.add(User(line_id=line_bot_api.get_profile(event.source.user_id).user_id, created_at=datetime.now().timestamp()))
        db.session.commit()

        items = [
            QuickReplyButton(
                action=MessageAction(
                    label=line_bot_api.get_profile(event.source.user_id).display_name + "に設定する",
                    text=line_bot_api.get_profile(event.source.user_id).display_name
                )
            )
        ]
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(
                    text=greeting + '友達追加ありがとうございます！'
                ),
                TextSendMessage(
                    text='このボットは、あなたのことをなんとお呼びすればいいですか？お名前またはニックネームを教えてください。',
                    quick_reply=QuickReply(items=items)
                )
            ]
        )


def sendQuickReply(event, q_num):
    items = [
        QuickReplyButton(
            action=PostbackAction(
                label=option[0],
                text=option[0],
                data='qid='+str(q_num)+'&ans='+str(option[1])
            )
        ) for option in fb_options[q_num]
    ]
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=fb_questions[q_num],
            quick_reply=QuickReply(items=items)
        )
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
                TextSendMessage(text='有効なメールアドレスではないようです。もう一度入力してください。')
            )
        else:
            user.email = event.message.text
            db.session.commit()

            items = [
                QuickReplyButton(action=PostbackAction(label="オンにする", text="オンにする", data='enabled_weather=1')),
                QuickReplyButton(action=PostbackAction(label="オフにする", text="オフにする", data='enabled_weather=0'))
            ]

            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text='メールアドレスを ' + user.email + ' に設定しました。'),
                    TextSendMessage(
                        text='このボットは、日々の天気予報をお知らせすることもできます。天気予報機能をオンにしますか?',
                        quick_reply=QuickReply(items=items)
                    )
                ]
            )
    else:
        if event.message.text == '登録情報':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=user.name+'さんの登録情報は以下の通りです。\n\n' \
                        'LINE ID: '+user.line_id+'\n' \
                        'Email: '+user.email+'\n' \
                        '定期購入: '+('定期購入中' if user.is_subscribing else '設定されていません')+'\n' \
                        'サプリ摂取時刻: '+(user.default_time if user.default_time else '設定されていません')+'\n' \
                        '天気予報: '+('オン' if user.enabled_weather else 'オフ')+'\n' \
                        'Twitter連携: '+('オン' if user.enabled_twitter else 'オフ')+'\n' \
                        '招待人数: '+str(user.num_of_referrals)
                )
            )
        elif event.message.text == '設定変更':
            setting_template = ButtonsTemplate(
                text='変更したい項目をタップしてください',
                actions=[
                    PostbackTemplateAction(
                        label='メールアドレス',
                        data='email'
                    )
                ]
            )
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage(alt_text='設定変更', template=setting_template)
            )
        elif event.message.text == 'フィードバック':
            sendQuickReply(event, 1)
        # WIP: no need of templates
        elif (event.message.text == 'メールアドレスを変更する'):
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
        elif event.message.text == '天気' or event.message.text == '天気予報':
            pref, city = parse_address(user.address)
            with open('src/areas.json') as f:
                city_ids = json.load(f)
                if not city in city_ids[pref]:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='この天気予報はお住まいの地域には対応していないようです...\n今後のアップデートをお待ちください。')
                    )
                else:
                    items = [
                        QuickReplyButton(
                            action=PostbackAction(label=time, text=time, data='display_time='+time)
                        ) for time in ['すべてみる', '9時', '12時', '15時', '18時', '21時', '0時', '3時', '6時']
                    ]
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text='何時頃の天気予報を表示しますか?',
                            quick_reply=QuickReply(items=items)
                        )
                    )
        elif event.message.text in MSGS_IGNORED:
            pass
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='会話機能は現在開発中です...')
            )


@handler.add(MessageEvent, message=LocationMessage)
def message_location(event):
    user = User.query.filter_by(line_id=line_bot_api.get_profile(event.source.user_id).user_id).first()
    user.address = event.message.address
    db.session.commit()

    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text='現在地を' + user.address + 'に設定しました。今後は「天気」または「天気予報」と送ると現在地の天気予報が返ってくるようになります。'),
            TextSendMessage(text='初期設定は以上となります。今後の基本操作・設定は画面下のメニューから行なってください。')
        ]
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


def display_weather_info(event, time, pref, city, forecast):
    month = datetime.fromtimestamp(event.timestamp // 1000).month
    day = datetime.fromtimestamp(event.timestamp // 1000).day
    time_index = {'0時': 0, '3時': 1, '6時': 2, '9時': 3, '12時': 4, '15時': 5, '18時': 6, '21時': 7}

    if time == 'すべてみる':
        template = str(month)+'月'+str(day)+'日の'+pref+city+'の天気予報です。\n\n'
        template += ''.join([forecast[time_index[i]]['time']+':\n天気: '+forecast[time_index[i]]['Weather']+'\n気温: ' \
            +forecast[time_index[i]]['Temperature']+'\n湿度: '+forecast[time_index[i]]['Humidity']+'\n降水量: ' \
            +forecast[time_index[i]]['Precipitation']+'\n風速: '+forecast[time_index[i]]['WindSpeed']+('' if i=='21時' else '\n\n') \
            for i in time_index])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=template)
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=str(month)+'月'+str(day)+'日'+forecast[time_index[time]]['time']+'頃の'+pref+city+'の天気は' \
                    +forecast[time_index[time]]['Weather']+'、気温は'+forecast[time_index[time]]['Temperature'] \
                    +'の予報です。詳細な予報については以下をご確認ください。\n\n湿度: '+forecast[time_index[time]]['Humidity'] \
                    +'\n降水量: '+forecast[time_index[time]]['Precipitation']+'\n風速: '+forecast[time_index[time]]['WindSpeed']
            )
        )


@handler.add(PostbackEvent)
def on_postback(event):
    user = User.query.filter_by(line_id=line_bot_api.get_profile(event.source.user_id).user_id).first()

    if event.postback.data == 'email':
        generateMsgTemplate(event, 'メールアドレス')
    elif 'enabled_weather' in event.postback.data:
        if event.postback.data.split('=')[1] == '1':
            user.enabled_weather = True
            db.session.commit()

            items = [
                QuickReplyButton(action=LocationAction(label="位置情報を送る"))
            ]
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='天気予報機能をオンにしました。正確な天気予報のため、下記ボタンより位置情報を送ってください。',
                    quick_reply=QuickReply(items=items)
                )
            )
        elif event.postback.data.split('=')[1] == '0':
            user.enabled_weather = False
            db.session.commit()

            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text='天気予報機能をオフにしました。メニューからはいつでも設定の変更ができます。'),
                    TextSendMessage(text='初期設定は以上となります。今後の基本操作・設定は画面下のメニューから行なってください。')
                ]
            )
    elif 'display_time' in event.postback.data:
        pref, city = parse_address(user.address)
        forecast = fetch_weather_driver(pref, city)
        display_weather_info(event, event.postback.data.split('=')[1], pref, city, forecast)
    else:
        if '&' in event.postback.data and event.postback.data.split('&')[0] == 'qid=1':
            sendQuickReply(event, 2)
        elif '&' in event.postback.data and event.postback.data.split('&')[0] == 'qid=2':
            sendQuickReply(event, 3)
        elif '&' in event.postback.data and event.postback.data.split('&')[0] == 'qid=3':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='ご回答ありがとうございます！フィードバックは、今後のサービス改善に役立たせて頂きます。')
            )


if __name__ == "__main__":
    app.run()
