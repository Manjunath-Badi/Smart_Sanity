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



class Test_Run_Record_Coverage():
    def __init__(self,Config_File):
        self.Config_File = Config_File
        
    def Parse_Config(self):
        # Opening and Reading "Config.json" file
        with open(self.Config_File, 'r') as openfile:
            self.Config_Data = json.load(openfile)
            
    def Clear_Coverage_File(self):
        Cov_File = self.Config_Data["Test_Bed_Machine"]['Coverage_File']
        covclear_exe = self.Config_Data["Test_Bed_Machine"]['covclear']
        cmd = f" {covclear_exe} -f {Cov_File}"
        
        self.Test_Bed_Machine = self.Config_Data["Test_Bed_Machine"]
        SSH_Connection = SSH_Connect(self.Test_Bed_Machine["IP_Address"], self.Test_Bed_Machine["UserName"], self.Test_Bed_Machine["Password"])

        Cov_Clear_Response  = SSH_Connection.Execute(cmd)
        SSH_Connection.ssh.close()

                
    def Execute_Test(self, TestName, Cmd_Line):
        print(f" TestName : {TestName}  - Command Line : {Cmd_Line}")
        
        # Execute the test and update the result of test in Smart_Sanity at Test_List Collection.
        
        
    def Record_Coverage(self, TestName, Cmd_Line):
        
        
        # Convert Test.cov to Test.xml
        Cov_File = self.Config_Data["Test_Bed_Machine"]['Coverage_File']
        covxml_exe = self.Config_Data["Test_Bed_Machine"]['covclear']
        xml_file = Cov_File.replace(".cov", ".xml")
        cmd = f" {covxml_exe} -f {Cov_File} -o {xml_file}"
        
        self.Test_Bed_Machine = self.Config_Data["Test_Bed_Machine"]
        SSH_Connection = SSH_Connect(self.Test_Bed_Machine["IP_Address"], self.Test_Bed_Machine["UserName"], self.Test_Bed_Machine["Password"])

        Cov_Clear_Response  = SSH_Connection.Execute(cmd)
        SSH_Connection.ssh.close()
        
        #Start Recording the coverage to DataBase for particular Test
        from xml.dom import minidom
        CoverageCollection = []
        xmlObj = minidom.parse(xml_file)
        folderobj = xmlObj.getElementsByTagName("folder")
        folderCatched = 0 
        SourceFileCount = 0
        FunctionCount = 0
        FolderCount = 0
        CoverageDict = {}
        CoverageDict["TestName"] = "TestName"
        for folder in folderobj:
            if folderCatched:
                break
            if folder.getAttribute("name") == "..":
                folderCatched = 1
                source_Files = folder.getElementsByTagName("src")
                for sourcefile in source_Files:
                    CoverageDict[sourcefile.getAttribute('name')] = {}
                    SourceFileCount += 1
                    sourcefile.attributes.items()
                    Functions = sourcefile.getElementsByTagName("fn")
                    for Function in Functions:
                        CoverageDict[sourcefile.getAttribute('name')][Function.getAttribute('name')] = {"condition":[], "decision" : [] , "switch-label" : [] , "block" :[] }
                        Func_Coverage = Function.attributes.items()
                        if Func_Coverage[1][1] == "1":
                            Probes = Function.getElementsByTagName("probe")
                            for Probe in Probes:
                                if Probe.getAttribute('event') in ['full','false','true']:
                                    if Probe.getAttribute('kind') == 'decision':
                                        CoverageDict[sourcefile.getAttribute('name')][Function.getAttribute('name')]['decision'].append(Probe.getAttribute('line'))
                                    if Probe.getAttribute('kind') == 'condition':
                                        CoverageDict[sourcefile.getAttribute('name')][Function.getAttribute('name')]['condition'].append(Probe.getAttribute('line'))
                                    if Probe.getAttribute('kind') == 'switch-label':
                                        CoverageDict[sourcefile.getAttribute('name')][Function.getAttribute('name')]['switch-label'].append(Probe.getAttribute('line'))
                            Blocks = Function.getElementsByTagName("block")
                            for Block in Blocks:
                                if Block.getAttribute('entered') == '1':
                                    CoverageDict[sourcefile.getAttribute('name')][Function.getAttribute('name')]['block'].append(Block.getAttribute('line'))
                                    
        # Access or create collection if doesent exists.
        collection_name = 'Coverage_Record'
        if collection_name not in db.list_collection_names():
            Cov_Test_List_Collection = db.create_collection(collection_name)
        else:
            Cov_Test_List_Collection = db[collection_name]
            
        Cov_Test_List_Collection.insert_one(CoverageDict)
        

if __name__ == "__main__":

    Test_Run_Record_Coverage_Obj = Test_Run_Record_Coverage('Config.json')

    Test_Run_Record_Coverage_Obj.Parse_Config()
    
    Database_Config = Test_Run_Record_Coverage_Obj.Config_Data["Database"]
    DB_IP_Address = Database_Config['IP_Address']
    DB_Port_ID = Database_Config['Port']
    
    # Connect to MongoDB
    client = MongoClient(f'mongodb://{DB_IP_Address}:{DB_Port_ID}')

    # Access or create the database
    db_name = Database_Config['DB_Name']
    db = client[db_name]
    
    # Access or create collection if doesent exists.
    collection_name = 'Coverage_Recording_Tests'
    Cov_Test_List_Collection = db[collection_name]

    # Find all documents/tests from 'Coverage_Recording_Tests' collection.
    cursor = Cov_Test_List_Collection.find()
 
    # Iterate over the cursor and insert each document in 'Coverage_Recording_Tests' Collection.
    for document in cursor:
        Test_Run_Record_Coverage_Obj.Clear_Coverage_File()
        Test_Run_Record_Coverage_Obj.Execute_Test(document['TestName'], document['CommandLine'])
        Test_Run_Record_Coverage_Obj.Record_Coverage(document['TestName'], document['CommandLine'])
        break

