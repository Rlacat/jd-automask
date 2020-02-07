# -*- coding=utf-8 -*-
'''
京东抢购口罩程序
通过商品的skuid、地区id抢购
'''
import requests,re,pickle
import time
import json
import sys,os,logging
import random
import math
from bs4 import BeautifulSoup
from log.jdlogger import logger
from jdemail.jdEmail import sendMail
from config.config import global_config
import configparser
config = configparser.ConfigParser()


'''
需要修改
'''
#cookies在单独文件中保存 通过扫二维码登陆获取并自动保存
# 有货通知 收件邮箱
mail = global_config.getRaw('config', 'mail')
# 地区id
area = global_config.getRaw('config', 'area')
# 商品id
skuidsString = global_config.getRaw('config', 'skuids')
skuids = str(skuidsString).split(',')
#print(skuids)
if len(skuids[0]) == 0:
    logger.error('请在config.ini文件中输入你的商品id')
    sys.exit(1)
'''
备用
'''
timesleep = random.randint(5, 15) / 10
# eid
eid = global_config.getRaw('config', 'eid')
fp = global_config.getRaw('config', 'fp')
# 支付密码
payment_pwd = global_config.getRaw('config', 'payment_pwd')

session = requests.session()
session.headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "Connection": "keep-alive"
}
manual_cookies = {}


def get_tag_value(tag, key='', index=0):
    if key:
        value = tag[index].get(key)
    else:
        value = tag[index].text
    return value.strip(' \t\r\n')


def response_status(resp):
    if resp.status_code != requests.codes.OK:
        print('Status: %u, Url: %s' % (resp.status_code, resp.url))
        return False
    return True

'''
for item in cookies_String.split(';'):
    name, value = item.strip().split('=', 1)
    # 用=号分割，分割1次
    manual_cookies[name] = value
    # 为字典cookies添加内容

cookiesJar = requests.utils.cookiejar_from_dict(manual_cookies, cookiejar=None, overwrite=True)
已更新为扫二维码获取
'''



def validate_cookies():
    for flag in range(1, 3):
        if not spider.checkLogin():
            if not spider.login_by_QR():
                sys.exit(-1)


def getUsername():
    userName_Url = 'https://passport.jd.com/new/helloService.ashx?callback=jQuery339448&_=' + str(
        int(time.time() * 1000))
    session.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://order.jd.com/center/list.action",
        "Connection": "keep-alive"
    }
    resp = session.get(url=userName_Url, allow_redirects=True)
    resultText = resp.text
    resultText = resultText.replace('jQuery339448(', '')
    resultText = resultText.replace(')', '')
    usernameJson = json.loads(resultText)
    logger.info('登录账号名称' + usernameJson['nick'])


'''
检查是否有货
'''


def check_item_stock(itemUrl):
    response = session.get(itemUrl)
    if (response.text.find('无货') > 0):
        return True
    else:
        return False


'''
取消勾选购物车中的所有商品
'''


def cancel_select_all_cart_item():
    url = "https://cart.jd.com/cancelAllItem.action"
    data = {
        't': 0,
        'outSkus': '',
        'random': random.random()
    }
    resp = session.post(url, data=data)
    if resp.status_code != requests.codes.OK:
        print('Status: %u, Url: %s' % (resp.status_code, resp.url))
        return False
    return True


'''
购物车详情
'''


def cart_detail():
    url = 'https://cart.jd.com/cart.action'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://order.jd.com/center/list.action",
        "Host": "cart.jd.com",
        "Connection": "keep-alive"
    }
    resp = session.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    cart_detail = dict()
    for item in soup.find_all(class_='item-item'):
        try:
            sku_id = item['skuid']  # 商品id
        except Exception as e:
            logger.info('购物车中有套装商品，跳过')
            continue
        try:
            # 例如：['increment', '8888', '100001071956', '1', '13', '0', '50067652554']
            # ['increment', '8888', '100002404322', '2', '1', '0']
            item_attr_list = item.find(class_='increment')['id'].split('_')
            p_type = item_attr_list[4]
            promo_id = target_id = item_attr_list[-1] if len(item_attr_list) == 7 else 0

            cart_detail[sku_id] = {
                'name': get_tag_value(item.select('div.p-name a')),  # 商品名称
                'verder_id': item['venderid'],  # 商家id
                'count': int(item['num']),  # 数量
                'unit_price': get_tag_value(item.select('div.p-price strong'))[1:],  # 单价
                'total_price': get_tag_value(item.select('div.p-sum strong'))[1:],  # 总价
                'is_selected': 'item-selected' in item['class'],  # 商品是否被勾选
                'p_type': p_type,
                'target_id': target_id,
                'promo_id': promo_id
            }
        except Exception as e:
            logger.error("商品%s在购物车中的信息无法解析，报错信息: %s，该商品自动忽略", sku_id, e)

    logger.info('购物车信息：%s', cart_detail)
    return cart_detail


