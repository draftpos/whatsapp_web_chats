import paramiko
host = '173.249.39.201'
user = 'amakoni'
password = 'Ashley@#'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password)
stdin, stdout, stderr = client.exec_command('echo Ashley@# | sudo -S docker logs --tail 100 odoo_bestbeginnings_s2_havano_pro_nyyrglzxjnfn')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))
client.close()
