import paramiko
import sys

def main():
    host = '173.249.39.201'
    user = 'amakoni'
    password = 'Ashley@#$1234'
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=15)
    
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    if query:
        cmd = f"echo 'Ashley@#$1234' | sudo -S docker exec odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae grep -a -C 5 -i '{query}' /var/log/odoo/odoo.log | tail -n 100"
    else:
        cmd = "echo 'Ashley@#$1234' | sudo -S docker exec odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae tail -n 200 /var/log/odoo/odoo.log"
    
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
