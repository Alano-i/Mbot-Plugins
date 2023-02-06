#!/usr/bin/env python3
from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from typing import Dict, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup, SoupStrainer
from PIL import Image, ImageDraw, ImageFont
import time
import json
import random
import re
import os
import shutil
import requests
import logging
import yaml
from zhdate import ZhDate
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import datetime
server = mbot_api
_LOGGER = logging.getLogger(__name__)
plugins_name = '「每天60秒读懂世界」'
plugins_path = '/data/plugins/daily_news'

@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    global user_id,wecom_proxy_url,message_to_uid,qywx_channel_extra,corpid_extra,corpsecret_extra,agentid_extra,touser_extra,city,key
    message_to_uid = config.get('uid')
    qywx_channel_extra = config.get('qywx_channel_extra')
    corpid_extra = config.get('corpid_extra')
    corpsecret_extra = config.get('corpsecret_extra')
    agentid_extra = config.get('agentid_extra')
    touser_extra = config.get('touser_extra')
    city = config.get('city')
    key = config.get('key')
    wecom_proxy_url = config.get('wecom_proxy_url')
    if message_to_uid:
        user_id = message_to_uid[0]
    else:
         _LOGGER.error(f'{plugins_name}获取推送用户失败，可能是设置了没保存成功或者还未设置')
         user_id = ''

@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    global user_id,wecom_proxy_url,message_to_uid,qywx_channel_extra,corpid_extra,corpsecret_extra,agentid_extra,touser_extra,city,key
    _LOGGER.info(f'{plugins_name}配置发生变更，加载新设置！')
    message_to_uid = config.get('uid')
    qywx_channel_extra = config.get('qywx_channel_extra')
    corpid_extra = config.get('corpid_extra')
    corpsecret_extra = config.get('corpsecret_extra')
    agentid_extra = config.get('agentid_extra')
    touser_extra = config.get('touser_extra')
    city = config.get('city')
    key = config.get('key')
    wecom_proxy_url = config.get('wecom_proxy_url')
    if message_to_uid:
        user_id = message_to_uid[0]
    else:
         _LOGGER.error(f'{plugins_name}获取推送用户失败，可能是设置了没保存成功或者还未设置')
         user_id = ''

@plugin.task('daily_news', '每天60秒读懂世界', cron_expression='0 9 * * *')
def task():
    # time.sleep(random.randint(1, 600))
    _LOGGER.info(f'{plugins_name}定时任务启动，开始获取每日新闻和天气')
    main()
    _LOGGER.info(f'{plugins_name}每日新闻和天气获取完成并已推送消息')

def get_daily_news(img_url):
    url = "https://www.zhihu.com/api/v4/columns/c_1261258401923026944/items"
    headers = {
        "Content-Type": "text/html;charset=utf-8",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Headers": "x-requested-with, content-type"
    }
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    res = session.request("GET", url, headers=headers, timeout=30)

    # res = requests.get(url, headers=headers, timeout=20)
    if res.status_code == 200:
        data = json.loads(res.text)["data"]
        news_url = data[0]["url"]
        news_content = data[0]["content"]
        soup = BeautifulSoup(news_content, 'html.parser')
        p_tags = soup.find_all('p')[2:]
        news_digest = '\n\n'.join([p.text for p in p_tags])
        news_digest = news_digest.replace('在这里，每天60秒读懂世界！', '')
        news_digest = news_digest.strip()
        # _LOGGER.error(news_digest)
        if (len(news_digest)>1000):
            news_digest = news_digest[0:1000]
        # _LOGGER.error(news_digest)
        
        news_content = re.sub(r"<figcaption>.*?</figcaption>", "", news_content, flags=re.DOTALL)
        news_content = re.sub(r"<a.*?</a>", "", news_content, flags=re.DOTALL)
        news_content = news_content.replace('<figure', '<div style="border-radius: 12px; overflow: hidden; margin-top: -22px;"><figure')
        news_content = news_content.replace('<img', '<img style="border-radius: 12px; transform: translateY(22px);"')
        news_content = news_content.replace('</figure>', '</figure></div>')
        news_content = news_content.replace('<p', '<p style="line-height: 175%; font-size:15px; margin: 10px 0px 10px 0px"')
        news_content = news_content.replace('在这里，每天60秒读懂世界！', '')
        news_content = news_content.replace('<p style="line-height: 175%; font-size:15px; margin: 10px 0px 10px 0px"></p>', '')
        # news_content = re.sub(r'<p style="line-height: 175%; font-size:15px; margin: 10px 0px 10px 0px" data-pid="(.*?)"></p>', '', news_content, flags=re.DOTALL)
        news_content = re.sub(r'<p(.*?)></p>', '', news_content, flags=re.DOTALL)
        news_content = news_content.strip()
        # _LOGGER.error(news_content)
        # news_content = f'<div style="border-radius: 12px; overflow: hidden;"><img src="{img_url}" alt="封面"></div>{news_content}'
    else:
        news_content = '热点新闻'
        news_digest = '热点新闻'
        _LOGGER.error('热点新闻获取失败') 
    return news_digest, news_content, news_url

