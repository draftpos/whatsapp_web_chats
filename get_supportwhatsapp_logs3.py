import paramiko
import sys

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect('173.249.39.201', username='amakoni', password='Ashley@#$1234')
    cmd = "echo 'Ashley@#$1234' | sudo -S docker logs odoo_supportwhatsapp_s4_havano_pro_yvnmgevazsj 2>&1 | tail -n 100"
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', 'ignore'))
    print(stderr.read().decode('utf-8', 'ignore'))
finally:
    client.close()
