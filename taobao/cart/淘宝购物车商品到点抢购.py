import time
from datetime import datetime
from loguru import logger

from selenium import webdriver
from selenium.webdriver.common.by import By


def tao_bao_cat_submit():
    '''
    程序运行前修改此值
    建议在抢购时间前3分钟运行
    '''
    begin_time = "2022-11-23 18:27:00.00000000"
    browser = webdriver.Chrome()
    browser.get("https://www.taobao.com")
    browser.find_element(By.LINK_TEXT, "亲，请登录").click()
    '''
    程序休眠0秒，等待用户登录操作
    '''
    print(f'请小主在10秒内登录')
    time.sleep(10)
    browser.get("https://cart.taobao.com/cart.htm")
    time.sleep(3)
    '''
    全选点击
    '''
    while True:
        try:
            if browser.find_element(By.ID, "J_SelectAll2"):
                logger.info("找到全选框")
                browser.find_element(By.ID, "J_SelectAll2").click()
                break
        except Exception as ex:
            logger.info("全选出现异常:%s" % str(ex))

    while True:
        current_time = datetime.now()
        current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")
        logger.info("当前时间:%s" % current_time_str)
        if current_time_str >= begin_time:
            while True:
                try:
                    if browser.find_element(By.ID, "J_SmallSubmit"):
                        logger.info("开始点击结算")
                        browser.find_element(By.ID, "J_SmallSubmit").click()
                        break
                except Exception as ex:
                    logger.warning("未找到结算按钮,%s" % str(ex))
            break

    while True:
        try:
            if browser.find_element(By.XPATH, "//*[@id='submitOrderPC_1']/div[1]/a[2]"):
                logger.info("开始点击提交订单")
                browser.find_element(By.XPATH, "//*[@id='submitOrderPC_1']/div[1]/a[2]").click()
                break
        except Exception as ex:
            logger.warning("未找到提交订单,%s" % str(ex))
    logger.info("小主，已经为你抢到商品，请及时付款")
    time.sleep(30)


if __name__ == '__main__':
    tao_bao_cat_submit()
