# -*- coding: utf-8 -*-
# app.py

import os, json, random, string, schedule
from datetime import datetime
from time import sleep
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
from src.models import db, User, Feedback
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
    '18時', '21時', '0時', '3時', '6時', '定期購入について', '注文・お支払いについて', '配送について', 'LINE Botについて', 'サプリメントについて',
    '解約について', '配送サイクルについて', '注文内容を確認したい', '送料について', 'お支払い方法について', '配送状況を確認したい',
    '配送先住所を変更したい', 'LINE Botの使い方が分からない', 'LINE Botが使いにくい', 'いつ飲めばいいのか?', '副作用などはないのか?', '特になし',
    'はい', 'いいえ', 'ユーザー名を変更', '位置情報を変更', 'サプリ摂取時刻を変更', '天気予報設定を変更', 'Twitter連携設定を変更'
]
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
FB_QUESTIONS_NUM = len(fb_questions)
FAQs = {
    1: {
        'category': '定期購入について',
        'questions':
            {
                1: {'Q': '解約について', 'A': '解約をご希望の場合は、以下のリンクより入力をお願い致します(現状リンクなし)。'},
                2: {'Q': '配送サイクルについて', 'A': '私たちは、サプリメントは「毎日」飲み続けてこそ価値があるものだと考えております。そのため、配送サイクルは「毎月」のみとなります。'}
            }
        },
    2: {
        'category': '注文・お支払いについて',
        'questions':
            {
                1: {'Q': '注文内容を確認したい', 'A': '現在の注文内容は、以下のリンクよりご確認ください(現状リンクなし)。'},
                2: {'Q': '送料について', 'A': '配達送料は、毎月のお支払い料金に含まれております。'},
                3: {'Q': 'お支払い方法について', 'A': '毎月のお支払いには、各種クレジットカードがご利用頂けます。お支払い方法は、以下のリンクより変更頂けます(現状リンクなし)。'}
            }
        },
    3: {
        'category': '配送について',
        'questions':
            {
                1: {'Q': '配送状況を確認したい', 'A': '現在の配送状況は、以下のリンクよりご確認ください(現状リンクなし)。'},
                2: {'Q': '配送先住所を変更したい', 'A': '配送先住所の変更は、以下のリンクよりご確認ください(現状リンクなし)。'}
            }
        },
    4: {
        'category': 'LINE Botについて',
        'questions':
            {
                1: {'Q': 'LINE Botの使い方が分からない', 'A': 'このBotでは、各種登録情報の確認・変更に加え、毎日の天気予報やサプリメント・健康管理に関する情報を受け取ることができます。操作方法は、画面最下部のメニューバーよりご確認ください。'},
                2: {'Q': 'LINE Botが使いにくい', 'A': 'ご指摘ありがとうございます。製品・サービスに関するフィードバックは、画面最下部のメニューバーよりご入力ください。'}
            }
        },
    5: {'category': 'サプリメントについて',
        'questions':
            {
                1: {'Q': 'いつ飲めばいいのか?', 'A': '毎日お好きなタイミングでお飲みください。食事後がお勧めです。'},
                2: {'Q': '副作用などはないのか?', 'A': 'サプリメントの配合成分は、医師やサプリメントアドバイザーと共同開発しており、論文による効果・副作用の有無の裏付けもありますので、どうぞご安心してご利用ください。'}
            }
        }
}


def scheduler():
    schedule.every().day.at("06:00").do(push_weather_forecast, 6)
    schedule.every().day.at("12:00").do(push_weather_forecast, 12)
    schedule.every().day.at("18:00").do(push_weather_forecast, 18)
    schedule.every().day.at("00:00").do(push_weather_forecast, 0)

    while True:
        schedule.run_pending()
        sleep(30)


