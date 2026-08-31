import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('173.249.39.201', username='amakoni', password='Ashley@#$1234')
stdin, stdout, stderr = client.exec_command('echo "Ashley@#$1234" | sudo -S docker restart psql_bestbeginnings_s2_havano_pro_nyyrglzxjnfn odoo_bestbeginnings_s2_havano_pro_nyyrglzxjnfn')
print("Restarting containers...\n", stdout.read().decode('utf-8', 'ignore'))
client.close()
