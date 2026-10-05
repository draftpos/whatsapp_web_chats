import paramiko

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname, username=username, password=password)

command = f"echo '{password}' | sudo -S docker logs --tail 200 odoo_jlink_havano_pro_cpsmddqqvbceafpdpqoknnae"

stdin, stdout, stderr = ssh.exec_command(command)

out = stdout.read().decode('utf-8')

with open('docker_logs.txt', 'w', encoding='utf-8') as f:
    f.write(out)
    
print("Saved docker logs.")
ssh.close()
