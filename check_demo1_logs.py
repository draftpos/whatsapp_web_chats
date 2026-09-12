import paramiko
import sys

def main():
    host = '173.249.39.201'
    user = 'amakoni'
    password = 'Ashley@#$1234'
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=15)
    
    # Run the exact upgrade command
    cmd = "echo 'Ashley@#$1234' | sudo -S docker exec odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae tail -n 200 /var/log/odoo/odoo.log"
    
    print("Running upgrade...")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=900)
    
    for line in stdout:
        sys.stdout.write(line)
        sys.stdout.flush()

    for line in stderr:
        sys.stderr.write(line)
        sys.stderr.flush()
        
    client.close()

if __name__ == '__main__':
    main()
