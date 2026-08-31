import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('173.249.39.201', username='amakoni', password='Ashley@#$1234')
cmd = "echo 'Ashley@#$1234' | sudo -S sh -c 'docker exec odoo_bestbeginnings_s2_havano_pro_nyyrglzxjnfn odoo -i havano_schools_odoo -d bestbeginnings_s2_havano_pro_nyyrglzxjnfn --stop-after-init > /home/amakoni/install_log.txt 2>&1'"
stdin, stdout, stderr = client.exec_command(cmd)
stdout.channel.recv_exit_status()
stdin, stdout, stderr = client.exec_command("cat /home/amakoni/install_log.txt")
print("Log:\n", stdout.read().decode('utf-8', 'ignore'))
client.close()
