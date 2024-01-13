import sys
import re
import subprocess
import time
import csv
import json
import re
import os
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
        print(f" Coverage Clear Completed Successfully.")

                
    def Execute_Test(self, TestName, Cmd_Line):
        print(f" Test Started : TestName : {TestName}  - Command Line : {Cmd_Line}")
        
        self.Test_Launch_Machine = self.Config_Data["Test_Launch_Machine"]
        #SSH_Connection = SSH_Connect(self.Test_Launch_Machine["IP_Address"], self.Test_Launch_Machine["UserName"], self.Test_Launch_Machine["Password"])
        #self.Test_Result = SSH_Connection.Execute(Cmd_Line)
        #self.Test_Result = os.system(Cmd_Line)
        self.Last_Test_Result = os.system(Cmd_Line)
        #self.Last_Test_Result = SSH_Connection.exit_status
        print(f" exit_status : {self.Last_Test_Result}")
        #SSH_Connection.ssh.close()
        
        current_datetime = datetime.now()
        
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
            
        criteria = {'TestName': TestName , 'CommandLine' : Cmd_Line}
            
        Test_List_Collection.update_one(criteria,{"$set":{"Last_Run_DT":current_datetime, "Last_Exec_Result" : self.Last_Test_Result}})
            
        #SSH_Connection.ssh.close()
        # Close the MongoDB connection
        client.close()
        
        print(f" Test Execution Completed.")
        
        
    def Record_Coverage(self, TestName, Cmd_Line):
        print(f" Coverage Recording Started : TestName : {TestName}  - Command Line : {Cmd_Line}")
        # Convert Test.cov to Test.xml
        Cov_File = self.Config_Data["Test_Bed_Machine"]['Coverage_File']
        covxml_exe = self.Config_Data["Test_Bed_Machine"]['covxml']
        xml_file = Cov_File.replace(".cov", ".xml")
        
        self.Test_Bed_Machine = self.Config_Data["Test_Bed_Machine"]
        SSH_Connection = SSH_Connect(self.Test_Bed_Machine["IP_Address"], self.Test_Bed_Machine["UserName"], self.Test_Bed_Machine["Password"])
        
        CovPost_cmd = "covpost -q /proc/BullseyeCoverage.data-*"
        CovPost_RSP = SSH_Connection.Execute(CovPost_cmd)
        
        cmd = f" {covxml_exe} -f {Cov_File} -o {xml_file}"
        Cov_Clear_Response  = SSH_Connection.Execute(cmd)

        #Copy_Cmd = f"cp {Cov_File} /root/{TestName}.cov"
        #Copy_Cmd_Response  = SSH_Connection.Execute(Copy_Cmd)

        # Read coverage xml
        sftp  = SSH_Connection.ssh.open_sftp()
        remote_file = sftp.open(xml_file)
        file_contents = remote_file.read().decode('utf-8')
        remote_file.close()
        sftp.close()

        SSH_Connection.ssh.close()
        
        #Start Recording the coverage to DataBase for particular Test
        from xml.dom import minidom
        CoverageCollection = []
        #xmlObj = minidom.parse(xml_file)
        xmlObj = minidom.parseString(file_contents)
        folderobj = xmlObj.getElementsByTagName("folder")
        folderCatched = 0 
        SourceFileCount = 0
        FunctionCount = 0
        FolderCount = 0
        CoverageDict = {}
        CoverageDict["TestName"] = TestName
        CoverageDict["Coverage"] = {}
        Coverage_Types = ["condition", "decision", "switch-label", "block"]
        try:
            for folder in folderobj:
                if folderCatched:
                    break
                if folder.getAttribute("name") == "..":
                    folderCatched = 1
                    source_Files = folder.getElementsByTagName("src")
                    for sourcefile in source_Files:
                        Src_Coverage = sourcefile.attributes.items()
                        if int(Src_Coverage[2][1]) > 0:
                            Src_File_Name = sourcefile.getAttribute('name').replace(".", "*")
                            CoverageDict["Coverage"][Src_File_Name] = {}
                            SourceFileCount += 1
                            Functions = sourcefile.getElementsByTagName("fn")
                            for Function in Functions:
                                Func_Coverage = Function.attributes.items()
                                if Func_Coverage[1][1] == "1":
                                    Func_Name = re.search("([\w_\d]+)\(", Function.getAttribute('name'), re.I).group(1)
                                    CoverageDict["Coverage"][Src_File_Name][Func_Name] = {"condition":[], "decision" : [] , "switch-label" : [] , "block" :[] }
                                    Probes = Function.getElementsByTagName("probe")
                                    for Probe in Probes:
                                        if ((Probe.getAttribute('event') in ['full','false','true']) and (Probe.getAttribute('kind') != 'function')):
                                                CoverageDict["Coverage"][Src_File_Name][Func_Name][Probe.getAttribute('kind')].append(Probe.getAttribute('line'))
                                            #if Probe.getAttribute('kind') == 'decision':
                                            #    CoverageDict["Coverage"][Src_File_Name][Func_Name]['decision'].append(Probe.getAttribute('line'))
                                            #if Probe.getAttribute('kind') == 'condition':
                                            #    CoverageDict["Coverage"][Src_File_Name][Func_Name]['condition'].append(Probe.getAttribute('line'))
                                            #if Probe.getAttribute('kind') == 'switch-label':
                                            #    CoverageDict["Coverage"][Src_File_Name][Func_Name]['switch-label'].append(Probe.getAttribute('line'))
                                    Blocks = Function.getElementsByTagName("block")
                                    for Block in Blocks:
                                        if Block.getAttribute('entered') == '1':
                                            CoverageDict["Coverage"][Src_File_Name][Func_Name]['block'].append(Block.getAttribute('line'))
                                    for cov_type in Coverage_Types:
                                        if CoverageDict["Coverage"][Src_File_Name][Func_Name][cov_type] == []:
                                            CoverageDict["Coverage"][Src_File_Name][Func_Name].pop(cov_type)
        except Exception as ex:
            print(f"Exception occured : {ex}")

                                    
        print("**********************   Coverage Dump start  **********************")
        #print(f"{CoverageDict['Coverage']}")
        print("**********************   Coverage Dump end  **********************")
        # Access or create collection if doesent exists.
        collection_name = 'Coverage_Record'
        if collection_name not in db.list_collection_names():
            Coverage_Record_Collection = db.create_collection(collection_name)
        else:
            Coverage_Record_Collection = db[collection_name]
            
        # Define your search criteria
        criteria = {'TestName': TestName}

        # Search for a document that matches the criteria in 'Coverage_Record' Collection
        # Check if a document was found
        if not Coverage_Record_Collection.find_one(criteria):
            Coverage_Record_Collection.insert_one(CoverageDict)
        else:
            Coverage_Record_Collection.update_one(criteria,{"$set":{"Coverage":CoverageDict["Coverage"]}})

