# -*- coding: utf-8 -*-
# weather.py

import requests, json, re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from googletrans import Translator


AREA_URL = 'http://weather.livedoor.com/forecast/rss/primary_area.xml'
BASE_URL = 'http://weather.livedoor.com/forecast/webservice/json/v1'

translator = Translator()


def fetch_area(url=AREA_URL):
    area_dict = {}
    root = ET.fromstring(requests.get(url).text)
    for category in root[0]:
        if category.tag == '{http://weather.livedoor.com/%5C/ns/rss/2.0}source':
            for pref in category:
                if pref.get('title')[0] == '道' and '北海道' not in area_dict:
                    area_dict['北海道'] = {}
                elif pref.get('title')[0] == '道' and '北海道' in area_dict:
                    pass
                else:
                    area_dict[pref.get('title')] = {}
                for city in pref:
                    if city.get('id'):
                        if pref.get('title')[0] == '道':
                            area_dict['北海道'][city.get('title')] = city.get('id')
                        else:
                            area_dict[pref.get('title')][city.get('title')] = city.get('id')

    return area_dict


def expand_area(area_dict):
    area_dict_new = {}
    for pref in area_dict:
        area_dict_new[pref] = {}
        for area in area_dict[pref]:
            res = requests.get(BASE_URL+'?city='+area_dict[pref][area])
            locations = json.loads(res.content)['pinpointLocations']
            for location in locations:
                area_dict_new[pref][location['name']] = location['link'][-7:]

    return area_dict_new


def save_as_JSON():
    area_dict_new = expand_area(fetch_area())
    print('Saving data to JSON file...')
    with open('src/areas.json', 'w') as f:
        json.dump(area_dict_new, f, indent=4, ensure_ascii=False)
    print('Done.')


def fetch_weather_details(url):
    forecast = []
    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    weather_today = soup.find('div', id='main').find_all('table')[0]
    rows = weather_today.find_all('tr')
    for row in rows:
        if row.find_all('th')[0].text == '風向':
            continue
        elif len(row.find_all('th')) != 1:
            for col in row.find_all('th')[1:]:
                forecast.append({translator.translate(row.find_all('th')[0].text).text: col.text})
        else:
            for i, col in enumerate(row.find_all('td')):
                forecast[i][(translator.translate(row.find('th').text).text).title().replace(' ', '')] = col.text.strip().replace('\n', '')

    return forecast


def parse_address(addr):
    if ',' in addr:     # en
        pref = translator.translate(addr.split(',')[2].split()[0], dest='ja').text
        city = translator.translate(addr.split(',')[1], dest='ja').text
    else:     # ja
        result = re.search('(...??[都道府県])(.+?市.+?区|.+?[市区町村])', addr.split()[1]).group()
        pref = re.search('(...??[都道府県])', addr.split()[1]).group()
        city = result[len(pref):]

    return pref, city


def fetch_weather_driver(pref, city):
    with open('src/areas.json') as f:
        city_ids = json.load(f)
        print('city_ids:', city_ids)
        try:
            return fetch_weather_details('http://weather.livedoor.com/area/forecast/'+city_ids[pref][city])
        except:
            return None