# 请求天气数据
def get_weather():
    # city = "北京"
    city_url = "https://geoapi.qweather.com/v2/city/lookup?location=" + city + "&key=" + key
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    response_city = session.request("GET", city_url, timeout=30)
    # response_city = requests.get(city_url, timeout=20)
    # _LOGGER.error(f'response_city:{response_city}')
    city_data = response_city.json()
    # _LOGGER.error(f'city_data:{city_data}')
    if city_data['code'] == '200':
        city_data = city_data["location"][0]
        city_name = city_data["name"]
        city_id = city_data["id"]
        weather_url = "https://devapi.qweather.com/v7/weather/3d?location=" + city_id + "&key=" + key
        response = session.request("GET", weather_url, timeout=30)
        # response = requests.get(weather_url, timeout=20)
        weather_data = response.json()
        if weather_data['code'] == '200':
            daily_weather_data = weather_data["daily"][0]
            daily_weather_iconDay = daily_weather_data["iconDay"]
            daily_weather_desc = daily_weather_data["textDay"]
            daily_weather_tempMin = daily_weather_data["tempMin"]
            daily_weather_tempMax = daily_weather_data["tempMax"]
            cond = f'{daily_weather_desc}  {daily_weather_tempMin}°~{daily_weather_tempMax}°'
        else:
            cond = '风雨难测°'
            daily_weather_iconDay = '100'
            _LOGGER.error(f'{plugins_name}获取天气信息失败')
    else:
        city_name = '你在天涯海角'
        cond = '风雨难测°'
        daily_weather_iconDay = '100'
        _LOGGER.error(f'{plugins_name}获取城市名失败,请确定 ➊「城市名称」是否设置正确，示例：北京。➋「和风天气」的 key 设置正确')
        _LOGGER.error(f'{plugins_name}和风天气的 key 在 https://dev.qweather.com 申请，创建项目后进入控制台新建项目然后添加 key')
 
    return city_name, cond, daily_weather_iconDay

# 获取当天日期
def get_date():
    today = time.strftime("%Y-%m", time.localtime())
    today_day = time.strftime("%d", time.localtime())
    today_month = time.strftime("%m", time.localtime())
    today_year = time.strftime("%Y", time.localtime())
    return today,today_day,today_month,today_year

# 获取当天星期
def get_weekday():
    week_day_dict = {
        0: '一',
        1: '二',
        2: '三',
        3: '四',
        4: '五',
        5: '六',
        6: '日',
    }
    date = datetime.now()
    day = date.weekday()
    weekday = week_day_dict[day]
    return weekday

# 获取当天农历
def get_lunar_date(today_day,today_month,today_year):
    solar_date = datetime(int(today_year), int(today_month), int(today_day)) # 新建一个阳历日期
    solar_to_lunar_date = ZhDate.from_datetime(solar_date)  # 阳历日期转换农历日期
    # 输出中文农历日期
    lunar_date = solar_to_lunar_date.chinese()
    # 二零二二年三月初一 壬寅年 (虎年)提取三月初一
    lunar_date = re.search(r'年(.*?) ', lunar_date)
    if lunar_date:
        lunar_date = lunar_date.group(1)
    else:
        lunar_date = ''
    return lunar_date

