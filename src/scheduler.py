# -*- coding: utf-8 -*-
# scheduler.py

from datetime import datetime
from linebot.models import TextSendMessage
from src.app import ensureDBConnection, line_bot_api
from src.weather import parse_address, fetch_weather_driver


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


if __name__ == "__main__":
    push_weather_forecast(int(sys.argv[1]))
