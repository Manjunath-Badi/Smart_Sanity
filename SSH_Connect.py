import pip

try:
    __import__("paramiko")
    import paramiko
except ImportError:
    pip.main(['install', "paramiko"]) 
    __import__("paramiko")

class SSH_Connect():

    def __init__(self, IP_Address, UserName, Password):
        self.IP_Address = IP_Address
        self.UserName = UserName
        self.Password = Password
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(IP_Address, username=UserName, password=Password, timeout=90.0)


    def Execute(self, Command):
        print(f'SSH Cmd : {Command}')
        self.stdin, self.stdout, self.stderr = self.ssh.exec_command(Command)
        self.exit_status = self.stdout.channel.recv_exit_status()
        self.Response = self.stdout.readlines()