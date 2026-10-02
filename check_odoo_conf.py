import paramiko

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)
    stdin, stdout, stderr = ssh.exec_command('sudo -S cat /home/jlink_havano_pro_cpsmddqqvbceafpdpqoknnae/config/odoo.conf')
    stdin.write(password + '\n')
    stdin.flush()
    print("ODOO CONF:")
    print(stdout.read().decode())
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