'''
修改购物车商品的数量
'''


def change_item_num_in_cart(sku_id, vender_id, num, p_type, target_id, promo_id):
    url = "https://cart.jd.com/changeNum.action"
    data = {
        't': 0,
        'venderId': vender_id,
        'pid': sku_id,
        'pcount': num,
        'ptype': p_type,
        'targetId': target_id,
        'promoID': promo_id,
        'outSkus': '',
        'random': random.random(),
        # 'locationId'
    }
    session.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://cart.jd.com/cart",
        "Connection": "keep-alive"
    }
    resp = session.post(url, data=data)
    return json.loads(resp.text)['sortedWebCartResult']['achieveSevenState'] == 2


'''
添加商品到购物车
'''


def add_item_to_cart(sku_id):
    url = 'https://cart.jd.com/gate.action'
    payload = {
        'pid': sku_id,
        'pcount': 1,
        'ptype': 1,
    }
    resp = session.get(url=url, params=payload)
    if 'https://cart.jd.com/cart.action' in resp.url:  # 套装商品加入购物车后直接跳转到购物车页面
        result = True
    else:  # 普通商品成功加入购物车后会跳转到提示 "商品已成功加入购物车！" 页面
        soup = BeautifulSoup(resp.text, "html.parser")
        result = bool(soup.select('h3.ftx-02'))  # [<h3 class="ftx-02">商品已成功加入购物车！</h3>]

    if result:
        logger.info('%s  已成功加入购物车', sku_id)
    else:
        logger.error('%s 添加到购物车失败', sku_id)


def get_checkout_page_detail():
    """获取订单结算页面信息

    该方法会返回订单结算页面的详细信息：商品名称、价格、数量、库存状态等。

    :return: 结算信息 dict
    """
    url = 'http://trade.jd.com/shopping/order/getOrderInfo.action'
    # url = 'https://cart.jd.com/gotoOrder.action'
    payload = {
        'rid': str(int(time.time() * 1000)),
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://cart.jd.com/cart.action",
        "Connection": "keep-alive",
        'Host': 'trade.jd.com',
    }
    try:
        resp = session.get(url=url, params=payload, headers=headers)
        if not response_status(resp):
            logger.error('获取订单结算页信息失败')
            return ''

        soup = BeautifulSoup(resp.text, "html.parser")
        risk_control = get_tag_value(soup.select('input#riskControl'), 'value')

        order_detail = {
            'address': soup.find('span', id='sendAddr').text[5:],  # remove '寄送至： ' from the begin
            'receiver': soup.find('span', id='sendMobile').text[4:],  # remove '收件人:' from the begin
            'total_price': soup.find('span', id='sumPayPriceId').text[1:],  # remove '￥' from the begin
            'items': []
        }

        logger.info("下单信息：%s", order_detail)
        return order_detail
    except requests.exceptions.RequestException as e:
        logger.error('订单结算页面获取异常：%s' % e)
    except Exception as e:
        logger.error('下单页面数据解析异常：%s', e)
    return risk_control


