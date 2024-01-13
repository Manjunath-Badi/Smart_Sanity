import sys
import re
import subprocess
import time
import csv
import json
import os
from pymongo import MongoClient
from datetime import datetime, timedelta

from SSH_Connect import SSH_Connect



class List_Code_Changes():
    def __init__(self,Config_File):
        self.Config_File = Config_File
        
    def Parse_Config(self):
        # Opening and Reading "Config.json" file
        cwd = os.getcwd()
        print(f"Current Working Dir : {cwd}")
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
        collection_name = 'Code_Changes'
        col = db[collection_name]
         
        # drop collection col1
        if col.drop():
            print(f'Collection {collection_name} Deleted')
        else:
            print(f'Collection {collection_name} Not Present')
            
            
        # Access or create collection if doesent exists.
        collection_name = 'Missed_Report'
        col = db[collection_name]
         
        # drop collection col1
        if col.drop():
            print(f'Collection {collection_name} Deleted')
        else:
            print(f'Collection {collection_name} Not Present')
        
        # Close the MongoDB connection
        client.close()
        
    def Get_Commit_Details(self, Commit_ID = 'latest'):


        self.Test_Bed_Machine = self.Config_Data["Test_Bed_Machine"]
        SSH_Connection = SSH_Connect(self.Test_Bed_Machine["IP_Address"], self.Test_Bed_Machine["UserName"], self.Test_Bed_Machine["Password"])
        Repository_Path = self.Test_Bed_Machine["Repository_Path"]
        if Commit_ID == 'latest':
            cmd = f"cd {Repository_Path} && git log -1"
        else:
            cmd = f"cd {Repository_Path} && git show {Commit_ID}"
        SSH_Connection.Execute(cmd)
        #print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        #for line in SSH_Connection.Response:
            #print(line)
        #print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        self.Commit_ID = self.Date_time = self.Author = self.Commit_Message = None
        
        print(f"Response : {SSH_Connection.Response}")
        for line in SSH_Connection.Response:
            if not (self.Commit_ID != self.Date_time != self.Author != self.Commit_Message != None):
                line = line.strip()
                serobj = re.search("commit ([\d\w]+)", line, re.I)
                if serobj:
                    self.Commit_ID = serobj.group(1)
                    continue
                    
                serobj = re.search("Date:\s*([0-9a-zA-Z:\s]+)", line, re.I)
                if serobj:
                    self.Date_time = serobj.group(1)
                    continue
                    
                if "author" in line.lower():
                    self.Author = line.replace("Author: ", "")
                    continue
                    
                serobj = re.search("\s*([0-9a-zA-Z]+)", line, re.I)
                if serobj:
                    self.Commit_Message = line
                    continue
            else:
                return 0

    def Map_Conditions_with_line_numbers(self, code):
        pass

    def locate_code_blocks_with_line_numbers(self):
        brace_pairs = []
        for filename in self.Code_Changes["Code_Change"].keys():
            for FunctionName, code in self.Code_Changes["Code_Change"][filename].items():
                brace_starts = []
                if_Starts = []
                else_starts = []
                closing_braces = []
                multiline_comment = 0

                self.if_Statements = []
                self.else_Statements = []
                for Line_no, line in enumerate(code, 1):
                    if line.startswith('//'):
                        continue
                    elif line.startswith('/*'):
                        multiline_comment = 1
                    elif line.endswith('*/'):
                        multiline_comment = 0

                    if multiline_comment == 0:
                        if ('if' in line):
                            if_Starts.append(Line_no)
                            if ('}' in line):
                                closing_braces.append(Line_no)
                                if brace_starts or if_Starts:
                                    open_brace_position  = brace_starts.pop()
                                    brace_pairs.append((open_brace_position, Line_no))
                            if ('{' in line):
                                brace_starts.append(Line_no)
                            continue

                        if ('else' in line):
                            else_starts.append(Line_no)
                            if ('}' in line):
                                closing_braces.append(Line_no)
                                if brace_starts or if_Starts:
                                    open_brace_position  = brace_starts.pop()
                                    brace_pairs.append((open_brace_position, Line_no))
                            if ('{' in line):
                                brace_starts.append(Line_no)
                            continue
                            
                        if ('}' in line):
                            closing_braces.append(Line_no)
                            if brace_starts or if_Starts:
                                open_brace_position  = brace_starts.pop()
                                brace_pairs.append((open_brace_position, Line_no))
                            continue

                        if ('{' in line):
                            brace_starts.append(Line_no)
                            continue
                
                for i in if_Starts:
                    for pair in brace_pairs:
                        if pair[0] == i:
                            self.if_Statements.append(brace_pairs.pop(brace_pairs.index(pair)))

                for i in else_starts:
                    for pair in brace_pairs:
                        if pair[0] == i:
                            self.else_Statements.append(brace_pairs.pop(brace_pairs.index(pair)))

                print('Parsing Work in progress')
                
            
    def List_Functions(self):
        Commit_ID = self.Commit_ID
        print(f"Commit ID : {Commit_ID}")
        self.Code_Changes = {}
        self.Test_Bed_Machine = self.Config_Data["Test_Bed_Machine"]
        SSH_Connection = SSH_Connect(self.Test_Bed_Machine["IP_Address"], self.Test_Bed_Machine["UserName"], self.Test_Bed_Machine["Password"])
        Repository_Path = self.Test_Bed_Machine["Repository_Path"]

        self.Code_Changes["Commit_ID"] = self.Commit_ID
        self.Code_Changes["Date_time"] = self.Date_time
        self.Code_Changes["Commit_Message"] = self.Commit_Message
        self.Code_Changes["Author"] = self.Author
        
        self.Code_Changes["Code_Change"] = {}

        cmd = f"cd {Repository_Path} && git show {Commit_ID}"
        SSH_Connection.Execute(cmd)
        #print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        #for line in SSH_Connection.Response:
            #print(line)
        #print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        Block_Started = 0
        source_file_found = 0
        Current_Function_Name = None
        #files_split = re.split("^---[.]+_*+_-$", "_*+_-".join(SSH_Connection.Response))
        changes = {}
        filename = ''
        for line in SSH_Connection.Response:
            line = line.strip()
            
            if line.startswith("+++") :
                if (line.endswith(".c") or line.endswith(".cpp")):
                    filename = line.split("/")[-1]
                    changes[filename] = []
                continue
            if line.startswith("diff"):
                filename = ''
                continue
            
            if (filename != ''):
                changes[filename].append(line)

        Block_Started = 0
        oldFilename  = None
        for filename , modified_lines in changes.items():
            line_count = 0
            Current_Function_Name = None
            for line in modified_lines:
                line_count += 1

                if oldFilename != filename:
                    oldFilename = filename
                    line_count = 1
                    if Current_Function_Name != None:
                        self.Code_Changes["Code_Change"][filename].append(Current_Function_Name)
                        Current_Function_Name = None

                if filename not in self.Code_Changes["Code_Change"].keys():
                    self.Code_Changes["Code_Change"][filename] = {}

                if (re.search("(@@[\d\s\-,+]+@@)", line, re.I)):
                    if re.search("([\w_\d]+)\([\w\d_\*]+\s+[\w\d_\*]+", line, re.I):
                        #Block_Started = 1
                        Current_Function_Name = re.search("([\w_\d]+)\(", line, re.I).group(1)
                        Current_Function_Name += '|' + re.search("(@@[\d\s\-,+]+@@)", line, re.I).group(1)
                        self.Code_Changes["Code_Change"][filename][Current_Function_Name] = []
                    elif (re.search("(@@[\d\s\-,+]+@@)\s+([\w_\d]+)\(", line, re.I)):
                        Current_Function_Name = re.search("([\w_\d]+)\(", line, re.I).group(1)
                        Current_Function_Name += '|' + re.search("(@@[\d\s\-,+]+@@)", line, re.I).group(1)
                        self.Code_Changes["Code_Change"][filename][Current_Function_Name] = []
                    continue

                if (re.search("^[-\+]", line) and re.search("([\w_\d]+)\([\w\d_\*]+\s+[\w\d_\*]+", line, re.I)):
                    #Block_Started = 0
                    #if line_count < 6:
                        #self.Code_Changes["Code_Change"][filename].remove(Current_Function_Name)
                    Current_Function_Name = re.search("([\w_\d]+)\(", line, re.I).group(1)
                    self.Code_Changes["Code_Change"][filename][Current_Function_Name] = []
                    Current_Function_Name = None
                    continue

                if Current_Function_Name != None:
                    self.Code_Changes["Code_Change"][filename][Current_Function_Name].append(line)

            
            self.locate_code_blocks_with_line_numbers()
            self.Map_Conditions_with_line_numbers()


        #----------------------------------------------------------------------------------------------------

        """for line in SSH_Connection.Response:
            line = line.strip()
            #if line.startswith("+++") and (line.endswith(".c") or line.endswith(".cpp") or line.endswith(".h")):
            if line.startswith("---"):
                source_file_found = 0
                continue

            if line.startswith("+++") and (line.endswith(".c") or line.endswith(".cpp")):
                source_file_found = 1
                Current_Source_File = line.split("/")[-1]
                self.Code_Changes["Code_Change"][Current_Source_File] = []
                continue

            if (re.search("(@@[\d\s\-,+]+@@)", line, re.I) and (Block_Started == 0) and (source_file_found == 1)): 
                Block_Started = 1
                if re.search("([\w_\d]+)\([\w\d_\*]+\s+[\w\d_\*]+", line, re.I):
                    #Block_Started = 1
                    Current_Function_Name = re.search("([\w_\d]+)\(", line, re.I).group(1)
                continue
                    
            if (re.search("^[-\+]", line) and re.search("([\w_\d]+)\([\w\d_\*]+\s+[\w\d_\*]+", line, re.I) and (Block_Started == 1) and (source_file_found == 1)):
                #Block_Started = 0
                Current_Function_Name = re.search("([\w_\d]+)\(", line, re.I).group(1)
                self.Code_Changes["Code_Change"][Current_Source_File].append(Current_Function_Name)
                Current_Function_Name = None
                continue

            if (re.search("(@@[\d\s\-,+]+@@)", line, re.I) and (Block_Started == 1) and (source_file_found == 1)): 
                if Current_Function_Name != None:
                    self.Code_Changes["Code_Change"][Current_Source_File].append(Current_Function_Name)
                    Current_Function_Name = None
                    Block_Started = 0

        if Current_Function_Name != None:
            self.Code_Changes["Code_Change"][Current_Source_File].append(Current_Function_Name)

        for src_file in self.Code_Changes["Code_Change"].copy():
            Functions_List = list(set(self.Code_Changes["Code_Change"][src_file]))
            self.Code_Changes["Code_Change"][src_file] = Functions_List
            if not self.Code_Changes["Code_Change"][src_file]:
                self.Code_Changes["Code_Change"].pop(src_file)
             

        print(self.Code_Changes)"""
 
    def Store_Code_Changes(self):
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
        collection_name = 'Code_Changes'
        if collection_name not in db.list_collection_names():
            Test_List_Collection = db.create_collection(collection_name)
        else:
            Test_List_Collection = db[collection_name]
            
        Test_List_Collection.insert_one(self.Code_Changes)
            
        # Close the MongoDB connection
        client.close()
    
if __name__ == "__main__":
    print("************ Detect Code Changes Process Started ************")
    List_Code_Changes_Obj = List_Code_Changes('C:\\SmartSanity\\Config.json')
    List_Code_Changes_Obj.Parse_Config()
    List_Code_Changes_Obj.Drop_Collection()
    List_Code_Changes_Obj.Get_Commit_Details('0a155b30051356ec2ca504c22f0d2b3d30022372')
    # if len(sys.argv) == 2:
    #     List_Code_Changes_Obj.Get_Commit_Details(sys.argv[1])
    # else:
    #     List_Code_Changes_Obj.Get_Commit_Details()
    List_Code_Changes_Obj.List_Functions()
    List_Code_Changes_Obj.Store_Code_Changes()
    print("************ Detect Code Changes Process Ended ************")
    

