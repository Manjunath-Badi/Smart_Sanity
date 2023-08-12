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
            
                
    def Prepare_Build(self):
        # Need to impliment Normal Build Generation and copying the build to Test Machine through SSH.
        pass
        

if __name__ == "__main__":

    Coverage_Build_Obj = Generate_Coverage_Build('Config.json')
    Coverage_Build_Obj.Parse_Config()
    Coverage_Build_Obj.Prepare_Build()

