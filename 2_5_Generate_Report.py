import sys
import re
import subprocess
import time
import csv
import json
import re
import random
from pymongo import MongoClient
from datetime import datetime, timedelta

from SSH_Connect import SSH_Connect



class Report():
    def __init__(self,Config_File):
        self.Config_File = Config_File
        
    def Parse_Config(self):
        # Opening and Reading "Config.json" file
        with open(self.Config_File, 'r') as openfile:
            self.Config_Data = json.load(openfile)
            

    def Generate_report(self):
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
        collection_name = 'Test_Execution_Report'
        if collection_name not in db.list_collection_names():
            Test_Execution_Report_Collection = db.create_collection(collection_name)
        else:
            Test_Execution_Report_Collection = db[collection_name]
            
        # Find all documents that match the query
        cursor = Test_Execution_Report_Collection.find()
        
        # Access or create collection if doesent exists.
        collection_name = 'Code_Changes'
        if collection_name not in db.list_collection_names():
            Code_Changes_Collection = db.create_collection(collection_name)
        else:
            Code_Changes_Collection = db[collection_name]
            
        for doc in Code_Changes_Collection.find():
            Commit_ID = doc['Commit_ID']
            Date_time = doc['Date_time']
            Commit_Message = doc['Commit_Message']
            Author = doc['Author']
        
        HTML = """
            <!DOCTYPE html>
            <html>
            <head>
            <style>
            table {
              font-family: arial, sans-serif;
              border-collapse: collapse;
              width: 60%;
            }

            td, th {
              border: 1px solid #dddddd;
              text-align: left;
              padding: 8px;
            }

            </style>
            </head>
            <body>""" + f"""<h1>Execution Report</h1>
            <br>
            <br>
            
            <h2>Commit Details</h2>
            <table>
            <tr>
                <td>Commit Date Time</td>
                <td>{Date_time}</td>
            </tr>
            
            <tr>
                <td>Commit ID</td>
                <td>{Commit_ID}</td>
            </tr>
            
            <tr>
                <td>Author</td>
                <td>{Author}</td>
            </tr>
            
            <tr>
                <td>Commit Message</td>
                <td>{Commit_Message}</td>
            </tr>
            </table>


            <h2>Test Run Details</h2>

            <table>
              <tr bgcolor="#9a9a9a">
                <th>SL No</th>
                <th>TestName</th>
                <th>Duration</th>
                <th>Status</th>
              </tr>
            """

        # Iterate over the cursor and Prepare the Test execution table.
        SL_No = 1
        Test_row = ""
        for document in cursor:
            Test_name = document['TestName']
            if document['Duration'] != None:
                Duration = document['Duration'].split(".")[0]
            else:
                Duration = "None"
            Status = {"PASS": "#6ff669", "FAIL" : "#f67669", "None" : "#FFE033"}
            if document['Result'] != None:
                state = document['Result']
            else:
                state = "None"
            Test_row += f"""
            <tr>
                <td>{SL_No}</td>
                <td>{Test_name}</td>
                <td>{Duration}</td>
                <td bgcolor="{Status[state]}">{state}</td>
            </tr>
            """
            SL_No += 1
        
        Un_Cov = """
        </table>
        <br>
        <br>
        <br>
        <h2>Un-Covered Source Code</h2>
        <table>
        <tr bgcolor="#9a9a9a">
            <th>Source File</th>
            <th>Function</th>
            <th>Count</th>
        </tr>
        """
        # Access or create collection if doesent exists.
        collection_name = "Missed_Report"
        if collection_name not in db.list_collection_names():
            Missed_Report_Collection = db.create_collection(collection_name)
        else:
            Missed_Report_Collection = db[collection_name]
            
        # Find all documents that match the query
        cursor = Missed_Report_Collection.find()
        
        Un_cov_row = ""
        for document in cursor:
            File = document['FileName'].replace("*", ".")
            Function = document['Function']
            cnt = document['Count']
            Un_cov_row += f"""
            <tr>
                <td>{File}</td>
                <td>{Function}</td>
                <td>{cnt}</td>
            </tr>
            """
        
        Footer = """
        </table>
        </body>
        </html>
        """
        
        Content = HTML + Test_row + Un_Cov + Un_cov_row + Footer
        
        with open("C:\\SmartSanity\\Report.html", "w") as fh:
            fh.write(Content)

if __name__ == "__main__":

    Report_Obj = Report('C:\\SmartSanity\\Config.json')

    Report_Obj.Parse_Config()
    Report_Obj.Generate_report()

