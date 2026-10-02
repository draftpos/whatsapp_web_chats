import paramiko

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)
    
    cmd = """
sudo -S sed -i 's/demo1/jlink/g' /home/jlink_havano_pro_cpsmddqqvbceafpdpqoknnae/config/odoo.conf
sudo -S docker restart odoo_jlink_havano_pro_cpsmddqqvbceafpdpqoknnae
"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdin.write(password + '\n')
    stdin.flush()
    print("STDOUT:")
    print(stdout.read().decode())
    print("STDERR:")
    print(stderr.read().decode())
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