def submit_order(risk_control):
    """提交订单

    重要：
    1.该方法只适用于普通商品的提交订单（即可以加入购物车，然后结算提交订单的商品）
    2.提交订单时，会对购物车中勾选✓的商品进行结算（如果勾选了多个商品，将会提交成一个订单）

    :return: True/False 订单提交结果
    """
    url = 'https://trade.jd.com/shopping/order/submitOrder.action'
    # js function of submit order is included in https://trade.jd.com/shopping/misc/js/order.js?r=2018070403091

    # overseaPurchaseCookies:
    # vendorRemarks: []
    # submitOrderParam.sopNotPutInvoice: false
    # submitOrderParam.trackID: TestTrackId
    # submitOrderParam.ignorePriceChange: 0
    # submitOrderParam.btSupport: 0
    # riskControl:
    # submitOrderParam.isBestCoupon: 1
    # submitOrderParam.jxj: 1
    # submitOrderParam.trackId:

    data = {
        'overseaPurchaseCookies': '',
        'vendorRemarks': '[]',
        'submitOrderParam.sopNotPutInvoice': 'false',
        'submitOrderParam.trackID': 'TestTrackId',
        'submitOrderParam.ignorePriceChange': '0',
        'submitOrderParam.btSupport': '0',
        'riskControl': risk_control,
        'submitOrderParam.isBestCoupon': 1,
        'submitOrderParam.jxj': 1,
        'submitOrderParam.trackId': '9643cbd55bbbe103eef18a213e069eb0',  # Todo: need to get trackId
        # 'submitOrderParam.eid': eid,
        # 'submitOrderParam.fp': fp,
        'submitOrderParam.needCheck': 1,
    }

    def encrypt_payment_pwd(payment_pwd):
        return ''.join(['u3' + x for x in payment_pwd])

    if len(payment_pwd) > 0:
        data['submitOrderParam.payPassword'] = encrypt_payment_pwd(payment_pwd)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "http://trade.jd.com/shopping/order/getOrderInfo.action",
        "Connection": "keep-alive",
        'Host': 'trade.jd.com',
    }

    try:
        resp = session.post(url=url, data=data, headers=headers)
        resp_json = json.loads(resp.text)

        # 返回信息示例：
        # 下单失败
        # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60123, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '请输入支付密码！'}
        # {'overSea': False, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'orderXml': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60017, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '您多次提交过快，请稍后再试'}
        # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60077, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '获取用户订单信息失败'}
        # {"cartXml":null,"noStockSkuIds":"xxx","reqInfo":null,"hasJxj":false,"addedServiceList":null,"overSea":false,"orderXml":null,"sign":null,"pin":"xxx","needCheckCode":false,"success":false,"resultCode":600157,"orderId":0,"submitSkuNum":0,"deductMoneyFlag":0,"goJumpOrderCenter":false,"payInfo":null,"scaleSkuInfoListVO":null,"purchaseSkuInfoListVO":null,"noSupportHomeServiceSkuList":null,"msgMobile":null,"addressVO":{"pin":"xxx","areaName":"","provinceId":xx,"cityId":xx,"countyId":xx,"townId":xx,"paymentId":0,"selected":false,"addressDetail":"xx","mobile":"xx","idCard":"","phone":null,"email":null,"selfPickMobile":null,"selfPickPhone":null,"provinceName":null,"cityName":null,"countyName":null,"townName":null,"giftSenderConsigneeName":null,"giftSenderConsigneeMobile":null,"gcLat":0.0,"gcLng":0.0,"coord_type":0,"longitude":0.0,"latitude":0.0,"selfPickOptimize":0,"consigneeId":0,"selectedAddressType":0,"siteType":0,"helpMessage":null,"tipInfo":null,"cabinetAvailable":true,"limitKeyword":0,"specialRemark":null,"siteProvinceId":0,"siteCityId":0,"siteCountyId":0,"siteTownId":0,"skuSupported":false,"addressSupported":0,"isCod":0,"consigneeName":null,"pickVOname":null,"shipmentType":0,"retTag":0,"tagSource":0,"userDefinedTag":null,"newProvinceId":0,"newCityId":0,"newCountyId":0,"newTownId":0,"newProvinceName":null,"newCityName":null,"newCountyName":null,"newTownName":null,"checkLevel":0,"optimizePickID":0,"pickType":0,"dataSign":0,"overseas":0,"areaCode":null,"nameCode":null,"appSelfPickAddress":0,"associatePickId":0,"associateAddressId":0,"appId":null,"encryptText":null,"certNum":null,"used":false,"oldAddress":false,"mapping":false,"addressType":0,"fullAddress":"xxxx","postCode":null,"addressDefault":false,"addressName":null,"selfPickAddressShuntFlag":0,"pickId":0,"pickName":null,"pickVOselected":false,"mapUrl":null,"branchId":0,"canSelected":false,"address":null,"name":"xxx","message":null,"id":0},"msgUuid":null,"message":"xxxxxx商品无货"}
        # {'orderXml': None, 'overSea': False, 'noStockSkuIds': 'xxx', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'cartXml': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 600158, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': {'oldAddress': False, 'mapping': False, 'pin': 'xxx', 'areaName': '', 'provinceId': xx, 'cityId': xx, 'countyId': xx, 'townId': xx, 'paymentId': 0, 'selected': False, 'addressDetail': 'xxxx', 'mobile': 'xxxx', 'idCard': '', 'phone': None, 'email': None, 'selfPickMobile': None, 'selfPickPhone': None, 'provinceName': None, 'cityName': None, 'countyName': None, 'townName': None, 'giftSenderConsigneeName': None, 'giftSenderConsigneeMobile': None, 'gcLat': 0.0, 'gcLng': 0.0, 'coord_type': 0, 'longitude': 0.0, 'latitude': 0.0, 'selfPickOptimize': 0, 'consigneeId': 0, 'selectedAddressType': 0, 'newCityName': None, 'newCountyName': None, 'newTownName': None, 'checkLevel': 0, 'optimizePickID': 0, 'pickType': 0, 'dataSign': 0, 'overseas': 0, 'areaCode': None, 'nameCode': None, 'appSelfPickAddress': 0, 'associatePickId': 0, 'associateAddressId': 0, 'appId': None, 'encryptText': None, 'certNum': None, 'addressType': 0, 'fullAddress': 'xxxx', 'postCode': None, 'addressDefault': False, 'addressName': None, 'selfPickAddressShuntFlag': 0, 'pickId': 0, 'pickName': None, 'pickVOselected': False, 'mapUrl': None, 'branchId': 0, 'canSelected': False, 'siteType': 0, 'helpMessage': None, 'tipInfo': None, 'cabinetAvailable': True, 'limitKeyword': 0, 'specialRemark': None, 'siteProvinceId': 0, 'siteCityId': 0, 'siteCountyId': 0, 'siteTownId': 0, 'skuSupported': False, 'addressSupported': 0, 'isCod': 0, 'consigneeName': None, 'pickVOname': None, 'shipmentType': 0, 'retTag': 0, 'tagSource': 0, 'userDefinedTag': None, 'newProvinceId': 0, 'newCityId': 0, 'newCountyId': 0, 'newTownId': 0, 'newProvinceName': None, 'used': False, 'address': None, 'name': 'xx', 'message': None, 'id': 0}, 'msgUuid': None, 'message': 'xxxxxx商品无货'}
        # 下单成功
        # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': True, 'resultCode': 0, 'orderId': 8740xxxxx, 'submitSkuNum': 1, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': None}

        if resp_json.get('success'):
            logger.info('订单提交成功! 订单号：%s', resp_json.get('orderId'))
            return True
        else:
            message, result_code = resp_json.get('message'), resp_json.get('resultCode')
            if result_code == 0:
                # self._save_invoice()
                message = message + '(下单商品可能为第三方商品，将切换为普通发票进行尝试)'
            elif result_code == 60077:
                message = message + '(可能是购物车为空 或 未勾选购物车中商品)'
            elif result_code == 60123:
                message = message + '(需要在payment_pwd参数配置支付密码)'
            logger.info('订单提交失败, 错误码：%s, 返回信息：%s', result_code, message)
            logger.info(resp_json)
            return False
    except Exception as e:
        logger.error(e)
        return False


