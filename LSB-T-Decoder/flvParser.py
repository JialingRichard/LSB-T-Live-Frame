#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# 参考文章 https://stackoverflow.com/questions/22340265/python-download-file-using-requests-directly-to-memory
# https://stackoverflow.com/questions/21715298/python-requests-return-file-like-object-for-streaming
# https://zhuanlan.zhihu.com/p/33288426
# https://docs.python-requests.org/en/latest/api/#requests.Response.raw
# https://stackoverflow.com/questions/22340265/python-download-file-using-requests-directly-to-memory
# https://urllib3.readthedocs.io/en/latest/reference/urllib3.response.html#urllib3.response.HTTPResponse
import cv2


import struct
from threading import Thread
from simplebuffer import BytesBuffer
from flvConstant import *
from monitor import StatusMonitor
"""flv文件解析，元数据解析采用amf0格式"""


class UnSupportFileFormat(Exception):
    pass


class UnSupportAmfValFormat(Exception):
    pass


class Tag(object):
    """flv文件头"""
    previousTagsSize = 0
    type = 0
    length = 0
    timestamp = 0
    exTimestamp = 0
    pts = 0  # exTimestamp+timestamp的结果
    streamsId = 0
    # 原始数据
    headerdata = []  # 11字节header
    bodydata = []

    def parseTagheader(self, data):
        self.type = data[0]
        self.length = bytes2int(data[1:4])
        self.previousTagsSize = self.length + 11
        self.timestamp = bytes2int(data[4:7])
        self.exTimestamp = bytes2int(data[7:8])
        self.pts = bytes2int(
            data[7:8] + data[4:7])
        self.streamsId = bytes2int(data[8:11])
        # 11字节header
        self.headerdata = data

    def parse(self):
        """请子类实现此方法来解析原始数据"""
        pass

    def __str__(self):
        """like tostring"""
        return "%s previousTagsSize:%d type:%d length:%d timestamp:%d exTimestamp:%d streamsId:%d" % (
            self.__class__, self.previousTagsSize, self.type, self.length, self.timestamp, self.exTimestamp,
            self.streamsId)

    def getBytes(self):
        """获取原始字节数据"""
        return self.bodydata

    def write(self, fileIO):
        """写入tag数据到文件中（含previousTagSize数据）"""
        fileIO.write(packTagHeader(self))
        fileIO.write(self.bodydata)
        fileIO.write(int.to_bytes(self.previousTagsSize, 4, 'big'))
        return self.previousTagsSize + 4


class AudioTag(Tag):
    """音频tag"""
    format = None
    samplerate = None
    bits = 0
    sc = 0
    __flag = None
    __data = []

    def parse(self):
        data = super().getBytes()
        if len(data) != 0:
            self.__flag = data[0]
            self.__data = data[1:]
            # 前面4位为音频格式
            self.format = self.__flag >> 4
            # 5 6位是采样率 0000 0011&0010 1011= 0000 0011=3
            self.samplerate = (0x03 & self.__flag >> 2)
            # 7 位是采样长度 0 8bit 1 16bits
            self.bits = (self.__flag >> 1 & 0x01)
            # 单声道还是双声道 0单声道 1立体声
            self.sc = (self.__flag & 0x01)
        return self

    def getBytes(self):
        """获取字节数据"""
        return self.__data


# end of class AudioTag
class VideoTag(Tag):
    """视频tag"""
    frameType = None
    codec = None
    __flag = None
    __data = []

    def parse(self):
        """解析视频tag信息"""
        data = super().getBytes()
        if len(data) != 0:
            self.__flag = data[0]
            self.__data = data[1:]
            # 前4位为帧类型
            self.frameType = (self.__flag >> 4)
            # 后4位位编码类型（发现python左偏移貌似有些问题,不会自动补位，所以不能用左偏移）
            self.codec = (self.__flag & 0x0f)
        return self

    def getBytes(self):
        """获取字节数据"""
        return self.__data


