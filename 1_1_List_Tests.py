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



class List_Tests():
    def __init__(self,Config_File):
        self.Config_File = Config_File
        
    def Parse_Config(self):
        # Opening and Reading "Config.json" file
        with open(self.Config_File, 'r') as openfile:
            self.Config_Data = json.load(openfile)
            
    def List_Tests_To_Run(self):
        self.TestList = []
        self.Test_Launch_Machine = self.Config_Data["Test_Launch_Machine"]
        SSH_Connection = SSH_Connect(self.Test_Launch_Machine["IP_Address"], self.Test_Launch_Machine["UserName"], self.Test_Launch_Machine["Password"])
        
        print(f"Test Launch Machine Config : {self.Test_Launch_Machine }")
        
        if self.Test_Launch_Machine["Test_List_File_Path"] == "":
            print("Test_List_File_Path == '' ")
        else:
            print("Test_List_File_Path != '' ")
            sftp  = SSH_Connection.ssh.open_sftp()
            remote_file = sftp.open(self.Test_Launch_Machine["Test_List_File_Path"])
            file_contents = remote_file.read().decode('utf-8')
            remote_file.close()
            sftp.close()
            SSH_Connection.ssh.close()
            for line in file_contents.replace("#", '').split('\r\n'):
                if ":" in line:
                    self.TestList.append({line.split(":")[0] : line.split(":")[1]})
                else:
                    if line != '':
                        self.TestList.append({line : line + self.Test_Launch_Machine["Script_Expensions"]})
            print(self.TestList)
                
    def Store_Test_List_In_DB(self):
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
        
        
    def Select_Coverage_Record_Tests(self):
        Total_Tests_Selected = 0
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
            
        # Define multiple conditions
        current_datetime = datetime.now()
        delta_datetime = timedelta(hours=int(self.Test_Launch_Machine["Test_Coverage_Expiry_in_Hrs"]))
        print(f"Tests will be selected for code coverage based on configured expiry time {self.Test_Launch_Machine["Test_Coverage_Expiry_in_Hrs"]}.")
        expiry_datetime = current_datetime - delta_datetime
        conditions = [
            {'Last_Run_DT': None},
            {'Last_Run_DT': {'$lte': expiry_datetime}}
        ]

        # Construct the query using the $and operator
        query = {'$or': conditions}

        # Find all documents that match the query
        cursor = Test_List_Collection.find(query)

        # Access or create collection if doesent exists.
        collection_name = 'Coverage_Recording_Tests'
        if collection_name not in db.list_collection_names():
            Cov_Test_List_Collection = db.create_collection(collection_name)
        else:
            Cov_Test_List_Collection = db[collection_name]
            
        # Iterate over the cursor and insert each document in 'Coverage_Recording_Tests' Collection.
        for document in cursor:
            print(document)
            Cov_Test_List_Collection.insert_one(document)

if __name__ == "__main__":

    List_Test_Obj = List_Tests('Config.json')

    List_Test_Obj.Parse_Config()
    List_Test_Obj.List_Tests_To_Run()
    List_Test_Obj.Store_Test_List_In_DB()
    List_Test_Obj.Select_Coverage_Record_Tests()