# 获取心灵鸡汤
def get_quote():
    quote_url = 'https://v1.hitokoto.cn'
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    quote = session.request("GET", quote_url, timeout=30)
    # quote = requests.get(quote_url, timeout=20)
    response = quote.json()
    quote_content = response['hitokoto']
    line_length = 22
    lines = []
    for i in range(0, len(quote_content), line_length):
        lines.append(quote_content[i:i + line_length])
    if len(lines) > 2:
        lines[1] = lines[1][:-1] + "..."
    quote_content = '\n'.join(lines[:2])
    return quote_content

# 随机生成背景颜色
def get_random_color():
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)
    return color

# 处理天气数据
def process_weather_data(daily_weather_iconDay):
    # 定义颜色
    today_day_color = (252, 215, 102)
    line_color = (255, 255, 255, 50)
    weekday_color = (255, 255, 255)
    today_color = (255, 255, 255)
    lunar_date_color = (255, 255, 255)
    quote_content_color = (255, 255, 255, 150)
    icon_color = (255, 255, 255)
    city_color = (255, 255, 255)
    weather_desc_color = (255, 255, 255)
    daily_weather_iconDay = int(daily_weather_iconDay)
    if daily_weather_iconDay == 100: 
        bg_name = 'sunny'
        unicode_value = hex(0xf1cc + int(daily_weather_iconDay) - 100)
        unicode_text = chr(int(unicode_value, 16))
    elif daily_weather_iconDay in range(101, 105): 
        bg_name = 'cloud'
        unicode_value = hex(0xf1cc + int(daily_weather_iconDay) - 100)
        unicode_text = chr(int(unicode_value, 16))
    elif daily_weather_iconDay in range(300, 319): 
        bg_name = 'rain'
        unicode_value = hex(0xf1d5 + int(daily_weather_iconDay) - 300)
        unicode_text = chr(int(unicode_value, 16))
    elif daily_weather_iconDay == 399:
        bg_name = 'rain'
        unicode_value = hex(0xf1ea)
        unicode_text = chr(int(unicode_value, 16))
    elif daily_weather_iconDay in range(400, 411): 
        bg_name = 'snow'
        unicode_value = hex(0xf1eb + int(daily_weather_iconDay) - 400)
        unicode_text = chr(int(unicode_value, 16))
    elif daily_weather_iconDay == 499: 
        bg_name = 'snow'
        unicode_value = hex(0xf1f8)
        unicode_text = chr(int(unicode_value, 16))
    elif daily_weather_iconDay in range(500, 502): 
        bg_name = 'fog'
        unicode_value = hex(0xf1f9 + int(daily_weather_iconDay) - 500)
        unicode_text = chr(int(unicode_value, 16))
        today_day_color = (169, 67, 56)
        line_color = (72, 63, 61, 50)
        weekday_color = (72, 63, 61)
        today_color = (72, 63, 61)
        lunar_date_color = (72, 63, 61)
        quote_content_color = (72, 63, 61, 150)
        icon_color = (72, 63, 61)
        city_color = (72, 63, 61)
        weather_desc_color = (72, 63, 61)
    elif daily_weather_iconDay in range(509, 511): 
        bg_name = 'fog'
        unicode_value = hex(0xf200 + int(daily_weather_iconDay) - 509)
        unicode_text = chr(int(unicode_value, 16))
        today_day_color = (169, 67, 56)
        line_color = (72, 63, 61, 50)
        weekday_color = (72, 63, 61)
        today_color = (72, 63, 61)
        lunar_date_color = (72, 63, 61)
        quote_content_color = (72, 63, 61, 150)
        icon_color = (72, 63, 61)
        city_color = (72, 63, 61)
        weather_desc_color = (72, 63, 61)
    elif daily_weather_iconDay in range(514, 516): 
        bg_name = 'fog'
        unicode_value = hex(0xf205 + int(daily_weather_iconDay) - 514)
        unicode_text = chr(int(unicode_value, 16))
        today_day_color = (169, 67, 56)
        line_color = (72, 63, 61, 50)
        weekday_color = (72, 63, 61)
        today_color = (72, 63, 61)
        lunar_date_color = (72, 63, 61)
        quote_content_color = (72, 63, 61, 150)
        icon_color = (72, 63, 61)
        city_color = (72, 63, 61)
        weather_desc_color = (72, 63, 61)
    elif daily_weather_iconDay == 502:
        bg_name = 'haze'
        unicode_value = hex(0xf1fb)
        unicode_text = chr(int(unicode_value, 16))
        today_day_color = (169, 67, 56)
        line_color = (72, 63, 61, 50)
        weekday_color = (72, 63, 61)
        today_color = (72, 63, 61)
        lunar_date_color = (72, 63, 61)
        quote_content_color = (72, 63, 61, 150)
        icon_color = (72, 63, 61)
        city_color = (72, 63, 61)
        weather_desc_color = (72, 63, 61)
    elif daily_weather_iconDay in range(511, 514):
        bg_name = 'haze'
        unicode_value = hex(0xf202 + int(daily_weather_iconDay) - 511)
        unicode_text = chr(int(unicode_value, 16))
        today_day_color = (169, 67, 56)
        line_color = (72, 63, 61, 50)
        weekday_color = (72, 63, 61)
        today_color = (72, 63, 61)
        lunar_date_color = (72, 63, 61)
        quote_content_color = (72, 63, 61, 150)
        icon_color = (72, 63, 61)
        city_color = (72, 63, 61)
        weather_desc_color = (72, 63, 61)
    elif daily_weather_iconDay in range(503, 505):
        bg_name = 'dust'
        unicode_value = hex(0xf1fc + int(daily_weather_iconDay) - 503)
        unicode_text = chr(int(unicode_value, 16))
    elif daily_weather_iconDay in range(507, 509):
        bg_name = 'dust'
        unicode_value = hex(0xf1fe + int(daily_weather_iconDay) - 507)
        unicode_text = chr(int(unicode_value, 16))
    else:
        bg_name = 'sunny'
        unicode_text = '\uf1ca'
    return bg_name,unicode_text,today_day_color,line_color,weekday_color,today_color,lunar_date_color,quote_content_color,icon_color,city_color,weather_desc_color