def push_weather_forecast(time):
    users = ensureDBConnection('user', True)
    month = datetime.fromtimestamp(event.timestamp // 1000).month
    day = datetime.fromtimestamp(event.timestamp // 1000).day
    time_index = {6: '6時', 12: '12時', 18: '18時', 0: '0時'}

    for user in users:
        pref, city = parse_address(user.location)
        forecast = fetch_weather_driver(pref, city)
        line_bot_api.push_message(
            user.line_id,
            TextSendMessage(
                text=str(month)+'月'+str(day)+'日'+forecast[time_index[time]]['time']+'頃の'+pref+city+'の天気は' \
                    +forecast[time_index[time]]['Weather']+'、気温は'+forecast[time_index[time]]['Temperature'] \
                    +'の予報です。詳細な予報については以下をご確認ください。\n\n湿度: '+forecast[time_index[time]]['Humidity'] \
                    +'\n降水量: '+forecast[time_index[time]]['Precipitation']+'\n風速: '+forecast[time_index[time]]['WindSpeed']
            )
        )


scheduler()


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


# WIP: there might be better solutions (i.e., https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/)
def ensureDBConnection(table_name, multiple=False):
    duration = 2
    max_num_retries = 5
    for _ in range(max_num_retries):
        try:
            if table_name == 'user':
                print('enter')
                if multiple:
                    return User.query.filter_by(User.enabled_weather==True, User.location!=None)
                else:
                    print('ok')
                    return User.query.filter_by(line_id=line_bot_api.get_profile(event.source.user_id).user_id).first()
            error = None
        except:
            print('error')
            pass

        if error:
            sleep(duration)
            duration *= 2
        else:
            break


def setGreeting(hour):
    if 5 <= hour and hour <= 9:
        return 'おはようございます！'
    elif 10 <= hour and hour <= 18:
        return 'こんにちは！'
    else:
        return 'こんばんは！'


@handler.add(FollowEvent)
def message_init(event):

    user = ensureDBConnection('user')
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
        db.session.add(User(line_id=line_bot_api.get_profile(event.source.user_id).user_id, created_at=datetime.now()))
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


def sendQuickReply_FB(event, q_num):
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

def generateFAQCategories(confirm=False):
    if confirm:
        return [QuickReplyButton(
            action=PostbackAction(
                label='特になし',
                text='特になし',
                data='faq_done=1')
        )] + [
            QuickReplyButton(
                action=PostbackAction(
                    label=FAQs[category_id]['category'],
                    text=FAQs[category_id]['category'],
                    data='category_id='+str(category_id))
            ) for category_id in FAQs
        ]
    else:
        return [
            QuickReplyButton(
                action=PostbackAction(
                    label=FAQs[category_id]['category'],
                    text=FAQs[category_id]['category'],
                    data='category_id='+str(category_id))
            ) for category_id in FAQs
        ]


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):

    user = ensureDBConnection('user')
    greeting = setGreeting(datetime.fromtimestamp(event.timestamp // 1000).time().hour)

    if event.message.text in MSGS_IGNORED:
        pass
    elif not user.name:
        user.name = event.message.text
        db.session.commit()

        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text=user.name + 'さん、はじめまして！'),
                TextSendMessage(text='続いて、頻繁に使用するメールアドレスを教えてください。')
            ]
        )
    # WIP: Check if it matches email registered on ECF
    elif not user.email:
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
    # Use card (or image) for production
    elif not user.init_coupon:
        user.init_coupon = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        user.init_coupon_issued_at = datetime.now()
        db.session.commit()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='初期設定は以上となります。今後の基本操作は、画面下のメニューから行なってください。\n\n' \
                    'またこの度、LINE Botに登録してくださったお礼に、月々のお支払い等でご利用頂ける限定クーポンを発行致しました。\n\n' \
                    +user.name+'さんのクーポンコードは、\n\n'+user.init_coupon+'\n\nです。\n\n' \
                    'このコードを決済画面で入力することで、決済金額が1000円引きとなります。' \
                    'ただし、本クーポンのご利用期限は本日より3ヶ月となっておりますので、予めご注意ください。' \
                    'クーポンコードは、画面下メニューの「登録情報」よりご確認頂けます。'
            )
        )
    else:
        if event.message.text == '登録情報':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=user.name+'さんの登録情報は以下の通りです。\n\n' \
                        'LINE ID: '+user.line_id+'\n' \
                        'Email: '+user.email+'\n' \
                        '初回登録クーポンコード: '+user.init_coupon+'\n' \
                        '定期購入: '+('定期購入中' if user.is_subscribing else '設定されていません')+'\n' \
                        'サプリ摂取時刻: '+(user.default_time if user.default_time else '設定されていません')+'\n' \
                        '天気予報: '+('オン' if user.enabled_weather else 'オフ')+'\n' \
                        'Twitter連携: '+('オン' if user.enabled_twitter else 'オフ')+'\n' \
                        '招待人数: '+str(user.num_of_referrals)
                )
            )
        elif event.message.text == '設定変更':
            items = [
                QuickReplyButton(action=PostbackAction(label='ユーザー名を変更', text='ユーザー名を変更', data='name')),
                QuickReplyButton(action=PostbackAction(label='位置情報を変更', text='位置情報を変更', data='location')),
                QuickReplyButton(action=PostbackAction(label='サプリ摂取時刻を変更', text='サプリ摂取時刻を変更', data='default_time')),
                QuickReplyButton(action=PostbackAction(label='天気予報設定を変更', text='天気予報設定を変更', data='enabled_weather')),
                QuickReplyButton(action=PostbackAction(label='Twitter連携設定を変更', text='Twitter連携設定を変更', data='enabled_twitter'))
            ]
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='変更したい項目を下から選択してください。',
                    quick_reply=QuickReply(items=items)
                )
            )
        elif event.message.text == 'フィードバック':
            if not Feedback.query.filter_by(line_id=line_bot_api.get_profile(event.source.user_id).user_id).first():
                db.session.add(Feedback(line_id=line_bot_api.get_profile(event.source.user_id).user_id))
                db.session.commit()
            sendQuickReply_FB(event, 1)
        elif event.message.text == 'FAQ':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='何かお困りですか?\n下記の該当する項目から選んでください。',
                    quick_reply=QuickReply(items=generateFAQCategories())
                )
            )
        elif event.message.text == '天気' or event.message.text == '天気予報':
            if not user.enabled_weather:
                items = [
                    QuickReplyButton(action=PostbackAction(label="オンにする", text="オンにする", data='enabled_weather=1')),
                    QuickReplyButton(action=PostbackAction(label="オフにする", text="オフにする", data='enabled_weather=0'))
                ]
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text='天気予報機能がオフになっているようです。天気予報機能をオンにしますか?',
                        quick_reply=QuickReply(items=items)
                    )
                )
            elif not user.location:
                items = [
                    QuickReplyButton(action=LocationAction(label="位置情報を送る"))
                ]
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text='位置情報が設定されていないようです。正確な天気予報のため、下記ボタンより位置情報を送ってください。',
                        quick_reply=QuickReply(items=items)
                    )
                )
            else:
                pref, city = parse_address(user.location)
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
        # WIP
        elif event.message.text == 'Twitter':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='Twitter連携機能は現在開発中です...')
            )
        elif '感謝' in event.message.text or 'ありがとう' in event.message.text:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=random.choice(['どういたしまして！', 'こちらこそ製品を使用頂きありがとうございます！', 'いえいえ！'])
                )
            )
        # WIP
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='会話機能は現在開発中です...')
            )


