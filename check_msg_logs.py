import paramiko
import sys

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        # Grep for these message IDs in the log
        cmd = f"echo '{PASSWORD}' | sudo -S docker logs {CONTAINER} --tail 2000 | grep -E '7013|7014|7015|whatsapp_message'"
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        out = stdout.read().decode('utf-8', 'ignore')
        
        print(out)
    finally:
        client.close()

if __name__ == '__main__':
    main()
