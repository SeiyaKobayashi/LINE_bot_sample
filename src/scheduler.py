# -*- coding: utf-8 -*-
# scheduler.py

from apscheduler.schedulers.blocking import BlockingScheduler
from src.app import app.push_weather_forecast

if __name__ == '__main__':
    with app.app_context():
        scheduler = BlockingScheduler()
        # scheduler.add_job(push_weather_forecast, 'cron', hour='0, 6, 12')
        scheduler.add_job(push_weather_forecast, 'interval', minutes=2)
        scheduler.start()
