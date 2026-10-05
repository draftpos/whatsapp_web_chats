import paramiko

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname, username=username, password=password)

command = f"echo '{password}' | sudo -S docker exec odoo_jlink_havano_pro_cpsmddqqvbceafpdpqoknnae cat /usr/lib/python3/dist-packages/odoo/addons/crm/views/crm_lead_views.xml"

stdin, stdout, stderr = ssh.exec_command(command)

out = stdout.read().decode('utf-8')

with open('crm_view_source.xml', 'w', encoding='utf-8') as f:
    f.write(out)
    
print("Saved to crm_view_source.xml")
ssh.close()