'''

'''


def item_removed(sku_id):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "http://trade.jd.com/shopping/order/getOrderInfo.action",
        "Connection": "keep-alive",
        'Host': 'item.jd.com',
    }
    url = 'https://item.jd.com/{}.html'.format(sku_id)
    page = requests.get(url=url, headers=headers)
    return '该商品已下柜' not in page.text


'''
购买环节
测试三次
'''


def buyMask(sku_id):
    for count in range(1, 2):
        logger.info('第[%s/%s]次尝试提交订单', count, 3)
        cancel_select_all_cart_item()
        cart = cart_detail()
        if sku_id in cart:
            logger.info('%s 已在购物车中，调整数量为 %s', sku_id, 1)
            cart_item = cart.get(sku_id)
            change_item_num_in_cart(
                sku_id=sku_id,
                vender_id=cart_item.get('vender_id'),
                num=1,
                p_type=cart_item.get('p_type'),
                target_id=cart_item.get('target_id'),
                promo_id=cart_item.get('promo_id')
            )
        else:
            add_item_to_cart(sku_id)
        risk_control = get_checkout_page_detail()
        if len(risk_control) > 0:
            if submit_order(risk_control):
                return True
        logger.info('休息%ss', 3)
        time.sleep(3)
    else:
        logger.info('执行结束，提交订单失败！')
        return False


'''
查询库存
'''

