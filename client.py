from socket import *
import http
import threading
import sys
import time

serverIP = "192.168.3.14"

user_name = ""  # 用户名
password = ""  # 密码
userList = ()  # 在线用户列表


# 历史记录类
class history:
    def __init__(self, obj="", mess=""):
        self.object = obj  # 对象
        self.message = mess  # 记录

    def __str__(self) -> str:
        return self.object + "\n" + self.message

    def __hash__(self) -> int:
        return (self.object + self.message).__hash__()


historys = set()  # 集合存储历史记录
historys.add(history("Broadcast", ""))  # 第一个对象为广播


class MyThread(threading.Thread):
    def __init__(self, func, args=()):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result  # 如果子线程不使用join方法，此处可能会报没有self.result的错误
        except Exception:
            return None


# 客户端类
class client:
    # 初始化
    def __init__(self):
        self.Socket = socket(AF_INET, SOCK_STREAM)
        self.Socket.connect((serverIP, 50000))

    # 登录/注册
    def client_login(self, urn, pwd, request):
        global user_name, password
        user_name = urn
        password = pwd
        message = http.create_log(request, user_name, password)

        self.Socket.send(message)
        temp = self.recv_info(self.Socket)
        code = http.analysis_response(temp)

        if code == 100 or 200:  # 登录/注册成功
            self.thread = threading.Thread(target=self.thread_listen)  # 开始接受消息
            self.thread.start()
        return code

    # 退出，向服务器发送退出声明
    def client_logout(self):
        message = http.create_request("Offline")
        self.Socket.send(message)
        sys.exit(0)

    # 服务器监听线程
    def thread_listen(self):
        while True:
            message = self.recv_info(self.Socket)
            request = http.analysis_request(message)
            msl = http.analysis_message(message)
            match request:
                case "Message":
                    threading.Thread(target=self.thread_recv(mess=msl)).start()
                case "Update":
                    threading.Thread(target=self.thread_update(mess=msl)).start()
                case __:
                    continue

    # 收到消息，进行处理
    def thread_recv(self, mess):
        global historys
        obj = mess[0]
        message = mess[2]

        flag = 0
        for temp in historys:  # 修改本地历史记录
            if temp.object == obj:
                temp.message = temp.message + obj + ":" + message + "\n"
                flag = 1
        if flag == 0:  # 如果不存在与该对象的历史记录，则新建一个
            historys.add(history(obj, obj + ":" + message + "\n"))
        print(obj + ":" + message + "\n")

    # 更新用户列表
    def thread_update(self, mess):
        global userList
        userList = mess[2]

    # 发送消息
    def client_send(self, to_user, message):
        threading.Thread(target=self.thread_send(target=to_user, mess=message)).start()

    # 消息发送线程
    def thread_send(self, target, mess):
        global historys

        message = http.create_message("Message", user_name, target, mess)
        flag = 0
        for temp in historys:  # 先更新本地历史记录
            if temp.object == target:
                temp.message = temp.message + user_name + ":" + mess + "(local)" + "\n"
                flag = 1
        if flag == 0:
            historys.add(
                history(target, user_name + ":" + mess + "(local)" + "\n")
            )  # 与新对象的历史记录
        self.Socket.send(message)

    # 删除与某个对象的历史记录
    def delete_histroy(obj):
        for i in range(len(historys.object)):
            if historys[i].object == obj:
                historys[i].pop()
                break

            # 数据包拆分协议
    # 接收消息
    def recv_info(self,conn):
        head = conn.recv(http.head_size)
        data_len = int.from_bytes(head, "big")
        recvd_len = 0
        recvd_data = b''
        while recvd_len != data_len:
            if  data_len - recvd_len > http.buffer_size:
                data = conn.recv(http.buffer_size)
                recvd_len += len(data)
                recvd_data += data
            else:
                data = conn.recv(data_len - recvd_len)
                recvd_len = data_len
                recvd_data += data
        return recvd_data.decode('utf-8')


if __name__ == "__main__":
    while True:
        print("欢迎登录/注册")
        print("请输入用户名：")
        user_name = input()
        print("请输入密码：")
        pwd = input()
        print("请选择登录或注册，注册输入1，登录输入2：")
        cmd = input()
        Client = client()
        if cmd == "2":
            code = Client.client_login(user_name, pwd, "Login")
        elif cmd == "1":
            code = Client.client_login(user_name, pwd, "Register")
        if code == 100:
            print("注册成功！")
        elif code == 200:
            print("登陆成功！")
        else:
            print("登陆失败！")
            continue

        while True:
            print("请选择指令：1=群聊；2=私聊；3=查看历史纪录；4=退出")
            cmd = input()

            if cmd == "1":
                print("请输入消息：")
                message = input()
                Client.client_send("Broadcast", message)

            elif cmd == "2":
                print("UserList:")
                print(userList)
                print("请输入私聊对象:")
                to_user = input()
                print("请输入消息：")
                message = input()
                Client.client_send(to_user, message)

            elif cmd == "3":
                for h in historys:
                    print(h)

            elif cmd == "4":
                Client.client_logout()
                break

            else:
                continue

    sys.exit(0)
