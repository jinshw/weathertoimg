import requests
import hashlib
import time, datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import logging
import math
# import matplotlib.pyplot as plt
# import matplotlib

import matplotlib

matplotlib.use('Agg')
from matplotlib import pyplot as plt
import matplotlib as mpl
import configparser
import pymysql

config = configparser.ConfigParser()
config.read('config.ini')
token = config["DEFAULT"]["token"]
password = config["DEFAULT"]["password"]
nonce = config["DEFAULT"]["nonce"]
schedulerInterval = config["scheduler"]["interval"]
schedulerCrontype = config["scheduler"]["crontype"]

rain_2h_url = config["raian2h"]["rain_2h_url"]
rain_2h_suburl = config["raian2h"]["rain_2h_suburl"]
cldasreal_url = config["cldasreal"]["cldasreal_url"]
cldasreal_suburl = config["cldasreal"]["cldasreal_suburl"]
ec_forecast_url = config["ec_forecast"]["ec_forecast_url"]
ec_forecast_suburl = config["ec_forecast"]["ec_forecast_suburl"]

aPoint = [34.2708359516, 73.4655761719]
bPoint = [39.2708359516, 80.4655761719]
cPoint = [44.2708359516, 87.4655761719]
dPoint = [49.2678045506, 96.4599609375]
ePoint = [aPoint[0], cPoint[1]]
fPoint = [bPoint[0], dPoint[1]]
gPoint = [cPoint[0], aPoint[1]]
hPoint = [dPoint[0], bPoint[1]]

requestPoints = [
    {
        "_northEast": {"lat": bPoint[0], "lng": bPoint[1]},
        "_southWest": {"lat": aPoint[0], "lng": aPoint[1]}
    },
    {
        "_northEast": {"lat": cPoint[0], "lng": cPoint[1]},
        "_southWest": {"lat": bPoint[0], "lng": bPoint[1]}
    },
    {
        "_northEast": {"lat": dPoint[0], "lng": dPoint[1]},
        "_southWest": {"lat": cPoint[0], "lng": cPoint[1]}
    },

    {
        "_northEast": {"lat": fPoint[0], "lng": fPoint[1]},
        "_southWest": {"lat": ePoint[0], "lng": ePoint[1]}
    },
    {
        "_northEast": {"lat": fPoint[0], "lng": fPoint[1]},
        "_southWest": {"lat": cPoint[0], "lng": cPoint[1]}
    },
    {
        "_northEast": {"lat": ePoint[0], "lng": ePoint[1]},
        "_southWest": {"lat": bPoint[0], "lng": bPoint[1]}
    },

    {
        "_northEast": {"lat": hPoint[0], "lng": hPoint[1]},
        "_southWest": {"lat": gPoint[0], "lng": gPoint[1]}
    },
    {
        "_northEast": {"lat": hPoint[0], "lng": hPoint[1]},
        "_southWest": {"lat": cPoint[0], "lng": cPoint[1]}
    },
    {
        "_northEast": {"lat": gPoint[0], "lng": gPoint[1]},
        "_southWest": {"lat": bPoint[0], "lng": bPoint[1]}
    }
]

# token = "6072fd75f85c5632df9830c956d791b5"
# password = "e346ef0472828e1182dafe8d0835e749"
# nonce = "41f46b99497d46d4910baaa0e9b120d2"
# rain_2h_url = "http://hydrometeo.mojicb.com/v1/radar/rain/full/json"
# rain_2h_suburl = "/v1/radar/rain/full/json"


# 配置日志记录信息，日志文件在当前路径，文件名为 “log1.txt”
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='log1.txt',
                    filemode='a')
# 打开数据库连接
host = config["mysql"]["host"]
post = config["mysql"]["post"]
username = config["mysql"]["username"]
dbpassword = config["mysql"]["password"]
dbname = config["mysql"]["dbname"]