# end of class VideoTag
class ScriptTag(Tag):
    """
        script tag 简介 https: // blog.csdn.net / heyatzw / article / details / 74276813
        脚本数据也称元数据metadata，解析起来稍微有点麻烦
        amf0可以查看:
        https: // wwwimages2.adobe.com / content / dam / acom / en / devnet / pdf / amf0 - file - format - specification.pdf
    """
    """
    一般情况下Data由2个AMF包组成第一个为String类型(onMetadata)，第二个为ECMA arry(8)或Object(3)，主要装载音视频相关参数信息
    用到的变量是 strVal(2) objVal(3) arrVal(8)
    """
    numVal = 0
    strVal, lStrVal = "", ""
    objVal = []
    arrVal = {}
    boolVal = False
    nullVal, dateVal = None, None

    def parse(self):
        """解析脚本元meta数据"""
        data = bytes(super().getBytes())
        size = len(data)
        while size > 0:
            _type = data[0]
            data, size = data[1:], size - 1
            if _type == Amf0DataType.FLV_AMF0_NUMBER.value:
                data, size, self.numVal = self.__parse_number(data, size)
            elif _type == Amf0DataType.FLV_AMF0_BOOLEAN.value:
                data, size, self.boolVal = self.__parse_boolean(data, size)
            elif _type == Amf0DataType.FLV_AMF0_STRING.value:
                data, size, self.strVal = self.__parse_string(data, size)
            elif _type == Amf0DataType.FLV_AMF0_NULL.value:
                data, size, self.nullVal = self.__parse_null(data, size)
            elif _type == Amf0DataType.FLV_AMF0_OBJECT.value:
                data, size, self.objVal = self.__parse_object(data, size)
            elif _type == Amf0DataType.FLV_AMF0_DATE.value:
                data, size, self.dateVal = self.__parse_date(data, size)
            elif _type == Amf0DataType.FLV_AMF0_ARRAY.value:
                data, size, self.arrVal = self.__parse_array(data, size)
            elif _type == Amf0DataType.FLV_AMF0_STRICT_ARRAY.value:
                data, size, self.arrVal = self.__parse_strict_array(data, size)
            elif _type == Amf0DataType.FLV_AMF0_LONG_STRING.value:
                data, size, self.lStrVal = self.__parse_long_string(data, size)
            else:
                raise UnSupportAmfValFormat(_type)

        assert size == 0
        return self

    def write(self, fileIO):
        self.bodydata = packScriptTagData(self)
        self.previousTagsSize = len(self.bodydata) + 11
        fileIO.write(packTagHeader(self))
        fileIO.write(self.bodydata)
        fileIO.write(int.to_bytes(self.previousTagsSize, 4, 'big'))
        return self.previousTagsSize + 4

    def __parse_number(self, data, size):
        # 利用struct来处理double
        ret = struct.unpack('>d', data[:8])[0]
        return data[8:], size - 8, ret

    def __parse_boolean(self, data, size):
        """解析boolean值"""
        ret = False
        if int(data[0]) != 0:
            ret = True
        return data[1:], size - 1, ret

    def __parse_null(self, data, size):
        """解析null值"""
        return data[1:], size - 1, None

    def __parse_string(self, data, size):
        """解析string值(2字节的长度 + N字符串)"""
        offset = bytes2int(data[:2])
        offset += 2
        ret = bytes.decode(data[2:offset])
        return data[offset:], size - offset, ret

    def __parse_long_string(self, data, size):
        """解析string值(4字节的长度 + N字符串)"""
        offset = bytes2int(data[:4])
        offset += 4
        ret = bytes.decode(data[4:offset])
        return data[offset:], size - offset, ret

    def __parse_date(self, data, size):
        """解析data值(8字节的时间戳 + 2字节的时区), 返回一个dict"""
        time = struct.unpack('>d', data[:8])[0]
        zone = struct.unpack('>h', data[8:10])[0]
        return data[10:], size - 10, {"time": time, "zone": zone}

    def __parse_array(self, data, size):
        """ecma解析, 实际是map数据"""
        arrLen = bytes2int(data[:4])
        arrVal = None
        data, size, arrVal = self.__parse_object(data[4:], size - 4)
        return data, size, {"len": arrLen, "val": arrVal}

    def __parse_strict_array(self, data, size):
        """strict解析array, strict数组是没有key的"""
        alen = bytes2int(data[:4])
        ret = []
        tmp = None
        data, size = data[4:], size - 4
        while size > 0:
            size -= 1
            # if data[0] == Amf0DataType.FLV_AMF0_END_OF_OBJECT.value:
            #     data = data[1:]
            #     break
            if data[0] == Amf0DataType.FLV_AMF0_NUMBER.value:
                data, size, tmp = self.__parse_number(data[1:], size)
                ret.append(tmp)
            elif data[0] == Amf0DataType.FLV_AMF0_BOOLEAN.value:
                data, size, tmp = self.__parse_boolean(data[1:], size)
                ret.append(tmp)
            elif data[0] == Amf0DataType.FLV_AMF0_STRING.value:
                data, size, tmp = self.__parse_string(data[1:], size)
                ret.append(tmp)
            elif data[0] == Amf0DataType.FLV_AMF0_NULL.value:
                data, size, tmp = self.__parse_null(data[1:], size)
                ret.append(tmp)
            elif data[0] == Amf0DataType.FLV_AMF0_OBJECT.value:
                data, size, tmp = self.__parse_object(data[1:], size)
                ret.append(tmp)
            elif data[0] == Amf0DataType.FLV_AMF0_DATE.value:
                data, size, tmp = self.__parse_date(data[1:], size)
                ret.append(tmp)
            elif data[0] == Amf0DataType.FLV_AMF0_ARRAY.value:
                data, size, tmp = self.__parse_array(data[1:], size)
                ret.append(tmp)
            elif data[0] == Amf0DataType.FLV_AMF0_STRICT_ARRAY.value:
                data, size, tmp = self.__parse_strict_array(data[1:], size)
                ret.append(tmp)
            elif data[0] == Amf0DataType.FLV_AMF0_LONG_STRING.value:
                data, size, tmp = self.__parse_long_string(data[1:], size)
                ret.append(tmp)
            if len(ret) == alen:
                break
        return data, size, ret

    def __parse_object(self, data, size):
        """解析object信息，object由一组[key + value], 其中value可以是object来嵌套使用"""
        ret = dict()

        while size > 0:

            if data[0] == Amf0DataType.FLV_AMF0_END_OF_OBJECT.value:
                data = data[1:]
                # size -= 1 # 错误，已经在下面减了1
                break

            # 获取key的长度
            keyLen = bytes2int(data[:2])
            keyLen += 2
            keyVal = bytes.decode(data[2:keyLen])
            # 此处 -1 为减去data[0]的1个字节的大小，因为data[1:]没有减一，在此处处理
            data, size = data[keyLen:], size - keyLen - 1

            # 判断object-value类型
            if data[0] == Amf0DataType.FLV_AMF0_NUMBER.value:
                data, size, ret[keyVal] = self.__parse_number(data[1:], size)
            elif data[0] == Amf0DataType.FLV_AMF0_BOOLEAN.value:
                data, size, ret[keyVal] = self.__parse_boolean(data[1:], size)
            elif data[0] == Amf0DataType.FLV_AMF0_STRING.value:
                data, size, ret[keyVal] = self.__parse_string(data[1:], size)
            elif data[0] == Amf0DataType.FLV_AMF0_NULL.value:
                data, size, ret[keyVal] = self.__parse_null(data[1:], size)
            elif data[0] == Amf0DataType.FLV_AMF0_OBJECT.value:
                data, size, ret[keyVal] = self.__parse_object(data[1:], size)
            elif data[0] == Amf0DataType.FLV_AMF0_DATE.value:
                data, size, ret[keyVal] = self.__parse_date(data[1:], size)
            elif data[0] == Amf0DataType.FLV_AMF0_ARRAY.value:
                data, size, ret[keyVal] = self.__parse_array(data[1:], size)
            elif data[0] == Amf0DataType.FLV_AMF0_STRICT_ARRAY.value:
                data, size, ret[keyVal] = self.__parse_strict_array(
                    data[1:], size)
            elif data[0] == Amf0DataType.FLV_AMF0_LONG_STRING.value:
                data, size, ret[keyVal] = self.__parse_long_string(
                    data[1:], size)

        return data, size, ret


