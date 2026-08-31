import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('173.249.39.201', username='amakoni', password='Ashley@#$1234', timeout=30)
stdin, stdout, stderr = client.exec_command("echo 'Ashley@#$1234' | sudo -S sh -c \"docker logs --since 10m odoo_nadias_s4_havano_pro_qrmeqxutyzvhwwupoxju\"")
print(stdout.read().decode('utf-8', 'ignore'))
print(stderr.read().decode('utf-8', 'ignore'))
