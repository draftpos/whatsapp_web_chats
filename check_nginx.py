import paramiko

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)
    stdin, stdout, stderr = ssh.exec_command('sudo -S cat /etc/nginx/sites-enabled/jlink.havano.pro.conf')
    stdin.write(password + '\n')
    stdin.flush()
    print("NGINX CONFIG:")
    print(stdout.read().decode())
    
    stdin, stdout, stderr = ssh.exec_command('sudo -S nginx -t')
    stdin.write(password + '\n')
    stdin.flush()
    print("NGINX TEST:")
    print(stderr.read().decode())
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