# 生成图片
def generate_image(push_wx, access_token, agentid, touser, wecom_api_url):
    # 画布大小
    width = 1500
    height = 640
    weekday = get_weekday()
    # 获取天气数据
    city_name, cond, daily_weather_iconDay = get_weather()
    today,today_day,today_month,today_year = get_date()
    lunar_date = get_lunar_date(today_day,today_month,today_year)
    quote_content = get_quote()
    bg_name,unicode_text,today_day_color,line_color,weekday_color,today_color,lunar_date_color,quote_content_color,icon_color,city_color,weather_desc_color = process_weather_data(daily_weather_iconDay)
    
    # 加载图片
    # image_path = f"/Users/alano/Downloads/py测试/icon/{daily_weather_iconDay}.svg"
    bg = Image.open(f"{plugins_path}/bg/{bg_name}.png")

    # 创建画布
    image = Image.new("RGBA", (width, height), (0, 0, 255, 0))
    square = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    # suqredraw = ImageDraw.Draw(square)
    
    # 绘制天气背景，覆盖整个画布
    square.paste(bg, (0, 0), mask=bg)

    # 加载字体
    icon_font = ImageFont.truetype(f"{plugins_path}/font/qweather-icons.ttf", 85)
    num_font_Bold = ImageFont.truetype(f"{plugins_path}/font/ALIBABA_Bold.otf", 345)
    num_font_Regular = ImageFont.truetype(f"{plugins_path}/font/ALIBABA_Regular.otf", 62)
    week_font_Regular = ImageFont.truetype(f"{plugins_path}/font/zh.ttf", 140)
    text_font = ImageFont.truetype(f"{plugins_path}/font/syht.otf", 53)
    quote_font = ImageFont.truetype(f"{plugins_path}/font/syht.otf", 60)

    day_x = 85
    day_y = 35
    # 绘制日期
    draw.text((day_x, day_y), today_day, fill=today_day_color, font=num_font_Bold, align='center')
    # today_day_width, today_day_height = draw.textsize(today_day, num_font_Bold)
    # 获取文字宽度
    today_day_width = draw.textlength(today_day, num_font_Bold)

    # 绘制竖线
    # 定义线段的起始坐标和终止坐标
    x0, y0 = day_x + today_day_width + 25, day_y+118
    x1, y1 = x0, y0 + 210

    # 绘制白色线段，宽度为4
    draw.line((x0, y0, x1, y1), fill=line_color, width=4)

    # 绘制星期
    draw.text((day_x + today_day_width + 80, day_y+95), '星', fill=weekday_color, font=week_font_Regular)
    draw.text((day_x + today_day_width + 80 + 120 + 20, day_y+95), '期', fill=weekday_color, font=week_font_Regular)
    draw.text((day_x + today_day_width + 80+ 120 + 130 + 20, day_y+95), weekday, fill=weekday_color, font=week_font_Regular)
    # 绘制年月
    year_month_width = draw.textlength(today, num_font_Regular)
    draw.text((day_x + today_day_width + 80, day_y+270), today, fill=today_color, font=num_font_Regular)
    draw.text((day_x + today_day_width + 80 + year_month_width + 20 , day_y+270), lunar_date, fill=lunar_date_color, font=text_font)

    # 绘制鸡汤
    draw.text((day_x + 20, day_y+400), quote_content, fill=quote_content_color, font=quote_font)

    # 绘制天气图标
    icon_width = draw.textlength(unicode_text, icon_font)
    draw.text((width - 105 - icon_width, day_y +100), unicode_text, fill=icon_color, font=icon_font, align='center')
    
    # 绘制城市
    city_width = draw.textlength(city_name, text_font)
    draw.text((width - 105 - city_width, day_y +195), city_name, fill=city_color, font=text_font)
    # 绘制天气说明
    cond_width = draw.textlength(cond, text_font)
    draw.text((width - 105 - cond_width + 18, day_y +270), cond, fill=weather_desc_color, font=text_font)
    # 保存图片
    image1 = Image.alpha_composite(square,image)
    image1.save(f"{plugins_path}/weather.png")
    shutil.copy(f'{plugins_path}/weather.png', f'{plugins_path}/weather.jpg')
    img_url = mbot_api.user.upload_img_to_cloud_by_filepath(f'{plugins_path}/weather.jpg')
    _LOGGER.info(f'{plugins_name}上传到MR服务器的图片URL是:{img_url}')
    image_path = f'{plugins_name}{plugins_path}/weather.png'
    try:
        if not os.path.exists(image_path):
            image_path = f'{plugins_path}/weather.png'
    except Exception as e:
        _LOGGER.error(f'{plugins_name}检查文件是否存在时发生异常，原因：{e}')
    wecom_title = '🌎 每天60秒读懂世界'
    wecom_digest, wecom_content, news_url = get_daily_news(img_url)
    author = f'农历{lunar_date} 星期{weekday}'
    content_source_url = news_url
    if push_wx:
        thumb_media_id = get_media_id(access_token, image_path)
        result = push_msg_wx(access_token, touser, agentid, wecom_title, thumb_media_id, content_source_url, wecom_digest, wecom_content, wecom_api_url, author)
        _LOGGER.info(f'{plugins_name}企业微信推送结果: {result}')
    else:
        pic_url = img_url
        result = push_msg_mr(wecom_title, wecom_digest, pic_url, content_source_url)
        _LOGGER.info(f'{plugins_name}自选推送通道推送结果: {result}')

