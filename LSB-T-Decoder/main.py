from flvParser import Flv, packScriptDataECMAArray, packScriptDataValue, ScriptTag
import requests
from monitor import StatusMonitor
from threading import Thread
import time
from HttpRequset import req
import json
import signal
import sys
import os
from flv_image_player import play
import threading
import subprocess
import multiprocessing
def getLiveStreamUrl(roomid, qn=10000):
    url = f"https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo?room_id={roomid}&protocol=0,1&format=0,1,2&codec=0,1&qn={qn}&platform=web&ptype=8"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": "https://live.bilibili.com",
        "Referer": "https://live.bilibili.com/"}
    js = json.loads(req(url, header=header)[0])

    if js['code'] != 0:
        raise Exception(js['message'])
    if not js['data']['live_status']:
        raise Exception("主播未开播或已下播")
    for s in js['data']['playurl_info']['playurl']['stream']:
        if s['protocol_name'] == 'http_stream':
            for f in s['format']:
                if f['format_name'] == 'flv':
                    host = f['codec'][0]['url_info'][0]['host']
                    extra = f['codec'][0]['url_info'][0]['extra']
                    base_url = f['codec'][0]['base_url']
                    return host + base_url + extra


def startFlvStreamParse(url, statusMonitor, fileIO):
    def task():
        f = Flv()
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36", "Origin": "https://live.bilibili.com",
            "Referer": "https://live.bilibili.com/"}
        r = requests.get(url, headers=header, stream=True)
        if r.status_code == 200:
            f.parseStream(r.raw, statusMonitor, fileIO)
        else:
            raise Exception(f"错误的响应代码{r.status_code}")
    Thread(target=task).start()


def startRecorder(roomID, qn):
    def beforeExit(signum, frame):
        statusMonitor.stopRecorder()
    signal.signal(signal.SIGINT, beforeExit)
    signal.signal(signal.SIGTERM, beforeExit)

    statusMonitor = StatusMonitor()
    url = getLiveStreamUrl(roomID, qn)
    print("url:"+url)
    rootpath = os.path.abspath(os.path.dirname(__file__))
    if not os.path.exists(f'{rootpath}/recorder/'):
        os.mkdir(f'{rootpath}/recorder/')
    if not os.path.exists(f'{rootpath}/recorder/{roomID}'):
        os.mkdir(f'{rootpath}/recorder/{roomID}')

    temp_time = round(time.time())
    fileIO = open(
        f'{rootpath}/recorder/{roomID}/{temp_time}.flv', "wb")
    file_location = "recorder/"+roomID+"/"+str(temp_time)+".flv"
    print("file location:",file_location)


    # target:指定进程执行的函数名，不加括号
    # args:使用元组方式给指定任务传参，顺序一致(参数顺序)
    # kwargs:使用字典的方式给指定任务传参，名称一致(参数名称)
    play_process = multiprocessing.Process(target=play, kwargs={"location":file_location})
    # dance_process = multiprocessing.Process(target=dance, kwargs={"name": "珊珊", "num": 2})

    # 3. 使用进程对象启动进程执行指定任务
    play_process.start()


    # thread_play_flv = threading.Thread(target=play(location=file_location))
    # thread_play_flv.start()
    # thread_play_flv.join()


    startFlvStreamParse(url, statusMonitor, fileIO)

    while 1:
        if statusMonitor.stopFlag:
            print("直播录制停止中...")
            break
        if statusMonitor.connectionclosed:
            print("连接中断，已停止录制...")
            break
        print(
            f"平均下载速度{statusMonitor.downloadspeedavg} 瞬时下载速度{statusMonitor.downloadspeed}")
        print(
            f"已写入数据量{statusMonitor.wrotefilebyte}bytes 瞬时帧率{statusMonitor.videotagspeed}")

        time.sleep(1)


if __name__ == "__main__":

    args = sys.argv
    if len(args) == 3:
        roomID = args[1]
        qn = args[2]
    elif len(args) == 2:
        roomID = args[1]
        qn = 10000
    else:
        print("用法 main.py 房间ID [qn数值(默认10000即原画)]")
        exit()

    startRecorder(roomID, qn)
