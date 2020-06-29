import socket
import logging
import json
import time
logger = logging.getLogger(__name__)
from threading import Thread, Lock


class SocketServer:
    """
    socket服务器
    客户端连接服务器进行网络通行
    需要使用该服务器的功能通过委托方式进行
    """

    def __init__(self, server_address, deligation_func):
        self.server_is_ok = True
        self.deligation_func = deligation_func
        self.init_server(server_address)


    def init_server(self, server_address):
        """
        初始化服务器
        """
        try:
            self.server_address = server_address
            self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logger.info(f'|socket server| init')
            self.socket_server.bind(server_address)
            logger.info(f'|socket server| bind on: {server_address}')
        except Exception as e:
            self.server_is_ok = False
            logger.info(f'|socket server| init failed: {e}')


    def listen_thread(self):
        """
        当监听到新的连接
        在子线程中启用委托函数,将新连接传入子线程中使用
        """
        while True:
            try:
                socket_connected, connected_address = self.socket_server.accept()
                logger.info(f'|socket server| connect from: {connected_address}')
                Thread(target=self.deligation_func, args=(socket_connected, connected_address), daemon=True).start()
            except Exception as e:
                print(e)
                logger.info(f'|socket server| disconnect from: {self.server_address}')
                break

    
    def block(self, block_flag=None):
        """
        阻塞器
        """
        logger.info(f'|socket server| block in main thread')
        if block_flag is None:
            while True:
                if input('看到该提示后任何时候输入"q"退出socket服务!\n') == 'q':
                    logger.info(f'|socket server| perpare shutdown')
                    break
        else:
            while block_flag():
                time.sleep(3)
            logger.info(f'|socket server| perpare shutdown')


    def launch(self, block_flag=None):
        """
        服务器启动监听客户端的连接
        """
        if self.server_is_ok:
            logger.info(f'|socket server| launching')
            self.socket_server.listen(3)
            Thread(target=self.listen_thread, args=(), daemon=True).start()
            self.block(block_flag)
            self.socket_server.close()
            time.sleep(1) # 让子线程线推出，否则在windows上会报Python Error
            logger.info(f'|socket server| shutdown normal')
        else:
            self.socket_server.close()
            logger.info(f'|socket server| shutdown abnormal')


def recive_fixedlength(sock, count):
    """
    接收函数
    固定消息长度的传输方式

    参数
        sock  socket对象
        count 已知socket传输消息字节数
    """
    buf = b''#buf是一个byte类型
    while count:
        #接受TCP套接字的数据。数据以字符串形式返回，count指定要接收的最大数据量.
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf


def recive_byEOF(sock, EOF, buffer_size=1024):
    """
    接收函数
    通过设定终止符的接收方式

    参数
        sock  socket对象
        eof   终止符,是单个字节的bytes类型数据
        buffer_size 单次从缓冲区读取的字节长度
    """
    buf = []
    while True:
        newbuf = sock.recv(buffer_size)
        if not newbuf:
            return None
        
        if newbuf[-1:] == EOF:
            buf.append(newbuf[0:-1])
            break
        else:
            buf.append(newbuf)
    return b''.join(buf)


def simple_client(server_address, task="InitIdentifying"):
    """
    用于配合socket服务器测试
    """
    try:
		#建立socket对象
		#socket.AF_INET：服务器之间网络通信 
		#socket.SOCK_STREAM：流式socket , for TCP
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		#开启连接
        sock.connect(server_address)
        logger.info(f'connected {server_address}')
    except socket.error as msg:
        print(msg)

    if task == 'InitIdentifying':
        send_msg = {"SessionId": "87BB23D2-79F2", "CommandName": "InitIdentifying"}
        sock.send((json.dumps(send_msg) + '\n').encode('utf-8'))
        recv_msg = recive_byEOF(sock, (10).to_bytes(1, 'little'))
        print(json.loads(recv_msg.decode('utf-8')))
    elif task == 'CollectingImages':
        send_msg = {"SessionId": "87BB23D2-79F2", "CommandName": "CollectingImages", 'Data': "233333"}
        sock.send((json.dumps(send_msg) + '\n').encode('utf-8'))
        recv_msg = recive_byEOF(sock, (10).to_bytes(1, 'little'))
        print(recv_msg.decode('utf-8'))
        recv_msg = recive_byEOF(sock, (10).to_bytes(1, 'little'))
        print(recv_msg.decode('utf-8'))
        recv_msg = recive_byEOF(sock, (10).to_bytes(1, 'little'))
        print(recv_msg.decode('utf-8'))

    sock.close()


if __name__ == '__main__':
    simple_client(server_address=('127.0.0.1', 9004), task='InitIdentifying')