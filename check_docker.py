import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('173.249.39.201', username='amakoni', password='Ashley@#$1234')
stdin, stdout, stderr = client.exec_command('echo "Ashley@#$1234" | sudo -S docker ps -a | grep bestbeginnings')
print(stdout.read().decode())
client.close()