def is_push_to_wx():
    push_wx = True
    extra_flag = True
    wecom_api_url = 'https://qyapi.weixin.qq.com'
    access_token = ''
    agentid = ''
    touser = ''
    if qywx_channel_extra:
        if corpid_extra and agentid_extra and corpsecret_extra and touser_extra:
            corpid = corpid_extra
            agentid = agentid_extra
            corpsecret = corpsecret_extra
            touser = touser_extra
            _LOGGER.error(f'{plugins_name}设置的独立微信应用参数:「agentid: {agentid} corpid: {corpid} corpsecret: {corpsecret} touser: {touser}」')
        else:
            _LOGGER.error(f'{plugins_name}设置的独立微信应用参数不完整或错误，注意 touser 不带 @ 符号（除非设置的@all,所有人接收）。将采用默认消息通道推送')
            push_wx = False
            extra_flag = False
    if user_id and not qywx_channel_extra:
        corpid, agentid, corpsecret = get_qywx_info()
        touser = server.user.get(user_id).qywx_user
        _LOGGER.info(f'{plugins_name}获取到 MR 系统主干设置的的企业微信信息:「agentid: {agentid} corpid: {corpid} corpsecret: {corpsecret} touser: {touser}」')
        if not agentid or not corpid or not corpsecret or not touser:
            _LOGGER.error(f'{plugins_name}企业微信信息获取失败或填写不完整')
            _LOGGER.error(f'{plugins_name}在设置-设置企业微信页设置：「agentid」，「corpid」，「corpsecret」')
            _LOGGER.error(f'{plugins_name}在用户管理页设置微信账号，获取方法参考: https://alanoo.notion.site/thumb_media_id-64f170f7dcd14202ac5abd6d0e5031fb')
            _LOGGER.error(f'{plugins_name}本插件选用微信通道推送消息效果最佳，但现在没获取到，将采用默认消息通道推送')
            # _LOGGER.error('默认消息通道推送：每个站点封面图无法一站一图，都是统一的')
            push_wx = False
    elif not user_id and not qywx_channel_extra:
        _LOGGER.error(f'{plugins_name}未设置推送人，也没有设置独立微信应用参数，将采用默认消息通道推送')
        # _LOGGER.error('默认消息通道推送：每个站点封面图无法一站一图，都是统一的')
        push_wx = False
    if (push_wx or qywx_channel_extra) and extra_flag:
        if wecom_proxy_url:
            _LOGGER.info(f'{plugins_name}设置了微信白名单代理，地址是：{wecom_proxy_url}')
            wecom_api_url = wecom_proxy_url
        else:
            _LOGGER.info(f'{plugins_name}未设置微信白名单代理，使用官方 api 地址: https://qyapi.weixin.qq.com')
        push_wx, access_token = getToken(corpid, corpsecret, wecom_api_url)
    return push_wx, access_token, agentid, touser, wecom_api_url