'''
update by rlacat
解决skuid长度过长（超过99个）导致无法查询问题
'''
def check_stock():
    logger.info("["+str(len(skuids))+"]个需要检测的商品")
    st_tmp = []
    len_arg = 70
    #print("skustr:",skuidStr)
    #print("skuids:",len(skuids))
    skuid_nums = len(skuids)
    skuid_batchs = math.ceil(skuid_nums / len_arg)
    #print("skuid_batchs:",skuid_batchs)
    if(skuid_batchs > 1):
        logger.info("###数据过大 分["+str(skuid_batchs)+"]批进行####")
        for i in range(0,skuid_batchs):
            logger.info("###正在处理 第["+str(i+1)+"]批####")
            if(len_arg*(i+1) <= len(skuids)):
                #print("取个数：",len_arg*i,"至",len_arg*(i+1))
                skuidStr = ','.join(skuids[len_arg*i:len_arg*(i+1)])
                st_tmp+=check_stock_tmp(skuidStr,skuids[len_arg*i:len_arg*(i+1)])
            else:
                #print("取个数：",len_arg*i,"至",len_arg*(i+1))
                skuidStr = ','.join(skuids[len_arg*i:skuid_nums])#skuid配置的最后一段
                #print(skuidStr)
                st_tmp+=check_stock_tmp(skuidStr,skuids[len_arg*i:skuid_nums])
    else:
        #<=1的情况
        skuidStr = ','.join(skuids)
        st_tmp=check_stock_tmp(skuidStr,skuids)
    return st_tmp

def check_stock_tmp(skuidString,skuids_a):
    callback = 'jQuery' + str(random.randint(1000000, 9999999))
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://cart.jd.com/cart.action",
        "Connection": "keep-alive",
    }
    url = 'https://c0.3.cn/stocks'
    payload = {
        'type': 'getstocks',
        'skuIds': skuidString,
        'area': area,
        'callback': callback,
        '_': int(time.time() * 1000),
    }
    resp = session.get(url=url, params=payload, headers=headers)
    resptext = resp.text.replace(callback + '(', '').replace(')', '')
    respjson = json.loads(resptext)
    inStockSkuid = []
    nohasSkuid = []
    #print(resptext,respjson)
    for i in skuids_a:
        #print("当前处理：",i)
        if(respjson[i]['StockStateName'] != '无货'):
            inStockSkuid.append(i)
        else:
            nohasSkuid.append(i)
    #print(nohasSkuid)
    logger.info('[%s]类型口罩无货', ','.join(nohasSkuid))
    return inStockSkuid

