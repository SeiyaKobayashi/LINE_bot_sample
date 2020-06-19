# -*- coding: utf-8 -*-
# config.py

import os


class Base():
    ENV='development'
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{user}:{password}@{host}/{db_name}?charset=utf8'.format(**{
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'db_name': os.getenv('DB_NAME')
    })
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY='SomeRandomValue'


class Development(Base):
    DEBUG = True


class Testing(Base):
    DEBUG = True
    TESTING = True


class Production(Base):
    ENV='production'
    SECRET_KEY=os.getenv('SECRET_KEY')
