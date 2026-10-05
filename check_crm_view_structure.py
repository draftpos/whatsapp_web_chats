import paramiko
import sys

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

print(f"Connecting to {hostname}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)
    stdin, stdout, stderr = ssh.exec_command("docker exec odoo_jlink_havano_pro_cpsmddqqvbceafpdpqoknnae cat /usr/lib/python3/dist-packages/odoo/addons/crm/views/crm_lead_views.xml | grep -n -A 20 -B 10 'name=\"%(crm.crm_lead_lost_action)d\"'")
    print(stdout.read().decode())
    
    print("--- Searching for header and sheet ---")
    stdin, stdout, stderr = ssh.exec_command("docker exec odoo_jlink_havano_pro_cpsmddqqvbceafpdpqoknnae cat /usr/lib/python3/dist-packages/odoo/addons/crm/views/crm_lead_views.xml | grep -n -A 30 '<header>'")
    print(stdout.read().decode())
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
