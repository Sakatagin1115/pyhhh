#这是数据结构

import os
import pandas as pd

class user:
    def __init__(self,user_name:str,password:str):
        self.user_name=user_name
        self.password=password

    def __hash__(self) -> int:
        return self.user_name.__hash__()

def register_init():
    if os.path.exists("./users.csv") == False:
        f=open("./users.csv",mode='w',encoding="utf-8")
        f.close()
        df =pd.read_csv("./users.csv", header=None, names=['user_names','passwords'])
        df.to_csv("./users.csv",index=False)

class data:
    def __init__(self):

        pass

    def add_user(self,user:user):
        df= pd.DataFrame([[user.user_name,user.password]])
        df.to_csv('./users.csv' ,mode='a' ,index= False ,header = False)

    # def del_user(self,user:user):
    #     self.user_registered.remove(user)
    
    def select_user(self,user:user):
        with open("./users.csv",mode="r",encoding="utf-8", newline="") as f:
            csv_reader = pd.read_csv(f,dtype=str)
        for i in range(len(csv_reader)):
            if str(csv_reader["user_names"][i]) == user.user_name:
                if str(csv_reader["passwords"][i]) == user.password:
                    return 11
                else:
                    return 10
        return 00
