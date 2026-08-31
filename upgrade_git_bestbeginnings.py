import paramiko
host = '173.249.39.201'
user = 'amakoni'
password = 'Ashley@#'
db = 'bestbeginnings_s2_havano_pro_nyyrglzxjnfn'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=30)
script = f'''
echo '{password}' | sudo -S sh -c "
cd /home/{db}/custom-addons/havano_schools_odoo
git pull origin main
chown -R 105:106 .
"
echo '{password}' | sudo -S docker restart odoo_{db}
echo '{password}' | sudo -S docker exec odoo_{db} odoo -u havano_schools_odoo -d {db} --stop-after-init
'''
stdin, stdout, stderr = client.exec_command(script, timeout=600)
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))
client.close()