@handler.add(MessageEvent, message=LocationMessage)
def message_location(event):
    user = ensureDBConnection('user')
    user.location = event.message.address
    db.session.commit()

    if not user.init_coupon:
        items = [QuickReplyButton(action=MessageAction(label="了解", text="了解"))]

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='現在地を' + user.location + 'に設定しました。メニュー内の「天気予報」から、いつでも天気の確認ができます。',
                quick_reply=QuickReply(items=items)
            )
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='現在地を' + user.location + 'に設定しました。メニュー内の「天気予報」から、いつでも天気の確認ができます。'
            )
        )


def sendQuickReply_settings(event, keyword):
    items = [
        QuickReplyButton(action=PostbackAction(label="はい", text="はい", data='modify_'+keyword+'=1')),
        QuickReplyButton(action=PostbackAction(label="いいえ", text="いいえ", data='modify_'+keyword+'=0'))
    ]
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=keyword+'を変更しますか？', quick_reply=QuickReply(items=items))
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
    user = ensureDBConnection('user')

    if event.postback.data == 'name':
        sendQuickReply_settings(event, 'LINE Bot内でのユーザー名')
    elif event.postback.data == 'location':
        sendQuickReply_settings(event, '天気予報に使用される位置情報')
    elif event.postback.data == 'default_time':
        sendQuickReply_settings(event, '毎日のサプリの摂取時刻')
    elif event.postback.data == 'enabled_weather':
        items = [
            QuickReplyButton(action=PostbackAction(label="はい", text="はい", data='enabled_weather='+('0' if user.enabled_weather else '1'))),
            QuickReplyButton(action=PostbackAction(label="いいえ", text="いいえ", data='enabled_weather='+('1' if user.enabled_weather else '0')))
        ]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='現在は、天気予報機能が'+('オン' if user.enabled_weather else 'オフ')+'になっています。天気予報機能を'+('オフ' if user.enabled_weather else 'オン')+'にしますか?',
                quick_reply=QuickReply(items=items)
            )
        )
    elif event.postback.data == 'enabled_twitter':
        items = [
            QuickReplyButton(action=PostbackAction(label="はい", text="はい", data='enabled_twitter='+('0' if user.enabled_twitter else '1'))),
            QuickReplyButton(action=PostbackAction(label="いいえ", text="いいえ", data='enabled_twitter='+('1' if user.enabled_twitter else '0')))
        ]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='現在は、Twitter連携機能が'+('オン' if user.enabled_twitter else 'オフ')+'になっています。Twitter連携機能を'+('オフ' if user.enabled_twitter else 'オン')+'にしますか?',
                quick_reply=QuickReply(items=items)
            )
        )
    elif 'modify' in event.postback.data:
        keyword = event.postback.data.split('=')[0].split('_')[1]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='設定機能は現在開発中です...')
        )
    elif 'category_id' in event.postback.data:
        if 'question_id' in event.postback.data:
            category_id = event.postback.data.split('=')[1].split('&')[0]
            question_id = event.postback.data.split('=')[2]
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text=FAQs[int(category_id)]['questions'][int(question_id)]['A']),
                    TextSendMessage(
                        text='その他にお困りのことはありますか?',
                        quick_reply=QuickReply(items=generateFAQCategories(True))
                    )
                ]
            )
        else:
            category_id = event.postback.data.split('=')[1]
            questions = [
                QuickReplyButton(
                    action=PostbackAction(
                        label=FAQs[int(category_id)]['questions'][question_id]['Q'],
                        text=FAQs[int(category_id)]['questions'][question_id]['Q'],
                        data='category_id='+category_id+'&question_id='+str(question_id)
                )) for question_id in FAQs[int(category_id)]['questions']
            ]
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=FAQs[int(category_id)]['category']+'のお問い合わせですね。\n詳細を下記からお選びください。',
                    quick_reply=QuickReply(items=questions)
                )
            )
    elif event.postback.data == 'faq_done=1':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='FAQは随時追加しておりますので、またご不明点などありましたら画面最下部のメニューよりご確認ください。'
            )
        )
    elif 'enabled_weather' in event.postback.data:
        if event.postback.data.split('=')[1] == '1':
            if user.enabled_weather:
                if not user.location:
                    items = [
                        QuickReplyButton(action=LocationAction(label="位置情報を送る"))
                    ]
                    line_bot_api.reply_message(
                        event.reply_token,
                        [
                            TextSendMessage(text='天気予報機能をオンのままに設定しました。'),
                            TextSendMessage(
                                text='位置情報が設定されていないようです。正確な天気予報のため、下記ボタンより位置情報を送ってください。',
                                quick_reply=QuickReply(items=items)
                            )
                        ]
                    )
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='天気予報機能をオンのままに設定しました。メニュー内の「天気予報」から、いつでも天気の確認ができます。')
                    )
            else:
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
            if user.enabled_weather == False:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text='天気予報機能をオフのままに設定しました。メニュー内の「天気予報」から、いつでも設定の変更ができます。'
                    )
                )
            else:
                user.enabled_weather = False
                db.session.commit()

                items = [QuickReplyButton(action=MessageAction(label="了解", text="了解"))]

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text='天気予報機能をオフにしました。メニュー内の「天気予報」から、いつでも設定の変更ができます。',
                        quick_reply=QuickReply(items=items)
                    )
                )
    elif 'display_time' in event.postback.data:
        pref, city = parse_address(user.location)
        forecast = fetch_weather_driver(pref, city)
        display_weather_info(event, event.postback.data.split('=')[1], pref, city, forecast)
    elif 'qid' in event.postback.data:
        FB = Feedback.query.filter_by(line_id=line_bot_api.get_profile(event.source.user_id).user_id).first()
        if event.postback.data.split('&')[0] == 'qid=1':
            FB.Q1 = int(event.postback.data.split('=')[2])
            db.session.commit()
            sendQuickReply_FB(event, 2)
        elif event.postback.data.split('&')[0] == 'qid=2':
            FB.Q2 = int(event.postback.data.split('=')[2])
            db.session.commit()
            sendQuickReply_FB(event, 3)
        elif event.postback.data.split('&')[0] == 'qid=3':
            FB.Q3 = int(event.postback.data.split('=')[2])
            db.session.commit()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='ご回答ありがとうございます！フィードバックは、今後のサービス改善に役立たせて頂きます。')
            )


if __name__ == "__main__":
    app.run()