if __name__ == "__main__":
    try:
        #Test_Run_Record_Coverage_Obj = Test_Run_Record_Coverage('/home/SmartSanity/Config.json')
        Test_Run_Record_Coverage_Obj = Test_Run_Record_Coverage('C:\SmartSanity\Config.json')

        Test_Run_Record_Coverage_Obj.Parse_Config()
        print(f"Config Parsing completed")
        
        Database_Config = Test_Run_Record_Coverage_Obj.Config_Data["Database"]
        DB_IP_Address = Database_Config['IP_Address']
        DB_Port_ID = Database_Config['Port']
        
        # Connect to MongoDB
        client = MongoClient(f'mongodb://{DB_IP_Address}:{DB_Port_ID}')
        
        print(f"DB Connection completed")

        # Access or create the database
        db_name = Database_Config['DB_Name']
        db = client[db_name]
        
        # Access or create collection if doesent exists.
        collection_name = 'Coverage_Recording_Tests'
        Cov_Test_List_Collection = db[collection_name]
        print(f"Collection read completed")

        # Find all documents/tests from 'Coverage_Recording_Tests' collection.
        cursor = Cov_Test_List_Collection.find()
        print(f"Collection find completed")
        
        #---------------------------
        s = """document = {'TestName' : 'QCC_FC_Port_Alias' , 'CommandLine' : 'python C:\Dev-ps\eit_automation\Tests\Common\FC\QCC_FC_Port_Alias.py'}
        Test_Run_Record_Coverage_Obj.Clear_Coverage_File()
        Test_Run_Record_Coverage_Obj.Execute_Test(document['TestName'], document['CommandLine'])
        if Test_Run_Record_Coverage_Obj.Last_Test_Result == 0:
            print(f"Test {document['TestName']} returns Success. ")
        else:
            print(f"Test {document['TestName']} returns Non-Success \(!=0\) ")
        Test_Run_Record_Coverage_Obj.Record_Coverage(document['TestName'], document['CommandLine'])
        
        if Cov_Test_List_Collection.drop():
            print(f'Collection {collection_name} Deleted')
        else:
            print(f'Collection {collection_name} Not Present')
        
        # Close the MongoDB connection
        
        
        
        exit(0)"""
        #---------------------------
        # Iterate over the cursor and insert each document in 'Coverage_Recording_Tests' Collection.
        for document in cursor:
            print(f"Iteration TestName : {document['TestName']} , Command Line : {document['CommandLine']}")
               
            Test_Run_Record_Coverage_Obj.Clear_Coverage_File()
            Test_Run_Record_Coverage_Obj.Execute_Test(document['TestName'], document['CommandLine'])
            if Test_Run_Record_Coverage_Obj.Last_Test_Result == 0:
                print(f"Test {document['TestName']} returns Success. ")
            else:
                print(f"Test {document['TestName']} returns Non-Success \(!=0\) ")
            Test_Run_Record_Coverage_Obj.Record_Coverage(document['TestName'], document['CommandLine'])
    except Exception as ex:
        print(f"Exception occured : {ex}")
        
    finally:

        # drop collection col1
        if Cov_Test_List_Collection.drop():
            print(f'Collection {collection_name} Deleted')
        else:
            print(f'Collection {collection_name} Not Present')
        
        # Close the MongoDB connection
        client.close()
        