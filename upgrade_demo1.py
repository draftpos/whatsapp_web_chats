import os
import paramiko

host = "173.249.39.201"
user = "amakoni"
password = "Ashley@#$1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port=22, username=user, password=password, timeout=15)

# The command to upgrade the module. We use -d for db name and -u for module. 
# We don't need --stop-after-init if we just run odoo in the container? Wait, if we use --stop-after-init it might conflict if the db is in use? No, usually it's fine.
cmd = f"echo '{password}' | sudo -S docker exec odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae odoo -d demo1_havano_pro_cpsmddqqvbceafpdpqoknnae -u whatsapp_web_chats --stop-after-init --no-http"

print(f"Running upgrade command...")
stdin, stdout, stderr = ssh.exec_command(cmd)

for line in stdout:
    print(line, end="")
for line in stderr:
    print(line, end="")

ssh.close()