class WeatherType:
    type = ""
    states = ""
    interval = 0
    values = []

    def __init__(self, states, values):
        """
        初始化函数
        :param states: rain2h,cldasreal,ec_forecast等
        """
        self.states = states
        self.values = values

    def getSQLField(self):
        """
        :return:返回type字段
        """
        fieldType = ""
        if self.states == "rain2h":
            fieldType = "2"
        elif self.states == "cldasreal":
            fieldType = "3"
        elif self.states == "ec_forecast":
            fieldType = "4"
        return fieldType

    def getColors(self):
        colors = {}
        if self.states == "rain2h":
            colors = {
                "colors": ['none', '#A3F589', '#39AA00', '#62BAFF', '#0001FB'],
                "bounds": [0, 0.1, 10, 25, 50, 100]
            }
        elif self.states == "ec_forecast":  # 7day 未来7天
            #  value: (gridItem.value - 15.97) * 1000 // 格点未来7天预报接口返回降雨量单位为米，转为毫米(偏移量15.97)
            colors = {
                "colors": ['none', '#7fffff', '#23B7FF', '#0078B4', '#0C28AB', '#BF6BFB', '#500486'],
                "bounds": [0, 15.9701, 15.98, 15.995, 16.02, 16.07, 16.22, 16.97]
            }
            # colors = {
            #     "colors": ['none', '#7fffff', '#23B7FF', '#0078B4', '#0C28AB', '#BF6BFB', '#500486'],
            #     "bounds": [0, 0.1, 10, 25, 50, 100, 250, 1000]
            # }
        elif self.states == "cldasreal":  # livedatas 实时降水
            # 实况接口返回降雨量单位为米，转为毫米 需要*1000
            colors = {
                "colors": ['none', '#CDFFFF', '#23FFFC', '#23B7FF', '#0078B4', '#0051CA', '#092FD1', "#4C0669",
                           "#6A059F", "#4C0669"],
                "bounds": [0, 0.0001, 0.001, 0.002, 0.003, 0.006, 0.008, 0.01, 0.02, 0.05, 1]
            }
            # colors = {
            #     "colors": ['none', '#CDFFFF', '#23FFFC', '#23B7FF', '#0078B4', '#0051CA', '#092FD1', "#4C0669",
            #                "#6A059F", "#4C0669"],
            #     "bounds": [0, 0.1, 1, 2, 3, 6, 8, 10, 20, 50, 1000]
            # }
        return colors

    def getValues(self):
        """
        气象接口返回的数据统一单位为毫米
        :return:
        """
        _rvals = []
        if self.states == "rain2h":
            _rvals = self.values
        elif self.states == "cldasreal":  # 实况接口返回降雨量单位为米，转为毫米
            _rvals = self.values * 1000
        elif self.states == "ec_forecast":  # 格点未来7天预报接口返回降雨量单位为米，转为毫米(偏移量15.97)
            _rvals = (self.values - 15.97) * 1000
        return _rvals


def printMsg(msg):
    now = datetime.datetime.now()
    ts = now.strftime('%Y-%m-%d %H:%M:%S')
    print(msg, ts)


def getSignature(map):
    signature = map["password"] + "\n" + map["date"] + "\n" + map["nonce"] + "\n" + map["suburl"]
    # 处理中文字符
    # print(hashlib.md5('加密'.encode(encoding='UTF-8')).hexdigest())
    m = hashlib.md5()
    m.update(signature.encode("utf8"))
    md5 = m.hexdigest()
    return md5


def datasToImgs(datas, index, type, interval):
    """
    气象数据转换成图片
    :param datas: 气象数据矩阵数组
    :param index: 执行坐标点下标
    :param type: 类型：rain2h,cldasreal,ec_forecast等
    :return:
    """
    code = datas["code"]
    msg = datas["msg"]
    if code == 200:
        data = datas["data"]
        startLon = data["startLon"]
        startLat = data["startLat"]
        endLon = data["endLon"]
        endLat = data["endLat"]
        rows = data["rows"]
        cols = data["cols"]
        values = data["values"]
        weatherType = WeatherType(type, values)
        # values = weatherType.getValues()

        # colors = ['none', '#A3F589', '#39AA00', '#62BAFF', '#0001FB']
        # bounds = [0, 0.1, 10, 25, 50, 100]
        colorsbounds = weatherType.getColors()
        colors = colorsbounds["colors"]
        bounds = colorsbounds["bounds"]
        cmap = mpl.colors.ListedColormap(colors)
        norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
        im = plt.imshow(values, interpolation='none', cmap=cmap, norm=norm, alpha=0.8)

        ax = plt.gca()
        # x轴方向调整：
        ax.xaxis.set_ticks_position('top')  # 将x轴的位置设置在顶部
        # ax.invert_xaxis()  # x轴反向
        # y轴方向调整：
        ax.yaxis.set_ticks_position('left')  # 将y轴的位置设置在右边
        # ax.invert_yaxis()  # y轴反向

        plt.axis('off')  # 去掉坐标轴

        fig = plt.gcf()
        fig.set_size_inches(rows / 100, cols / 100)

        # plt.gca().xaxis.set_major_locator(plt.NullLocator())
        # plt.gca().yaxis.set_major_locator(plt.NullLocator())
        # plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        # plt.margins(0, 0)
        # imgName = "rain2h" + "[" + str(startLat) + "," + str(startLon) + "," + str(endLat) + "," + str(endLon) + "]"
        imgName = type + "_" + str(interval) + "_" + str(index)
        plt.savefig(imgName + ".png", dpi=100, transparent=True, alpha=0.8, pad_inches=0, bbox_inches='tight')
        # plt.show()
        plt.close()

        # conn = pymysql.connect(host,int(post), username, dbpassword, dbname)
        conn = pymysql.connect(host=host, port=int(post), user=username, password=dbpassword, db=dbname)
        cursorInsert = conn.cursor()

        fieldType = weatherType.getSQLField()
        insertSQL = "insert into weather_img(type,pointtime,pointunit,imgname,startlat,startlon,endlat,endlon,createtime) values (" + fieldType + "," + str(
            interval) + ",'d','" + imgName + "','" + str(
            startLat) + "','" + str(startLon) + "','" + str(endLat) + "','" + str(endLon) + "',SYSDATE())"
        cursorInsert.execute(insertSQL)
        conn.commit()
        cursorInsert.close()
        conn.close()
    else:
        print("接口返回code=" + str(code) + " msg=" + msg)