class OtherTag(Tag):
    """其他标签不予处理"""

    def parse(self):
        """获取字节数据, 这部分暂不处理"""
        return self


def bytes2int(data):
    """字节转换为int"""
    return int.from_bytes(data, byteorder="big")


def packTagHeader(tag: Tag):
    """打包tagheader数据为bytes"""
    headerbyte = int.to_bytes(tag.type, 1, 'big')
    headerbyte += int.to_bytes(tag.length, 3, 'big')
    headerbyte += int.to_bytes(tag.timestamp, 3, 'big')
    headerbyte += int.to_bytes(tag.exTimestamp, 1, 'big')
    headerbyte += int.to_bytes(tag.streamsId, 3, 'big')
    return headerbyte


def packScriptDataECMAArray(array):
    array = array['val']
    amfbyte = bytearray()
    amfbyte += int.to_bytes(Amf0DataType.FLV_AMF0_ARRAY.value, 1, 'big')
    amfbyte += int.to_bytes(len(array), 4, 'big')
    for key in array:
        # ECMA array 的 key 默认为文本类型
        amfbyte += int.to_bytes(len(key), 2, 'big')
        amfbyte += str.encode(key)
        # 写value
        amfbyte += packScriptDataValue(array[key])
    # 结束符号
    amfbyte += int.to_bytes(0, 2, 'big')
    amfbyte += int.to_bytes(Amf0DataType.FLV_AMF0_END_OF_OBJECT.value, 1, 'big')
    return bytes(amfbyte)


