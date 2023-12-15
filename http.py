# 这是收发协议

# request = Login \ Message \ Register \ Get \ Offline \Update
# register code{
#     100 = 注册成功
#     101 = 有重名，注册失败
# }

# login code{
#     200 = 登陆成功
#     201 = 密码错误
#     202 = 无此用户
# }

head_size = 3
buffer_size = 1024

# 创建登录协议
def create_log(request, user_name, password) -> str:
    return add_head(f"\r\n{request}\r\nUCCP\r\n{user_name}\r\n{password}")


# 创建聊天协议
def create_message(request, from_user, to_user, message) -> str:
    return add_head(f"\r\n{request}\r\n{from_user}\r\n{to_user}\r\nMSG_UCCP\r\n{message}")


# 创建客户端请求协议
def create_request(request) -> str:
    return add_head(f"\r\n{request}")


# 创建返回协议，谁发送谁返回
def create_response(code) -> str:
    request = "Code"
    return add_head(f"\r\n{request}\r\nUCCP\r\n{code}")


# 解析请求
def analysis_request(data):
    request = data.split("\r\n")[1]
    return request


# 解析登录协议
def analysis_log(data):
    msl = data.split("\r\n")
    id = msl[3]
    password = msl[4]
    return id, password


# 解析聊天协议
def analysis_message(data):
    msl = data.split("\r\n")
    from_user = msl[2]
    to_user = msl[3]
    message = msl[5]
    return from_user, to_user, message


# 解析返回协议
def analysis_response(data):
    code = data.split("\r\n")[3]
    return int(code)


# 文件头添加协议
def add_head(data):
    data = data.encode()
    head = len(data).to_bytes(head_size, "big")
    package = head + data
    return package
