import paramiko
import scp

ssh = paramiko.SSHClient()
ssh.load_system_host_keys()
#ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.RSAKey.from_private_key_file ("Brian_rsa")
ssh.connect ('192.168.2.27', username = 'brian', pkey = key)

#sftp = ssh.open_sftp()
#sftp.put ('2019-09-05 21.29.38.png', '/home/brian')
scp = scp.SCPClient (ssh.get_transport())
scp.put("K2019-09-05 21.29.38.png")
print ('done')