class JDSpider:
    '''
    登陆模块作者 zstu-lly
    参考 https://github.com/zstu-lly/JD_Robot
    '''
    def __init__(self):

        # init url related
        self.home = 'https://passport.jd.com/new/login.aspx'
        self.login = 'https://passport.jd.com/uc/loginService'
        self.imag = 'https://authcode.jd.com/verify/image'
        self.auth = 'https://passport.jd.com/uc/showAuthCode'

        self.sess = requests.Session()

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
            'ContentType': 'text/html; charset=utf-8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
        }

        self.cookies = {

        }

        self.eid = 'DHPVSQRUFPP6GFJ7WPOFDKYQUGQSREWJLJ5QJPDOSJ2BYF55IZHP5XX3K2BKW36H5IU3S4R6GPU7X3YOGRJGW7XCF4'
        self.fp = 'b450f02af7d98727ef061e8806361c67'

    def checkLogin(self):
        # 恢复之前保存的cookie
        checkUrl = 'https://passport.jd.com/uc/qrCodeTicketValidation'
        try:
            print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++')
            print(f'{time.ctime()} > 自动登录中... ')
            with open('cookie', 'rb') as f:
                cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
                response = requests.get(checkUrl, cookies=cookies)
                if response.status_code != requests.codes.OK:
                    print('登录过期, 请重新登录!')
                    return False
                else:
                    print('登录成功!')
                    self.cookies.update(dict(cookies))
                    return True

        except Exception as e:
            logger.error(e)
            return False

    def login_by_QR(self):
        # jd login by QR code
        try:
            print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++')
            print(f'{time.ctime()} > 请打开京东手机客户端，准备扫码登录:')
            urls = (
                'https://passport.jd.com/new/login.aspx',
                'https://qr.m.jd.com/show',
                'https://qr.m.jd.com/check',
                'https://passport.jd.com/uc/qrCodeTicketValidation'
            )
            # step 1: open login page
            response = self.sess.get(
                urls[0],
                headers=self.headers
            )
            if response.status_code != requests.codes.OK:
                print(f"获取登录页失败:{response.status_code}")
                return False
            # update cookies
            self.cookies.update(response.cookies)

            # step 2: get QR image
            response = self.sess.get(
                urls[1],
                headers=self.headers,
                cookies=self.cookies,
                params={
                    'appid': 133,
                    'size': 147,
                    't': int(time.time() * 1000),
                }
            )
            if response.status_code != requests.codes.OK:
                print(f"获取二维码失败:{response.status_code}")
                return False

            # update cookies
            self.cookies.update(response.cookies)

            # save QR code
            image_file = 'qr.png'
            with open(image_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)

            # scan QR code with phone
            if os.name == "nt":
                # for windows
                os.system('start ' + image_file)
            else:
                if os.uname()[0] == "Linux":
                    # for linux platform
                    os.system("eog " + image_file)
                else:
                    # for Mac platform
                    os.system("open " + image_file)

            # step 3: check scan result    京东上也是不断去发送check请求来判断是否扫码的
            self.headers['Host'] = 'qr.m.jd.com'
            self.headers['Referer'] = 'https://passport.jd.com/new/login.aspx'

            # check if QR code scanned
            qr_ticket = None
            retry_times = 100  # 尝试100次
            while retry_times:
                retry_times -= 1
                response = self.sess.get(
                    urls[2],
                    headers=self.headers,
                    cookies=self.cookies,
                    params={
                        'callback': 'jQuery%d' % random.randint(1000000, 9999999),
                        'appid': 133,
                        'token': self.cookies['wlfstk_smdl'],
                        '_': int(time.time() * 1000)
                    }
                )
                if response.status_code != requests.codes.OK:
                    continue
                rs = json.loads(re.search(r'{.*?}', response.text, re.S).group())
                if rs['code'] == 200:
                    print(f"{rs['code']} : {rs['ticket']}")
                    qr_ticket = rs['ticket']
                    break
                else:
                    print(f"{rs['code']} : {rs['msg']}")
                    time.sleep(3)

            if not qr_ticket:
                print("二维码登录失败")
                return False

            # step 4: validate scan result
            # must have
            self.headers['Host'] = 'passport.jd.com'
            self.headers['Referer'] = 'https://passport.jd.com/new/login.aspx'
            response = requests.get(
                urls[3],
                headers=self.headers,
                cookies=self.cookies,
                params={'t': qr_ticket},
            )
            if response.status_code != requests.codes.OK:
                print(f"二维码登录校验失败:{response.status_code}")
                return False

            # 京东有时候会认为当前登录有危险，需要手动验证
            # url: https://safe.jd.com/dangerousVerify/index.action?username=...
            res = json.loads(response.text)
            if not response.headers.get('p3p'):
                if 'url' in res:
                    print(f"需要手动安全验证: {res['url']}")
                    return False
                else:
                    print(res)
                    print('登录失败!!')
                    return False

            # login succeed
            self.headers['P3P'] = response.headers.get('P3P')
            self.cookies.update(response.cookies)
            session.cookies = response.cookies
             # 保存cookie
            with open('cookie', 'wb') as f:
                pickle.dump(self.cookies, f)
            return True

        except Exception as e:
            print(e)
            raise

flag = 1
spider = JDSpider()
while (1):
    try:
        if flag == 1:
            validate_cookies()
            getUsername()
        checkSession = requests.Session()
        checkSession.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Connection": "keep-alive"
        }
        logger.info('第' + str(flag) + '次 ')
        flag += 1
        inStockSkuid = check_stock()
        for skuId in inStockSkuid:
            if item_removed(skuId):
                logger.info('[%s]类型口罩有货啦!马上下单', skuId)
                skuidUrl = 'https://item.jd.com/' + skuId + '.html'
                if buyMask(skuId):
                    sendMail(mail, skuidUrl, True)
                    sys.exit(1)
                else:
                    sendMail(mail, skuidUrl, False)
            else:
                logger.info('[%s]类型口罩有货，但已下柜商品', skuId)

        time.sleep(timesleep)
        if flag % 20 == 0:
            logger.info('校验是否还在登录')
            validate_cookies()
    except Exception as e:
        import traceback

        print(traceback.format_exc())
        time.sleep(10)
