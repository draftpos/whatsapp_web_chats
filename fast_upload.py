import paramiko
import os

host = '173.249.39.201'
user = 'amakoni'
password = 'Ashley@#'
db = 'bestbeginnings_s2_havano_pro_nyyrglzxjnfn'
remote_base = f'/home/{db}/custom-addons/havano_schools_odoo'
local_base = r'c:\odoo19\addons\havano_schools_odoo'

files_to_push = [
    (r'__manifest__.py', '__manifest__.py'),
    (r'security\multi_school_rules.xml', 'security/multi_school_rules.xml'),
]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print('Connecting...')
client.connect(host, username=user, password=password, timeout=30)
sftp = client.open_sftp()

for local_rel, remote_rel in files_to_push:
    local_path = os.path.join(local_base, local_rel)
    remote_path = f'{remote_base}/{remote_rel}'
    print(f'Uploading {local_rel}...')
    sftp.put(local_path, remote_path)
sftp.close()
print('Files uploaded! Running upgrade...')

script = f'''
echo '{password}' | sudo -S docker restart odoo_{db}
echo '{password}' | sudo -S docker exec odoo_{db} odoo -u havano_schools_odoo -d {db} --stop-after-init
'''
stdin, stdout, stderr = client.exec_command(script, timeout=600)
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))
client.close()
print('Done!')
