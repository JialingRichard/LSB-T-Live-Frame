from threading import Thread
import time
from flvConstant import *
import math


class StatusMonitor():
    starttime = 0

    _downloadspeed = 0  # 单位mbps
    _processSpeed = 0  # 单位mbps

    downloadspeed = 0  # 单位mbps
    processSpeed = 0  # 单位mbps

    downloadedbyte = 0
    wrotefilebyte = 0

    downloadspeedavg = 0  # 单位mbps
    processSpeedavg = 0  # 单位mbps

    videoduration = 0  # 最新pts 单位ms

    videotagcount = 0
    audiotagcount = 0
    scripttagcount = 0

    _videotagspeed = 0
    _audiotagspeed = 0

    videotagspeed = 0
    audiotagspeed = 0

    videotagspeedavg = 0
    audiotagspeedavg = 0

    videoframegapavg = 0
    audioframegapavg = 0

    lastvideotimestamp = 0
    lastaudiotimestamp = 0

    videotagstarttimestamp = -1
    audiotagstarttimestamp = -1

    videoBitrates = 0

    stopFlag = False

    connectionclosed = False

    rawObj = None

    def init(self):
        self.starttime = time.perf_counter()

        def _init():
            while 1:
                if self.stopFlag or self.connectionclosed:
                    break

                self.downloadspeed = round(self._downloadspeed, 2)  # 单位mbps
                self.processSpeed = round(self._downloadspeed, 2)  # 单位mbps

                self.videotagspeed = round(self._videotagspeed, 2)
                self.audiotagspeed = round(self._audiotagspeed, 2)

                self._videotagspeed = 0
                self._audiotagspeed = 0

                self._downloadspeed = 0
                self._processSpeed = 0

                self.downloadspeedavg = round(self.downloadedbyte /
                                              (time.perf_counter() - self.starttime) / 1024 / 1024 * 8, 2)
                self.processSpeedavg = round(self.wrotefilebyte /
                                             (time.perf_counter() - self.starttime) / 1024 / 1024 * 8, 2)

                self.videotagspeedavg = round(self.videotagcount /
                                              (time.perf_counter() - self.starttime), 2)
                self.audiotagspeedavg = round(self.audiotagcount /
                                              (time.perf_counter() - self.starttime), 2)

                time.sleep(1)
        Thread(target=_init).start()

    def addDownloadByte(self, size):
        self.downloadedbyte += size
        self._downloadspeed += size / 1024 / 1024 * 8

    def addWroteByte(self, size):
        self.wrotefilebyte += size
        self._processSpeed += size / 1024 / 1024 * 8

    def addTag(self, tagtype, tagtimestamp):

        if tagtype == TagType.FLV_TAG_VIDEO.value:
            if self.lastvideotimestamp == 0:
                self.videotagstarttimestamp = tagtimestamp
            elif self.lastvideotimestamp > 0:
                self.videoframegapavg = math.ceil((
                    self.lastvideotimestamp + tagtimestamp) / 2)

            self.videoduration = tagtimestamp
            self.lastvideotimestamp = tagtimestamp
            self.videotagcount += 1
            self._videotagspeed += 1
        elif tagtype == TagType.FLV_TAG_AUDIO.value:
            if self.lastaudiotimestamp == 0:
                self.audiotagstarttimestamp = tagtimestamp
            elif self.lastaudiotimestamp > 0:
                self.audioframegapavg = math.ceil((
                    self.lastaudiotimestamp - tagtimestamp) / 2)

            self.lastaudiotimestamp = tagtimestamp
            self.audiotagcount += 1
            self._audiotagspeed += 1
        elif tagtype == TagType.FLV_TAG_SCRIPT.value:
            self.scripttagcount += 1

    def stopRecorder(self):
        self.stopFlag = True
        self.rawObj.close()
