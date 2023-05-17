from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QMessageBox

import time
import sys, os
import configparser

import json
import requests
import sched, time


from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

from PyQt5.uic import loadUiType

FORM_CLASS,_=loadUiType(resource_path("main.ui"))
REG_CLASS,_=loadUiType(resource_path("registration.ui"))
ACCOUNT_CLASS,_=loadUiType(resource_path("create_account.ui"))


class Main(QDialog, FORM_CLASS):
    def __init__(self,parent=None):
        super(Main,self).__init__(parent)
        self.setupUi(self)
        self.handle_Btns()
        global mainWindow
        mainWindow = self

    def handle_Btns(self):        
        self.scrapBtn.clicked.connect(self.scrapGroup)

    def groupChanged(self):
        print(self.groupList.currentRow())

    def scrapGroup(self):
        # self.accountTable.insertRow(self.accountTable.rowCount())
        # self.accountTable.setItem(self.accountTable.rowCount()-1,0, QTableWidgetItem("text1"));

        # name, done1 = QtWidgets.QInputDialog.getText(self , "Code Dialog" , "Input verification code : ")
        # print(name)
        self.groupList.currentRowChanged.connect(self.groupChanged)
        cpass = configparser.RawConfigParser()
        cpass.read('config.data')

        try:
            api_id = cpass['cred']['id']
            api_hash = cpass['cred']['hash']
            phone = cpass['cred']['phone']
            client = TelegramClient(phone, api_id, api_hash)
            print(phone)
        except KeyError:
            os.system('clear')
            print("[!] run python3 setup.py first !!\n")
            sys.exit(1)

        client.connect()
        if not client.is_user_authorized():
            print("not authorized yet")
            client.send_code_request(phone)
            name, done1 = QtWidgets.QInputDialog.getText(self , "Code Dialog" , "Input verification code : ")
            print(name)
            #os.system('clear')
            #code = input('input the code : ')
            # print("still")
            client.sign_in(phone, name)
        
        # os.system('cls')
        chats = []
        last_date = None
        chunk_size = 200
        groups=[]

        result = client(GetDialogsRequest(
             offset_date=last_date,
             offset_id=0,
             offset_peer=InputPeerEmpty(),
             limit=chunk_size,
             hash = 0
         ))         
        chats.extend(result.chats)
        
        for chat in chats:
            try:
                if chat.megagroup== True:
                    groups.append(chat)
            except:
                continue
 
        print('[+] Choose a group to scrape members :')
        for g in groups:
            print(g.title)
            self.groupList.addItem(QListWidgetItem(g.title))
            
        # time.sleep(1)
        # print('[+] Fetching Members...')

        # all_participants = []
        # all_participants = client.get_participants(groups[int(1)], aggressive=True)
        # time.sleep(1)
        # for user in all_participants:
        #     self.scrapTable.insertRow(self.scrapTable.rowCount())
        #     self.scrapTable.setItem(self.scrapTable.rowCount() - 1 , 0,  QTableWidgetItem(user.username))
        #     print(user.username)
        #     if user.username:
        #         username= user.username
        #     else:
        #         username= ""
        #     if user.first_name:
        #         first_name= user.first_name
        #     else:
        #         first_name= ""
        #     if user.last_name:
        #         last_name= user.last_name
        #     else:
        #         last_name= ""
        #     name= (first_name + ' ' + last_name).strip()
        #     self.scrapTable.setItem(self.scrapTable.rowCount()-1, 1, QTableWidgetItem( str(user.id) ))
        #     self.scrapTable.setItem(self.scrapTable.rowCount()-1, 2, QTableWidgetItem( str(user.access_hash) ))
        #     self.scrapTable.setItem(self.scrapTable.rowCount()-1, 3, QTableWidgetItem(name))
        #     # writer.writerow([username,user.id,user.access_hash,name,target_group.title, target_group.id])  
  
        # print("added to table widget")


