import os
import paramiko
import getpass
import argparse

def run_fix(host, user, container_name, db_name):
    password = os.environ.get('SSH_PASS')
    if not password:
        password = getpass.getpass(f"Enter SSH password for {user}@{host}: ")
    password = password.strip()

    print(f"Connecting to {host} as {user}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=22, username=user, password=password, timeout=15)
        
        print("Uploading fix_messages.py to /tmp...")
        sftp = ssh.open_sftp()
        sftp.put(r'C:\odoo19\addons\whatsapp_web_chats\fix_messages.py', '/tmp/fix_messages.py')
        sftp.close()

        print("Executing fix script inside Odoo container...")
        # Add --no-http so odoo shell doesn't try to bind to port 8069, which is already in use
        cmd = f"(echo '{password}'; cat /tmp/fix_messages.py) | sudo -S docker exec -i {container_name} odoo shell -d {db_name} --no-http"
        
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("STDOUT:")
        print(stdout.read().decode())
        print("STDERR:")
        print(stderr.read().decode())
        
        print("Fix applied successfully!")
    except Exception as e:
        print(f"Execution failed: {e}")
    finally:
        ssh.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="173.249.39.201")
    parser.add_argument("--user", default="amakoni")
    parser.add_argument("--container", default="odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae")
    parser.add_argument("--db", default="demo1_havano_pro_cpsmddqqvbceafpdpqoknnae")
    
    args = parser.parse_args()
    run_fix(args.host, args.user, args.container, args.db)