def packScriptDataObject(obj):
    amfbyte = bytearray()
    amfbyte += int.to_bytes(
        Amf0DataType.FLV_AMF0_OBJECT.value, 1, 'big')
    for key in obj:
        # key 默认为文本类型
        amfbyte += int.to_bytes(len(key), 2, 'big')
        amfbyte += str.encode(key)
        amfbyte += packScriptDataValue(obj[key])
    # 结束符号
    amfbyte += int.to_bytes(0, 2, 'big')
    amfbyte += int.to_bytes(Amf0DataType.FLV_AMF0_END_OF_OBJECT.value, 1, 'big')
    return bytes(amfbyte)


def packScriptDataValue(value):
    scriptDataValueBytes = bytearray()
    if type(value) == float or type(value) == int:
        # Amf0DataType.FLV_AMF0_NUMBER.value = 0
        scriptDataValueBytes += int.to_bytes(0, 1, 'big')
        scriptDataValueBytes += struct.pack(">d", value)
    elif type(value) == str:
        if len(value) > 65535:
            # Amf0DataType.FLV_AMF0_LONG_STRING.value = 12
            scriptDataValueBytes += int.to_bytes(12, 1, 'big')
            scriptDataValueBytes += int.to_bytes(len(value), 4, 'big')
            scriptDataValueBytes += str.encode(value)
        else:
            # Amf0DataType.FLV_AMF0_STRING.value = 2
            scriptDataValueBytes += int.to_bytes(2, 1, 'big')
            scriptDataValueBytes += int.to_bytes(len(value), 2, 'big')
            scriptDataValueBytes += str.encode(value)
    elif type(value) == list:
        # Amf0DataType.FLV_AMF0_STRICT_ARRAY.value = 10
        scriptDataValueBytes += int.to_bytes(10, 1, 'big')
        scriptDataValueBytes += int.to_bytes(len(value), 4, 'big')
        # scriptDataValueBytes += b''.join(list(map(packScriptDataValue, value)))
        for v in value:
            scriptDataValueBytes += packScriptDataValue(v)
    elif type(value) == dict:
        if len(value) == 2 and 'time' in value and 'zone' in value:
            # date类型 Amf0DataType.FLV_AMF0_DATE.value = 11
            scriptDataValueBytes += int.to_bytes(11, 1, 'big')
            scriptDataValueBytes += struct.pack(">d", value['time'])
            scriptDataValueBytes += struct.pack(">h", value['zone'])
        elif len(value) == 2 and 'len' in value and 'val' in value:
            # ECMA Array 类型
            scriptDataValueBytes += packScriptDataECMAArray(value)
        else:
            # Object类型
            scriptDataValueBytes += packScriptDataObject(value)
    elif value == None:
        # Amf0DataType.FLV_AMF0_NULL.value = 5
        scriptDataValueBytes += int.to_bytes(5, 1, 'big')
    elif type(value) == bool:
        # Amf0DataType.FLV_AMF0_BOOLEAN.value = 1
        scriptDataValueBytes += int.to_bytes(1, 1, 'big')
        if value:
            scriptDataValueBytes += int.to_bytes(255, 1, 'big')
        else:
            scriptDataValueBytes += int.to_bytes(0, 1, 'big')
    return bytes(scriptDataValueBytes)


