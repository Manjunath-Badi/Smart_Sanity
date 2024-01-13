import sys
import re
import subprocess
import time
import csv
import json
import re
import os
from pymongo import MongoClient
from datetime import datetime

from SSH_Connect import SSH_Connect

class Execute_Tests():
    def __init__(self,Config_File):
        self.Config_File = Config_File
        
    def Parse_Config(self):
        # Opening and Reading "Config.json" file
        with open(self.Config_File, 'r') as openfile:
            self.Config_Data = json.load(openfile)
                    
    def Execute_Test(self):
        #print(f" Test Started : TestName : {TestName}  - Command Line : {Cmd_Line}")
        
        # Updating the DateTime in Test_List
        self.Database_Config = self.Config_Data["Database"]
        DB_IP_Address = self.Database_Config['IP_Address']
        DB_Port_ID = self.Database_Config['Port']
        
        # Connect to MongoDB
        client = MongoClient(f'mongodb://{DB_IP_Address}:{DB_Port_ID}')

        # Access or create the database
        db_name = self.Database_Config['DB_Name']
        db = client[db_name]
        
        # Access or create collection if doesent exists.
        collection_name = 'Test_List'
        if collection_name not in db.list_collection_names():
            Test_List_Collection = db.create_collection(collection_name)
        else:
            Test_List_Collection = db[collection_name]
            
        # Access or create collection if doesent exists.
        collection_name = 'Test_Execution_Report'
        if collection_name not in db.list_collection_names():
            Test_Execution_Report_Collection = db.create_collection(collection_name)
        else:
            Test_Execution_Report_Collection = db[collection_name]
        
        Test_List_to_Run = Test_Execution_Report_Collection.find()
        
        
        self.Test_Launch_Machine = self.Config_Data["Test_Launch_Machine"]
        SSH_Connection = SSH_Connect(self.Test_Launch_Machine["IP_Address"], self.Test_Launch_Machine["UserName"], self.Test_Launch_Machine["Password"])
        
        for document in Test_List_to_Run:
            print(document)
        
            TestName = document["TestName"]
            Test_Collection_obj = Test_List_Collection.find_one({"TestName" : TestName})
            Cmd_Line = Test_Collection_obj["CommandLine"]
            
            Start_datetime = datetime.now()
            
            #self.Test_Result = SSH_Connection.Execute(Cmd_Line)
            #self.Last_Test_Result = SSH_Connection.exit_status
            self.Test_Result = os.system(Cmd_Line)
            print(f" exit_status : {self.Test_Result}")

            
            Duration = datetime.now() - Start_datetime
            
            criteria = {'TestName': TestName}
            if self.Test_Result == 0:
                Test_Execution_Report_Collection.update_one(criteria,{"$set":{"Result": "PASS", "Duration": str(Duration) }})
            else:
                Test_Execution_Report_Collection.update_one(criteria,{"$set":{"Result": "FAIL", "Duration": str(Duration) }})
            
        SSH_Connection.ssh.close()
        # Close the MongoDB connection
        client.close()
        print(f" Test Execution Completed.")
        
if __name__ == "__main__":

    Execute_Tests_Obj = Execute_Tests('C:\\SmartSanity\\Config.json')
    Execute_Tests_Obj.Parse_Config()
    
    Execute_Tests_Obj.Execute_Test()
        
        