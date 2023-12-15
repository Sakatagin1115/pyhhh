# 这是服务器端

import socket
import os
import threading
import time
import http
from data import user,data,register_init

#  定义套接字 s
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)

#  服务器IP以及端口
PORT = 50000
ServeIP = "192.168.3.14"

class server:
    def __init__(self):
        self.data=data()
        register_init()
        self.connection_list=[]
        self.connected = False

    # 开启服务器端函数
    def start(self):
        s.bind((ServeIP, PORT)) # 绑定IP和端口（参数为二元组），就是寻址
        s.listen(5) #  因为是TCP，所以要监听端口
        print("服务器启动·····")
        threadqq=threading.Thread(target=self.thread_body,name="Server")
        threadqq.start()

    def thread_body(self):
        while True:
            conn,address=s.accept() # 等待客户端连接（参数为最大连接数），返回一个二元组（新的socket对象+客户端地址）
            print(f'----create connection: {address}----')
            threaduser=threading.Thread(target=self.thread_user,name="User",args=(conn,address))
            threaduser.start()

    def thread_user(self,conn,address):
            try:
                while True:
                    data = self.recv_info(conn)  # 接受数据（这个函数阻塞，直到接受到数据）
                    # 解析请求
                    request = http.analysis_request(data)
                    match request:
                        case "Login":
                            threadlog=threading.Thread(target=self.thread_server_log,name="Login",args=(data,conn,address)) # 创建登录线程
                            threadlog.start()
                            threadlog.join()
                            if self.connected == 0:
                                raise

                        case "Register":
                            threadrig=threading.Thread(target=self.thread_server_rig,name="Register",args=(data,conn,address)) # 创建注册线程
                            threadrig.start()
                            threadrig.join()
                            if self.connected == 0:
                                raise

                        case "Message":
                            threadmes=threading.Thread(target=self.thread_server_mes,name="Message",args=(data,conn,address)) # 创建会话线程
                            threadmes.start()
                    
                        case "Offline":
                            threadoff=threading.Thread(target=self.thread_server_offline,name="Offline",args=(conn,address)) # 创建用户下线线程
                            threadoff.start()
                            break
                    
            #用户下线处理
            except:
                if self.connected == 1:
                    self.thread_server_offline(conn,address)
                else:
                    print(f'----{address}offline----')
                    conn.close()

    # def send_message(address,message):
    #     temp=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    #     temp.connect(address)
    #     temp.send(message)
    #     temp.close()

    #注册线程
    def thread_server_rig(self,data,conn,address):
        print(f'{address}请求注册')
        user_name, password = http.analysis_log(data)
        rismess=user(user_name,password)
        res = self.data.select_user(rismess) 
        #检查是否有重名
        match res:
            case 00:
                Errorcode = 100
                self.connected = 1
            case _:
                Errorcode = 101
        self.send_errorcode(Errorcode,conn)
        if Errorcode == 100:
            #写入注册信息
            self.data.add_user(rismess)
            #将用户加入在线列表并广播更新
            self.connection_list.append((user_name,conn))
            print(f'----{address}注册成功，{user_name}已加入聊天室')
            threadonline=threading.Thread(target=self.thread_server_online,name="Message",args=(user_name,conn,address))
            threadonline.start()
        else:
            print(f'{address}注册失败，请求已关闭')

    #登录线程
    def thread_server_log(self,data,conn,address):
        print(f'{address}请求登录')
        user_name, password = http.analysis_log(data)
        # logmess = {user_name, password}
        logmess=user(user_name,password)
        #检查输入信息与服务器中信息是否匹配
        res=self.data.select_user(logmess) 
        match res:
            case 11:
                Errorcode = 200
                self.connected = 1
            case 10:
                Errorcode = 201
            case 00:
                Errorcode = 202
        self.send_errorcode(Errorcode,conn)
        if Errorcode != 200:
            print(f'{address}登录失败,请求已关闭')
        else:
            print(f'----{address}登陆成功，{user_name}已加入聊天室')
            #将用户加入在线列表并广播更新
            self.connection_list.append((user_name,conn))
            thread=threading.Thread(target=self.thread_server_online,name="Message",args=(user_name,conn,address))
            thread.start()
    
    #消息线程
    def thread_server_mes(self,data,conn,address):
        from_user, to_user, message = http.analysis_message(data)
        #向群组广播
        if to_user == "Broadcast" :
            for name,sock in (self.connection_list):
                if sock != conn:
                    try:
                        new_message=http.create_message("Message",from_user,to_user,message)
                        sock.send(new_message)
                    except:
                        self.thread_server_offline(sock,address)

        #向单个用户发消息
        else:
            for name,sock in (self.connection_list):
                if name == to_user:
                    try:
                        new_message=http.create_message("Message",from_user,to_user,message)
                        sock.send(new_message)
                    except:
                        self.thread_server_offline(sock,address)

    #用户下线
    def thread_server_offline(self,conn,address):
        for u,v in (self.connection_list):
            if v == conn:
                offname = u
                break
        print(f'----{address}offline，{offname}已下线')
        message = f'----{offname}已下线！'
        to_user = "Broadcast"
        from_user = "Broadcast"
        new_message=http.create_message("Message",from_user,to_user,message)                    
        self.remove_online_users(conn)
        conn.close()
        for name,sock in (self.connection_list):         
            if sock != conn:
                try:
                    #广播下线
                    sock.send(new_message)   
                    #更新用户列表
                    user_list=self.get_users()
                    update_message=http.create_message("Update",from_user,to_user,user_list)        
                    sock.send(update_message)
                except:
                    self.thread_server_offline(sock,address)

    #用户上线
    def thread_server_online(self,name,conn,address):
        message = f'----{name}已上线！'
        to_user = "Broadcast"
        from_user = "Broadcast"                    
        new_message=http.create_message("Message",from_user,to_user,message)
        for name,sock in (self.connection_list):         
            try:
                #广播上线
                sock.send(new_message)  
                #更新用户列表  
                user_list=self.get_users()
                update_message=http.create_message("Update",from_user,to_user,user_list)      
                sock.send(update_message)
            except:
                self.thread_server_offline(sock,address)

    #获取在线用户列表
    def get_users(self):
        user_list=[]
        for u,v in self.connection_list:
            user_list.append(u)
        return user_list

    #从在线用户中移除下线用户
    def remove_online_users(self,sock):
        # print("before:",self.connection_list)
        for temp in (self.connection_list):
            if temp[1]==sock:
                self.connection_list.remove(temp)
                # print("after:",self.connection_list)
                break

    #发送错误代码
    def send_errorcode(self,Errorcode,conn):
        return conn.send(http.create_response(Errorcode))
    
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

if __name__=="__main__":
    Server=server()
    Server.start()