def packScriptTagData(scripttag: ScriptTag):
    """根据flv script tag通常格式，将只打包一个onMetaata的String和一个ECMA array 或 Object"""
    amfbyte = bytearray()

    amfbyte += packScriptDataValue(scripttag.strVal)
    if scripttag.arrVal:
        amfbyte += packScriptDataValue(scripttag.arrVal)
    elif scripttag.objVal:
        amfbyte += packScriptDataValue(scripttag.objVal)
    return bytes(amfbyte)


class Head(object):
    signature = None
    version = None
    flag = None
    length = 0
    data = []

    def __init__(self, data):
        self.data = bytes(data[0:9])
        """初始化flv文件头信息, 一般占用9个字节"""
        self.signature = self.data[0:3]
        self.signature = bytes.decode(self.signature)
        if self.signature != "FLV":
            raise UnSupportFileFormat("文件格式不被支持")
        self.version = self.data[3]
        self.flag = self.data[4]
        self.length = bytes2int(self.data[5:9])

    def has_audio(self):
        """是否有音频"""
        return self.flag & 1

    def has_video(self):
        """是否有视频"""
        return self.flag >> 2

    def len(self):
        """对于大于9个字节可能是拓展或其他"""
        return self.length


class Flv(object):
    head = None
    tags = []

    def writeTagData(self, Tags, fileIO, statusMonitor, lastThreadObj=None):
        def _writeTagData():
            if lastThreadObj:
                lastThreadObj.join()
            for tag in Tags:
                statusMonitor.addWroteByte(tag.write(fileIO))
            fileIO.flush()
        t = Thread(target=_writeTagData)
        t.start()
        return t

    def parseStream(self, stream, statusMonitor: StatusMonitor, outputfileIO=None, buffSize=2048):
        statusMonitor.init()  # 初始化数据监控
        stream.decode_content = True
        statusMonitor.rawObj = stream
        TagDict = {8: AudioTag, 9: VideoTag, 18: ScriptTag}
        Tag = None
        lastThreadObj = None

        rawData = BytesBuffer(stream.read(buffSize))

        while not self.head:
            if stream.closed:
                statusMonitor.connectionclosed = True
                outputfileIO.flush()
                raise Exception("连接已断开")

            if rawData.size >= 15:
                self.head = Head(rawData.read(9))
                # 9字节flv header
                outputfileIO.write(self.head.data)
                # 4字节previousTagsSize 第一个永远为0
                outputfileIO.write(rawData.read(4))
                statusMonitor.addDownloadByte(13)
                break

            rawData.write(stream.read(buffSize))
            statusMonitor.addDownloadByte(buffSize)

        while 1:
            if stream.closed:
                statusMonitor.connectionclosed = True
                outputfileIO.flush()
                raise Exception("连接已断开")
                # break

            if rawData.size >= 11 and not Tag:
                buffer = rawData.read(11)
                previousTagType = buffer[0]

                try:
                    Tag = TagDict[previousTagType]()
                except:
                    print(f"接收到了未定义的Tag {previousTagType}")
                    Tag = OtherTag()
                Tag.parseTagheader(buffer)

            # 4字节previousTagSize
            if Tag and rawData.size >= Tag.length + 4:
                Tag.bodydata = rawData.read(Tag.length)
                rawData.read(4)  # 4字节 previousTagSize
                statusMonitor.addTag(Tag.type, Tag.pts)
                self.tags.append(Tag.parse())
                if Tag.type == 9 and Tag.frameType == 1:  # 关键帧
                    lastThreadObj = self.writeTagData(
                        self.tags, outputfileIO, statusMonitor, lastThreadObj)
                    self.tags = []
                Tag = None

            rawData.write(stream.read(buffSize))
            statusMonitor.addDownloadByte(buffSize)
            # end of class Flv
