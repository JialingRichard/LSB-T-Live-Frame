# https://stackoverflow.com/questions/33395004/python-streamio-reading-and-writing-from-the-same-stream
class BytesBuffer():

    def __init__(self, s=b''):
        self.buffer = bytearray(s)
        self.size = len(self.buffer)

    def read(self, n=-1):
        # if self.size < n:
        #     raise Exception(f"buffer里面没这么多数据啊，最多只有{self.size}bytes了")
        self.size -= n
        chunk = self.buffer[:n]
        self.buffer = self.buffer[n:]
        return chunk

    def write(self, s):
        self.buffer += s
        self.size += len(s)
