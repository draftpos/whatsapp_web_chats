import paramiko

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname, username=username, password=password)

command = f"echo '{password}' | sudo -S docker exec odoo_jlink_havano_pro_cpsmddqqvbceafpdpqoknnae tail -n 100 /var/log/odoo/odoo-server.log"

stdin, stdout, stderr = ssh.exec_command(command)

out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')

with open('odoo_logs.txt', 'w', encoding='utf-8') as f:
    f.write(out)
    if err:
        f.write("\n\n--- ERRORS ---\n" + err)
        
print("Saved logs.")
ssh.close()