def get_qywx_info():
    try:
        yml_file = "/data/conf/base_config.yml"
        with open(yml_file, encoding='utf-8') as f:
            yml_data = yaml.load(f, Loader=yaml.FullLoader)
        for channel in yml_data['notify_channel']:
            if channel['enable']:
                agentid = channel.get('agentid')
                corpid = channel.get('corpid')
                corpsecret = channel.get('corpsecret')
                return corpid, agentid, corpsecret
    except Exception as e:
        _LOGGER.error(f'{plugins_name}获取「企业微信配置信息」错误，可能 MR 中填写的信息有误或不全: {e}')
        pass
    return '','',''

def getToken(corpid, corpsecret, wecom_api_url):
    url = wecom_api_url + "/cgi-bin/gettoken?corpid=" + corpid + "&corpsecret=" + corpsecret
    MAX_RETRIES = 3
    for i in range(MAX_RETRIES):
        try:
            r = requests.get(url, timeout=20)
            # _LOGGER.info(f'{plugins_name}尝试 {i+1} 次后，请求「获取token接口」成功')
            break
        except requests.RequestException as e:
            _LOGGER.error(f'{plugins_name}第 {i+1} 次尝试，请求「获取token接口」异常，原因：{e}')
            time.sleep(2)
    if r.json()['errcode'] == 0:
        access_token = r.json()['access_token']
        return True, access_token
    else:
        _LOGGER.error(f'{plugins_name}请求企业微信「access_token」失败,请检查企业微信各个参数是否设置正确，将采用默认消息通道推送！')
        # _LOGGER.error(f'{plugins_name}默认消息通道推送：每个站点封面图无法一站一图，都是统一的')
        return False, ''

def get_media_id(access_token, image_path):
    media_id = upload_image_and_get_media_id(access_token, image_path)
    return media_id

