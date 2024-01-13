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
            
            
    def Drop_Collection(self):
        self.Database_Config = self.Config_Data["Database"]
        DB_IP_Address = self.Database_Config['IP_Address']
        DB_Port_ID = self.Database_Config['Port']

        # Connect to MongoDB
        client = MongoClient(f'mongodb://{DB_IP_Address}:{DB_Port_ID}')

        # Access or create the database
        db_name = self.Database_Config['DB_Name']
        db = client[db_name]
        
        # Access or create collection if doesent exists.
        collection_names = ['Test_Execution_Report', "Missed_Report"]
        
        # drop collection col1
        for collection_name in collection_names:
            col = db[collection_name]
            if col.drop():
                print(f'Collection {collection_name} Deleted')
            else:
                print(f'Collection {collection_name} Not Present')
        
        # Close the MongoDB connection
        client.close()
            

    def Store_Test_List_In_DB(self):
    # Test_Execution_Report
        
        #Test_List = {}

        self.Database_Config = self.Config_Data["Database"]
        DB_IP_Address = self.Database_Config['IP_Address']
        DB_Port_ID = self.Database_Config['Port']

        # Connect to MongoDB
        client = MongoClient(f'mongodb://{DB_IP_Address}:{DB_Port_ID}')

        # Access or create the database
        db_name = self.Database_Config['DB_Name']
        db = client[db_name]
        
        # Access or create collection if doesent exists.
        collection_name = 'Code_Changes'
        if collection_name not in db.list_collection_names():
            Code_Changes_Collection = db.create_collection(collection_name)
        else:
            Code_Changes_Collection = db[collection_name]
            
            
        collection_name = "Test_Execution_Report"
        if collection_name not in db.list_collection_names():
            Test_Execution_Report_Collection = db.create_collection(collection_name)
        else:
            Test_Execution_Report_Collection = db[collection_name]
            
        collection_name = "Missed_Code"
        if collection_name not in db.list_collection_names():
            Missed_Code_Collection = db.create_collection(collection_name)
            Missed_Code_Collection.insert_one({'Missed_Code' : {}})
        else:
            Missed_Code_Collection = db[collection_name]
            
        
        collection_name = "Missed_Report"
        if collection_name not in db.list_collection_names():
            Missed_Report_Collection = db.create_collection(collection_name)
        else:
            Missed_Report_Collection = db[collection_name]
        
        
        collection_name = "Coverage_Record"
        Coverage_Record_Collection = db[collection_name]
        
        
        for doc in Code_Changes_Collection.find():
            for File_Name , Functions in doc['Code_Change'].items():
                for Function_Name in Functions:
                    count = 0
                    print(f"FileName : {File_Name} , Function : {Function_Name}")
                    File_Name = File_Name.replace('.','*')
                    search_query = f"Coverage.{File_Name}.{Function_Name}"
                    cursor = Coverage_Record_Collection.find({search_query : {'$exists' : True}})
                    
                    for document in cursor:
                        print(document["TestName"])
                        count += 1
                        Test_List = {"TestName" : document['TestName'], 'Result' : None , 'Duration' : None }
                        if not Test_Execution_Report_Collection.find_one(Test_List):
                            Test_Execution_Report_Collection.insert_one(Test_List)
                    print(f"Total Selected Tests : {count}")

                    if count == 0:
                        criteria = {'FileName': File_Name , 'Function' : Function_Name }
                        if not Missed_Code_Collection.find_one(criteria):
                            Store_Query = {'FileName': File_Name , 'Function' : Function_Name , 'Count' : 1}
                            Missed_Code_Collection.insert_one(Store_Query)
                            Missed_Report_Collection.insert_one(Store_Query)
                        else:
                            for doc in Missed_Code_Collection.find(criteria):
                                Counter = doc['Count']
                            Counter += 1
                            #To Handle if the Missed code does exists in Missed_Code Collection, just increase the counter.
                            Missed_Code_Collection.update_one(criteria,{"$set":{"Count":Counter}})
                            Missed_Report_Collection.insert_one({'FileName': File_Name , 'Function' : Function_Name , 'Count' : Counter})
        client.close()
    
if __name__ == "__main__":

    List_Test_Obj = List_Tests('C:\\SmartSanity\\Config.json')

    List_Test_Obj.Parse_Config()
    List_Test_Obj.Drop_Collection()
    List_Test_Obj.Store_Test_List_In_DB()

