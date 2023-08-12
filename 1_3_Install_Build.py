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


class Generate_Coverage_Build():
    def __init__(self,Config_File):
        self.Config_File = Config_File
        
    def Parse_Config(self):
        # Opening and Reading "Config.json" file
        with open(self.Config_File, 'r') as openfile:
            self.Config_Data = json.load(openfile)
            
                
    def Install_Build(self):
        # Need to impliment Normal Build Generation and copying the build to Test Machine through SSH.
        self.Test_Bed_Machine = self.Config_Data["Test_Bed_Machine"]
        Build_Path = self.Config_Data["Test_Bed_Machine"]['Build_Full_Path']
        SSH_Connection = SSH_Connect(self.Test_Bed_Machine["IP_Address"], self.Test_Bed_Machine["UserName"], self.Test_Bed_Machine["Password"])

        Cov_Clear_Response  = SSH_Connection.Execute(cmd)
        SSH_Connection.ssh.close()
       

if __name__ == "__main__":

    Coverage_Build_Obj = Generate_Coverage_Build('Config.json')
    Coverage_Build_Obj.Parse_Config()
    Coverage_Build_Obj.Install_Build()

