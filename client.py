import socket
import time
from cv2 import cv2
import numpy
 

def recive_video():
    address = ('192.168.0.100', 9004)

    try:
		#建立socket对象
		#socket.AF_INET：服务器之间网络通信 
		#socket.SOCK_STREAM：流式socket , for TCP
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		#开启连接
        sock.connect(address)
        print(f'[{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}] connected {address}')
    except socket.error as msg:
        print(msg)

    def recvall(sock, count):
        """
        接收函数
        """
        buf = b''#buf是一个byte类型
        while count:
            #接受TCP套接字的数据。数据以字符串形式返回，count指定要接收的最大数据量.
            newbuf = sock.recv(count)
            if not newbuf: return None
            buf += newbuf
            count -= len(newbuf)
        return buf
		
    while True:
        start = time.time()                                 #用于计算帧率信息

        length = recvall(sock, 4)                          #获得图片文件的长度,4代表获取长度,int一般默认转换为4个byte的byte型数据
        if length is None: break
        stringData = recvall(sock, int.from_bytes(length, byteorder='little'))            #根据获得的文件长度，获取图片文件

        # data = numpy.frombuffer(stringData, numpy.uint8)    #将获取到的字符流数据转换成1维数组
        # decode_image = cv2.imdecode(data, cv2.IMREAD_COLOR) #将数组解码成图像
        # cv2.imshow('Client display', decode_image)          #显示图像

        data = numpy.frombuffer(stringData, numpy.uint8)    #将获取到的字符流数据转换成1维数组
        data = data.reshape(720, 1280, 3)
        cv2.imshow('Client display', data)          #显示图像
		
        end = time.time()
        seconds = end - start
        print(f"frame time: {seconds*1000:.1f} ms")
        key = cv2.waitKey(10)
        if key != -1:
            break
    sock.close()
    cv2.destroyAllWindows()
 
if __name__ == '__main__':
    recive_video()