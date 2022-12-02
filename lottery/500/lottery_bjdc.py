#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import math
import random
import time

import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger
import demjson3
import numpy as np
import pandas as pd
from lxml import etree
from datetime import datetime
import configparser
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from UserAgent_Pool import UserAgent_Pool


def get_500_html(url):
    headers = {
        "user-agent": random.choice(UserAgent_Pool.UserAgent().c),
        "authority": "odds.500.com",
        "method": "GET",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate, br",
        "sec-fetch-dest": "document",
        'referer': "https://trade.500.com/bjdc/"

    }
    res = requests.get(url, headers=headers)
    res.encoding = 'gbk'
    return res


result_template = "gameId:%s 赛事:%s 比赛时间:%s \n " \
                  "主    队:%s VS 客队:%s \n " \
                  "初盘方差:%s ,初盘预测:%s \n" \
                  "即盘方差:%s ,临盘预测:%s \n" \
                  "==========分隔符==========\n"


def conf_file():
    conf = configparser.ConfigParser()
    conf.read("config.ini")
    return conf


def send_email(msg):
    conf = conf_file()
    send_email = conf.get("send-email", "email")
    send_email_pwd = conf.get("send-email", "password")
    to_email = conf.get("receive-email", "to")
    to_email_array = to_email.split(";")
    today = datetime.now().strftime("%Y-%m-%d")
    msg = MIMEText(msg, 'plain', _charset="utf-8")
    msg['Subject'] = today + "单场数据"
    msg["from"] = send_email
    msg["to"] = to_email

    with SMTP_SSL(host="smtp.qq.com", port=465) as smtp:
        smtp.login(send_email, send_email_pwd)
        smtp.sendmail(from_addr=send_email, to_addrs=to_email_array, msg=msg.as_string())


def calc_avg(data):
    kai_li_sum = 0
    for i in data:
        kai_li_sum += i
    return kai_li_sum / len(data)


def calc(param):
    df = pd.DataFrame(param)
    df1 = pd.DataFrame(df.values.T)
    data_array = np.array(df1)
    data_list = data_array.tolist()
    fc_list = list()
    for kai_li_data in data_list:
        avg = calc_avg(kai_li_data)
        temp_sum = 0
        for i in kai_li_data:
            temp_sum += math.pow((i - avg), 2)

        fc = temp_sum / len(kai_li_data)
        fc_list.append(round(fc, 8))
    return fc_list


def min_value(value_list):
    sheng_value = value_list[0]
    ping_value = value_list[1]
    fu_value = value_list[2]

    min_result = min(float(sheng_value), float(ping_value), float(fu_value))
    if min_result == sheng_value:
        return '胜'
    elif min_result == ping_value:
        return '平'
    elif min_result == fu_value:
        return '负'
    else:
        return 'None'


def get_today_game():
    today = datetime.now().strftime("%Y-%m-%d")
    # today = "2022-11-29"
    logger.info(today + "定时任务开始执行")
    today_game_url = "https://trade.500.com/bjdc/"
    begin = time.time()
    game_html = get_500_html(today_game_url)
    game_tree = etree.HTML(game_html.text)
    match = "//*[starts-with(@id,\"" + today + "\")]/tr"
    tr_list = game_tree.xpath(match)
    result_email_content = ""
    for tr in tr_list:
        fid = tr.attrib.get('fid')
        value = tr.attrib.get('value')
        value_json = demjson3.decode(value)
        index = value_json['index']
        leagueName = value_json['leagueName']
        homeTeam = value_json['homeTeam']
        guestTeam = value_json['guestTeam']
        endTime = value_json['endTime']

        game_fid_html = get_fid_ouzhi(fid)
        game_fid_tree = etree.HTML(game_fid_html.text)
        game_fid_tr = game_fid_tree.xpath('//*[@id="datatb"]/tr')
        game_kai_li_chu_list = list()
        game_kai_li_li_list = list()
        for current_tr in game_fid_tr:
            tds = current_tr.xpath("td")
            if len(tds) < 7:
                break
            gong_si = tds[1].attrib['title']
            if '威廉希尔' == gong_si or '立博' == gong_si or 'Bet365' == gong_si or 'Interwetten' == gong_si:
                kai_li_trs = tds[5].xpath("table/tbody/tr")
                game_kai_li_chu_list.append(
                    (float(kai_li_trs[0].xpath('td')[0].text), float(kai_li_trs[0].xpath('td')[1].text),
                     float(kai_li_trs[0].xpath('td')[2].text)))
                game_kai_li_li_list.append(
                    (float(kai_li_trs[1].xpath('td')[0].text), float(kai_li_trs[1].xpath('td')[1].text),
                     float(kai_li_trs[1].xpath('td')[2].text)))
        if len(game_kai_li_li_list) >= 3:
            chu_fang_cha = calc(game_kai_li_chu_list)
            chu_fang_result = min_value(chu_fang_cha)
            lin_fang_cha = calc(game_kai_li_li_list)
            lin_fang_result = min_value(lin_fang_cha)
            result_email_content += result_template % (index,
                                                       leagueName, endTime, homeTeam, guestTeam,
                                                       chu_fang_cha, chu_fang_result, lin_fang_cha, lin_fang_result)

    end = time.time()
    if '' != result_email_content:
        print(result_email_content)
        # send_email(result_email_content)
    logger.info("拉取全部数据耗时:[%d]秒" % (end - begin))


def get_fid_ouzhi(fid):
    fid_game_url = "https://odds.500.com/fenxi/ouzhi-%s.shtml"
    fid_game_url = fid_game_url % fid
    return get_500_html(fid_game_url)


if __name__ == '__main__':
    get_today_game()
    # 每天中午21:01分开始运行
    # conf = conf_file()
    # test = conf.get("scheduler", "test")
    # if test == 'True':
    #     get_today_game()
    # else:
    #     hour_s = conf.get("scheduler", "hour")
    #     minute_s = conf.get("scheduler", "minute")
    #     scheduler = BlockingScheduler()
    #     scheduler.add_job(get_today_game, 'cron', hour=hour_s, minute=minute_s, timezone='Asia/Shanghai')
    #     scheduler.start()