def upload_image_and_get_media_id(access_token, image_path):
    url = "https://qyapi.weixin.qq.com/cgi-bin/media/upload"
    querystring = {"access_token": access_token, "type": "image"}
    files = {"media": ("image.gif", open(image_path, "rb"))}
    MAX_RETRIES = 3
    for i in range(MAX_RETRIES):
        try:
            response = requests.request("POST", url, params=querystring, files=files, timeout=20)
            # _LOGGER.info(f'{plugins_name}第 {i+1} 次尝试，请求「上传封面接口」成功')
            break
        except requests.RequestException as e:
            _LOGGER.error(f'{plugins_name}第 {i+1} 次尝试，请求「上传封面接口」异常，原因：{e}')
            time.sleep(2)
    _LOGGER.info(f'{plugins_name}上传封面返回结果：{response.text}')
    if response.status_code == 200:
        resp_data = response.json()
        media_id = resp_data.get('media_id')
        return media_id
    else:
        _LOGGER.error(f'{plugins_name}上传封面失败，状态码：{response.status_code}')

def push_msg_wx(access_token, touser, agentid, wecom_title, thumb_media_id, content_source_url, wecom_digest, wecom_content, wecom_api_url, author):
    url = wecom_api_url + '/cgi-bin/message/send?access_token=' + access_token
    data = {
        "touser": touser,
        "msgtype": "mpnews",
        "agentid": agentid,
        "mpnews": {
            "articles": [
                {
                    "title" : wecom_title,
                    "thumb_media_id" : thumb_media_id,
                    "author" : author,
                    "content_source_url" : content_source_url,
                    "digest" : wecom_digest,
                    "content" : wecom_content,
                }
            ]
        },
        "safe": 0,
        "enable_id_trans": 0,
        "enable_duplicate_check": 0,
        "duplicate_check_interval": 1800
    }
    MAX_RETRIES = 3
    for i in range(MAX_RETRIES):
        try:
            r = requests.post(url, json=data, timeout=20)
            # _LOGGER.info(f'{plugins_name}尝试 {i+1} 次后，请求「推送接口」成功')
            break
        except requests.RequestException as e:
            _LOGGER.error(f'{plugins_name}第 {i+1} 次尝试，请求「推送接口」异常，原因：{e}')
            time.sleep(2)
    if r is None:
        _LOGGER.error(f'{plugins_name}请求推送接口失败，将采用 MR 默认通知通道推送')
        result = push_msg_mr(wecom_title, wecom_digest, pic_url, content_source_url)
        return result
    elif r.json()['errcode'] != 0:
        _LOGGER.error(f'{plugins_name}通过设置的微信参数推送失败，采用 MR 默认通知通道推送')
        result = push_msg_mr(wecom_title, wecom_digest, pic_url, content_source_url)
        return result
    elif r.json()['errcode'] == 0:
        _LOGGER.info(f'{plugins_name}通过设置的微信参数推送消息成功')
        return r.json()

def push_msg_mr(msg_title, message, pic_url, link_url):
    # try:
    if message_to_uid:
        for _ in message_to_uid:
            for i in range(3):
                try:
                    server.notify.send_message_by_tmpl('{{title}}', '{{a}}', {
                        'title': msg_title,
                        'a': message,
                        'pic_url': pic_url,
                        'link_url': link_url
                    }, to_uid=_)
                    result = f'尝试 {i+1} 次后，已推送消息通知'
                    break
                    # return '已推送消息通知'
                except Exception as e:
                    result =  f'第 {i+1} 次尝试，消息推送异常，原因: {e}'
            return result
    else:
        for i in range(3):
            try:
                server.notify.send_message_by_tmpl('{{title}}', '{{a}}', {
                    'title': msg_title,
                    'a': message,
                    'pic_url': pic_url,
                    'link_url': link_url
                })
                result = f'尝试 {i+1} 次后，已推送消息通知'
                break
            except Exception as e:
                result =  f'第 {i+1} 次尝试，消息推送异常，原因: {e}'
        return result
    # except Exception as e:
    #     return f'消息推送异常，原因: {e}'
    #     pass

def main():
    push_wx, access_token, agentid, touser, wecom_api_url = is_push_to_wx()
    generate_image(push_wx, access_token, agentid, touser, wecom_api_url)
