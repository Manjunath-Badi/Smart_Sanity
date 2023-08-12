import sys
import re
import subprocess
import time
import csv
import json
import re
from pymongo import MongoClient
from datetime import datetime, timedelta

from SSH_Connect import SSH_Connect



class Coverage_Build():
    def __init__(self,Config_File):
        self.Config_File = Config_File
        
    def Parse_Config(self):
        # Opening and Reading "Config.json" file
        with open(self.Config_File, 'r') as openfile:
            self.Config_Data = json.load(openfile)
            
    def Enable_Instrumentation(self):
        self.TestList = []
        self.Build_Machine = self.Config_Data["Build_Machine"]
        SSH_Connection = SSH_Connect(self.Build_Machine["IP_Address"], self.Build_Machine["UserName"], self.Build_Machine["Password"])
        
        print(f"Test Launch Machine Config : {self.Build_Machine }")
        
        # Construct and execute 'cmd' to enable instrumentation in Build Machine.
       
        Enable_Inst_Response  = SSH_Connection.Execute(cmd)
        SSH_Connection.ssh.close()
        
                
    def Generate_Coverage_Build(self):
        Total_Items_Added = 0
        Total_Items_Skipped = 0
        
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
            
        for Test_Item in self.TestList:
            for TestName , CommandLine in Test_Item.items():
                # Define your search criteria
                criteria = {'TestName': TestName , 'CommandLine' : CommandLine}

            # Search for a document that matches the criteria in 'Test_List' Collection
            # Check if a document was found
            if Test_List_Collection.find_one(criteria):
                Total_Items_Skipped += 1
                print(f"Document {criteria} exists. Document Skipped to store in DB.")
            else:
                Total_Items_Added += 1
                
                criteria.update({'Last_Run_DT' : None, 'Last_Exec_Result' : None})
                Test_List_Collection.insert_one(criteria)
                print(f"Document {criteria} does not exists. Document will be stored in DB.")
                
        print(f'Total Items Added : {Total_Items_Added} and Skipped : {Total_Items_Skipped} during new test search.')
        # Close the MongoDB connection
        client.close()
        
        
            
    def Disable_Instrumentation(self):
        self.TestList = []
        self.Build_Machine = self.Config_Data["Build_Machine"]
        SSH_Connection = SSH_Connect(self.Build_Machine["IP_Address"], self.Build_Machine["UserName"], self.Build_Machine["Password"])
        
        print(f"Test Launch Machine Config : {self.Build_Machine }")
        
        # Construct and execute 'cmd' to disable instrumentation in Build Machine.
       
        Enable_Inst_Response  = SSH_Connection.Execute(cmd)
        SSH_Connection.ssh.close()

if __name__ == "__main__":
    Coverage_Build_Obj = Coverage_Build('Config.json')

    Coverage_Build_Obj.Parse_Config()
    Coverage_Build_Obj.Enable_Instrumentation()
    Coverage_Build_Obj.Store_Test_List_In_DB()
    Coverage_Build_Obj.Disable_Instrumentation()