def getRain2H():
    """
    未来2小时内降水
    :return:
    """
    printMsg('2小时内降水getRain2H--start :')

    for index, item in enumerate(requestPoints):
        request_param = {
            "startLat": item["_northEast"]["lat"],
            "startLon": item["_northEast"]["lng"],
            "endLat": item["_southWest"]["lat"],
            "endLon": item["_southWest"]["lng"]
        }

        # request_param = {
        #     "startLat": "41.572265625",
        #     "startLon": "81.903076171875",
        #     "endLat": "40.241546630859375",
        #     "endLon": "80.08621215820312"
        # }
        now_milli_time = str(int(time.time() * 1000))
        # now_milli_time = "1571038854655"
        map = {"password": password, "date": now_milli_time, "nonce": nonce, "suburl": rain_2h_suburl}
        signature = getSignature(map)

        headers = {
            "X-AC-Token": token,
            "X-Date": now_milli_time,
            "X-AC-Nonce": nonce,
            "X-AC-Signature": signature
        }

        response = requests.get(rain_2h_url, params=request_param, headers=headers)
        datas = response.json()
        # print(datas)
        datasToImgs(datas, index, "rain2h", 0)

    printMsg('2小时内降水getRain2H--end :')


def getCldasreal():
    """
    实况降水
    :return:
    """
    # now = datetime.datetime.now()
    # ts = now.strftime('%Y-%m-%d %H:%M:%S')
    printMsg('实况降水getCldasreal--start :')

    elem = "RAIN"
    for index, item in enumerate(requestPoints):
        request_param = {
            "startLat": item["_northEast"]["lat"],
            "startLon": item["_northEast"]["lng"],
            "endLat": item["_southWest"]["lat"],
            "endLon": item["_southWest"]["lng"],
            "elem": elem
        }

        now_milli_time = str(int(time.time() * 1000))
        map = {"password": password, "date": now_milli_time, "nonce": nonce, "suburl": cldasreal_suburl}
        signature = getSignature(map)

        headers = {
            "X-AC-Token": token,
            "X-Date": now_milli_time,
            "X-AC-Nonce": nonce,
            "X-AC-Signature": signature
        }

        response = requests.get(cldasreal_url, params=request_param, headers=headers)
        datas = response.json()
        # print(datas)
        datasToImgs(datas, index, "cldasreal", 0)

    printMsg('实况降水getCldasreal--end :')


def get7Days():
    """
    获取系统当前时间之后的7天时间
    :return: 7天后时间数组
    """
    daysArr = []
    now_time = datetime.datetime.now()
    oneDay = now_time + datetime.timedelta(days=1)
    for index in range(0, 7):
        oneDay = now_time + datetime.timedelta(days=index)
        oneDayStr = oneDay.strftime('%Y-%m-%d %H:%M:%S')
        daysArr.append(oneDayStr)
    return daysArr


def getEcForecast():
    """
    未来7天降水
    :return:
    """
    printMsg('未来7天降水getEcForecast--start :')
    elem = "RAIN"
    days = get7Days()
    for i, daystr in enumerate(days):
        forecastTime = daystr
        for index, item in enumerate(requestPoints):
            request_param = {
                "startLat": item["_northEast"]["lat"],
                "startLon": item["_northEast"]["lng"],
                "endLat": item["_southWest"]["lat"],
                "endLon": item["_southWest"]["lng"],
                "elem": elem,
                "forecastTime": forecastTime
            }

            now_milli_time = str(int(time.time() * 1000))
            map = {"password": password, "date": now_milli_time, "nonce": nonce, "suburl": ec_forecast_suburl}
            signature = getSignature(map)

            headers = {
                "X-AC-Token": token,
                "X-Date": now_milli_time,
                "X-AC-Nonce": nonce,
                "X-AC-Signature": signature
            }

            response = requests.get(ec_forecast_url, params=request_param, headers=headers)
            datas = response.json()
            # print(datas)
            datasToImgs(datas, index, "ec_forecast", i + 1)

    printMsg('未来7天降水getEcForecast--end :')


def getWeather():
    """
    获取气象函数
    :return:
    """
    printMsg('========定时任务开始========')

    getRain2H()
    getCldasreal()
    getEcForecast()

    printMsg('========定时任务结束========')
    print("************************************************")


def my_listener(event):
    if event.exception:
        print('任务出错了！！！！！！')
    else:
        print('任务照常运行...')


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    cronStr = "*/" + schedulerInterval
    if schedulerCrontype == "second":
        trigger = CronTrigger(second=cronStr)
    elif schedulerCrontype == "minute":
        trigger = CronTrigger(minute=cronStr)
    # trigger = CronTrigger(second='*/3')
    # trigger = CronTrigger(minute='*/1')
    scheduler.add_job(getWeather, trigger)
    # scheduler.add_job(getRain2H, 'cron', minute='*/5', hour='*')
    scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    scheduler._logger = logging  # 行启用 scheduler 模块的日记记录
    scheduler.daemon = True
    try:
        scheduler.start()
    except Exception as e:
        print("scheduler启动异常=" + e)
