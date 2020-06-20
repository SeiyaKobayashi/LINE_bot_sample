# -*- coding: utf-8 -*-
# scheduler.py

from apscheduler.schedulers.blocking import BlockingScheduler
from src.app import push_weather_forecast, push_daily_reminder_fetch_users, push_daily_reminder

if __name__ == '__main__':
    scheduler = BlockingScheduler()
    users = push_daily_reminder_fetch_users()
    for user in users:
        hour = user.default_time.split(':')[0] if user.default_time.split(':')[0][0] != '0' else user.default_time.split(':')[0][1]
        minute = user.default_time.split(':')[1] if user.default_time.split(':')[1][0] != '0' else user.default_time.split(':')[1][1]
        scheduler.add_job(push_daily_reminder, 'cron', hour=hour, minute=minute, args=[user])
    scheduler.add_job(push_weather_forecast, 'cron', hour='0, 6, 12')
    scheduler.start()