class Registration(QDialog, REG_CLASS):
    count = 0
    def __init__(self, parent=None):
        super(Registration, self).__init__(parent)
        self.setupUi(self)


class CreateAccount(QDialog, ACCOUNT_CLASS):
    token = ""
    proList = ["2ndline.io", "5sim.net", "sms-active.org"]
    countryId = -1
    count = 0  # count of phone numbers to buy
    def __init__(self, parent=None):
        super(CreateAccount,self).__init__(parent)
        self.setupUi(self)
        self.getPhonesBtn.clicked.connect(self.getPhones)
        # A GET request to get Coiuntries information
        response = requests.get("https://2ndline.io/apiv1/availablecountry")
        # Print the response
        countries = response.json()
        for country in countries:
            self.countryCbx.addItem(country["name"])    

        self.countryCbx.currentIndexChanged.connect(self.countryChanged)
        self.createSpb.valueChanged.connect(self.countChanged)

    def countryChanged(self):
        print(self.countryCbx.currentIndex())
        self.countryId = self.countryCbx.currentIndex()
        # get price of OTP sms
        url = "https://2ndline.io/apiv1/availableservice?countryId=0&operatorId=any"
        rep_countryId = "countryId=" + str(self.countryId)
        print(rep_countryId)
        url = url.replace("countryId=0",rep_countryId)
        print(url)
        response = requests.get(url)
        services = response.json()
        for service in services:
            if(service["name"] == "Telegram"):
                print( str(service["quantity"]))
                self.priceLbl.setText( str(service["price"]) )
                self.waitSpb.setValue( service["lockTime"]) 
                if(service["quantity"] == 0):
                    QMessageBox.about(self, "Sorry", "There isn't available telegram phone numbers for this country. Please choose another country")
        
    def countChanged(self):
        self.count = self.createSpb.value()
        print("count = " + str(self.count))

    def getPhones(self):
        # serviceId:269  telegram
        self.token = self.apiTokenIpt.text()
        print("token = " + self.token)
        # loop count
        i = 0
        while i < self.count:
            url = "https://2ndline.io/apiv1/order?apikey=" + self.token +"&serviceId=tg&countryId=" + str(self.countryId) + "&operatorId=any"
            print("buy : " + url)
            response = requests.get(url)
            result = response.json()
            if result["status"] == 1:    #success
                print("bought phone number = ", result["phone"])
                self.accountTable.insertRow(self.accountTable.rowCount())             
                self.accountTable.setItem(self.accountTable.rowCount()-1,0, QTableWidgetItem( result["phone"] ))
                self.accountTable.setItem(self.accountTable.rowCount()-1,1, QTableWidgetItem( "Success" ))
                i += 1
            else:
                print("Error in buying phone number : " + result["message"])
                if(result["message"] == "NO_NUMBERS"):
                    print("NO_NUMBERS")
                    break
        # 5692f17ec489080fB9BB772c6eBf1966
        
        # for i in range(self.count):
        #     url = "https://2ndline.io/apiv1/order?apikey=" + self.token +"&serviceId=tg&countryId=" + str(self.countryId) + "&operatorId=any"
        #     print("buy : " + url)
        #     response = requests.get(url)
        #     result = response.json()
        #     if result["status"] == 1:    #success
        #         print("bought phone number = ", result["phone"])
        #         # my_scheduler = sched.scheduler(time.time, time.sleep)
        #         # my_scheduler.enter(60, 1, self.checkPhone, (my_scheduler, ))
        #         # my_scheduler.run()
        #     else:
        #         print("Error in buying phone number : " + result["message"])

    # def checkPhone(scheduler):
    #     scheduler.enter(60, 1, self.checkPhone, (scheduler, ))  # book next loop
    #     print("looping")
    #     # print('called : ' + phone)





def main():    
    app=QApplication(sys.argv)
    
    createAccount = CreateAccount()
    createAccount.show()

    # window=Main()
    # window.show()

    # reg = Registration()
    # reg.show()

    app.exec_()


if __name__=='__main__':
    main() 