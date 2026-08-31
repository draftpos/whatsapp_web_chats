import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('173.249.39.201', username='amakoni', password='Ashley@#$1234')
cmd = "echo 'Ashley@#$1234' | sudo -S docker logs odoo_bestbeginnings_s2_havano_pro_nyyrglzxjnfn 2>&1 | grep -E '(ERROR|WARNING|Traceback|module|loaded|odoo.modules)' | tail -40"
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode('utf-8', 'ignore'))
print(stderr.read().decode('utf-8', 'ignore'))
client.close()
