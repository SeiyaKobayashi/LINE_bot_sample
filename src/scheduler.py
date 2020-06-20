# -*- coding: utf-8 -*-
# scheduler.py

from time import sleep
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from src.app import push_weather_forecast, push_daily_reminder_fetch_users, push_daily_reminder


if __name__ == '__main__':
    # bl_scheduler = BlockingScheduler()
    # bl_scheduler.add_job(push_weather_forecast, 'cron', hour='0, 6, 12')
    # bl_scheduler.start()
    while True:
        users = push_daily_reminder_fetch_users()
        for user in users:
            print('name:', user.name)
            hour = user.default_time.split(':')[0] if user.default_time.split(':')[0][0] != '0' else user.default_time.split(':')[0][1]
            minute = user.default_time.split(':')[1] if user.default_time.split(':')[1][0] != '0' else user.default_time.split(':')[1][1]
            print('hour:', hour)
            print('minute:', minute)
            bl_scheduler.add_job(push_daily_reminder, 'cron', hour=hour, minute=minute, args=[user])
        sleep(20)

    bl_scheduler = BlockingScheduler()
    bl_scheduler.add_job(push_weather_forecast, 'cron', hour='0, 6, 12')
    bl_scheduler.start()
