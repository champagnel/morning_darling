from datetime import date, datetime, timedelta
import math
from wechatpy import WeChatClient, WeChatClientException
from wechatpy.client.api import WeChatMessage
import requests
import os
import random

nowtime = datetime.utcnow() + timedelta(hours=8)  # 东八区时间
today = datetime.strptime(str(nowtime.date()), "%Y-%m-%d") #今天的日期

start_date = os.getenv('START_DATE')
city = os.getenv('CITY')
birthday_1 = os.getenv('BIRTHDAY_1')
birthday_2 = os.getenv('BIRTHDAY_2')

app_id = os.getenv('APP_ID')
app_secret = os.getenv('APP_SECRET')

user_ids = os.getenv('USER_ID', '').split("\n")
template_id = os.getenv('TEMPLATE_ID')

if app_id is None or app_secret is None:
  print('请设置 APP_ID 和 APP_SECRET')
  exit(422)

if not user_ids:
  print('请设置 USER_ID，若存在多个 ID 用回车分开')
  exit(422)

if template_id is None:
  print('请设置 TEMPLATE_ID')
  exit(422)

# weather 直接返回对象，在使用的地方用字段进行调用。
def get_weather_1():
  if city is None:
    print('请设置城市')
    return None
  url = "https://restapi.amap.com/v3/weather/weatherInfo?key=eb3e408763bfbbc686f7ec51296e0e3a&city=511500&extensions=base&output=JSON"
  while True:
    try:
      res = requests.get(url).json()
      if res is None:
        return None
      weather = res['lives'][0]
      return weather
    except (requests.exceptions.RequestException, ValueError):
      continue

def get_weather_2():
  if city is None:
    print('请设置城市')
    return None
  url = "https://restapi.amap.com/v3/weather/weatherInfo?key=eb3e408763bfbbc686f7ec51296e0e3a&city=330100&extensions=base&output=JSON"
  while True:
    try:
      res = requests.get(url).json()
      if res is None:
        return None
      weather = res['lives'][0]
      return weather
    except (requests.exceptions.RequestException, ValueError):
      continue

# 获取当前日期为星期几
def get_week_day():
  week_list = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
  week_day = week_list[datetime.date(today).weekday()]
  return week_day

# 纪念日正数
def get_memorial_days_count():
  if start_date is None:
    print('没有设置 START_DATE')
    return 0
  delta = today - datetime.strptime(start_date, "%Y-%m-%d")
  return delta.days

# 生日倒计时
def get_birthday_left():
  if birthday_1 is None:
    print('没有设置 BIRTHDAY')
    return 0
  next = datetime.strptime(str(today.year) + "-" + birthday_1, "%Y-%m-%d")
  if next < nowtime:
    next = next.replace(year=next.year + 1)
  return (next - today).days

def get_birthday_right():
  if birthday_2 is None:
    print('没有设置 BIRTHDAY')
    return 0
  next = datetime.strptime(str(today.year) + "-" + birthday_2, "%Y-%m-%d")
  if next < nowtime:
    next = next.replace(year=next.year + 1)
  return (next - today).days

# 彩虹屁 接口不稳定，所以失败的话会重新调用，直到成功
def get_words():
  words = requests.get("https://api.shadiao.pro/chp")
  if words.status_code != 200:
    return get_words()
  return words.json()['data']['text']

def format_temperature(temperature):
  return math.floor(temperature)

# 随机颜色
def get_random_color():
  return "#%06x" % random.randint(0, 0xFFFFFF)

try:
  client = WeChatClient(app_id, app_secret)
except WeChatClientException as e:
  print('微信获取 token 失败，请检查 APP_ID 和 APP_SECRET，或当日调用量是否已达到微信限制。')
  exit(502)

wm = WeChatMessage(client)
weather_1 = get_weather_1()
weather_2 = get_weather_2()
if weather_1 is None:
  print('获取天气失败')
  exit(422)
if weather_2 is None:
  print('获取天气失败')
  exit(422)
data = {
  "city": {
    "value": city,
    "color": get_random_color()
  },
  "date": {
    "value": today.strftime('%Y年%m月%d日'),
    "color": get_random_color()
  },
  "week_day": {
    "value": get_week_day(),
    "color": get_random_color()
  },
  "weather_1": {
    "value": weather_1['weather'],
    "color": get_random_color()
  },
  "weather_2": {
    "value": weather_2['weather'],
    "color": get_random_color()
  },
  # "humidity": {
  #   "value": weather['humidity'],
  #   "color": get_random_color()
  # },
  # "wind": {
  #   "value": weather['wind'],
  #   "color": get_random_color()
  # },
  # "air_data": {
  #   "value": weather['airData'],
  #   "color": get_random_color()
  # },
  # "air_quality": {
  #   "value": weather['airQuality'],
  #   "color": get_random_color()
  # },
  "temperature_1": {
    "value": weather_1['temperature'],
    "color": get_random_color()
  },
  "temperature_2": {
    "value": weather_2['temperature'],
    "color": get_random_color()
  },
  # "highest": {
  #   "value": math.floor(weather['high']),
  #   "color": get_random_color()
  # },
  # "lowest": {
  #   "value": math.floor(weather['low']),
  #   "color": get_random_color()
  # },
  "love_days": {
    "value": get_memorial_days_count(),
    "color": get_random_color()
  },
  "birthday_left": {
    "value": get_birthday_left(),
    "color": get_random_color()
  },
  "birthday_right": {
    "value": get_birthday_right(),
    "color": get_random_color()
  },
  "words": {
    "value": get_words(),
    "color": get_random_color()
  },
}

if __name__ == '__main__':
  count = 0
  try:
    for user_id in user_ids:
      res = wm.send_template(user_id, template_id, data)
      count+=1
  except WeChatClientException as e:
    print('微信端返回错误：%s。错误代码：%d' % (e.errmsg, e.errcode))
    exit(502)

  print("发送了" + str(count) + "条消息")
