from enum import Enum, unique


@unique
class TagType(Enum):
    """标签类型"""
    FLV_TAG_AUDIO = 0x08
    FLV_TAG_VIDEO = 0x09
    FLV_TAG_SCRIPT = 0x12


@unique
class Amf0DataType(Enum):
    """脚本中的变量类型（本程序支持的元数据类型）"""
    FLV_AMF0_NUMBER = 0x00
    FLV_AMF0_BOOLEAN = 0x01
    FLV_AMF0_STRING = 0x02
    FLV_AMF0_OBJECT = 0X03
    FLV_AMF0_NULL = 0x05
    FLV_AMF0_ARRAY = 0x08
    FLV_AMF0_END_OF_OBJECT = 0x09
    FLV_AMF0_STRICT_ARRAY = 0X0a
    FLV_AMF0_DATE = 0X0b
    FLV_AMF0_LONG_STRING = 0X0c
