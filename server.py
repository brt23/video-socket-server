import numpy as np
from cv2 import cv2
import socket
import time
from threading import Lock, Thread
import logging

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler("log.txt")
file_handler.setLevel(level=logging.INFO)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(level=logging.INFO)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


class VideoReader:
    """
    捕获视频数据

    参数
        video_addr 视频地址 
                可以是摄像头的编号如0或1等
                可以是网络摄像头的IP
                可以是网络流视频的地址
                可以是视频文件的路径
    """

    def __init__(self, video_addr):
        self.init_capture(video_addr)
        self.init_buffer()
        self.init_capture_thread()


    def init_capture(self, video_addr):
        """
        初始化捕获器

        参数
            video_addr 视频地址 
                       可以是摄像头的编号如0或1等
                       可以是网络摄像头的IP
                       可以是网络流视频的地址
                       可以是视频文件的路径
        """
        self.cap = cv2.VideoCapture(video_addr)
        if not self.cap.isOpened():
            raise Exception("video open failed!")


    def init_buffer(self):
        """
        初始化缓存
        """
        self.buffer_lock = Lock()
        self.buffer_frame = np.zeros((100, 100))


    def capture_frame_in_thread(self):
        """
        用于在子线程中捕获视频帧的函数
        """
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret: 
                raise Exception('Read frame failed!')
            with self.buffer_lock:
                self.buffer_frame = frame.copy()
            time.sleep(0.001)

    
    def init_capture_thread(self):
        """
        初始化视频捕获线程
        """
        self.capture_thread = Thread(target=self.capture_frame_in_thread, args=())


    def start(self):
        """
        启用视频捕获
        """
        self.is_running = True
        self.capture_thread.start()
        time.sleep(1)


    def stop(self):
        """
        关闭视频捕获
        """
        self.is_running = False
        self.capture_thread.join()
        self.cap.release()


    def read(self):
        """
        读取视频帧
        """
        with self.buffer_lock:
            frame = self.buffer_frame
        return frame


class ImageFrameReadr:
    """
    读取图片数据
    用于传输测试或满足图片传输功能
    """

    def __init__(self, image_path):
        self.image_path = image_path


    def start(self):
        self.frame = cv2.imread(self.image_path)


    def read(self):
        return self.frame


    def stop(self):
        self.frame = np.zeros((100, 100))


def video_socket_sever():
    """
    发送视频服务
    """
    # 初始化视频读取器
    video_reader = VideoReader(r'rtsp://admin:1234qwer@192.168.0.64:554/Streaming/Channels/101')
    # video_reader = ImageFrameReadr(r'C:\Users\huangqingyu\Desktop\yo.jpg')
    video_reader.start()

    # IP地址'0.0.0.0'为等待客户端连接
    address_listening = ('192.168.0.100', 9004)
    # 建立socket对象
    # socket.AF_INET：服务器之间网络通信 
    # socket.SOCK_STREAM：流式socket , for TCP
    socket_listening = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 将套接字绑定到地址, 在AF_INET下,以元组（host,port）的形式表示地址.
    socket_listening.bind(address_listening)
    logger.info(f'socket bind on: {address_listening}')
    # 开始监听TCP传入连接。参数指定在拒绝连接之前，操作系统可以挂起的最大连接数量。该值至少为1，大部分应用程序设为5就可以了。
    socket_listening.listen(3)
    # 压缩参数，后面cv2.imencode将会用到，对于jpeg来说，15代表图像质量，越高代表图像质量越好为 0-100，默认95
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100]

    def send_in_thread(socket_connected, address_connected):
        """
        发送视频子线程
        通过连接socket对象发送数据
        """
        while True:
            time.sleep(0.01)
            frame = video_reader.read()
            frame = cv2.resize(frame, (640, 360))
            frame = frame[..., ::-1]
            retval, imgencode = cv2.imencode('.jpg', frame, encode_param)
            data = np.array(imgencode)
            stringData = data.tostring()
            stringData = frame.tostring()

            try:
                socket_connected.send(len(stringData).to_bytes(4, byteorder='little'))
                socket_connected.send(stringData)
            except Exception:
                socket_connected.close()
                logger.info(f'disconnect from: {address_connected}')
                break


    def listen_in_thread():
        """
        监听子线程
        监听连接,当获取连接时新建一个连接socket对象conn
        """
        while True:
            try:
                socket_connected, address_connected = socket_listening.accept()
                logger.info(f'connect from: {address_connected}')
                Thread(target=send_in_thread, args=(socket_connected, address_connected), daemon=True).start()
            except Exception:
                logger.info(f'quit listening from: {address_listening}')
                break


    Thread(target=listen_in_thread, args=(), daemon=True).start()

    # 阻塞
    while True:
        if input('输入"q"退出!\n') == 'q':
            break

    # 释放资源
    socket_listening.close()
    video_reader.stop()
    logger.info(f'program exits')


if __name__ == '__main__':
    video_socket_sever()