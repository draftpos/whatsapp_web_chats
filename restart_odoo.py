import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('173.249.39.201', username='amakoni', password='Ashley@#$1234')
cmd = "echo 'Ashley@#$1234' | sudo -S docker restart odoo_bestbeginnings_s2_havano_pro_nyyrglzxjnfn"
stdin, stdout, stderr = client.exec_command(cmd)
print("Stdout:\n", stdout.read().decode('utf-8', 'ignore'))
client.close()
